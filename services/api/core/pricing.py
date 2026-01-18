"""Deterministic pricing model for Datum quotes."""

import hashlib
from datetime import datetime, timezone
from typing import TypedDict
from services.api.core.supply_chain import analyze_supply_chain_risks, generate_supply_risk_factors
from services.api.core.drc import run_drc_checks


class PricingInputs(TypedDict):
    """Inputs for pricing calculation."""
    gerber_upload_id: str
    bom_upload_id: str | None
    board_metrics: dict | None
    bom_items: list[dict] | None
    gerber_files: list[dict] | None  # Gerber file list for DRC checks
    quantity: int
    assumptions: dict | None


class PricingResult(TypedDict):
    """Result of pricing calculation."""
    lines: list[dict]
    total: float
    lead_time_days: int
    risk_factors: list[dict]


def _sha256_hash(data: str) -> str:
    """Compute SHA256 hash of string data."""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def calculate_inputs_fingerprint(inputs: PricingInputs) -> str:
    """Calculate deterministic fingerprint from inputs."""
    # Create deterministic string representation
    parts = []
    parts.append(f"gerber:{inputs['gerber_upload_id']}")
    if inputs.get("bom_upload_id"):
        parts.append(f"bom:{inputs['bom_upload_id']}")
    if inputs.get("board_metrics"):
        metrics = inputs["board_metrics"]
        parts.append(f"metrics:layers={metrics.get('layer_count', 0)},area={metrics.get('area_mm2', 0)}")
    if inputs.get("bom_items"):
        part_count = len(inputs["bom_items"])
        parts.append(f"bom_parts:{part_count}")
    parts.append(f"qty:{inputs.get('quantity', 1)}")
    if inputs.get("assumptions"):
        # Sort assumptions for determinism
        assump_str = ",".join(f"{k}={v}" for k, v in sorted(inputs["assumptions"].items()))
        parts.append(f"assump:{assump_str}")
    
    fingerprint_str = "|".join(parts)
    return _sha256_hash(fingerprint_str)


def calculate_pcb_fab_cost(
    area_mm2: float | None,
    layer_count: int,
    quantity: int,
    assumptions: dict | None = None,
) -> float:
    """
    Calculate PCB fabrication cost based on board metrics.
    
    This is a placeholder deterministic pricing model.
    Real pricing would use vendor-specific models and current rates.
    """
    # Base cost per board (in USD)
    base_cost_per_board = 5.0  # Base setup cost
    
    # Area-based pricing (cost per mm² per layer)
    area_cost_per_mm2_per_layer = 0.001  # $0.001 per mm² per layer
    
    # Use area if available, otherwise estimate
    if area_mm2 and area_mm2 > 0:
        effective_area = area_mm2
    else:
        # Estimate area (assume 50mm x 50mm = 2500 mm² if unknown)
        effective_area = 2500.0
    
    # Layer cost multiplier (more layers = higher cost)
    layer_multiplier = 1.0 + (layer_count - 2) * 0.3  # 2-layer base, +30% per additional layer
    if layer_count < 2:
        layer_multiplier = 0.8  # Single layer discount
    
    # Area cost
    area_cost = effective_area * layer_count * area_cost_per_mm2_per_layer
    
    # Volume discount (lower per-unit cost at higher quantities)
    if quantity >= 100:
        volume_discount = 0.7  # 30% discount
    elif quantity >= 50:
        volume_discount = 0.8  # 20% discount
    elif quantity >= 10:
        volume_discount = 0.9  # 10% discount
    else:
        volume_discount = 1.0  # No discount
    
    # Per-board cost
    cost_per_board = (base_cost_per_board + area_cost) * layer_multiplier * volume_discount
    
    # Total cost
    total = cost_per_board * quantity
    
    # Apply assumption-based adjustments if present
    if assumptions:
        # IPC class affects cost
        ipc_class = assumptions.get("ipc_class")
        if ipc_class == "CLASS_3A":
            total *= 1.5  # 50% premium for Class 3A
        elif ipc_class == "CLASS_3":
            total *= 1.2  # 20% premium for Class 3
        
        # Controlled impedance adds cost
        if assumptions.get("controlled_impedance"):
            total *= 1.15  # 15% premium
    
    return round(total, 2)


def calculate_assembly_labor_cost(
    bom_items: list[dict] | None,
    quantity: int,
    assumptions: dict | None = None,
) -> float:
    """
    Calculate assembly labor cost based on component count and complexity.
    
    This is a placeholder deterministic pricing model.
    """
    if not bom_items:
        return 0.0
    
    # Count total component placements
    total_placements = sum(item.get("qty", 1) for item in bom_items)
    
    # Base setup cost per board
    setup_cost_per_board = 2.0  # $2 per board setup
    
    # Cost per component placement
    placement_cost = 0.05  # $0.05 per placement
    
    # Assembly labor cost
    labor_cost = (setup_cost_per_board + total_placements * placement_cost) * quantity
    
    # Volume discount
    if quantity >= 100:
        labor_cost *= 0.8  # 20% discount
    elif quantity >= 50:
        labor_cost *= 0.85  # 15% discount
    elif quantity >= 10:
        labor_cost *= 0.9  # 10% discount
    
    # Two-sided assembly adds complexity
    if assumptions:
        assembly_sides = assumptions.get("assembly_sides", ["TOP"])
        if len(assembly_sides) > 1:
            labor_cost *= 1.3  # 30% premium for two-sided assembly
    
    return round(labor_cost, 2)


def calculate_components_cost(
    bom_items: list[dict] | None,
    quantity: int,
) -> float:
    """
    Calculate component cost (placeholder - would normally query vendor APIs).
    
    This is a placeholder deterministic pricing model.
    Real implementation would look up component costs from vendor databases.
    """
    if not bom_items:
        return 0.0
    
    # Placeholder: estimate $0.50 per unique component type
    # In reality, this would query component databases
    unique_components = len(set(item.get("mpn", "") for item in bom_items if item.get("mpn")))
    
    # Estimate cost per component type
    avg_component_cost = 0.50  # Placeholder average cost
    
    # Total component cost
    total = unique_components * avg_component_cost * quantity
    
    return round(total, 2)


def calculate_pricing(inputs: PricingInputs, soe_cost_modifiers: list[dict] | None = None) -> PricingResult:
    """
    Calculate deterministic pricing for a quote.
    
    Args:
        inputs: PricingInputs with board metrics, BOM, quantity, etc.
    
    Returns:
        PricingResult with cost breakdown lines and total.
    """
    board_metrics = inputs.get("board_metrics") or {}
    bom_items = inputs.get("bom_items") or []
    quantity = inputs.get("quantity", 1)
    assumptions = inputs.get("assumptions") or {}
    
    # Extract metrics
    area_mm2 = board_metrics.get("area_mm2")
    layer_count = board_metrics.get("layer_count", 2)
    
    # Calculate cost lines
    lines = []
    
    # PCB Fabrication
    pcb_fab_cost = calculate_pcb_fab_cost(area_mm2, layer_count, quantity, assumptions)
    if pcb_fab_cost > 0:
        lines.append({
            "code": "PCB_FAB",
            "label": "PCB Fabrication",
            "amount": pcb_fab_cost,
        })
    
    # Assembly Labor
    assembly_cost = calculate_assembly_labor_cost(bom_items, quantity, assumptions)
    if assembly_cost > 0:
        lines.append({
            "code": "ASSEMBLY_LABOR",
            "label": "Assembly Labor",
            "amount": assembly_cost,
        })
    
    # Components
    components_cost = calculate_components_cost(bom_items, quantity)
    if components_cost > 0:
        lines.append({
            "code": "COMPONENTS",
            "label": "Components",
            "amount": components_cost,
        })
    
    # Supply Chain Risk Analysis
    supply_risks = analyze_supply_chain_risks(bom_items)
    risk_factors = generate_supply_risk_factors(supply_risks)
    
    # DRC Checks
    gerber_files = inputs.get("gerber_files") or []
    if gerber_files:
        try:
            drc_result = run_drc_checks(inputs["gerber_upload_id"], gerber_files)
            risk_factors.extend(drc_result["risk_factors"])
            
            # Add cost impact from DRC violations
            if drc_result["has_violations"]:
                drc_cost = sum(v.get("impacts", {}).get("cost_delta", 0) for v in drc_result["violations"])
                if drc_cost > 0:
                    lines.append({
                        "code": "OTHER",
                        "label": "DRC Correction / Rework",
                        "amount": round(drc_cost, 2),
                        "notes": "Design rule check violations require rework",
                    })
        except Exception as drc_exc:
            # Don't fail pricing if DRC checks fail
            print(f"Warning: DRC checks failed: {drc_exc}")
    
    # Add SUPPLY_CHAIN_RISK cost line if there are risks
    if supply_risks["has_risk"]:
        supply_risk_cost = supply_risks["estimated_risk_cost"]
        if supply_risk_cost > 0:
            lines.append({
                "code": "SUPPLY_CHAIN_RISK",
                "label": "Supply Chain Risk (Long-Lead / EEE Handling)",
                "amount": round(supply_risk_cost, 2),
                "notes": f"{len(supply_risks['long_lead_parts'])} long-lead parts, {len(supply_risks['eee_parts'])} EEE parts",
            })
    
    # EEE Handling cost (if EEE parts present)
    if supply_risks["eee_parts"]:
        eee_handling_cost = len(supply_risks["eee_parts"]) * 100.0
        if eee_handling_cost > 0:
            lines.append({
                "code": "EEE_HANDLING",
                "label": "EEE Parts Handling",
                "amount": round(eee_handling_cost, 2),
            })
    
    # Inventory carrying cost for long-lead parts
    if supply_risks["long_lead_parts"]:
        inventory_cost = len(supply_risks["long_lead_parts"]) * 50.0
        if inventory_cost > 0:
            lines.append({
                "code": "INVENTORY_CARRY",
                "label": "Inventory Carrying (Long-Lead Parts)",
                "amount": round(inventory_cost, 2),
            })
    
    # NRE (Non-Recurring Engineering) - placeholder
    nre_cost = 0.0
    if quantity < 10:
        nre_cost = 100.0  # One-time setup for small quantities
        lines.append({
            "code": "NRE",
            "label": "Non-Recurring Engineering",
            "amount": nre_cost,
        })
    
    # Margin (20% of total)
    subtotal = sum(line["amount"] for line in lines)
    margin_amount = round(subtotal * 0.2, 2)
    if margin_amount > 0:
        lines.append({
            "code": "MARGIN",
            "label": "Margin",
            "amount": margin_amount,
        })
    
    # Calculate total
    total = round(sum(line["amount"] for line in lines), 2)
    
    # Calculate lead time (placeholder)
    lead_time_days = 10  # Base lead time
    if layer_count > 4:
        lead_time_days += 2  # Extra time for complex boards
    if quantity > 100:
        lead_time_days += 5  # Extra time for large orders
    
    # Adjust lead time for long-lead parts
    if supply_risks["long_lead_parts"]:
        longest_lead_weeks = max(p["lead_time_weeks"] for p in supply_risks["long_lead_parts"])
        longest_lead_days = longest_lead_weeks * 7
        if longest_lead_days > lead_time_days:
            lead_time_days = longest_lead_days
    
    return PricingResult(
        lines=lines,
        total=total,
        lead_time_days=lead_time_days,
        risk_factors=risk_factors,
    )
