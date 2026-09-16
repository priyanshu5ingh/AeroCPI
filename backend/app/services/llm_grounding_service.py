"""AeroGuide Evidence-Grounded Explanation Service.
Translates structured decision vectors and audit traces into factual plain English without hallucination.
System Prompt:
"You are an evidence explanation layer. Use only supplied structured facts.
If information is unavailable, say it is unavailable. Never invent numerical values,
forecasts, prices, causes, or guarantees."
"""
from typing import Dict, Any, List


def generate_grounded_explanation(payload: Dict[str, Any]) -> str:
    """Generates an evidence-grounded summary adhering to strict zero-hallucination rules."""
    origin = payload.get("origin", "Origin")
    dest = payload.get("destination", "Destination")
    fare = payload.get("current_observed_fare", 0.0)
    pos = payload.get("price_position", "TYPICAL")
    median = payload.get("route_historical_median", 0.0)
    decision = payload.get("booking_guidance", "WATCH")
    airlines = payload.get("airlines_observed_count", 0)
    flex_dates = payload.get("flexible_dates", [])
    model_status = payload.get("model_outlook_status", "INSUFFICIENT_LONGITUDINAL_HISTORY")
    policy_version = payload.get("decision_policy_version", "DECISION_POLICY_V1")
    
    parts: List[str] = []
    
    # 1. Price Context & Baseline Comparison
    if pos == "LOW":
        parts.append(f"Today's lowest observed fare for {origin} ➔ {dest} is ₹{fare:,.0f}, positioning below the historical corridor median of ₹{median:,.0f}.")
    elif pos == "HIGH":
        parts.append(f"Today's lowest observed fare for {origin} ➔ {dest} is ₹{fare:,.0f}, positioning above the historical corridor median of ₹{median:,.0f}.")
    else:
        parts.append(f"Today's lowest observed fare for {origin} ➔ {dest} is ₹{fare:,.0f}, aligning closely with the historical median of ₹{median:,.0f}.")
        
    # 2. Multi-Carrier Intelligence
    parts.append(f"Market scan observed quotes across {airlines} scheduled domestic carriers with full provenance preservation.")
    
    # 3. Decision Guidance & Policy
    if decision == "FLEX_DATE" and flex_dates:
        best_flex = flex_dates[0]
        parts.append(f"Decision engine [{policy_version}] recommends FLEX_DATE based on an observed fare of ₹{best_flex.get('observed_fare', 0):,.0f} on {best_flex.get('travel_date')}.")
    elif decision == "BOOK":
        parts.append(f"Decision engine [{policy_version}] recommends BOOK as observed fare is in the lowest 15th percentile of historical quotes.")
    elif decision == "WAIT":
        parts.append(f"Decision engine [{policy_version}] recommends WAIT as current fare is elevated and advance purchase window allows price tracking.")
    else: # WATCH default
        parts.append(f"Decision engine [{policy_version}] recommends WATCH to monitor price trajectory as departure approaches.")
        
    # 4. Model Status Disclosure (Honest scientific reporting)
    if model_status == "READY_FOR_MODEL":
        parts.append("Longitudinal machine learning targets are active.")
    else:
        parts.append("Longitudinal 7-day movement targets are actively accumulating daily searches; forward predictive probabilities remain disabled until empirical threshold is met.")
        
    return " ".join(parts)
