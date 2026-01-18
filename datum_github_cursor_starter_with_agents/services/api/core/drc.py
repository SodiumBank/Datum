"""Basic Design Rule Check (DRC) for Gerber files."""

import re
from pathlib import Path
from typing import TypedDict


class DRCResult(TypedDict):
    """Result of DRC checks."""
    violations: list[dict]
    has_violations: bool
    risk_factors: list[dict]


def _parse_gerber_coordinates(content: str) -> tuple[list[float], list[float], list[tuple[float, float]]]:
    """
    Parse X and Y coordinates from Gerber file.
    
    Returns:
        Tuple of (x_coords, y_coords, xy_pairs)
    """
    x_coords = []
    y_coords = []
    xy_pairs = []
    
    # Pattern for X and Y coordinates
    # Common formats: X12345Y67890 or X123.45Y67.890
    x_pattern = r"X(-?\d+(?:\.\d+)?)"
    y_pattern = r"Y(-?\d+(?:\.\d+)?)"
    
    # Find all X coordinates
    for match in re.finditer(x_pattern, content):
        try:
            x_val = float(match.group(1))
            x_coords.append(x_val)
        except (ValueError, IndexError):
            continue
    
    # Find all Y coordinates
    for match in re.finditer(y_pattern, content):
        try:
            y_val = float(match.group(1))
            y_coords.append(y_val)
        except (ValueError, IndexError):
            continue
    
    # Try to find X Y pairs together
    pair_pattern = r"X(-?\d+(?:\.\d+)?)Y(-?\d+(?:\.\d+)?)"
    for match in re.finditer(pair_pattern, content):
        try:
            x_val = float(match.group(1))
            y_val = float(match.group(2))
            xy_pairs.append((x_val, y_val))
        except (ValueError, IndexError):
            continue
    
    return x_coords, y_coords, xy_pairs


def _detect_units_and_scale(content: str) -> tuple[str, float]:
    """
    Detect units (mm or mils) from Gerber format specifier.
    
    Returns:
        Tuple of (unit, scale_factor) where scale_factor converts to mm
    """
    # Look for unit specifiers
    if re.search(r"%FSLAX(\d)(\d)\*%", content):  # Format specifier
        match = re.search(r"%FSLAX(\d)(\d)\*%", content)
        if match:
            # First digit: unit (2=mils, 3=mm)
            unit_code = int(match.group(1))
            if unit_code == 3:
                return "mm", 1.0
            elif unit_code == 2:
                return "mils", 0.0254  # Convert mils to mm
    elif re.search(r"G71|G70", content):  # Inches vs mm
        if "G71" in content:  # Inches
            return "inches", 25.4
        elif "G70" in content:  # mm
            return "mm", 1.0
    
    # Default: assume mils (common in Gerber)
    return "mils", 0.0254


def check_drill_to_copper_clearance(
    drill_file_path: Path,
    copper_file_paths: list[Path],
    min_clearance_mm: float = 0.15,  # Minimum 0.15mm clearance
) -> list[dict]:
    """
    Check drill-to-copper clearance.
    
    Heuristic: Checks if drill coordinates are too close to copper pads/traces.
    This is a simplified check - full DRC would require proper Gerber parsing.
    
    Returns:
        List of violation dicts with code, severity, summary, details
    """
    violations = []
    
    if not drill_file_path.exists():
        return violations
    
    try:
        drill_content = drill_file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return violations
    
    # Parse drill coordinates
    drill_x, drill_y, drill_pairs = _parse_gerber_coordinates(drill_content)
    
    if not drill_pairs:
        # Try to parse from separate X/Y lists
        if drill_x and drill_y:
            min_len = min(len(drill_x), len(drill_y))
            drill_pairs = [(drill_x[i], drill_y[i]) for i in range(min_len)]
    
    if not drill_pairs:
        return violations  # Cannot check without drill coordinates
    
    # Detect units for drill file
    drill_unit, drill_scale = _detect_units_and_scale(drill_content)
    
    # Check each copper file
    for copper_file in copper_file_paths:
        if not copper_file.exists():
            continue
        
        try:
            copper_content = copper_file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        
        # Parse copper coordinates
        copper_x, copper_y, copper_pairs = _parse_gerber_coordinates(copper_content)
        if not copper_pairs and copper_x and copper_y:
            min_len = min(len(copper_x), len(copper_y))
            copper_pairs = [(copper_x[i], copper_y[i]) for i in range(min_len)]
        
        if not copper_pairs:
            continue
        
        # Detect units for copper file
        copper_unit, copper_scale = _detect_units_and_scale(copper_content)
        
        # Check clearance (simplified: check distance between drill and copper)
        violations_count = 0
        min_clearance_scaled = min_clearance_mm / drill_scale  # Convert to file units
        
        for drill_x, drill_y in drill_pairs[:100]:  # Limit check to first 100 for performance
            for copper_x, copper_y in copper_pairs[:100]:  # Limit check
                # Calculate distance
                dx = (drill_x - copper_x) * drill_scale
                dy = (drill_y - copper_y) * drill_scale
                distance_mm = (dx**2 + dy**2) ** 0.5
                
                if distance_mm < min_clearance_mm:
                    violations_count += 1
                    if violations_count >= 5:  # Flag if multiple violations
                        break
            
            if violations_count >= 5:
                break
        
        if violations_count > 0:
            violations.append({
                "code": "DRILL_TO_COPPER_CLEARANCE",
                "severity": "MEDIUM",
                "summary": f"Drill-to-copper clearance may be insufficient (< {min_clearance_mm}mm)",
                "details": f"Found {violations_count}+ drill holes potentially too close to copper in {copper_file.name}",
                "impacts": {
                    "cost_delta": violations_count * 5.0,  # Estimated cost impact
                },
            })
    
    return violations


def check_copper_to_edge_clearance(
    copper_file_paths: list[Path],
    outline_file_path: Path | None,
    min_clearance_mm: float = 0.5,  # Minimum 0.5mm clearance to edge
) -> list[dict]:
    """
    Check copper-to-edge clearance.
    
    Heuristic: Checks if copper features are too close to board edge.
    
    Returns:
        List of violation dicts
    """
    violations = []
    
    if not outline_file_path or not outline_file_path.exists():
        # Cannot check without outline
        return violations
    
    try:
        outline_content = outline_file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return violations
    
    # Parse outline to get board bounds
    outline_x, outline_y, outline_pairs = _parse_gerber_coordinates(outline_content)
    
    if not outline_x or not outline_y:
        return violations
    
    # Detect units
    outline_unit, outline_scale = _detect_units_and_scale(outline_content)
    
    # Calculate board bounds
    x_min = min(outline_x) * outline_scale
    x_max = max(outline_x) * outline_scale
    y_min = min(outline_y) * outline_scale
    y_max = max(outline_y) * outline_scale
    
    # Check each copper file
    for copper_file in copper_file_paths:
        if not copper_file.exists():
            continue
        
        try:
            copper_content = copper_file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        
        copper_x, copper_y, copper_pairs = _parse_gerber_coordinates(copper_content)
        copper_unit, copper_scale = _detect_units_and_scale(copper_content)
        
        if not copper_x or not copper_y:
            continue
        
        # Check if copper features are too close to edge
        violations_count = 0
        min_clearance_scaled = min_clearance_mm / copper_scale
        
        for x, y in zip(copper_x[:100], copper_y[:100]):  # Limit check
            x_mm = x * copper_scale
            y_mm = y * copper_scale
            
            # Check distance to each edge
            dist_to_left = x_mm - x_min
            dist_to_right = x_max - x_mm
            dist_to_bottom = y_mm - y_min
            dist_to_top = y_max - y_mm
            
            min_dist = min(dist_to_left, dist_to_right, dist_to_bottom, dist_to_top)
            
            if min_dist < min_clearance_mm:
                violations_count += 1
                if violations_count >= 5:
                    break
        
        if violations_count > 0:
            violations.append({
                "code": "COPPER_TO_EDGE_CLEARANCE",
                "severity": "HIGH",
                "summary": f"Copper features too close to board edge (< {min_clearance_mm}mm)",
                "details": f"Found {violations_count}+ copper features potentially too close to edge in {copper_file.name}",
                "impacts": {
                    "cost_delta": violations_count * 10.0,  # Higher cost for edge violations
                },
            })
    
    return violations


def run_drc_checks(
    upload_id: str,
    gerber_files: list[dict],
) -> DRCResult:
    """
    Run basic DRC checks on Gerber files.
    
    Args:
        upload_id: Upload ID to locate extracted files
        gerber_files: List of file dicts from gerber_set (with path and type)
    
    Returns:
        DRCResult with violations and risk factors
    """
    from services.api.core.storage import UPLOADS_DIR
    
    violations = []
    
    # Organize files by type
    drill_files = []
    copper_files = []
    outline_file = None
    
    upload_dir = UPLOADS_DIR / upload_id
    
    for file_info in gerber_files:
        file_type = file_info.get("type", "OTHER")
        file_path_str = file_info.get("path", "")
        
        if not file_path_str:
            continue
        
        file_path = upload_dir / file_path_str.split("/", 1)[-1] if "/" in file_path_str else upload_dir / file_path_str
        
        if file_type == "EXCELLON":
            drill_files.append(file_path)
        elif file_type == "GERBER":
            copper_files.append(file_path)
        
        # Look for outline
        filename_lower = file_path.name.lower()
        if "outline" in filename_lower or "edge" in filename_lower or "keepout" in filename_lower:
            outline_file = file_path
    
    # Run checks
    if drill_files and copper_files:
        drill_violations = check_drill_to_copper_clearance(drill_files[0], copper_files)
        violations.extend(drill_violations)
    
    if copper_files and outline_file:
        edge_violations = check_copper_to_edge_clearance(copper_files, outline_file)
        violations.extend(edge_violations)
    
    # Generate risk factors from violations
    risk_factors = []
    for violation in violations:
        risk_factors.append({
            "code": violation["code"],
            "severity": violation["severity"],
            "summary": violation["summary"],
            "details": violation["details"],
            "impacts": violation.get("impacts", {}),
        })
    
    return DRCResult(
        violations=violations,
        has_violations=len(violations) > 0,
        risk_factors=risk_factors,
    )
