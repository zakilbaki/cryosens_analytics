from cryosens.units import display_unit, unit_label


def test_display_unit_formats_temperature_units() -> None:
    assert display_unit("C") == "°C"
    assert display_unit("F") == "°F"
    assert display_unit("bar") == "bar"


def test_unit_label_supports_rate_of_change() -> None:
    assert unit_label("Value", "C") == "Value (°C)"
    assert unit_label("ROC", "bar", per_min=True) == "ROC (bar/min)"
    assert unit_label("Value") == "Value"
