"""Red-team checks for Datum - prevent security violations and guardrail breaches.

Sprint 2: Extend checks to prevent edits/overrides in Sprint 2 artifacts.
"""

import json
import re
from pathlib import Path
from typing import List, Tuple


def check_plan_mutation_endpoints() -> List[Tuple[str, bool, str]]:
    """
    Check that DatumPlan mutation endpoints are disabled (Sprint 2).
    
    Returns:
        List of (file_path, passed, error_message) tuples
    """
    results = []
    plans_router = Path(__file__).parent.parent / "routers" / "plans.py"
    
    if not plans_router.exists():
        return [("plans.py", False, "plans.py router not found")]
    
    content = plans_router.read_text(encoding="utf-8")
    
    # Check that update endpoint returns 403 or is commented out
    update_pattern = r'@router\.post\(["\'].*steps["\']\)'
    if re.search(update_pattern, content):
        # Check if it raises 403 or is disabled
        if "HTTP_403_FORBIDDEN" in content or "Sprint 2: DatumPlan is immutable" in content:
            results.append(("plans.py", True, "Update endpoint correctly disabled for Sprint 2"))
        else:
            results.append(("plans.py", False, "Update endpoint exists but not disabled for Sprint 2"))
    else:
        results.append(("plans.py", True, "No update endpoint found (good for Sprint 2)"))
    
    return results


def check_no_edit_buttons_in_ui() -> List[Tuple[str, bool, str]]:
    """
    Check that Ops UI has no edit buttons for DatumPlan (Sprint 2).
    
    Returns:
        List of (file_path, passed, error_message) tuples
    """
    results = []
    ops_ui = Path(__file__).parent.parent.parent.parent / "apps" / "ops" / "app"
    
    if not ops_ui.exists():
        # UI might not exist yet - that's okay for Sprint 2
        results.append(("ops/app", True, "Ops UI not yet implemented (okay for Sprint 2)"))
        return results
    
    # Check for edit buttons in plan viewer
    for ui_file in ops_ui.rglob("*.tsx"):
        content = ui_file.read_text(encoding="utf-8")
        file_name = str(ui_file.relative_to(ops_ui))
        
        # Check for edit-related patterns
        edit_patterns = [
            r'edit.*plan',
            r'onEdit',
            r'handleEdit',
            r'mutate.*plan',
            r'update.*plan',
        ]
        
        for pattern in edit_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                # Check if it's disabled or commented
                if "Sprint 2" in content or "read-only" in content.lower() or "disabled" in content.lower():
                    results.append((file_name, True, f"Edit pattern found but disabled: {pattern}"))
                else:
                    results.append((file_name, False, f"Edit functionality found in Sprint 2 UI: {pattern}"))
                    break
    
    if not results:
        results.append(("ops/app", True, "No edit functionality found in Ops UI"))
    
    return results


def check_no_override_flags() -> List[Tuple[str, bool, str]]:
    """
    Check that no override flags exist in Sprint 2 code.
    
    Returns:
        List of (file_path, passed, error_message) tuples
    """
    results = []
    api_dir = Path(__file__).parent.parent
    
    override_patterns = [
        r'override.*plan',
        r'force.*update',
        r'bypass.*lock',
        r'ignore.*validation',
    ]
    
    for file_path in api_dir.rglob("*.py"):
        if "test" in str(file_path) or "__pycache__" in str(file_path):
            continue
        
        content = file_path.read_text(encoding="utf-8")
        relative_path = str(file_path.relative_to(api_dir))
        
        for pattern in override_patterns:
            matches = list(re.finditer(pattern, content, re.IGNORECASE))
            if matches:
                # Check each match to see if it's in a comment/docstring explaining what's NOT allowed
                for match in matches:
                    line_start = content.rfind("\n", 0, match.start())
                    line_end = content.find("\n", match.end())
                    line = content[max(0, line_start):line_end] if line_end != -1 else content[line_start:]
                    
                    # Skip if it's in a comment, docstring, or explaining Sprint 2 restrictions
                    if (
                        line.strip().startswith("#")
                        or '"""' in line
                        or "Sprint 2" in line
                        or "NOT ALLOWED" in line
                        or "disabled" in line.lower()
                        or "immutable" in line.lower()
                        or "read-only" in line.lower()
                    ):
                        continue
                    else:
                        results.append((relative_path, False, f"Override pattern found: {pattern}"))
                        break
                if results and results[-1][1] is False:
                    break
    
    if not results:
        results.append(("api/", True, "No override flags found"))
    
    return results


def run_sprint2_guardrail_checks() -> bool:
    """
    Run all Sprint 2 guardrail checks.
    
    Returns:
        True if all checks pass, False otherwise
    """
    all_results = []
    
    all_results.extend(check_plan_mutation_endpoints())
    all_results.extend(check_no_edit_buttons_in_ui())
    all_results.extend(check_no_override_flags())
    
    # Print results
    passed = 0
    failed = 0
    
    for file_path, check_passed, message in all_results:
        if check_passed:
            print(f"✅ {file_path}: {message}")
            passed += 1
        else:
            print(f"❌ {file_path}: {message}")
            failed += 1
    
    print(f"\nSprint 2 Guardrail Checks: {passed} passed, {failed} failed")
    
    return failed == 0


if __name__ == "__main__":
    import sys
    success = run_sprint2_guardrail_checks()
    sys.exit(0 if success else 1)
