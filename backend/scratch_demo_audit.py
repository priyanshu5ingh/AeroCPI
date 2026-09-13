import json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
run_id = "e1c05338-bc7a-4e2f-8b81-f855ca54c3be"

response = client.get(f"/api/v1/index-runs/{run_id}/audit")

print(f"Status Code: {response.status_code}")
data = response.json()

print("\n--- COMPLETE AUDIT JSON RESPONSE ---")
print(json.dumps(data, indent=2))

print("\n--- AUDIT PROVENANCE & REPRODUCIBILITY SUMMARY ---")
print(f"Run ID: {data['audit_scope']['run_id']}")
print(f"Provenace Status: {data['population_audit']['provenance_status']}")
print(f"Canonical Run Fingerprint: {data['reproducibility_audit']['canonical_run_fingerprint']}")
print(f"Manifest SHA-256: {data['reproducibility_audit']['manifest_sha256']}")
print(f"Manifest Present: {data['reproducibility_audit']['manifest_present']}")
print(f"Raw Input Artifacts Available: {data['reproducibility_audit']['raw_input_artifacts_available']}")
print(f"Reproducibility Status: {data['reproducibility_audit']['reproducibility_status']}")
print(f"Trust Evaluation Status: {data['trust_audit']['trust_evaluation_status']}")
print(f"Headline Index Level: {data['run_identity']['headline_index_value']} ({data['run_identity']['headline_horizon_code']})")
print(f"Total Basket Routes: {data['route_audit']['total_basket_routes']}")
print(f"Expected Route Horizon Pairs: {data['route_audit']['expected_route_horizon_pairs']}")
print(f"Calculated Route Horizon Pairs: {data['route_audit']['calculated_route_horizon_pairs']}")
print(f"Unavailable Route Horizon Pairs: {data['route_audit']['unavailable_route_horizon_pairs']}")
print("\nLimitations:")
for lim in data["limitations"]:
    print(f" - {lim}")
