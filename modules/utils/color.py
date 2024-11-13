def hex_to_rgba(hex_color: str) -> tuple[float, float, float, float]:
    """Convert hex color to RGBA"""
    hex_color = hex_color.lstrip('#')
    return (
        int(hex_color[0:2], 16) / 255,
        int(hex_color[2:4], 16) / 255,
        int(hex_color[4:6], 16) / 255,
        1.0
    )

def rgba_to_hex(rgba: tuple[float, float, float, float]) -> str:
    """Convert RGBA to hex color"""
    return '#{:02x}{:02x}{:02x}'.format(
        int(rgba[0] * 255),
        int(rgba[1] * 255),
        int(rgba[2] * 255)
    )
