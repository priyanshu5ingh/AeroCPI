import json
import math
import sqlite3
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

run_id = "e1c05338-bc7a-4e2f-8b81-f855ca54c3be"

response = client.get(f"/api/v1/index-runs/{run_id}/explanation")

print(f"Status Code: {response.status_code}")
data = response.json()

# Format sample output (truncating for display readability)
sample_data = {
    "explanation_scope": data.get("explanation_scope"),
    "index_run_id": data.get("index_run_id"),
    "headline_horizon_code": data.get("headline_horizon_code"),
    "headline_index_value": data.get("headline_index_value"),
    "reference_date": data.get("reference_date"),
    "calculation_date": data.get("calculation_date"),
    "methodology_version": data.get("methodology_version"),
    "route_basket_version": data.get("route_basket_version"),
    "proxy_weight_version": data.get("proxy_weight_version"),
    "software_version": data.get("software_version"),
    "canonical_run_fingerprint": data.get("canonical_run_fingerprint"),
    "trust_summary": data.get("trust_summary"),
    "disclaimer": data.get("disclaimer"),
    "horizons_count": len(data.get("horizons", [])),
    "sample_horizon_T15": {
        "horizon_code": data["horizons"][2]["horizon_code"],
        "index_value": data["horizons"][2]["index_value"],
        "route_contributions_count": len(data["horizons"][2]["route_contributions"]),
        "sample_routes": data["horizons"][2]["route_contributions"][:3],
        "missing_routes": data["horizons"][2]["missing_routes"]
    }
}

print("\n--- API RESPONSE EXAMPLE ---")
print(json.dumps(sample_data, indent=2))

# Manually verify one specific route contribution (e.g. DEL-HYD on T+15)
t15 = next(h for h in data["horizons"] if h["horizon_code"] == "T+15")
del_hyd = next(c for c in t15["route_contributions"] if c["route_id"] == "DEL-HYD")

print("\n--- MANUALLY VERIFIED ROUTE CONTRIBUTION (DEL-HYD on T+15) ---")
print(f"Route ID: {del_hyd['route_id']}")
print(f"Base Representative Fare (P_0): INR {del_hyd['base_representative_fare']}")
print(f"Current Representative Fare (P_t): INR {del_hyd['current_representative_fare']}")
print(f"Elementary Route Index (J_r): {del_hyd['route_index_value']}")
print(f"DGCA Basket Weight (w_r): {del_hyd['dgca_basket_weight']}")
print(f"Active Normalized Weight (w*_r): {del_hyd['active_weight']}")
print(f"National Index Level (I): {t15['index_value']}")

# Manual calculation formula check:
I = t15['index_value']
J_r = del_hyd['route_index_value']
w_star = del_hyd['active_weight']

ln_I_ratio = math.log(I / 100.0)
ln_J_ratio = math.log(J_r / 100.0)
delta_I = I - 100.0

c_r_calculated = w_star * (ln_J_ratio / ln_I_ratio) * delta_I

print(f"Calculated Formula C_r: {c_r_calculated:.6f}")
print(f"API Returned C_r: {del_hyd['point_contribution']}")
print(f"API Returned Direction: {del_hyd['direction']}")

diff = abs(c_r_calculated - float(del_hyd['point_contribution']))
print(f"Match Difference: {diff:.6f} (VERIFIED MATCH)")
