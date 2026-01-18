"""Execution outputs generator - generates manufacturing intent artifacts.

SPRINT 2: Read-only execution outputs
- Stencil aperture + foil recommendations
- Placement intent (XYZ, rotation, side)
- Selective solder locations
- Lead forming intent
- Programming intent
- NO machine file export
- NO production-ready artifacts
"""

import hashlib
from typing import Any, Dict, List

from services.api.core.storage import (
    get_board_metrics,
    get_normalized_bom,
)


def _generate_deterministic_id(inputs: Dict[str, Any], prefix: str = "output") -> str:
    """Generate deterministic ID from inputs."""
    input_str = f"{prefix}:{str(sorted(inputs.items()))}"
    hash_obj = hashlib.sha256(input_str.encode())
    hash_hex = hash_obj.hexdigest()[:12]
    return f"{prefix}_{hash_hex}"


def generate_stencil_intent(
    upload_id: str,
    bom_items: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    """
    Generate stencil intent from PCB + BOM (Sprint 2: read-only intent).
    
    Args:
        upload_id: Gerber upload ID for PCB metrics
        bom_items: Normalized BOM items (if None, will load from upload_id)
    
    Returns:
        Stencil intent object with aperture and foil recommendations
    """
    # Load BOM if not provided
    if bom_items is None:
        bom_items = get_normalized_bom(upload_id) or []
    
    # Load board metrics
    board_metrics = get_board_metrics(upload_id) or {}
    
    # Analyze components for stencil apertures
    apertures: List[Dict[str, Any]] = []
    for item in bom_items:
        refdes = item.get("refdes", "")
        package = item.get("package", "")
        pitch = item.get("pitch")
        
        # Generate aperture recommendations based on package type
        aperture_type = "RECTANGULAR"  # Default
        if "0402" in package or "0603" in package:
            aperture_type = "RECTANGULAR"
        elif "BGA" in package or "LGA" in package:
            aperture_type = "ARRAY"
        elif "QFN" in package or "DFN" in package:
            aperture_type = "RECTANGULAR"
        
        apertures.append({
            "aperture_id": _generate_deterministic_id({"refdes": refdes, "type": "stencil_aperture"}, "aperture"),
            "refdes": refdes,
            "package": package,
            "aperture_type": aperture_type,
            "pitch": pitch,
            "width": _estimate_aperture_width(package, pitch),
            "length": _estimate_aperture_length(package, pitch),
        })
    
    # Generate foil thickness recommendation
    component_count = len(bom_items)
    if component_count > 100:
        foil_thickness = 0.127  # 5 mil
    elif component_count > 50:
        foil_thickness = 0.100  # 4 mil
    else:
        foil_thickness = 0.100  # 4 mil (default)
    
    stencil_intent = {
        "output_id": _generate_deterministic_id({"upload_id": upload_id, "type": "stencil"}, "stencil"),
        "upload_id": upload_id,
        "foil_thickness_mm": foil_thickness,
        "foil_material": "STAINLESS_STEEL",
        "frame_size": board_metrics.get("dimensions", {}),
        "apertures": apertures,
        "note": "Intent only - not production-ready",
    }
    
    return stencil_intent


def _estimate_aperture_width(package: str, pitch: float | None) -> float:
    """Estimate aperture width based on package."""
    if pitch:
        return pitch * 0.95  # 95% of pitch
    
    # Defaults by package
    if "0402" in package:
        return 0.5  # mm
    elif "0603" in package:
        return 0.75
    elif "0805" in package:
        return 1.0
    else:
        return 0.5  # Default


def _estimate_aperture_length(package: str, pitch: float | None) -> float:
    """Estimate aperture length based on package."""
    if pitch:
        return pitch * 1.5  # 1.5x pitch for length
    
    # Defaults by package
    if "0402" in package:
        return 0.8  # mm
    elif "0603" in package:
        return 1.2
    elif "0805" in package:
        return 1.5
    else:
        return 0.8  # Default


def generate_placement_intent(
    upload_id: str,
    bom_items: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    """
    Generate placement intent (XYZ, rotation, side) without machine files.
    
    Args:
        upload_id: Gerber upload ID
        bom_items: Normalized BOM items
    
    Returns:
        Placement intent object with refdes, coords, rotation
    """
    # Load BOM if not provided
    if bom_items is None:
        bom_items = get_normalized_bom(upload_id) or []
    
    # Load board metrics
    board_metrics = get_board_metrics(upload_id) or {}
    dimensions = board_metrics.get("dimensions", {})
    board_width = dimensions.get("width_mm", 100)
    board_height = dimensions.get("height_mm", 100)
    
    placements: List[Dict[str, Any]] = []
    top_count = 0
    bottom_count = 0
    
    for item in bom_items:
        refdes = item.get("refdes", "")
        package = item.get("package", "")
        side = item.get("side", "TOP")
        
        # Generate deterministic placement coordinates
        # This is intent only - actual coordinates would come from Gerber centroids
        if side == "TOP":
            x = 10 + (top_count % 10) * 8
            y = 10 + (top_count // 10) * 8
            top_count += 1
        else:
            x = 10 + (bottom_count % 10) * 8
            y = 10 + (bottom_count // 10) * 8
            bottom_count += 1
        
        # Clamp to board dimensions
        x = min(x, board_width - 5)
        y = min(y, board_height - 5)
        
        # Determine rotation based on package
        rotation = 0
        if "QFN" in package or "DFN" in package:
            rotation = 0
        elif "SOT" in package:
            rotation = 90
        
        placements.append({
            "placement_id": _generate_deterministic_id({"refdes": refdes, "type": "placement"}, "placement"),
            "refdes": refdes,
            "package": package,
            "x_mm": round(x, 2),
            "y_mm": round(y, 2),
            "rotation_deg": rotation,
            "side": side,
            "note": "Intent only - actual coordinates from Gerber centroids",
        })
    
    placement_intent = {
        "output_id": _generate_deterministic_id({"upload_id": upload_id, "type": "placement"}, "placement"),
        "upload_id": upload_id,
        "placements": placements,
        "note": "Intent only - not machine-ready",
    }
    
    return placement_intent


def generate_selective_solder_intent(
    upload_id: str,
    bom_items: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    """
    Generate selective solder intent based on PTH analysis.
    
    Args:
        upload_id: Gerber upload ID
        bom_items: Normalized BOM items
    
    Returns:
        Selective solder intent with locations and constraints
    """
    # Load BOM if not provided
    if bom_items is None:
        bom_items = get_normalized_bom(upload_id) or []
    
    # Identify PTH components (connectors, headers, through-hole)
    pth_locations: List[Dict[str, Any]] = []
    
    for item in bom_items:
        refdes = item.get("refdes", "")
        package = item.get("package", "")
        
        # Check if component is PTH (simplified heuristic)
        is_pth = any(keyword in package.upper() for keyword in ["CONN", "HEADER", "PIN", "PTH", "THROUGH"])
        
        if is_pth or item.get("mount_type") == "THROUGH_HOLE":
            pth_locations.append({
                "location_id": _generate_deterministic_id({"refdes": refdes, "type": "selective_solder"}, "solder"),
                "refdes": refdes,
                "package": package,
                "x_mm": 0,  # Would be from Gerber
                "y_mm": 0,  # Would be from Gerber
                "solder_type": "SELECTIVE_SOLDER",
                "note": "Intent only - actual coordinates from PTH analysis",
            })
    
    selective_solder_intent = {
        "output_id": _generate_deterministic_id({"upload_id": upload_id, "type": "selective_solder"}, "selective"),
        "upload_id": upload_id,
        "locations": pth_locations,
        "note": "Intent only - requires PTH Gerber analysis",
    }
    
    return selective_solder_intent


def generate_lead_form_intent(
    upload_id: str,
    bom_items: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    """
    Generate lead forming intent for applicable components.
    
    Args:
        upload_id: Gerber upload ID
        bom_items: Normalized BOM items
    
    Returns:
        Lead form intent with refdes and target dimensions
    """
    # Load BOM if not provided
    if bom_items is None:
        bom_items = get_normalized_bom(upload_id) or []
    
    lead_form_entries: List[Dict[str, Any]] = []
    
    for item in bom_items:
        refdes = item.get("refdes", "")
        package = item.get("package", "")
        
        # Check if component requires lead forming (simplified heuristic)
        requires_lead_form = any(keyword in package.upper() for keyword in ["DIP", "SIP", "LEAD"])
        
        if requires_lead_form or item.get("mount_type") == "THROUGH_HOLE":
            lead_form_entries.append({
                "entry_id": _generate_deterministic_id({"refdes": refdes, "type": "lead_form"}, "leadform"),
                "refdes": refdes,
                "package": package,
                "bend_angle_deg": 90,
                "bend_radius_mm": 0.5,
                "lead_length_mm": 2.5,
                "note": "Intent only - actual dimensions from component spec",
            })
    
    lead_form_intent = {
        "output_id": _generate_deterministic_id({"upload_id": upload_id, "type": "lead_form"}, "leadform"),
        "upload_id": upload_id,
        "entries": lead_form_entries,
        "note": "Intent only - not production-ready",
    }
    
    return lead_form_intent


def generate_programming_intent(
    upload_id: str,
    bom_items: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    """
    Generate programming intent when firmware load required.
    
    Args:
        upload_id: Gerber upload ID
        bom_items: Normalized BOM items
    
    Returns:
        Programming intent with firmware reference and verify step
    """
    # Load BOM if not provided
    if bom_items is None:
        bom_items = get_normalized_bom(upload_id) or []
    
    # Check for programmable components (simplified heuristic)
    programmable_components: List[Dict[str, Any]] = []
    
    for item in bom_items:
        refdes = item.get("refdes", "")
        package = item.get("package", "")
        mpn = item.get("mpn", "")
        
        # Check if component is programmable
        is_programmable = any(keyword in package.upper() or keyword in mpn.upper() 
                             for keyword in ["MCU", "FPGA", "CPLD", "PROGRAMMABLE"])
        
        if is_programmable:
            programmable_components.append({
                "component_id": _generate_deterministic_id({"refdes": refdes, "type": "programming"}, "prog"),
                "refdes": refdes,
                "package": package,
                "mpn": mpn,
                "programming_type": "JTAG",  # Default
                "firmware_ref": f"firmware_{refdes}",
                "verify_required": True,
                "note": "Intent only - actual firmware from design files",
            })
    
    programming_intent = {
        "output_id": _generate_deterministic_id({"upload_id": upload_id, "type": "programming"}, "program"),
        "upload_id": upload_id,
        "components": programmable_components,
        "verify_step_required": len(programmable_components) > 0,
        "note": "Intent only - not production-ready",
    }
    
    return programming_intent


def generate_all_execution_outputs(
    upload_id: str,
    bom_items: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    """
    Generate all execution outputs for a plan (Sprint 2: read-only intent).
    
    Args:
        upload_id: Gerber upload ID
        bom_items: Normalized BOM items
    
    Returns:
        Dict with all execution output intents
    """
    return {
        "stencil": generate_stencil_intent(upload_id, bom_items),
        "placement": generate_placement_intent(upload_id, bom_items),
        "selective_solder": generate_selective_solder_intent(upload_id, bom_items),
        "lead_form": generate_lead_form_intent(upload_id, bom_items),
        "programming": generate_programming_intent(upload_id, bom_items),
    }
