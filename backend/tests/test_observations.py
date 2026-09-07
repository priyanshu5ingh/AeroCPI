from datetime import date, datetime, timezone

def test_create_and_retrieve_observation(client):
    payload = {
        "source_id": "INDIGO_DIRECT",
        "route_id": "DEL-BOM",
        "carrier_id": "6E",
        "travel_date": "2026-09-20",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "booking_horizon_days": 15,
        "cabin": "ECONOMY",
        "base_fare": 4500.0,
        "taxes": 550.0,
        "mandatory_fees": 350.0,
        "total_fare": 5400.0,
        "currency": "INR",
        "data_status": "OBSERVED",
        "baggage_information": {"cabin_kg": 7, "checkin_kg": 15}
    }

    # Create observation
    response = client.post("/api/v1/observations", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["observation_id"] is not None
    assert data["route_id"] == "DEL-BOM"
    assert data["carrier_id"] == "6E"
    assert data["data_status"] == "OBSERVED"

    # Verify deterministic normalization result attached
    assert data["normalization_result"] is not None
    norm = data["normalization_result"]
    assert norm["normalized_total"] == 5400.0
    assert norm["base_fare"] == 4500.0
    assert norm["taxes"] == 550.0
    assert norm["mandatory_fees"] == 350.0
    assert norm["normalization_version"] == "V1_SIMPLE_SUM"

    # Verify quality result attached
    assert data["quality_result"] is not None
    qual = data["quality_result"]
    assert qual["eligible"] is True
    assert qual["outlier_status"] == "VALID"

    obs_id = data["observation_id"]

    # Retrieve by ID
    get_res = client.get(f"/api/v1/observations/{obs_id}")
    assert get_res.status_code == 200
    retrieved = get_res.json()
    assert retrieved["observation_id"] == obs_id
    assert retrieved["total_fare"] == 5400.0

def test_observation_filtering(client):
    now_iso = datetime.now(timezone.utc).isoformat()
    # Create 3 observations across different routes and carriers
    client.post("/api/v1/observations", json={
        "source_id": "INDIGO_DIRECT",
        "route_id": "DEL-BOM",
        "carrier_id": "6E",
        "travel_date": "2026-09-20",
        "observed_at": now_iso,
        "booking_horizon_days": 7,
        "base_fare": 3000.0,
        "taxes": 400.0,
        "mandatory_fees": 100.0,
        "total_fare": 3500.0,
        "currency": "INR",
        "data_status": "OBSERVED"
    })

    client.post("/api/v1/observations", json={
        "source_id": "AIRINDIA_DIRECT",
        "route_id": "DEL-BOM",
        "carrier_id": "AI",
        "travel_date": "2026-09-20",
        "observed_at": now_iso,
        "booking_horizon_days": 7,
        "base_fare": 3200.0,
        "taxes": 400.0,
        "mandatory_fees": 100.0,
        "total_fare": 3700.0,
        "currency": "INR",
        "data_status": "OBSERVED"
    })

    client.post("/api/v1/observations", json={
        "source_id": "SYNTHETIC_SIMULATOR",
        "route_id": "BLR-DEL",
        "carrier_id": "QP",
        "travel_date": "2026-09-25",
        "observed_at": now_iso,
        "booking_horizon_days": 1,
        "base_fare": 6000.0,
        "taxes": 700.0,
        "mandatory_fees": 300.0,
        "total_fare": 7000.0,
        "currency": "INR",
        "data_status": "SYNTHETIC"
    })

    # Filter by route_id=DEL-BOM
    r1 = client.get("/api/v1/observations?route_id=DEL-BOM")
    assert r1.status_code == 200
    items1 = r1.json()
    assert len(items1) == 2

    # Filter by carrier_id=6E
    r2 = client.get("/api/v1/observations?carrier_id=6E")
    assert r2.status_code == 200
    items2 = r2.json()
    assert len(items2) == 1
    assert items2[0]["carrier_id"] == "6E"

    # Filter by data_status=SYNTHETIC
    r3 = client.get("/api/v1/observations?data_status=SYNTHETIC")
    assert r3.status_code == 200
    items3 = r3.json()
    assert len(items3) == 1
    assert items3[0]["data_status"] == "SYNTHETIC"

    # Filter by booking_horizon_days=1
    r4 = client.get("/api/v1/observations?booking_horizon_days=1")
    assert r4.status_code == 200
    items4 = r4.json()
    assert len(items4) == 1
    assert items4[0]["booking_horizon_days"] == 1
