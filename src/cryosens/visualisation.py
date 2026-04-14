#test1
# src/visualisation.py

import pandas as pd
import plotly.graph_objects as go
from IPython.display import display

from ipywidgets import ToggleButton, Button, HBox, VBox, Layout, Output as ipyOutput
from dash import Dash, dcc, html, Input, Output as dashOutput


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _display_unit(unit: str) -> str:
    """
    Convert user unit to display unit.
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


def _unit_label(base: str, unit: str | None = None, per_min: bool = False) -> str:
    """
    Build label with unit.
    Examples:
    - Value (°C)
    - ROC (bar/min)
    """
    if not unit:
        return base

    disp_unit = _display_unit(unit)
    return f"{base} ({disp_unit}/min)" if per_min else f"{base} ({disp_unit})"


# ─────────────────────────────────────────────────────────────────────────────
# RAW SIGNAL DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────

def plot_sensors_dashboard(
    df: pd.DataFrame,
    time_col: str = "time",
    unit: str = "C",
    value_label: str = "Value",
) -> None:
    """Interactive dashboard for raw sensor signals."""
    sensor_cols = [c for c in df.columns if c != time_col]

    fig = go.FigureWidget()
    fig.update_layout(
        template="simple_white",
        height=600,
        title="Sensor signals",
        xaxis_title="Time",
        yaxis_title=_unit_label(value_label, unit),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    sensor_buttons = []
    for sensor in sensor_cols:
        btn = ToggleButton(
            value=False,
            description=sensor,
            layout=Layout(width='auto', min_width='100px', margin='2px')
        )
        sensor_buttons.append(btn)

    def _update_plot(_=None):
        selected = [b.description for b in sensor_buttons if b.value]
        with fig.batch_update():
            fig.data = []
            for s in selected:
                fig.add_scatter(
                    x=df[time_col],
                    y=df[s],
                    name=s,
                    mode='lines'
                )

            fig.layout.title.text = (
                f"Selected sensors: {', '.join(selected[:3])}..."
                if selected else
                "Select at least one sensor"
            )

    def on_change(change):
        btn = change['owner']
        btn.icon, btn.button_style = ('check', 'info') if btn.value else ('', '')
        _update_plot()

    for b in sensor_buttons:
        b.observe(on_change, names='value')

    btn_all = Button(description="Select all", button_style='success')
    btn_none = Button(description="Clear all", button_style='warning')

    btn_all.on_click(lambda _: [setattr(b, 'value', True) for b in sensor_buttons])
    btn_none.on_click(lambda _: [setattr(b, 'value', False) for b in sensor_buttons])

    display(VBox([
        HBox([btn_all, btn_none]),
        HBox(sensor_buttons, layout=Layout(flex_flow='row wrap')),
        fig
    ]))

    if sensor_buttons:
        sensor_buttons[0].value = True

# ─────────────────────────────────────────────────────────────────────────────
# SENSOR DIFFERENCE DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────

def plot_sensor_difference_dashboard(
    df: pd.DataFrame,
    time_col: str = "time",
    unit: str = "C",
    value_label: str = "Difference",
) -> None:
    """Interactive dashboard to select exactly two sensors and plot their difference."""
    sensor_cols = [c for c in df.columns if c != time_col]

    fig = go.FigureWidget()
    fig.update_layout(
        template="simple_white",
        height=600,
        title="Sensor difference",
        xaxis_title="Time",
        yaxis_title=_unit_label(value_label, unit),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    sensor_buttons = []
    for sensor in sensor_cols:
        btn = ToggleButton(
            value=False,
            description=sensor,
            layout=Layout(width="auto", min_width="100px", margin="2px")
        )
        sensor_buttons.append(btn)

    status = Button(
        description="Select exactly 2 sensors",
        disabled=True,
        layout=Layout(width="260px")
    )

    def _update_plot(_=None):
        selected = [b.description for b in sensor_buttons if b.value]

        with fig.batch_update():
            fig.data = []

            if len(selected) == 2:
                s1, s2 = selected
                diff = df[s1] - df[s2]

                fig.add_scatter(
                    x=df[time_col],
                    y=diff,
                    name=f"{s1} - {s2}",
                    mode="lines"
                )

                fig.layout.title.text = f"Difference: {s1} - {s2}"
                status.description = f"Selected: {s1} and {s2}"

            elif len(selected) < 2:
                fig.layout.title.text = "Select exactly 2 sensors"
                status.description = f"{len(selected)} selected - need 2"

            else:
                fig.layout.title.text = "Too many sensors selected"
                status.description = f"{len(selected)} selected - keep only 2"

    def on_change(change):
        btn = change["owner"]

        selected_buttons = [b for b in sensor_buttons if b.value]

        # Limit selection to 2 sensors
        if len(selected_buttons) > 2:
            btn.value = False
            return

        btn.icon, btn.button_style = ("check", "info") if btn.value else ("", "")
        _update_plot()

    for b in sensor_buttons:
        b.observe(on_change, names="value")

    btn_clear = Button(description="Clear all", button_style="warning")
    btn_clear.on_click(lambda _: [setattr(b, "value", False) for b in sensor_buttons])

    display(VBox([
        HBox([btn_clear, status]),
        HBox(sensor_buttons, layout=Layout(flex_flow="row wrap")),
        fig
    ]))
# ─────────────────────────────────────────────────────────────────────────────
# ROC COMPUTATION
# ─────────────────────────────────────────────────────────────────────────────

def compute_roc(df: pd.DataFrame, time_col: str = "time") -> pd.DataFrame:
    """
    Compute ROC (rate of change) for each sensor column.

    Args:
        df       : DataFrame with a time column and sensor columns
        time_col : Time column name

    Returns:
        df_roc : DataFrame with same structure, values = ROC
    """
    df = df.copy()
    df_roc = pd.DataFrame()
    df_roc[time_col] = df[time_col]

    time_delta = pd.to_datetime(df[time_col]).diff().dt.total_seconds() / 60
    time_delta.iloc[0] = 1.0

    for col in df.columns:
        if col != time_col:
            df_roc[col] = df[col].diff() / time_delta

    return df_roc


# ─────────────────────────────────────────────────────────────────────────────
# ROC DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────

def plot_roc_dashboard(
    df: pd.DataFrame,
    time_col: str = "time",
    unit: str = "C",
) -> None:
    """Interactive ROC dashboard."""
    df_roc = compute_roc(df, time_col)
    sensor_cols = [c for c in df_roc.columns if c != time_col]

    fig = go.FigureWidget()
    fig.update_layout(
        template="plotly_white",
        height=500,
        title="Rate of change (ROC)",
        xaxis_title="Time",
        yaxis_title=_unit_label("ROC", unit, per_min=True),
        hovermode="x unified"
    )
    fig.add_hline(y=0, line=dict(color="black", dash="dash", width=1))

    sensor_buttons = []
    for sensor in sensor_cols:
        btn = ToggleButton(
            value=False,
            description=sensor,
            layout=Layout(width='auto', min_width='100px', margin='2px')
        )
        sensor_buttons.append(btn)

    def _update_roc_plot(_=None):
        selected = [b.description for b in sensor_buttons if b.value]
        with fig.batch_update():
            fig.data = []
            for s in selected:
                fig.add_scatter(
                    x=df_roc[time_col],
                    y=df_roc[s],
                    name=f"ROC {s}",
                    mode='lines',
                    line=dict(width=1)
                )

    def on_change(change):
        btn = change['owner']
        btn.icon, btn.button_style = ('check', 'danger') if btn.value else ('', '')
        _update_roc_plot()

    for b in sensor_buttons:
        b.observe(on_change, names='value')

    btn_all = Button(description="Select all", button_style='success')
    btn_none = Button(description="Clear all", button_style='warning')

    btn_all.on_click(lambda _: [setattr(b, 'value', True) for b in sensor_buttons])
    btn_none.on_click(lambda _: [setattr(b, 'value', False) for b in sensor_buttons])

    display(VBox([
        HBox([btn_all, btn_none]),
        HBox(sensor_buttons, layout=Layout(flex_flow='row wrap')),
        fig
    ]))

    if sensor_buttons:
        sensor_buttons[0].value = True