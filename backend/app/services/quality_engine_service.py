import math
from typing import List, Dict, Tuple
from sqlalchemy.orm import Session
from app.models.observation import Observation
from app.models.quality_result import QualityResult
from app.schemas.common import OutlierStatus, VALID_HORIZONS

class QualityEngineService:
    @staticmethod
    def calculate_median(values: List[float]) -> float:
        if not values:
            return 0.0
        sorted_v = sorted(values)
        n = len(sorted_v)
        mid = n // 2
        if n % 2 == 1:
            return float(sorted_v[mid])
        else:
            return float((sorted_v[mid - 1] + sorted_v[mid]) / 2.0)

    @classmethod
    def compute_mad_scores(cls, prices: List[float]) -> List[float]:
        """
        Calculates Modified Z-Score for a list of prices:
        M_i = 0.6745 * (x_i - median(x)) / MAD
        Handles MAD = 0 safely without crashing.
        """
        n = len(prices)
        if n <= 1:
            return [0.0] * n

        med = cls.calculate_median(prices)
        abs_deviations = [abs(p - med) for p in prices]
        mad = cls.calculate_median(abs_deviations)

        scores = []
        for p in prices:
            diff = p - med
            if abs(diff) < 1e-9:
                scores.append(0.0)
            elif mad > 1e-9:
                score = 0.6745 * diff / mad
                scores.append(score)
            else:
                # MAD is 0 but price differs from median (e.g. extreme single spike in flat group)
                scores.append(999.0 if diff > 0 else -999.0)

        return scores

    @classmethod
    def evaluate_observation_batch(cls, db: Session, observations: List[Observation]) -> List[QualityResult]:
        """
        Evaluates a batch of observations for:
        1. Duplicate detection
        2. Non-negative fares & validity rules
        3. MAD Outlier Detection grouped by (route_id, travel_date, booking_horizon_days, cabin, stop_type)
        Preserves all raw observations intact in the database.
        """
        results: List[QualityResult] = []

        # 1. Deterministic Duplicate Detection & Basic Validity Check
        seen_signatures: set = set()

        # Sort observations deterministically by observation_id
        sorted_obs = sorted(observations, key=lambda o: o.observation_id)

        # Temporary status mapping per observation_id
        obs_status: Dict[str, Tuple[bool, bool, bool, str, Optional[str]]] = {}
        # obs_id -> (eligible, duplicate_flag, missing_flag, outlier_status, exclusion_reason)

        for obs in sorted_obs:
            # Check basic invalidity rules
            base_fare = float(obs.base_fare)
            taxes = float(obs.taxes)
            mandatory_fees = float(obs.mandatory_fees)
            total_fare = float(obs.total_fare)

            if base_fare < 0 or taxes < 0 or mandatory_fees < 0 or total_fare < 0:
                obs_status[obs.observation_id] = (False, False, False, OutlierStatus.EXCLUDED.value, "NEGATIVE_FARE")
                continue

            if obs.booking_horizon_days not in VALID_HORIZONS:
                obs_status[obs.observation_id] = (False, False, False, OutlierStatus.EXCLUDED.value, "INVALID_BOOKING_HORIZON")
                continue

            if obs.currency.upper() != "INR":
                obs_status[obs.observation_id] = (False, False, False, OutlierStatus.EXCLUDED.value, "UNSUPPORTED_CURRENCY")
                continue

            # Duplicate signature
            sig = (
                obs.source_id,
                obs.route_id,
                obs.carrier_id,
                obs.travel_date,
                obs.booking_horizon_days,
                obs.cabin,
                obs.trip_type,
                obs.fare_class,
                obs.stop_type,
                total_fare
            )

            if sig in seen_signatures:
                obs_status[obs.observation_id] = (False, True, False, OutlierStatus.EXCLUDED.value, "DUPLICATE_OBSERVATION")
            else:
                seen_signatures.add(sig)
                obs_status[obs.observation_id] = (True, False, False, OutlierStatus.VALID.value, None)

        # 2. Group non-duplicate observations by (route_id, travel_date, booking_horizon_days, cabin, stop_type) for MAD
        groups: Dict[Tuple[str, str, int, str, str], List[Observation]] = {}
        for obs in sorted_obs:
            el, dup, miss, status, reason = obs_status[obs.observation_id]
            if el and not dup:
                key = (
                    obs.route_id,
                    str(obs.travel_date),
                    obs.booking_horizon_days,
                    obs.cabin,
                    obs.stop_type
                )
                groups.setdefault(key, []).append(obs)

        # 3. Apply MAD outlier score computation per group
        for key, group_obs in groups.items():
            if len(group_obs) < 2:
                continue

            prices = [float(o.total_fare) for o in group_obs]
            mad_scores = cls.compute_mad_scores(prices)

            for obs, score in zip(group_obs, mad_scores):
                if abs(score) > 3.5:
                    # Statistical outlier flagged!
                    # Do NOT delete. Transition status to OUTLIER_FLAGGED or EXCLUDED if extreme (>10 sigma)
                    if abs(score) > 10.0:
                        obs_status[obs.observation_id] = (
                            False, # EXCLUDED observations are NEVER eligible for index computation
                            False,
                            False,
                            OutlierStatus.EXCLUDED.value,
                            f"EXTREME_MAD_OUTLIER_SCORE_{score:.2f}"
                        )
                    else:
                        obs_status[obs.observation_id] = (
                            False, # OUTLIER_FLAGGED observations are NOT eligible for baseline index calculation
                            False,
                            False,
                            OutlierStatus.OUTLIER_FLAGGED.value,
                            f"MAD_OUTLIER_SCORE_{score:.2f}"
                        )

        # Construct QualityResult objects
        for obs in sorted_obs:
            el, dup, miss, status, reason = obs_status[obs.observation_id]
            
            # Save or update QualityResult in database
            existing_qr = db.query(QualityResult).filter(QualityResult.observation_id == obs.observation_id).first()
            if existing_qr:
                existing_qr.eligible = el
                existing_qr.duplicate_flag = dup
                existing_qr.missing_data_flag = miss
                existing_qr.outlier_status = status
                existing_qr.exclusion_reason = reason
                results.append(existing_qr)
            else:
                qr = QualityResult(
                    observation_id=obs.observation_id,
                    eligible=el,
                    duplicate_flag=dup,
                    missing_data_flag=miss,
                    outlier_status=status,
                    exclusion_reason=reason,
                    quality_rule_version="V1_MAD_DUPLICATE_CHECKS"
                )
                db.add(qr)
                results.append(qr)

        db.flush()
        return results
