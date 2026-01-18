"""Unit tests for SOE (Standards Overlay Engine)."""

import pytest
from services.api.core.soe_engine import (
    evaluate_soe,
    _evaluate_rule_expression,
    _load_industry_profile,
    _load_standards_pack,
    generate_why_explanation,
)
from services.api.core.soe_audit import (
    generate_deterministic_decision_id,
    export_audit_manifest,
    create_decision_log,
)
from services.api.core.schema_validation import validate_schema


class TestRuleExpressionEvaluator:
    """Test rule expression evaluation."""
    
    def test_equals_operator(self):
        """Test equals operator."""
        expr = {
            "field": "industry_profile",
            "operator": "equals",
            "value": "space",
        }
        context = {"industry_profile": "space"}
        assert _evaluate_rule_expression(expr, context) is True
        
        context = {"industry_profile": "medical"}
        assert _evaluate_rule_expression(expr, context) is False
    
    def test_contains_operator(self):
        """Test contains operator."""
        expr = {
            "field": "inputs.processes",
            "operator": "contains",
            "value": "CONFORMAL_COAT",
        }
        context = {
            "inputs": {
                "processes": ["SMT", "CONFORMAL_COAT", "REFLOW"],
            },
        }
        assert _evaluate_rule_expression(expr, context) is True
        
        context = {
            "inputs": {
                "processes": ["SMT", "REFLOW"],
            },
        }
        assert _evaluate_rule_expression(expr, context) is False
    
    def test_in_operator(self):
        """Test in operator."""
        expr = {
            "field": "hardware_class",
            "operator": "in",
            "value": ["flight", "protoflight"],
        }
        context = {"hardware_class": "flight"}
        assert _evaluate_rule_expression(expr, context) is True
        
        context = {"hardware_class": "test"}
        assert _evaluate_rule_expression(expr, context) is False
    
    def test_gt_operator(self):
        """Test greater than operator."""
        expr = {
            "field": "inputs.quantity",
            "operator": "gt",
            "value": 10,
        }
        context = {"inputs": {"quantity": 20}}
        assert _evaluate_rule_expression(expr, context) is True
        
        context = {"inputs": {"quantity": 5}}
        assert _evaluate_rule_expression(expr, context) is False
    
    def test_exists_operator(self):
        """Test exists operator."""
        expr = {
            "field": "hardware_class",
            "operator": "exists",
            "value": None,
        }
        context = {"hardware_class": "flight"}
        assert _evaluate_rule_expression(expr, context) is True
        
        context = {}
        assert _evaluate_rule_expression(expr, context) is False
        
        context = {"hardware_class": None}
        assert _evaluate_rule_expression(expr, context) is False
    
    def test_not_exists_operator(self):
        """Test not_exists operator."""
        expr = {
            "field": "hardware_class",
            "operator": "not_exists",
            "value": None,
        }
        context = {}
        assert _evaluate_rule_expression(expr, context) is True
        
        context = {"hardware_class": "flight"}
        assert _evaluate_rule_expression(expr, context) is False
    
    def test_all_composition(self):
        """Test all composition."""
        expr = {
            "all": [
                {
                    "field": "industry_profile",
                    "operator": "equals",
                    "value": "space",
                },
                {
                    "field": "hardware_class",
                    "operator": "equals",
                    "value": "flight",
                },
            ],
        }
        context = {
            "industry_profile": "space",
            "hardware_class": "flight",
        }
        assert _evaluate_rule_expression(expr, context) is True
        
        context = {
            "industry_profile": "space",
            "hardware_class": "test",
        }
        assert _evaluate_rule_expression(expr, context) is False
    
    def test_any_composition(self):
        """Test any composition."""
        expr = {
            "any": [
                {
                    "field": "hardware_class",
                    "operator": "equals",
                    "value": "flight",
                },
                {
                    "field": "hardware_class",
                    "operator": "equals",
                    "value": "protoflight",
                },
            ],
        }
        context = {"hardware_class": "flight"}
        assert _evaluate_rule_expression(expr, context) is True
        
        context = {"hardware_class": "test"}
        assert _evaluate_rule_expression(expr, context) is False
    
    def test_none_composition(self):
        """Test none composition."""
        expr = {
            "none": [
                {
                    "field": "hardware_class",
                    "operator": "equals",
                    "value": "test",
                },
            ],
        }
        context = {"hardware_class": "flight"}
        assert _evaluate_rule_expression(expr, context) is True
        
        context = {"hardware_class": "test"}
        assert _evaluate_rule_expression(expr, context) is False
    
    def test_nested_composition(self):
        """Test nested composition."""
        expr = {
            "all": [
                {
                    "field": "industry_profile",
                    "operator": "equals",
                    "value": "space",
                },
                {
                    "any": [
                        {
                            "field": "hardware_class",
                            "operator": "equals",
                            "value": "flight",
                        },
                        {
                            "field": "hardware_class",
                            "operator": "equals",
                            "value": "protoflight",
                        },
                    ],
                },
            ],
        }
        context = {
            "industry_profile": "space",
            "hardware_class": "flight",
        }
        assert _evaluate_rule_expression(expr, context) is True
        
        context = {
            "industry_profile": "space",
            "hardware_class": "test",
        }
        assert _evaluate_rule_expression(expr, context) is False


class TestIndustryProfileLoader:
    """Test industry profile loading."""
    
    def test_load_space_profile(self):
        """Test loading space industry profile."""
        profile = _load_industry_profile("space")
        assert profile["industry_profile"] == "space"
        assert profile["risk_posture"] == "max_rigor"
        assert "AS9100_BASE" in profile["default_packs"]
        assert "NASA_POLYMERICS" in profile["default_packs"]
    
    def test_load_medical_profile(self):
        """Test loading medical industry profile."""
        profile = _load_industry_profile("medical")
        assert profile["industry_profile"] == "medical"
        assert profile["risk_posture"] == "high"
        assert "ISO13485_BASE" in profile["default_packs"]
    
    def test_load_nonexistent_profile(self):
        """Test loading nonexistent profile raises error."""
        with pytest.raises(ValueError, match="Industry profile not found"):
            _load_industry_profile("nonexistent")


class TestStandardsPackLoader:
    """Test standards pack loading."""
    
    def test_load_space_env_tests_pack(self):
        """Test loading SPACE_ENV_TESTS pack."""
        pack = _load_standards_pack("SPACE_ENV_TESTS")
        assert pack["pack_id"] == "SPACE_ENV_TESTS"
        assert pack["name"] == "Space Environmental Tests"
        assert len(pack.get("rules", [])) > 0
    
    def test_load_nasa_polymerics_pack(self):
        """Test loading NASA_POLYMERICS pack."""
        pack = _load_standards_pack("NASA_POLYMERICS")
        assert pack["pack_id"] == "NASA_POLYMERICS"
        assert pack["name"] == "NASA Polymerics Control"
        assert len(pack.get("rules", [])) > 0
    
    def test_load_nonexistent_pack(self):
        """Test loading nonexistent pack raises error."""
        with pytest.raises(ValueError, match="Standards pack not found"):
            _load_standards_pack("NONEXISTENT_PACK")


class TestSOERuntime:
    """Test SOE runtime evaluation."""
    
    def test_evaluate_space_flight(self):
        """Test SOE evaluation for space flight hardware."""
        inputs = {
            "processes": ["SMT", "CONFORMAL_COAT"],
            "tests_requested": [],
            "materials": ["EPOXY_3M_SCOTCHWELD_2216"],
            "bom_risk_flags": [],
        }
        
        soe_run = evaluate_soe(
            industry_profile="space",
            inputs=inputs,
            hardware_class="flight",
        )
        
        # Validate SOERun structure
        assert soe_run["soe_version"] == "1.0.0"
        assert soe_run["industry_profile"] == "space"
        assert soe_run["hardware_class"] == "flight"
        assert "SPACE_ENV_TESTS" in soe_run["active_packs"]
        assert isinstance(soe_run["decisions"], list)
        assert isinstance(soe_run["gates"], list)
        assert isinstance(soe_run["cost_modifiers"], list)
        
        # Validate schema
        validate_schema(soe_run, "soe_run.schema.json")
        
        # Should have TVAC requirement for flight hardware
        tvac_decisions = [
            d for d in soe_run["decisions"]
            if d.get("object_id") == "TVAC"
        ]
        assert len(tvac_decisions) > 0
    
    def test_evaluate_deterministic(self):
        """Test SOE evaluation is deterministic."""
        inputs = {
            "processes": ["SMT", "CONFORMAL_COAT"],
            "tests_requested": [],
            "materials": ["EPOXY_3M_SCOTCHWELD_2216"],
            "bom_risk_flags": [],
        }
        
        soe_run1 = evaluate_soe(
            industry_profile="space",
            inputs=inputs,
            hardware_class="flight",
        )
        
        soe_run2 = evaluate_soe(
            industry_profile="space",
            inputs=inputs,
            hardware_class="flight",
        )
        
        # Decision IDs should be deterministic
        decisions1 = sorted(soe_run1["decisions"], key=lambda d: d["id"])
        decisions2 = sorted(soe_run2["decisions"], key=lambda d: d["id"])
        
        assert len(decisions1) == len(decisions2)
        for d1, d2 in zip(decisions1, decisions2):
            assert d1["id"] == d2["id"]
            assert d1["action"] == d2["action"]
            assert d1["object_id"] == d2["object_id"]
    
    def test_gate_blocking(self):
        """Test gate blocking when rules specify BLOCK_RELEASE."""
        inputs = {
            "processes": ["SMT", "CONFORMAL_COAT"],
            "tests_requested": [],
            "materials": ["EPOXY_3M_SCOTCHWELD_2216"],
            "bom_risk_flags": [],
        }
        
        soe_run = evaluate_soe(
            industry_profile="space",
            inputs=inputs,
            hardware_class="flight",
        )
        
        # Check gates
        release_gate = next(
            (g for g in soe_run["gates"] if g["gate_id"] == "GATE-RELEASE"),
            None,
        )
        assert release_gate is not None
        
        # Should be blocked if there are BLOCK_RELEASE decisions
        blocking_decisions = [
            d for d in soe_run["decisions"]
            if d.get("enforcement") == "BLOCK_RELEASE"
        ]
        if blocking_decisions:
            assert release_gate["status"] == "blocked"
            assert len(release_gate["blocked_by"]) > 0
        else:
            assert release_gate["status"] == "open"


class TestDecisionMaterialization:
    """Test decision materialization."""
    
    def test_decision_deterministic_ids(self):
        """Test decisions have deterministic IDs."""
        inputs = {
            "processes": ["SMT"],
            "tests_requested": [],
            "materials": [],
            "bom_risk_flags": [],
        }
        
        soe_run = evaluate_soe(
            industry_profile="space",
            inputs=inputs,
            hardware_class="flight",
        )
        
        # All decisions should have valid IDs
        for decision in soe_run["decisions"]:
            assert decision["id"].startswith("DEC-")
            assert "why" in decision
            assert "rule_id" in decision["why"]
            assert "pack_id" in decision["why"]


class TestWhyExplanations:
    """Test why explanation generation."""
    
    def test_generate_why_explanation(self):
        """Test generating why explanation."""
        decision = {
            "id": "DEC-0001",
            "object_type": "test",
            "object_id": "TVAC",
            "action": "REQUIRE",
            "enforcement": "BLOCK_RELEASE",
            "why": {
                "rule_id": "SPACE.TEST.TVAC.FLIGHT",
                "pack_id": "SPACE_ENV_TESTS",
                "citations": ["NASA_GEVS", "AS9100_8_5_1"],
            },
        }
        
        explanation = generate_why_explanation(decision)
        assert isinstance(explanation, str)
        assert len(explanation) > 0


class TestAuditFunctions:
    """Test audit functions."""
    
    def test_generate_deterministic_decision_id(self):
        """Test deterministic decision ID generation."""
        context = {
            "industry_profile": "space",
            "hardware_class": "flight",
        }
        
        id1 = generate_deterministic_decision_id(
            "SPACE.TEST.TVAC.FLIGHT",
            "test",
            "TVAC",
            context,
        )
        
        id2 = generate_deterministic_decision_id(
            "SPACE.TEST.TVAC.FLIGHT",
            "test",
            "TVAC",
            context,
        )
        
        # Should be deterministic
        assert id1 == id2
        assert id1.startswith("DEC-")
    
    def test_export_audit_manifest(self):
        """Test audit manifest export."""
        inputs = {
            "processes": ["SMT"],
            "tests_requested": [],
            "materials": [],
            "bom_risk_flags": [],
        }
        
        soe_run = evaluate_soe(
            industry_profile="space",
            inputs=inputs,
            hardware_class="flight",
        )
        
        manifest = export_audit_manifest(soe_run)
        
        assert manifest["soe_version"] == soe_run["soe_version"]
        assert manifest["industry_profile"] == soe_run["industry_profile"]
        assert "decisions" in manifest
        assert "rules_applied" in manifest
        assert "evidence_required" in manifest
    
    def test_create_decision_log(self):
        """Test decision log creation."""
        inputs = {
            "processes": ["SMT"],
            "tests_requested": [],
            "materials": [],
            "bom_risk_flags": [],
        }
        
        soe_run = evaluate_soe(
            industry_profile="space",
            inputs=inputs,
            hardware_class="flight",
        )
        
        decision_log = create_decision_log(soe_run)
        
        assert isinstance(decision_log, list)
        assert len(decision_log) == len(soe_run["decisions"])
        
        for log_entry in decision_log:
            assert "decision_id" in log_entry
            assert "timestamp" in log_entry
            assert "rule_id" in log_entry
