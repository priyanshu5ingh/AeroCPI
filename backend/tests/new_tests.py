# =============================================================================
# 20. OBSERVATION ACCOUNTING (AUDIT 1)
# =============================================================================

def test_20_observation_accounting_reconciliation(db_session):
    """
    Proves the persisted manifest's observation counts reconcile exactly to the sum 
    of the filtered underlying observation population (only reference and calculation dates).
    """
    seed_test_routes(db_session)
    ref_date = dt.date(2026, 9, 10)
    cur_date = dt.date(2026, 9, 12)
    other_date = dt.date(2026, 9, 11)

    # 2 on ref, 3 on cur, 5 on other
    db_session.add(create_obs("O_REF_1", "SRC_GOOGLE", 5000.00, route_id="DEL-BOM", collection_date=ref_date, horizon=15))
    db_session.add(create_obs("O_REF_2", "SRC_GOOGLE", 5000.00, route_id="DEL-BLR", collection_date=ref_date, horizon=15))
    db_session.add(create_obs("O_CUR_1", "SRC_GOOGLE", 5500.00, route_id="DEL-BOM", collection_date=cur_date, horizon=15))
    db_session.add(create_obs("O_CUR_2", "SRC_GOOGLE", 5500.00, route_id="DEL-BLR", collection_date=cur_date, horizon=15))
    db_session.add(create_obs("O_CUR_3", "SRC_GOOGLE", 5500.00, route_id="DEL-HYD", collection_date=cur_date, horizon=15))
    for i in range(5):
        db_session.add(create_obs(f"O_OTH_{i}", "SRC_GOOGLE", 6000.00, route_id="DEL-BOM", collection_date=other_date, horizon=15))
    db_session.commit()

    run, _, _ = StatisticalIndexEngineService.execute_statistical_index_run(
        db=db_session,
        reference_date=ref_date,
        calculation_date=cur_date,
        cabin="ECONOMY"
    )
    
    assert run.eligible_observations == 5 # 2 + 3
    assert run.calculation_manifest["observations"]["reference_date_count"] == 2
    assert run.calculation_manifest["observations"]["calculation_date_count"] == 3
    assert run.calculation_manifest["observations"]["total_eligible_used"] == 5


# =============================================================================
# 21. MATCHED-SAMPLE EQUALITY INVARIANT (AUDIT 2)
# =============================================================================

def test_21_matched_sample_equality_invariant(db_session):
    """
    Proves that when R_active == R_matched, primary_index == matched_sample_index
    within numerical tolerance.
    """
    seed_test_routes(db_session)
    ref_date = dt.date(2026, 9, 10)
    cur_date = dt.date(2026, 9, 12)

    # Add 2 routes for ref and cur dates
    db_session.add(create_obs("O1_REF", "SRC_GOOGLE", 5000.00, route_id="DEL-BOM", collection_date=ref_date, horizon=45))
    db_session.add(create_obs("O2_REF", "SRC_GOOGLE", 4000.00, route_id="DEL-BLR", collection_date=ref_date, horizon=45))
    
    db_session.add(create_obs("O1_CUR", "SRC_GOOGLE", 5500.00, route_id="DEL-BOM", collection_date=cur_date, horizon=45)) # 110.0 index
    db_session.add(create_obs("O2_CUR", "SRC_GOOGLE", 4800.00, route_id="DEL-BLR", collection_date=cur_date, horizon=45)) # 120.0 index
    
    db_session.commit()

    run, horizons, _ = StatisticalIndexEngineService.execute_statistical_index_run(
        db=db_session,
        reference_date=ref_date,
        calculation_date=cur_date,
        cabin="ECONOMY"
    )
    
    h45 = next(h for h in horizons if h.horizon_code == "T+45")
    
    # R_active and R_matched should both be 2
    assert h45.diagnostic_matched_sample_routes == 2
    assert abs(h45.diagnostic_matched_sample_index - h45.index_value) < 1e-4
    assert h45.diagnostic_matched_sample_index > 0
