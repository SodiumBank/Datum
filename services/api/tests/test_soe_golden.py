"""Golden tests for SOE - deterministic SOERun snapshots."""

import json
from pathlib import Path
from services.api.core.soe_engine import run_soe

ROOT = Path(__file__).resolve().parents[4]
EXAMPLES_DIR = ROOT / "examples"


class TestSOEGoldenSpaceFlight:
    """Golden test for Space Flight SOERun."""
    
    def test_space_flight_soe_run_matches_golden(self):
        """Test SOERun for Space Flight matches golden example."""
        # Load golden example
        golden_path = EXAMPLES_DIR / "soe_run.space.flight.json"
        if not golden_path.exists():
            # Create golden if it doesn't exist
            self._create_golden_space_flight()
            return
        
        with open(golden_path, encoding="utf-8") as f:
            golden = json.load(f)
        
        # Generate SOERun
        inputs = {
            "processes": ["SMT", "REFLOW", "CONFORMAL_COAT"],
            "tests_requested": ["FUNCTIONAL", "X_RAY"],
            "materials": ["EPOXY_3M_SCOTCHWELD_2216"],
            "bom_risk_flags": ["LONG_LEAD_EEE", "SINGLE_SOURCE"],
        }
        
        soe_run = run_soe(
            industry_profile="space",
            inputs=inputs,
            hardware_class="flight",
        )
        
        # Compare structure (decision IDs will be deterministic but may differ from example)
        assert soe_run["soe_version"] == golden["soe_version"]
        assert soe_run["industry_profile"] == golden["industry_profile"]
        assert soe_run["hardware_class"] == golden["hardware_class"]
        
        # Compare active packs (order may differ, so use set)
        assert set(soe_run["active_packs"]) == set(golden["active_packs"])
        
        # Compare decision count and actions
        assert len(soe_run["decisions"]) >= len(golden["decisions"]), \
            f"Expected at least {len(golden['decisions'])} decisions, got {len(soe_run['decisions'])}"
        
        # Find matching decisions by object_id and action
        golden_decisions_by_object = {
            (d["object_id"], d["action"]): d for d in golden["decisions"]
        }
        
        for decision in soe_run["decisions"]:
            key = (decision["object_id"], decision["action"])
            if key in golden_decisions_by_object:
                golden_decision = golden_decisions_by_object[key]
                assert decision["object_type"] == golden_decision["object_type"]
                assert decision["enforcement"] == golden_decision["enforcement"]
                assert decision["why"]["rule_id"] == golden_decision["why"]["rule_id"]
                assert decision["why"]["pack_id"] == golden_decision["why"]["pack_id"]
        
        # Compare gates
        assert len(soe_run["gates"]) >= len(golden["gates"])
        
        # Gate status should match
        release_gate = next(
            (g for g in soe_run["gates"] if g["gate_id"] == "GATE-RELEASE"),
            None,
        )
        golden_release_gate = next(
            (g for g in golden["gates"] if g["gate_id"] == "GATE-RELEASE"),
            None,
        )
        if release_gate and golden_release_gate:
            assert release_gate["status"] == golden_release_gate["status"]
    
    def _create_golden_space_flight(self):
        """Create golden example if it doesn't exist."""
        inputs = {
            "processes": ["SMT", "REFLOW", "CONFORMAL_COAT"],
            "tests_requested": ["FUNCTIONAL", "X_RAY"],
            "materials": ["EPOXY_3M_SCOTCHWELD_2216"],
            "bom_risk_flags": ["LONG_LEAD_EEE", "SINGLE_SOURCE"],
        }
        
        soe_run = run_soe(
            industry_profile="space",
            inputs=inputs,
            hardware_class="flight",
        )
        
        EXAMPLES_DIR.mkdir(exist_ok=True)
        golden_path = EXAMPLES_DIR / "soe_run.space.flight.json"
        with open(golden_path, "w", encoding="utf-8") as f:
            json.dump(soe_run, f, indent=2)


class TestSOEGoldenMedical:
    """Golden test for Medical SOERun."""
    
    def test_medical_soe_run_deterministic(self):
        """Test SOERun for Medical is deterministic."""
        inputs = {
            "processes": ["SMT", "REFLOW"],
            "tests_requested": [],
            "materials": [],
            "bom_risk_flags": [],
        }
        
        soe_run1 = run_soe(
            industry_profile="medical",
            inputs=inputs,
            hardware_class=None,
        )
        
        soe_run2 = run_soe(
            industry_profile="medical",
            inputs=inputs,
            hardware_class=None,
        )
        
        # Decision IDs must be deterministic
        decisions1 = sorted(soe_run1["decisions"], key=lambda d: d["id"])
        decisions2 = sorted(soe_run2["decisions"], key=lambda d: d["id"])
        
        assert len(decisions1) == len(decisions2)
        for d1, d2 in zip(decisions1, decisions2):
            assert d1["id"] == d2["id"], "Decision IDs must be deterministic"
            assert d1["action"] == d2["action"]
            assert d1["object_id"] == d2["object_id"]


class TestSOEGoldenAutomotive:
    """Golden test for Automotive SOERun."""
    
    def test_automotive_soe_run_deterministic(self):
        """Test SOERun for Automotive is deterministic."""
        inputs = {
            "processes": ["SMT"],
            "tests_requested": [],
            "materials": [],
            "bom_risk_flags": ["LONG_LEAD"],
        }
        
        soe_run1 = run_soe(
            industry_profile="automotive",
            inputs=inputs,
            hardware_class=None,
        )
        
        soe_run2 = run_soe(
            industry_profile="automotive",
            inputs=inputs,
            hardware_class=None,
        )
        
        # Decision IDs must be deterministic
        decisions1 = sorted(soe_run1["decisions"], key=lambda d: d["id"])
        decisions2 = sorted(soe_run2["decisions"], key=lambda d: d["id"])
        
        assert len(decisions1) == len(decisions2)
        for d1, d2 in zip(decisions1, decisions2):
            assert d1["id"] == d2["id"], "Decision IDs must be deterministic"
            assert d1["action"] == d2["action"]
            assert d1["object_id"] == d2["object_id"]
