"""AeroGuide Evidence-Grounded LLM Explanation Service.
Translates structured decision vectors into plain English without hallucination.
Never invents prices, savings, or guaranteed future movements.
"""
from typing import Dict, Any

def generate_grounded_explanation(payload: Dict[str, Any]) -> str:
    origin = payload.get("origin", "Origin")
    dest = payload.get("destination", "Destination")
    fare = payload.get("current_observed_fare", 0.0)
    pos = payload.get("price_position", "TYPICAL")
    median = payload.get("route_historical_median", 0.0)
    decision = payload.get("booking_guidance", "WATCH")
    airlines = payload.get("airlines_observed_count", 0)
    flex_dates = payload.get("flexible_dates", [])
    
    parts = []
    
    # 1. Price Context
    if pos == "LOW":
        parts.append(f"Today's lowest observed fare for {origin} → {dest} is ₹{fare:,.0f}, which is below the route's historical median of ₹{median:,.0f}.")
    elif pos == "HIGH":
        parts.append(f"Today's lowest observed fare for {origin} → {dest} is ₹{fare:,.0f}, which is higher than the route's typical median of ₹{median:,.0f}.")
    else:
        parts.append(f"Today's observed fare for {origin} → {dest} is ₹{fare:,.0f}, aligning with typical historical levels (median: ₹{median:,.0f}).")
        
    # 2. Market Coverage
    parts.append(f"Offers were observed across {airlines} carriers via search aggregator adapters, while direct NDC portals (IndiGo, Air India) operate under partner access constraints.")
    
    # 3. Model & Decision Status
    if decision == "FLEX_DATE" and flex_dates:
        best_flex = flex_dates[0]
        parts.append(f"AeroGuide recommends exploring flexible dates because an observed fare of ₹{best_flex['observed_fare']:,.0f} was recorded on {best_flex['travel_date']}.")
    else:
        parts.append("Because longitudinal 7-day target pairs are currently in active collection, the machine learning outlook is marked as monitoring. AeroGuide recommends WATCH to observe market movements as your departure approaches.")
        
    return " ".join(parts)
