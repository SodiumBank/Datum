"""Supply chain risk analysis for BOM parts."""

from typing import TypedDict


class SupplyRisk(TypedDict):
    """Supply chain risk information for a part."""
    mpn: str
    lead_time_weeks: int
    is_long_lead: bool
    is_eee: bool


class SupplyRiskSummary(TypedDict):
    """Summary of supply chain risks."""
    long_lead_parts: list[SupplyRisk]
    eee_parts: list[SupplyRisk]
    has_risk: bool
    estimated_risk_cost: float


def _lookup_lead_time_placeholder(mpn: str, is_eee: bool = False) -> int:
    """
    Placeholder lead time lookup for a part MPN.
    
    In production, this would query vendor APIs or databases.
    For now, returns placeholder values based on heuristics.
    
    Returns lead time in weeks.
    """
    mpn_upper = mpn.upper()
    
    # Placeholder logic: certain patterns indicate longer lead times
    if is_eee:
        # EEE parts typically have longer lead times
        return 32  # 32 weeks for EEE parts
    
    # Common long-lead components
    long_lead_keywords = ["MICROCONTROLLER", "MCU", "FPGA", "DDR", "MEMORY", "OSCILLATOR"]
    for keyword in long_lead_keywords:
        if keyword in mpn_upper:
            return 28  # 28 weeks for certain long-lead components
    
    # Standard lead time (most components)
    return 4  # 4 weeks typical lead time


def analyze_supply_chain_risks(bom_items: list[dict] | None) -> SupplyRiskSummary:
    """
    Analyze supply chain risks from BOM items.
    
    Flags long-lead parts (>26 weeks) and EEE parts.
    Returns summary with risk parts and estimated cost impact.
    """
    if not bom_items:
        return SupplyRiskSummary(
            long_lead_parts=[],
            eee_parts=[],
            has_risk=False,
            estimated_risk_cost=0.0,
        )
    
    long_lead_parts = []
    eee_parts = []
    
    for item in bom_items:
        mpn = item.get("mpn", "")
        if not mpn:
            continue
        
        is_eee = item.get("is_eee", False)
        qty = item.get("qty", 1)
        
        # Lookup lead time (placeholder)
        lead_time_weeks = _lookup_lead_time_placeholder(mpn, is_eee)
        
        # Check if long-lead
        is_long_lead = lead_time_weeks > 26
        
        risk_info: SupplyRisk = {
            "mpn": mpn,
            "lead_time_weeks": lead_time_weeks,
            "is_long_lead": is_long_lead,
            "is_eee": is_eee,
        }
        
        if is_long_lead:
            long_lead_parts.append(risk_info)
        
        if is_eee:
            eee_parts.append(risk_info)
    
    # Calculate estimated risk cost
    # Long-lead parts may require inventory carrying cost
    risk_cost = 0.0
    if long_lead_parts:
        # Estimate $50 per long-lead part type for inventory carrying
        risk_cost = len(long_lead_parts) * 50.0
    
    if eee_parts:
        # EEE handling adds ~$100 per part type
        risk_cost += len(eee_parts) * 100.0
    
    return SupplyRiskSummary(
        long_lead_parts=long_lead_parts,
        eee_parts=eee_parts,
        has_risk=len(long_lead_parts) > 0 or len(eee_parts) > 0,
        estimated_risk_cost=risk_cost,
    )


def generate_supply_risk_factors(supply_risks: SupplyRiskSummary) -> list[dict]:
    """
    Generate risk_factors list from supply chain risks.
    
    Returns list of risk factors formatted per DatumQuote schema.
    """
    risk_factors = []
    
    if supply_risks["long_lead_parts"]:
        long_lead_mpns = [p["mpn"] for p in supply_risks["long_lead_parts"]]
        longest_lead = max(p["lead_time_weeks"] for p in supply_risks["long_lead_parts"])
        
        risk_factors.append({
            "code": "LONG_LEAD_TIME",
            "severity": "HIGH" if longest_lead > 40 else "MEDIUM",
            "summary": f"{len(supply_risks['long_lead_parts'])} part(s) with lead time > 26 weeks",
            "details": f"Parts with long lead times: {', '.join(long_lead_mpns[:5])}{'...' if len(long_lead_mpns) > 5 else ''}",
            "impacts": {
                "lead_time_delta_days": longest_lead * 7,  # Convert weeks to days
                "cost_delta": supply_risks["estimated_risk_cost"],
            },
        })
    
    if supply_risks["eee_parts"]:
        eee_mpns = [p["mpn"] for p in supply_risks["eee_parts"]]
        
        risk_factors.append({
            "code": "EEE_HANDLING_REQUIRED",
            "severity": "MEDIUM",
            "summary": f"{len(supply_risks['eee_parts'])} EEE part(s) requiring special handling",
            "details": f"EEE parts: {', '.join(eee_mpns[:5])}{'...' if len(eee_mpns) > 5 else ''}",
            "impacts": {
                "cost_delta": len(supply_risks["eee_parts"]) * 100.0,
            },
        })
    
    return risk_factors
