from datetime import datetime, timezone

def test_routes_carriers_sources_endpoints(client):
    # Seed an observation to trigger auto-creation of reference entities
    client.post("/api/v1/observations", json={
        "source_id": "INDIGO_DIRECT",
        "route_id": "DEL-BOM",
        "carrier_id": "6E",
        "travel_date": "2026-09-20",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "booking_horizon_days": 7,
        "base_fare": 3000.0,
        "taxes": 400.0,
        "mandatory_fees": 100.0,
        "total_fare": 3500.0,
        "currency": "INR",
        "data_status": "OBSERVED"
    })

    # Test GET /api/v1/routes
    r1 = client.get("/api/v1/routes")
    assert r1.status_code == 200
    routes = r1.json()
    assert len(routes) >= 1
    assert any(r["route_id"] == "DEL-BOM" for r in routes)

    # Test GET /api/v1/carriers
    r2 = client.get("/api/v1/carriers")
    assert r2.status_code == 200
    carriers = r2.json()
    assert len(carriers) >= 1
    assert any(c["carrier_id"] == "6E" for c in carriers)

    # Test GET /api/v1/sources
    r3 = client.get("/api/v1/sources")
    assert r3.status_code == 200
    sources = r3.json()
    assert len(sources) >= 1
    assert any(s["source_id"] == "INDIGO_DIRECT" for s in sources)
