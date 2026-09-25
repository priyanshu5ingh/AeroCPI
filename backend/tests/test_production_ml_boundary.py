from app.services.forecast_dataset_service import classify_direction


def test_target_direction_threshold():
    assert classify_direction(2.01) == "UP"
    assert classify_direction(-2.01) == "DOWN"
    assert classify_direction(2.0) == "STABLE"
    assert classify_direction(-2.0) == "STABLE"
