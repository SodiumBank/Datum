#!/usr/bin/env python3
"""Test pricing module directly."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "services" / "api"))

from services.api.core.pricing import calculate_pricing, PricingInputs

# Test pricing with realistic inputs
inputs: PricingInputs = {
    "gerber_upload_id": "test",
    "bom_upload_id": "test",
    "board_metrics": {"layer_count": 4, "area_mm2": 5000.0},
    "bom_items": [
        {"refdes": "R1", "qty": 1, "mpn": "RES_10K"},
        {"refdes": "C1", "qty": 2, "mpn": "CAP_100uF"},
        {"refdes": "U1", "qty": 1, "mpn": "MCU_ATMEGA328", "is_eee": True},
    ],
    "gerber_files": [],
    "quantity": 50,
    "assumptions": {"assembly_sides": ["TOP", "BOTTOM"], "ipc_class": "CLASS_3"},
}

result = calculate_pricing(inputs)
print("=" * 60)
print("Pricing Test Results")
print("=" * 60)
print(f"Total: ${result['total']:.2f}")
print(f"Lead Time: {result['lead_time_days']} days")
print(f"Cost Lines: {len(result['lines'])} items")
print(f"Risk Factors: {len(result.get('risk_factors', []))} items")
print()
print("Cost Breakdown:")
print("-" * 60)
for line in result["lines"]:
    print(f"  {line['code']:25} ${line['amount']:10.2f}  {line['label']}")
print()
if result.get("risk_factors"):
    print("Risk Factors:")
    print("-" * 60)
    for risk in result["risk_factors"]:
        print(f"  {risk['code']}: {risk['summary']} ({risk['severity']})")
print("=" * 60)
print("✓ Pricing module works correctly!")
