"""Compliance Report Renderer - Generate PDF and HTML reports (Sprint 5)."""

import hashlib
import json
from typing import Any, Dict, List
from datetime import datetime

from services.api.core.compliance_report import build_compliance_report_data


def generate_report_hash(report_data: Dict[str, Any]) -> str:
    """
    Generate SHA256 hash for report data (Sprint 5: Export hardening).
    
    Args:
        report_data: Report data structure
    
    Returns:
        SHA256 hash as hex string
    """
    # Serialize to JSON (sorted keys for determinism)
    json_str = json.dumps(report_data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(json_str.encode("utf-8")).hexdigest()


def render_html_report(report_data: Dict[str, Any]) -> str:
    """
    Render compliance report as HTML.
    
    Args:
        report_data: Report data from build_compliance_report_data()
    
    Returns:
        HTML string
    """
    metadata = report_data.get("report_metadata", {})
    exec_summary = report_data.get("executive_summary", {})
    scope = report_data.get("scope", {})
    coverage = report_data.get("standards_coverage", {})
    deviations = report_data.get("deviations_overrides", {})
    approvals = report_data.get("approvals_trail", [])
    profile_stack = report_data.get("profile_stack", {})
    evidence = report_data.get("evidence_requirements", {})
    
    # Generate hash
    report_hash = generate_report_hash(report_data)
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Compliance Report - {metadata.get('plan_id', 'N/A')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; border-bottom: 2px solid #ecf0f1; padding-bottom: 5px; }}
        h3 {{ color: #555; margin-top: 20px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #3498db; color: white; font-weight: bold; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        .metadata {{ background: #ecf0f1; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .warning {{ background: #fff3cd; padding: 10px; border-left: 4px solid #ffc107; margin: 10px 0; }}
        .override {{ background: #f8d7da; padding: 10px; border-left: 4px solid #dc3545; margin: 10px 0; }}
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 2px solid #ecf0f1; font-size: 0.9em; color: #7f8c8d; }}
        .hash {{ font-family: monospace; font-size: 0.85em; color: #555; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Compliance Audit Report</h1>
        
        <div class="metadata">
            <strong>Plan ID:</strong> {metadata.get('plan_id', 'N/A')}<br>
            <strong>Plan Version:</strong> {metadata.get('plan_version', 'N/A')}<br>
            <strong>Generated:</strong> {metadata.get('generated_at', 'N/A')}<br>
            <strong>Report Version:</strong> {metadata.get('report_version', '1.0.0')}<br>
            <strong>Report Hash:</strong> <span class="hash">{report_hash}</span>
        </div>
        
        <h2>1. Executive Summary</h2>
        <table>
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>Plan Status</td><td>{exec_summary.get('status', 'N/A')}</td></tr>
            <tr><td>Total Steps</td><td>{exec_summary.get('total_steps', 0)}</td></tr>
            <tr><td>Total Tests</td><td>{exec_summary.get('total_tests', 0)}</td></tr>
            <tr><td>Total Evidence Items</td><td>{exec_summary.get('total_evidence', 0)}</td></tr>
            <tr><td>Profile Stack Count</td><td>{exec_summary.get('profile_stack_count', 0)}</td></tr>
            <tr><td>Override Count</td><td>{exec_summary.get('override_count', 0)}</td></tr>
            <tr><td>Has Deviations</td><td>{'Yes' if exec_summary.get('has_deviations') else 'No'}</td></tr>
        </table>
        
        <h2>2. Scope</h2>
        <table>
            <tr><th>Field</th><th>Value</th></tr>
            <tr><td>Plan ID</td><td>{scope.get('plan_id', 'N/A')}</td></tr>
            <tr><td>Plan Version</td><td>{scope.get('plan_version', 'N/A')}</td></tr>
            <tr><td>Quote ID</td><td>{scope.get('quote_id', 'N/A')}</td></tr>
            <tr><td>Organization ID</td><td>{scope.get('org_id', 'N/A')}</td></tr>
            <tr><td>Design ID</td><td>{scope.get('design_id', 'N/A')}</td></tr>
            <tr><td>SOE Run ID</td><td>{scope.get('soe_run_id', 'N/A')}</td></tr>
        </table>
        
        <h3>Active Profile Stack</h3>
        <table>
            <tr><th>Profile ID</th><th>Type</th><th>Name</th><th>Layer</th></tr>
"""
    
    for profile in profile_stack.get("profiles", []):
        html += f"""            <tr>
                <td>{profile.get('profile_id', 'N/A')}</td>
                <td>{profile.get('profile_type', 'N/A')}</td>
                <td>{profile.get('name', 'N/A')}</td>
                <td>{profile.get('layer', 'N/A')}</td>
            </tr>
"""
    
    html += """        </table>
        
        <h2>3. Standards Coverage Matrix</h2>
        <table>
            <tr>
                <th>Entity Type</th><th>Entity ID</th><th>Type Detail</th>
                <th>Source Standard</th><th>Clause</th><th>Profile Source</th><th>Rule ID</th>
            </tr>
"""
    
    for row in coverage.get("coverage_table", []):
        html += f"""            <tr>
                <td>{row.get('entity_type', 'N/A')}</td>
                <td>{row.get('entity_id', 'N/A')}</td>
                <td>{row.get('entity_type_detail', 'N/A')}</td>
                <td>{row.get('source_standard', 'N/A')}</td>
                <td>{row.get('standard_clause', 'N/A')}</td>
                <td>{row.get('profile_source', 'N/A')}</td>
                <td>{row.get('rule_id', 'N/A')}</td>
            </tr>
"""
    
    html += """        </table>
        
        <h2>4. Deviations and Overrides</h2>
"""
    
    if deviations.get("has_deviations"):
        html += f"""        <div class="warning">
            <strong>Warning:</strong> This plan contains {deviations.get('override_count', 0)} override(s).
        </div>
        <table>
            <tr><th>Level</th><th>Entity ID</th><th>Type</th><th>Reason</th><th>By</th><th>At</th></tr>
"""
        for override in deviations.get("overrides", []):
            html += f"""            <tr>
                <td>{override.get('level', 'N/A')}</td>
                <td>{override.get('entity_id', 'N/A')}</td>
                <td>{override.get('entity_type', 'N/A')}</td>
                <td>{override.get('override_reason', 'N/A')}</td>
                <td>{override.get('override_by', 'N/A')}</td>
                <td>{override.get('override_at', 'N/A')}</td>
            </tr>
"""
        html += """        </table>
"""
    else:
        html += """        <p>No deviations or overrides found.</p>
"""
    
    html += """        
        <h2>5. Approvals Trail</h2>
        <table>
            <tr><th>Event Type</th><th>User/Status</th><th>Timestamp</th><th>Details</th></tr>
"""
    
    for event in approvals:
        event_type = event.get("event_type", "unknown")
        timestamp = event.get("approved_at") or event.get("rejected_at") or event.get("override_at") or event.get("timestamp") or "N/A"
        details = ""
        if event_type == "approved":
            details = f"Version: {event.get('version', 'N/A')}"
        elif event_type == "rejected":
            details = "Rejected"
        elif event_type == "override_approved":
            details = event.get("override_reason", "")
        
        user = event.get("approved_by") or event.get("rejected_by") or event.get("override_by") or "N/A"
        
        html += f"""            <tr>
                <td>{event_type}</td>
                <td>{user}</td>
                <td>{timestamp}</td>
                <td>{details}</td>
            </tr>
"""
    
    html += """        </table>
        
        <h2>6. Evidence Requirements</h2>
        <table>
            <tr><th>Evidence ID</th><th>Evidence Type</th><th>Profile Source</th><th>Rule ID</th></tr>
"""
    
    for evidence_item in evidence.get("evidence_items", []):
        trace = evidence_item.get("compliance_trace", {})
        html += f"""            <tr>
                <td>{evidence_item.get('evidence_id', 'N/A')}</td>
                <td>{evidence_item.get('evidence_type', 'N/A')}</td>
                <td>{trace.get('profile_source', 'N/A')}</td>
                <td>{trace.get('rule_id', 'N/A')}</td>
            </tr>
"""
    
    html += f"""        </table>
        
        <div class="footer">
            <p><strong>Report Integrity:</strong></p>
            <p class="hash">SHA256: {report_hash}</p>
            <p>This report was generated from an approved plan and is suitable for audit purposes.</p>
            <p>Generated by Datum Compliance System v{metadata.get('report_version', '1.0.0')}</p>
        </div>
    </div>
</body>
</html>
"""
    
    return html


def generate_compliance_report(plan_id: str, format: str = "html") -> Dict[str, Any]:
    """
    Generate compliance report in specified format.
    
    Args:
        plan_id: Plan ID to generate report for
        format: Report format ("html" or "pdf")
    
    Returns:
        Report data with rendered content and metadata
    """
    # Build report data
    report_data = build_compliance_report_data(plan_id)
    
    # Render based on format
    if format == "html":
        rendered_content = render_html_report(report_data)
    elif format == "pdf":
        # TODO: Implement PDF rendering (would use reportlab or similar)
        raise NotImplementedError("PDF rendering not yet implemented")
    else:
        raise ValueError(f"Unsupported format: {format}")
    
    # Generate hash
    report_hash = generate_report_hash(report_data)
    
    return {
        "report_data": report_data,
        "rendered_content": rendered_content,
        "format": format,
        "hash": report_hash,
        "metadata": report_data.get("report_metadata", {}),
    }
