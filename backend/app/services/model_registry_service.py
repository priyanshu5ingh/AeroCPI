"""Filesystem registry for AeroGuide production model artifacts."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import pathlib
import shutil
from typing import Any, Dict, Optional

import joblib

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[3]
DEFAULT_MODEL_DIR = PROJECT_ROOT / "data" / "models" / "aeroguide"


class ModelRegistryService:
    """Stores candidate artifacts and one explicitly promoted production model."""

    @classmethod
    def model_dir(cls) -> pathlib.Path:
        path = pathlib.Path(os.getenv("AEROCPI_MODEL_DIR", str(DEFAULT_MODEL_DIR)))
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def sha256_file(path: pathlib.Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @classmethod
    def save_candidate(cls, bundle: Dict[str, Any], manifest: Dict[str, Any], model_version: str) -> Dict[str, Any]:
        model_dir = cls.model_dir()
        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        stem = f"{model_version}_{stamp}"
        artifact_path = model_dir / f"{stem}.joblib"
        manifest_path = model_dir / f"{stem}.json"

        joblib.dump(bundle, artifact_path, compress=3)
        artifact_sha = cls.sha256_file(artifact_path)
        manifest_data = dict(manifest)
        manifest_data.update({
            "model_version": model_version,
            "artifact_sha256": artifact_sha,
            "artifact_path": str(artifact_path),
            "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "status": manifest_data.get("status", "CANDIDATE"),
        })
        manifest_path.write_text(json.dumps(manifest_data, indent=2, sort_keys=True), encoding="utf-8")

        return {
            "artifact_path": str(artifact_path),
            "manifest_path": str(manifest_path),
            "artifact_sha256": artifact_sha,
            "manifest": manifest_data,
        }

    @classmethod
    def update_candidate_manifest(cls, manifest_path: str, manifest_data: Dict[str, Any]) -> None:
        path = pathlib.Path(manifest_path)
        if path.exists():
            path.write_text(json.dumps(manifest_data, indent=2, sort_keys=True), encoding="utf-8")

    @classmethod
    def promote(cls, candidate: Dict[str, Any]) -> Dict[str, Any]:
        model_dir = cls.model_dir()
        source = pathlib.Path(candidate["artifact_path"])
        source_manifest = pathlib.Path(candidate["manifest_path"])
        production = model_dir / "production.joblib"
        production_manifest = model_dir / "production.json"

        shutil.copy2(source, production)
        manifest_data = json.loads(source_manifest.read_text(encoding="utf-8"))
        manifest_data["status"] = "PROMOTED"
        manifest_data["promoted_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
        manifest_data["artifact_path"] = str(production)
        production_manifest.write_text(json.dumps(manifest_data, indent=2, sort_keys=True), encoding="utf-8")

        return {
            "artifact_path": str(production),
            "manifest_path": str(production_manifest),
            "manifest": manifest_data,
        }

    @classmethod
    def load_production(cls) -> Optional[Dict[str, Any]]:
        model_dir = cls.model_dir()
        artifact = model_dir / "production.joblib"
        manifest = model_dir / "production.json"
        if not artifact.exists() or not manifest.exists():
            return None
        manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
        if manifest_data.get("status") != "PROMOTED":
            return None
        return {"bundle": joblib.load(artifact), "manifest": manifest_data}
