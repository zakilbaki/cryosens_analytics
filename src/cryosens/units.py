def display_unit(unit: str) -> str:
    """
    Convert a user unit to a display unit.

    Examples:
    - C -> °C
    - F -> °F
    - K -> K
    - bar -> bar
    """
    mapping = {
        "C": "°C",
        "F": "°F",
    }
    return mapping.get(unit, unit)


def unit_label(base: str, unit: str | None = None, per_min: bool = False) -> str:
    """
    Build a label with unit.

    Examples:
    - Value (°C)
    - ROC (bar/min)
    """
    if not unit:
        return base

    disp_unit = display_unit(unit)
    return f"{base} ({disp_unit}/min)" if per_min else f"{base} ({disp_unit})"