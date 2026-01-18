"""Gerber file parser for board metrics extraction."""

import re
from pathlib import Path
from typing import TypedDict


class BoardMetrics(TypedDict):
    """Board metrics extracted from Gerber files."""
    layer_count: int
    width_mm: float | None
    height_mm: float | None
    area_mm2: float | None
    outline_detected: bool
    layers_detected: list[str]


def _detect_layer_from_filename(filename: str) -> str | None:
    """
    Detect layer type from filename using common naming conventions.
    
    Returns layer name (e.g., "TOP", "BOTTOM", "INNER_1", "OUTLINE") or None.
    """
    filename_upper = filename.upper()
    
    # Common layer naming patterns
    patterns = {
        "OUTLINE": [
            r".*OUTLINE.*",
            r".*EDGE.*",
            r".*GKO.*",
            r".*BOARD.*OUTLINE.*",
            r".*KEEPOUT.*",
        ],
        "TOP": [
            r".*GTL.*",
            r".*TOP.*",
            r".*L1.*",
            r".*LAYER1.*",
            r".*SIDE.*A.*",
        ],
        "BOTTOM": [
            r".*GBL.*",
            r".*BOTTOM.*",
            r".*L2.*",
            r".*LAYER2.*",
            r".*SIDE.*B.*",
        ],
        "INNER_1": [
            r".*G1.*",
            r".*INNER.*1.*",
            r".*L3.*",
            r".*LAYER3.*",
        ],
        "INNER_2": [
            r".*G2.*",
            r".*INNER.*2.*",
            r".*L4.*",
            r".*LAYER4.*",
        ],
        "INNER_3": [
            r".*G3.*",
            r".*INNER.*3.*",
            r".*L5.*",
            r".*LAYER5.*",
        ],
        "INNER_4": [
            r".*G4.*",
            r".*INNER.*4.*",
            r".*L6.*",
            r".*LAYER6.*",
        ],
        "TOP_SOLDERMASK": [
            r".*GTS.*",
            r".*TOP.*SOLDERMASK.*",
            r".*SMT.*",
        ],
        "BOTTOM_SOLDERMASK": [
            r".*GBS.*",
            r".*BOTTOM.*SOLDERMASK.*",
            r".*SMB.*",
        ],
        "TOP_OVERLAY": [
            r".*GTO.*",
            r".*TOP.*SILKSCREEN.*",
            r".*TOP.*OVERLAY.*",
        ],
        "BOTTOM_OVERLAY": [
            r".*GBO.*",
            r".*BOTTOM.*SILKSCREEN.*",
            r".*BOTTOM.*OVERLAY.*",
        ],
    }
    
    for layer_name, layer_patterns in patterns.items():
        for pattern in layer_patterns:
            if re.match(pattern, filename_upper):
                return layer_name
    
    # Try to detect inner layers by number pattern
    inner_match = re.search(r"INNER[_\s]*(\d+)", filename_upper, re.IGNORECASE)
    if inner_match:
        inner_num = inner_match.group(1)
        return f"INNER_{inner_num}"
    
    inner_match = re.search(r"G(\d+)", filename_upper)
    if inner_match:
        inner_num = inner_match.group(1)
        if inner_num.isdigit() and int(inner_num) > 2:
            return f"INNER_{int(inner_num) - 2}"
    
    return None


def _count_copper_layers(detected_layers: list[str]) -> int:
    """Count actual copper layers from detected layer list."""
    copper_layers = set()
    
    for layer in detected_layers:
        if layer in ("TOP", "BOTTOM"):
            copper_layers.add(layer)
        elif layer.startswith("INNER_"):
            copper_layers.add(layer)
    
    return len(copper_layers)


def _parse_gerber_outline(file_path: Path) -> tuple[float | None, float | None]:
    """
    Attempt to parse board outline dimensions from Gerber file.
    
    Returns (width_mm, height_mm) or (None, None) if not found.
    This is a basic heuristic - full Gerber parsing would require a proper parser.
    """
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None, None
    
    # Look for common outline commands in Gerber format
    # Format: X...Y... (coordinates)
    # We'll try to extract bounding box from coordinates
    
    # Pattern for X and Y coordinates (6 decimal places common)
    x_pattern = r"X(-?\d+(?:\.\d+)?)"
    y_pattern = r"Y(-?\d+(?:\.\d+)?)"
    
    x_coords = []
    y_coords = []
    
    for match in re.finditer(x_pattern, content):
        try:
            x_val = float(match.group(1))
            x_coords.append(x_val)
        except (ValueError, IndexError):
            continue
    
    for match in re.finditer(y_pattern, content):
        try:
            y_val = float(match.group(1))
            y_coords.append(y_val)
        except (ValueError, IndexError):
            continue
    
    if x_coords and y_coords:
        # Gerber coordinates are often in mils (0.001 inch) or mm
        # Assume mm for now (could be refined)
        x_min = min(x_coords)
        x_max = max(x_coords)
        y_min = min(y_coords)
        y_max = max(y_coords)
        
        width = x_max - x_min
        height = y_max - y_min
        
        # If dimensions seem too large, might be in mils - convert
        if width > 500 or height > 500:  # Unlikely to be mm if > 500mm
            width = width * 0.0254  # mils to mm
            height = height * 0.0254
        
        if width > 0 and height > 0:
            return round(width, 2), round(height, 2)
    
    return None, None


def extract_board_metrics(upload_id: str, gerber_files: list[dict]) -> BoardMetrics:
    """
    Extract board metrics from Gerber file list.
    
    Args:
        upload_id: Upload ID for locating extracted files
        gerber_files: List of file dicts from gerber_set (with path and type)
    
    Returns:
        BoardMetrics dict with layer_count, dimensions, etc.
    """
    from services.api.core.storage import UPLOADS_DIR
    
    detected_layers = []
    outline_path = None
    
    # Analyze each file
    for file_info in gerber_files:
        file_type = file_info.get("type", "OTHER")
        file_path_str = file_info.get("path", "")
        
        if file_type == "GERBER":
            filename = Path(file_path_str).name
            layer = _detect_layer_from_filename(filename)
            if layer:
                detected_layers.append(layer)
            
            # Look for outline file
            if layer == "OUTLINE" or "outline" in filename.lower() or "edge" in filename.lower():
                outline_path = UPLOADS_DIR / file_path_str
        
        # Also check for outline in OTHER type files
        elif file_type == "OTHER":
            filename = Path(file_path_str).name
            if "outline" in filename.lower() or "edge" in filename.lower() or "keepout" in filename.lower():
                outline_path = UPLOADS_DIR / file_path_str
                if "OUTLINE" not in detected_layers:
                    detected_layers.append("OUTLINE")
    
    # Count copper layers
    layer_count = _count_copper_layers(detected_layers)
    if layer_count == 0:
        # Fallback: count distinct Gerber files as layers
        gerber_count = sum(1 for f in gerber_files if f.get("type") == "GERBER")
        if gerber_count > 0:
            # Estimate: typically 2 layers (top/bottom) plus soldermask/overlay
            # If we have many files, might be multilayer
            layer_count = max(2, min(gerber_count // 3, 8))  # Heuristic
    
    # Try to extract board dimensions from outline file
    width_mm = None
    height_mm = None
    area_mm2 = None
    outline_detected = False
    
    if outline_path and outline_path.exists():
        outline_detected = True
        width_mm, height_mm = _parse_gerber_outline(outline_path)
        if width_mm and height_mm:
            area_mm2 = round(width_mm * height_mm, 2)
    
    return BoardMetrics(
        layer_count=layer_count,
        width_mm=width_mm,
        height_mm=height_mm,
        area_mm2=area_mm2,
        outline_detected=outline_detected,
        layers_detected=sorted(list(set(detected_layers))),
    )
