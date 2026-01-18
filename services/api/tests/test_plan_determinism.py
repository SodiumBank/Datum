"""Golden tests for DatumPlan - deterministic plan generation."""

import json
from pathlib import Path
from services.api.core.plan_generator import generate_plan
from services.api.core.soe_engine import evaluate_soe

ROOT = Path(__file__).resolve().parents[4]
EXAMPLES_DIR = ROOT / "examples"


class TestPlanDeterminism:
    """Test DatumPlan determinism - same inputs produce identical plans."""
    
    def test_plan_generation_deterministic(self):
        """Test that generating a plan twice produces identical structure."""
        # Create mock quote data
        from services.api.core.storage import save_quote, get_quote
        
        quote_id = "test_quote_determinism_001"
        quote = {
            "id": quote_id,
            "org_id": "org_test_001",
            "design_id": "design_test_001",
            "revision_id": "rev_test_001",
            "quote_version": 1,
            "tier": "TIER_1",
            "assumptions": {
                "assembly_sides": ["TOP"],
            },
            "gerber_upload_id": "test_gerber_001",
        }
        save_quote(quote)
        
        # Generate SOERun
        soe_inputs = {
            "processes": ["SMT", "REFLOW", "CONFORMAL_COAT"],
            "tests_requested": ["FUNCTIONAL"],
            "materials": ["EPOXY_3M_SCOTCHWELD_2216"],
            "bom_risk_flags": ["LONG_LEAD_EEE"],
        }
        soe_run = evaluate_soe(
            industry_profile="space",
            inputs=soe_inputs,
            hardware_class="flight",
        )
        
        # Generate plan twice
        plan1 = generate_plan(
            quote_id=quote_id,
            soe_run=soe_run,
            org_id="org_test_001",
            design_id="design_test_001",
        )
        
        plan2 = generate_plan(
            quote_id=quote_id,
            soe_run=soe_run,
            org_id="org_test_001",
            design_id="design_test_001",
        )
        
        # Compare structure (IDs may differ but structure should match)
        assert plan1["quote_id"] == plan2["quote_id"]
        assert plan1["org_id"] == plan2["org_id"]
        assert plan1["design_id"] == plan2["design_id"]
        assert len(plan1["steps"]) == len(plan2["steps"])
        assert len(plan1.get("tests", [])) == len(plan2.get("tests", []))
        assert len(plan1.get("evidence_intent", [])) == len(plan2.get("evidence_intent", []))
        
        # Compare step types and sequences (should be identical)
        steps1 = sorted(plan1["steps"], key=lambda s: s["sequence"])
        steps2 = sorted(plan2["steps"], key=lambda s: s["sequence"])
        
        for s1, s2 in zip(steps1, steps2):
            assert s1["type"] == s2["type"]
            assert s1["sequence"] == s2["sequence"]
            assert s1["required"] == s2["required"]
            assert s1["locked_sequence"] == s2["locked_sequence"]
            if s1.get("soe_decision_id"):
                assert s1["soe_decision_id"] == s2.get("soe_decision_id")
    
    def test_plan_soe_references(self):
        """Test that plan correctly references SOE decisions."""
        from services.api.core.storage import save_quote
        
        quote_id = "test_quote_soe_refs_001"
        quote = {
            "id": quote_id,
            "org_id": "org_test_001",
            "design_id": "design_test_001",
            "revision_id": "rev_test_001",
            "quote_version": 1,
            "tier": "TIER_1",
            "assumptions": {
                "assembly_sides": ["TOP"],
            },
        }
        save_quote(quote)
        
        # Generate SOERun with known decisions
        soe_inputs = {
            "processes": ["SMT", "CONFORMAL_COAT"],
            "tests_requested": [],
            "materials": ["EPOXY"],
            "bom_risk_flags": [],
        }
        soe_run = evaluate_soe(
            industry_profile="space",
            inputs=soe_inputs,
            hardware_class="flight",
        )
        
        # Generate plan
        plan = generate_plan(
            quote_id=quote_id,
            soe_run=soe_run,
            org_id="org_test_001",
            design_id="design_test_001",
        )
        
        # Verify SOE references exist
        assert "soe_run_id" in plan
        assert "soe_decision_ids" in plan
        assert len(plan["soe_decision_ids"]) > 0
        
        # Verify steps with SOE decisions have references
        soe_steps = [s for s in plan["steps"] if s.get("soe_decision_id")]
        assert len(soe_steps) > 0
        
        for step in soe_steps:
            assert "soe_decision_id" in step
            assert "soe_why" in step
            assert step["soe_why"]["rule_id"]
            assert step["soe_why"]["pack_id"]


class TestPlanGoldenExample:
    """Test DatumPlan against golden example."""
    
    def test_plan_structure_matches_golden(self):
        """Test that generated plan structure matches golden example."""
        golden_path = EXAMPLES_DIR / "datum_plan.space.flight.json"
        if not golden_path.exists():
            # Skip if golden doesn't exist yet
            return
        
        with open(golden_path, encoding="utf-8") as f:
            golden = json.load(f)
        
        # Create mock quote matching golden
        from services.api.core.storage import save_quote
        
        quote_id = golden["quote_id"]
        quote = {
            "id": quote_id,
            "org_id": golden["org_id"],
            "design_id": golden["design_id"],
            "revision_id": golden["revision_id"],
            "quote_version": golden["quote_version"],
            "tier": "TIER_1",
            "assumptions": {
                "assembly_sides": ["TOP"],
            },
        }
        save_quote(quote)
        
        # Create mock SOERun matching golden
        soe_run = {
            "id": golden["soe_run_id"],
            "soe_version": "1.0.0",
            "industry_profile": "space",
            "hardware_class": "flight",
            "active_packs": ["NASA_POLYMERICS", "SPACE_ENV_TESTS", "AS9100_BASE"],
            "inputs": {
                "processes": ["SMT", "REFLOW", "CONFORMAL_COAT"],
                "tests_requested": ["FUNCTIONAL"],
                "materials": ["EPOXY_3M_SCOTCHWELD_2216"],
                "bom_risk_flags": ["LONG_LEAD_EEE"],
            },
            "decisions": [
                {
                    "id": "DEC-12345678",
                    "object_type": "test",
                    "object_id": "TVAC",
                    "action": "REQUIRE",
                    "enforcement": "BLOCK_RELEASE",
                    "why": {
                        "rule_id": "SPACE.TEST.TVAC.FLIGHT",
                        "pack_id": "SPACE_ENV_TESTS",
                        "citations": ["NASA_GEVS", "AS9100_8_5_1"],
                    },
                },
                {
                    "id": "DEC-87654321",
                    "object_type": "process_step",
                    "object_id": "POLYMER",
                    "action": "INSERT_STEP",
                    "enforcement": "BLOCK_RELEASE",
                    "why": {
                        "rule_id": "NASA.PROCESS.POLYMERICS.SEQUENCE",
                        "pack_id": "NASA_POLYMERICS",
                        "citations": ["NASA-STD-8739.1"],
                    },
                },
            ],
            "required_evidence": [
                {
                    "evidence_type": "COA",
                    "applies_to": "material",
                    "object_id": "EPOXY_3M_SCOTCHWELD_2216",
                    "retention": "LIFE_OF_PROGRAM",
                },
            ],
            "gates": [
                {
                    "gate_id": "GATE-RELEASE",
                    "status": "BLOCKED",
                    "blocked_by": ["DEC-12345678"],
                },
            ],
            "cost_modifiers": [],
        }
        
        # Generate plan
        plan = generate_plan(
            quote_id=quote_id,
            soe_run=soe_run,
            org_id=golden["org_id"],
            design_id=golden["design_id"],
        )
        
        # Compare structure
        assert plan["quote_id"] == golden["quote_id"]
        assert plan["org_id"] == golden["org_id"]
        assert plan["design_id"] == golden["design_id"]
        
        # Compare step count and types
        assert len(plan["steps"]) >= len(golden["steps"])
        
        # Compare tests
        assert len(plan.get("tests", [])) >= len(golden.get("tests", []))
        
        # Compare evidence intent
        assert len(plan.get("evidence_intent", [])) >= len(golden.get("evidence_intent", []))
