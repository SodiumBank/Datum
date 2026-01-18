#!/usr/bin/env python3
"""Quick validation tests for Datum API."""

import sys
from pathlib import Path

# Add services/api to path
sys.path.insert(0, str(Path(__file__).parent / "services" / "api"))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    try:
        from services.api.main import app
        print("✓ main.py imports OK")
        
        from services.api.core.storage import save_gerber_zip, get_board_metrics
        print("✓ storage.py imports OK")
        
        from services.api.core.bom_parser import parse_bom
        print("✓ bom_parser.py imports OK")
        
        from services.api.core.gerber_parser import extract_board_metrics
        print("✓ gerber_parser.py imports OK")
        
        from services.api.core.pricing import calculate_pricing
        print("✓ pricing.py imports OK")
        
        from services.api.core.supply_chain import analyze_supply_chain_risks
        print("✓ supply_chain.py imports OK")
        
        from services.api.core.drc import run_drc_checks
        print("✓ drc.py imports OK")
        
        from services.api.core.schema_validation import validate_schema
        print("✓ schema_validation.py imports OK")
        
        from services.api.routers import uploads, quotes, auth, health
        print("✓ routers import OK")
        
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_schema_validation():
    """Test schema validation."""
    print("\nTesting schema validation...")
    try:
        from services.api.core.schema_validation import validate_schema
        
        # Test with valid quote data
        test_quote = {
            "id": "quote_test_001",
            "org_id": "org_test_001",
            "design_id": "design_test_001",
            "tier": "TIER_1",
            "revision_id": "rev_test_001",
            "quote_version": 1,
            "inputs_fingerprint": "a" * 64,
            "lead_time_days": 10,
            "cost_breakdown": {
                "currency": "USD",
                "total": 1000.0,
                "lines": [
                    {"code": "PCB_FAB", "label": "PCB Fabrication", "amount": 300.0}
                ]
            },
            "risk_factors": [],
            "assumptions": {"assembly_sides": ["TOP"]},
            "status": "ESTIMATED",
            "created_at": "2026-01-17T00:00:00Z"
        }
        
        validate_schema(test_quote, "datum_quote.schema.json")
        print("✓ Schema validation works")
        return True
    except Exception as e:
        print(f"✗ Schema validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pricing_logic():
    """Test pricing calculation logic."""
    print("\nTesting pricing logic...")
    try:
        from services.api.core.pricing import calculate_pricing, PricingInputs
        
        test_inputs: PricingInputs = {
            "gerber_upload_id": "test_gerb",
            "bom_upload_id": "test_bom",
            "board_metrics": {
                "layer_count": 2,
                "area_mm2": 2500.0,
                "width_mm": 50.0,
                "height_mm": 50.0,
            },
            "bom_items": [
                {"refdes": "R1", "qty": 1, "mpn": "RES_10K"}
            ],
            "gerber_files": [],
            "quantity": 10,
            "assumptions": {"assembly_sides": ["TOP"]},
        }
        
        result = calculate_pricing(test_inputs)
        assert "lines" in result
        assert "total" in result
        assert "lead_time_days" in result
        assert "risk_factors" in result
        assert result["total"] > 0
        print(f"✓ Pricing calculation works (total: ${result['total']:.2f})")
        return True
    except Exception as e:
        print(f"✗ Pricing calculation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all quick tests."""
    print("=" * 50)
    print("Datum API - Quick Validation Tests")
    print("=" * 50)
    
    results = []
    results.append(("Imports", test_imports()))
    results.append(("Schema Validation", test_schema_validation()))
    results.append(("Pricing Logic", test_pricing_logic()))
    
    print("\n" + "=" * 50)
    print("Results:")
    print("=" * 50)
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{name:25} {status}")
    
    all_passed = all(passed for _, passed in results)
    if all_passed:
        print("\n✓ All quick tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
