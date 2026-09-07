def test_create_and_get_virtual_trip(client):
    payload = {
        "origin": "DEL",
        "destination": "BOM",
        "travel_date": "2026-09-25",
        "passengers": 1,
        "cabin": "ECONOMY",
        "trip_type": "ONE_WAY",
        "booking_horizon": 15,
        "baggage_requirement": "15KG_CHECKIN_7KG_CARRYON",
        "eligible_stop_type": "NON_STOP"
    }

    response = client.post("/api/v1/virtual-trips", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["spec_id"] is not None
    assert data["origin"] == "DEL"
    assert data["destination"] == "BOM"
    assert data["booking_horizon"] == 15

    spec_id = data["spec_id"]
    get_res = client.get(f"/api/v1/virtual-trips/{spec_id}")
    assert get_res.status_code == 200
    retrieved = get_res.json()
    assert retrieved["spec_id"] == spec_id
    assert retrieved["baggage_requirement"] == "15KG_CHECKIN_7KG_CARRYON"
