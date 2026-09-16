"""AeroGuide Verifiable Decision Trace Service.
Constructs an 8-stage transparent evidence chain linking inputs to decision verdicts.
Zero manufactured evidence.
"""
from typing import List, Dict, Any, Optional
from app.schemas.aeroguide import DecisionTraceNode

def build_decision_trace(
    origin: str,
    destination: str,
    travel_date: str,
    current_fare: float,
    route_median: float,
    route_min: float,
    route_max: float,
    days_to_departure: int,
    airline_count: int,
    source_count: int,
    flexible_options_count: int,
    decision_policy_version: str,
    decision: str,
    reason: str,
    readiness: Optional[Dict[str, Any]] = None
) -> List[DecisionTraceNode]:
    rd = readiness or {
        "dataset_classification": "INSUFFICIENT_LONGITUDINAL_HISTORY",
        "model_training_status": "DISABLED",
        "seven_day_target_pairs": 0,
        "fourteen_day_target_pairs": 0,
        "effective_forecasting_examples": 0
    }
    
    seven_d_cnt = rd.get("seven_day_target_pairs", 0)
    effective_cnt = rd.get("effective_forecasting_examples", 0)
    classification = rd.get("dataset_classification", "INSUFFICIENT_LONGITUDINAL_HISTORY")
    model_status = rd.get("model_training_status", "DISABLED")
    is_ready = seven_d_cnt >= 7
    forecast_availability = "AVAILABLE" if is_ready else "NOT_AVAILABLE"

    nodes = [
        DecisionTraceNode(
            stage_number=1,
            stage_name="User Context & Standardized Request",
            status="VERIFIED",
            evidence_summary=f"Search request: {origin} -> {destination} on {travel_date} (1 Adult, Economy, INR).",
            structured_payload={"origin": origin, "destination": destination, "travel_date": travel_date, "adults": 1}
        ),
        DecisionTraceNode(
            stage_number=2,
            stage_name="Current Market Observation",
            status="OBSERVED",
            evidence_summary=f"Lowest observed fare across live search aggregators is ₹{current_fare:,.0f}.",
            structured_payload={"current_fare": current_fare, "currency": "INR"}
        ),
        DecisionTraceNode(
            stage_number=3,
            stage_name="Route Historical Distribution",
            status="CALCULATED",
            evidence_summary=f"Historical median on {origin}-{destination} is ₹{route_median:,.0f} (Range: ₹{route_min:,.0f} - ₹{route_max:,.0f}).",
            structured_payload={"median": route_median, "min": route_min, "max": route_max}
        ),
        DecisionTraceNode(
            stage_number=4,
            stage_name="Advance Purchase Horizon Lead Time",
            status="VERIFIED",
            evidence_summary=f"Lead time: {days_to_departure} days to departure.",
            structured_payload={"days_to_departure": days_to_departure}
        ),
        DecisionTraceNode(
            stage_number=5,
            stage_name="Multi-Carrier Alternatives & NDC Capabilities",
            status="VERIFIED",
            evidence_summary=f"Observed across {airline_count} carriers and {source_count} distribution sources. NDC portals documented with partner-controlled access.",
            structured_payload={"airlines_observed": airline_count, "sources_available": source_count}
        ),
        DecisionTraceNode(
            stage_number=6,
            stage_name="Flexible Date Window Evaluation",
            status="EVALUATED",
            evidence_summary=f"Evaluated +/- 2 days window. Found {flexible_options_count} observed candidate flights.",
            structured_payload={"flexible_options_found": flexible_options_count}
        ),
        DecisionTraceNode(
            stage_number=7,
            stage_name="Longitudinal Evidence & Model Safety Check",
            status=classification,
            evidence_summary=f"7-day target pairs: {seven_d_cnt}. Effective forecasting examples: {effective_cnt}. Forecast: {forecast_availability}. Reason: {classification}. Zero synthetic predictions manufactured.",
            structured_payload={
                "status": classification,
                "seven_day_target_pairs": seven_d_cnt,
                "fourteen_day_target_pairs": rd.get("fourteen_day_target_pairs", 0),
                "effective_forecasting_examples": effective_cnt,
                "forecast": forecast_availability,
                "reason": classification,
                "model_training_status": model_status
            }
        ),
        DecisionTraceNode(
            stage_number=8,
            stage_name="Deterministic Policy Verdict",
            status="DECIDED",
            evidence_summary=f"Policy [{decision_policy_version}] rendered: {decision} — {reason}",
            structured_payload={"policy_version": decision_policy_version, "decision": decision, "reason": reason}
        )
    ]
    return nodes
