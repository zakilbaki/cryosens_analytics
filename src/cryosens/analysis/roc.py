import warnings
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from IPython.display import display
from ipywidgets import FloatSlider, Dropdown, Output, VBox, Button, HBox, HTML


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
    Build axis/title label with unit.
    """
    if not unit:
        return base
    disp_unit = _display_unit(unit)
    return f"{base} ({disp_unit}/min)" if per_min else f"{base} ({disp_unit})"


def _resolve_unit(unit: str | None) -> str:
    """
    Default unit if omitted.
    """
    if unit is None:
        warnings.warn(
            "\n[ROC] Unit not specified — defaulting to 'C'.\n"
            "  Example:\n"
            "  launch_roc(df_ti, unit='C')\n"
            "  launch_roc(df_ti, unit='F')\n"
            "  launch_roc(df_ti, unit='K')\n"
            "  launch_roc(df_pi, unit='bar')",
            UserWarning,
            stacklevel=3,
        )
        return "C"
    return unit


def _safe_display(df: pd.DataFrame) -> None:
    try:
        display(df)
    except NameError:
        print(df.to_string())


def _validate_clean_input(df: pd.DataFrame, sensor_name: str) -> None:
    if "time" not in df.columns:
        raise ValueError("DataFrame must contain a 'time' column.")
    if sensor_name not in df.columns:
        raise ValueError(f"Sensor not found: {sensor_name}")
    if not pd.api.types.is_datetime64_any_dtype(df["time"]):
        raise TypeError("Column 'time' must already be in datetime format.")


def _summarize_variations(df_res: pd.DataFrame) -> dict:
    if df_res.empty:
        return {
            "n_mont": 0, "n_desc": 0, "n_total": 0,
            "amp_mean": 0.0, "amp_max": 0.0,
            "dur_mean": 0.0, "dur_max": 0.0,
            "vmax_mean": 0.0, "vmax_max": 0.0,
        }
    return {
        "n_mont": int((df_res["Type"] == "Montée").sum()),
        "n_desc": int((df_res["Type"] == "Descente").sum()),
        "n_total": int(len(df_res)),
        "amp_mean": float(df_res["Variation"].abs().mean()),
        "amp_max": float(df_res["Variation"].abs().max()),
        "dur_mean": float(df_res["Duration_min"].mean()),
        "dur_max": float(df_res["Duration_min"].max()),
        "vmax_mean": float(df_res["Max_Speed"].mean()),
        "vmax_max": float(df_res["Max_Speed"].max()),
    }


def _widgets_roc(df: pd.DataFrame, unit: str = "C"):
    sensor_cols = [c for c in df.columns if c != "time"]
    disp_unit = _display_unit(unit)

    return (
        Dropdown(options=sensor_cols, value=sensor_cols[0], description="Sensor"),
        FloatSlider(
            value=1.0, min=0.1, max=10.0, step=0.1,
            description=f"ROC ({disp_unit}/min)",
            continuous_update=False
        ),
        FloatSlider(
            value=2.0, min=0.5, max=50.0, step=0.5,
            description=f"Min var. ({disp_unit})",
            continuous_update=False
        ),
    )


def _event_type_en(fr_value: str) -> str:
    return "Rising" if fr_value == "Montée" else "Falling"


# ─────────────────────────────────────────────────────────────────────────────
# PURE ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────

def compute_roc_series(
    df: pd.DataFrame,
    sensor_name: str,
) -> pd.DataFrame:
    _validate_clean_input(df, sensor_name)

    time_series = df["time"]
    temp = df[sensor_name]

    dt = time_series.diff() / np.timedelta64(1, "m")
    dt = dt.replace(0, np.nan)

    roc = temp.diff() / dt

    df_clean = pd.DataFrame({
        "time": time_series,
        "Value": temp,
        "ROC": roc,
    }).dropna().reset_index(drop=True)

    return df_clean


def detect_variations_cross_zero_from_clean(
    df_clean: pd.DataFrame,
    sensor_name: str,
    roc_min: float = 1.0,
    variation_min: float = 2.0,
    apply_iqr_filter: bool = True,
) -> pd.DataFrame:
    if not {"time", "Value", "ROC"}.issubset(df_clean.columns):
        raise ValueError("df_clean must contain columns 'time', 'Value' and 'ROC'.")

    values = df_clean["Value"].values
    roc_vals = df_clean["ROC"].values
    dates = df_clean["time"].values
    n = len(roc_vals)

    resultats = []
    points_deja_vus = set()
    i = 0

    while i < n:
        if abs(roc_vals[i]) >= roc_min and i not in points_deja_vus:
            direction = np.sign(roc_vals[i])

            debut_idx = i
            while debut_idx > 0:
                if np.sign(roc_vals[debut_idx]) != direction or abs(roc_vals[debut_idx]) < 1e-4:
                    break
                debut_idx -= 1

            fin_idx = i
            while fin_idx < n - 1:
                if np.sign(roc_vals[fin_idx]) != direction or abs(roc_vals[fin_idx]) < 1e-4:
                    fin_idx -= 1
                    break
                fin_idx += 1

            amplitude_val = values[fin_idx] - values[debut_idx]

            if abs(amplitude_val) >= variation_min:
                duree = (dates[fin_idx] - dates[debut_idx]) / np.timedelta64(1, "m")

                resultats.append({
                    "Sensor": sensor_name,
                    "Start": dates[debut_idx],
                    "End": dates[fin_idx],
                    "Value_Start": round(float(values[debut_idx]), 1),
                    "Value_End": round(float(values[fin_idx]), 1),
                    "Variation": round(float(amplitude_val), 2),
                    "Duration_min": round(float(duree), 2),
                    "Type": "Montée" if amplitude_val > 0 else "Descente",
                    "Max_Speed": round(float(np.max(np.abs(roc_vals[debut_idx:fin_idx + 1]))), 3),
                })

                for p in range(debut_idx, fin_idx + 1):
                    points_deja_vus.add(p)
                i = fin_idx + 1
            else:
                i += 1
        else:
            i += 1

    df_res = pd.DataFrame(resultats)

    if apply_iqr_filter and not df_res.empty:
        q1 = df_res["Max_Speed"].quantile(0.25)
        q3 = df_res["Max_Speed"].quantile(0.75)
        iqr = q3 - q1
        df_res = df_res[df_res["Max_Speed"] <= q3 + 1.5 * iqr].reset_index(drop=True)

    return df_res


def detect_variations_cross_zero(
    df: pd.DataFrame,
    sensor_name: str,
    roc_min: float = 1.0,
    variation_min: float = 2.0,
    apply_iqr_filter: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    df_clean = compute_roc_series(df, sensor_name)
    df_res = detect_variations_cross_zero_from_clean(
        df_clean=df_clean,
        sensor_name=sensor_name,
        roc_min=roc_min,
        variation_min=variation_min,
        apply_iqr_filter=apply_iqr_filter,
    )
    return df_res, df_clean


# ─────────────────────────────────────────────────────────────────────────────
# VISUALIZATIONS
# ─────────────────────────────────────────────────────────────────────────────

def plot_signal_roc(
    df_clean: pd.DataFrame,
    df_res: pd.DataFrame,
    sensor_name: str,
    unit: str | None = None,
) -> go.Figure:
    unit = _resolve_unit(unit)

    n_rising = len(df_res[df_res["Type"] == "Montée"]) if not df_res.empty else 0
    n_falling = len(df_res[df_res["Type"] == "Descente"]) if not df_res.empty else 0

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=("Signal — Detected variations", _unit_label("ROC", unit, per_min=True)),
    )

    fig.add_trace(go.Scattergl(
        x=df_clean["time"],
        y=df_clean["Value"],
        line=dict(color="rgba(200,200,200,0.4)", width=1),
        name="Raw signal",
    ), row=1, col=1)

    if not df_res.empty:
        x_up, y_up = [], []
        x_down, y_down = [], []

        for row in df_res.itertuples(index=False):
            mask = (df_clean["time"] >= row.Start) & (df_clean["time"] <= row.End)
            segment = df_clean.loc[mask, ["time", "Value"]]

            if row.Type == "Montée":
                x_up.extend(segment["time"].tolist())
                y_up.extend(segment["Value"].tolist())
                x_up.append(None)
                y_up.append(None)
            else:
                x_down.extend(segment["time"].tolist())
                y_down.extend(segment["Value"].tolist())
                x_down.append(None)
                y_down.append(None)

        if x_up:
            fig.add_trace(go.Scattergl(
                x=x_up,
                y=y_up,
                line=dict(color="#EF553B", width=2),
                name="Detected rising events",
            ), row=1, col=1)

        if x_down:
            fig.add_trace(go.Scattergl(
                x=x_down,
                y=y_down,
                line=dict(color="#636EFA", width=2),
                name="Detected falling events",
            ), row=1, col=1)

    fig.add_trace(go.Scattergl(
        x=df_clean["time"],
        y=df_clean["ROC"],
        line=dict(color="orange", width=0.8),
        name="ROC",
    ), row=2, col=1)

    fig.add_hline(y=0, line=dict(color="black", dash="dash", width=1), row=2, col=1)

    fig.update_yaxes(title_text=_unit_label("Temperature", unit), row=1, col=1)
    fig.update_yaxes(title_text=_unit_label("ROC", unit, per_min=True), row=2, col=1)
    fig.update_xaxes(title_text="Time", row=2, col=1)

    fig.update_layout(
        height=500,
        template="plotly_white",
        title=f"{sensor_name} — {n_rising} rising / {n_falling} falling",
        margin=dict(b=0),
    )
    return fig


def plot_variation_stats(
    df_res: pd.DataFrame,
    sensor_name: str,
    unit: str | None = None,
) -> go.Figure:
    unit = _resolve_unit(unit)

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=(
            _unit_label("Amplitudes", unit),
            "Durations (2-min bins)",
        ),
    )

    for t, couleur in [("Montée", "#EF553B"), ("Descente", "#636EFA")]:
        df_t = df_res[df_res["Type"] == t]

        fig.add_trace(go.Histogram(
            x=df_t["Variation"],
            name=_event_type_en(t),
            marker_color=couleur,
            nbinsx=20,
        ), row=1, col=1)

        if not df_t.empty:
            fig.add_trace(go.Histogram(
                x=df_t["Duration_min"],
                xbins=dict(start=0, end=df_res["Duration_min"].max(), size=2),
                marker_color=couleur,
                showlegend=False,
            ), row=1, col=2)

    fig.update_xaxes(title_text=_unit_label("Amplitude", unit), row=1, col=1)
    fig.update_xaxes(title_text="Duration (min)", row=1, col=2)
    fig.update_yaxes(title_text="Count", row=1, col=1)
    fig.update_yaxes(title_text="Count", row=1, col=2)

    fig.update_layout(
        height=400,
        template="plotly_white",
        title=f"Variation statistics — {sensor_name}",
        barmode="group",
        bargap=0.1,
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARDS
# ─────────────────────────────────────────────────────────────────────────────

def launch_roc(df: pd.DataFrame, unit: str | None = None) -> None:
    unit = _resolve_unit(unit)
    w_sensor, w_roc_min, w_var_min = _widgets_roc(df, unit)
    out = Output()

    def _run(_=None):
        df_res, df_clean = detect_variations_cross_zero(
            df=df,
            sensor_name=w_sensor.value,
            roc_min=w_roc_min.value,
            variation_min=w_var_min.value
        )

        with out:
            out.clear_output(wait=True)
            fig = plot_signal_roc(df_clean, df_res, w_sensor.value, unit=unit)
            display(fig)

            if df_res.empty:
                print("No variation detected with these parameters.")
                return

            print(f"\n── Top 5 fastest variations — {w_sensor.value} ──")
            _safe_display(df_res.sort_values("Max_Speed", ascending=False).head(5))

    for w in [w_sensor, w_roc_min, w_var_min]:
        w.observe(_run, names="value")

    display(VBox([w_sensor, w_roc_min, w_var_min, out]))
    _run()


def launch_roc_stats(df: pd.DataFrame, unit: str | None = None) -> None:
    unit = _resolve_unit(unit)
    w_sensor, w_roc_min, w_var_min = _widgets_roc(df, unit)
    out = Output()

    def _run(_=None):
        df_res, _ = detect_variations_cross_zero(
            df=df,
            sensor_name=w_sensor.value,
            roc_min=w_roc_min.value,
            variation_min=w_var_min.value
        )

        with out:
            out.clear_output(wait=True)

            if df_res.empty:
                print("No variation detected with these parameters.")
                return

            fig = plot_variation_stats(df_res, w_sensor.value, unit=unit)
            display(fig)

    for w in [w_sensor, w_roc_min, w_var_min]:
        w.observe(_run, names="value")

    display(VBox([w_sensor, w_roc_min, w_var_min, out]))
    _run()


def launch_roc_sensitivity(df: pd.DataFrame, unit: str | None = None) -> None:
    unit = _resolve_unit(unit)
    w_sensor, _, w_var_min = _widgets_roc(df, unit)
    out = Output()

    def _run(_=None):
        sensor = w_sensor.value
        df_clean = compute_roc_series(df, sensor)
        roc_abs = df_clean["ROC"].abs().dropna()

        thresholds = np.arange(0.1, 10.1, 0.3)
        counts_rising = []
        counts_falling = []

        for s in thresholds:
            df_res = detect_variations_cross_zero_from_clean(
                df_clean=df_clean,
                sensor_name=sensor,
                roc_min=s,
                variation_min=w_var_min.value
            )
            counts_rising.append(len(df_res[df_res["Type"] == "Montée"]) if not df_res.empty else 0)
            counts_falling.append(len(df_res[df_res["Type"] == "Descente"]) if not df_res.empty else 0)

        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=(
                f"Speed distribution ({sensor})",
                "Impact of threshold on detection"
            ),
            horizontal_spacing=0.15
        )

        fig.add_trace(go.Histogram(
            x=roc_abs.clip(upper=roc_abs.quantile(0.99)),
            nbinsx=50,
            name="ROC frequency",
            marker_color="#CFD8DC"
        ), row=1, col=1)

        q95 = roc_abs.quantile(0.95)
        fig.add_vline(
            x=q95,
            line=dict(color="orange", dash="dot"),
            annotation_text="95th pct",
            row=1, col=1
        )

        fig.add_trace(go.Scatter(
            x=thresholds, y=counts_rising, mode="lines+markers",
            name="Rising", line=dict(color="#EF553B")
        ), row=1, col=2)

        fig.add_trace(go.Scatter(
            x=thresholds, y=counts_falling, mode="lines+markers",
            name="Falling", line=dict(color="#636EFA")
        ), row=1, col=2)

        fig.update_layout(
            title=f"ROC calibration helper — {sensor}",
            template="plotly_white",
            height=450,
            showlegend=True
        )

        fig.update_xaxes(title_text=_unit_label("Speed", unit, per_min=True), row=1, col=1)
        fig.update_xaxes(title_text=_unit_label("ROC threshold", unit, per_min=True), row=1, col=2)
        fig.update_yaxes(title_text="Number of points", row=1, col=1)
        fig.update_yaxes(title_text="Detected variations", row=1, col=2)

        with out:
            out.clear_output(wait=True)
            display(fig)

    for w in [w_sensor, w_var_min]:
        w.observe(_run, names="value")

    display(VBox([w_sensor, w_var_min, out]))
    _run()


def launch_roc_helper(df: pd.DataFrame, unit: str | None = None) -> None:
    unit = _resolve_unit(unit)
    w_sensor, w_roc_min, w_var_min = _widgets_roc(df, unit)
    out = Output()

    def _run(_=None):
        sensor = w_sensor.value
        df_clean = compute_roc_series(df, sensor)
        roc_abs = df_clean["ROC"].abs().dropna()

        threshold = w_roc_min.value
        pct_capture = (roc_abs >= threshold).mean() * 100 if len(roc_abs) else 0

        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=(
                f"ROC distribution — {sensor}",
                "Detected variations vs ROC threshold"
            )
        )

        fig.add_trace(go.Histogram(
            x=roc_abs.clip(upper=roc_abs.quantile(0.99)),
            nbinsx=80,
            name="ROC distribution",
            marker_color="#CFD8DC",
        ), row=1, col=1)

        fig.add_vline(
            x=threshold,
            line=dict(color="red", dash="dash", width=2),
            row=1, col=1,
            annotation_text=f"Threshold={threshold:.1f} ({pct_capture:.1f}% of points)",
            annotation_position="top right",
        )

        thresholds = np.arange(0.1, 10.1, 0.3)
        counts_rising = []
        counts_falling = []

        for s in thresholds:
            df_res = detect_variations_cross_zero_from_clean(
                df_clean=df_clean,
                sensor_name=sensor,
                roc_min=s,
                variation_min=w_var_min.value
            )
            counts_rising.append(len(df_res[df_res["Type"] == "Montée"]) if not df_res.empty else 0)
            counts_falling.append(len(df_res[df_res["Type"] == "Descente"]) if not df_res.empty else 0)

        fig.add_trace(go.Scatter(
            x=thresholds, y=counts_rising,
            mode="lines+markers",
            name="Rising",
            line=dict(color="#EF553B")
        ), row=1, col=2)

        fig.add_trace(go.Scatter(
            x=thresholds, y=counts_falling,
            mode="lines+markers",
            name="Falling",
            line=dict(color="#636EFA")
        ), row=1, col=2)

        fig.add_vline(
            x=threshold,
            line=dict(color="red", dash="dash", width=2),
            row=1, col=2
        )

        fig.update_layout(
            height=450,
            template="plotly_white",
            title=f"ROC threshold helper — {sensor}"
        )

        fig.update_xaxes(title_text=_unit_label("Speed", unit, per_min=True), row=1, col=1)
        fig.update_xaxes(title_text=_unit_label("ROC threshold", unit, per_min=True), row=1, col=2)
        fig.update_yaxes(title_text="Number of points", row=1, col=1)
        fig.update_yaxes(title_text="Detected variations", row=1, col=2)

        with out:
            out.clear_output(wait=True)
            display(fig)
            print(f"  Median ROC   : {roc_abs.median():.2f} {_display_unit(unit)}/min")
            print(f"  75th pct ROC : {roc_abs.quantile(0.75):.2f} {_display_unit(unit)}/min")
            print(f"  95th pct ROC : {roc_abs.quantile(0.95):.2f} {_display_unit(unit)}/min")
            print(f"  Current threshold : {threshold:.1f} -> captures {pct_capture:.1f}% of ROC points")

    for w in [w_sensor, w_roc_min, w_var_min]:
        w.observe(_run, names="value")

    display(VBox([w_sensor, w_roc_min, w_var_min, out]))
    _run()


def launch_roc_all_sensors(df: pd.DataFrame, unit: str | None = None) -> None:
    unit = _resolve_unit(unit)
    sensor_cols = [c for c in df.columns if c != "time"]

    w_roc_min = FloatSlider(
        value=1.0, min=0.1, max=10.0, step=0.1,
        description=f"ROC ({_display_unit(unit)}/min)",
        continuous_update=False
    )
    w_var_min = FloatSlider(
        value=2.0, min=0.5, max=50.0, step=0.5,
        description=f"Min var. ({_display_unit(unit)})",
        continuous_update=False
    )
    out = Output()

    def _run(_=None):
        labels = []
        counts_rising = []
        counts_falling = []
        dur_rising = []
        dur_falling = []

        for sensor in sensor_cols:
            df_res, _ = detect_variations_cross_zero(
                df=df,
                sensor_name=sensor,
                roc_min=w_roc_min.value,
                variation_min=w_var_min.value
            )
            labels.append(sensor)

            if df_res.empty:
                counts_rising.append(0)
                counts_falling.append(0)
                dur_rising.append(0)
                dur_falling.append(0)
            else:
                m = df_res[df_res["Type"] == "Montée"]
                d = df_res[df_res["Type"] == "Descente"]

                counts_rising.append(len(m))
                counts_falling.append(len(d))
                dur_rising.append(round(m["Duration_min"].mean(), 1) if not m.empty else 0)
                dur_falling.append(round(d["Duration_min"].mean(), 1) if not d.empty else 0)

        totals = [m + d for m, d in zip(counts_rising, counts_falling)]
        order = sorted(range(len(labels)), key=lambda i: totals[i], reverse=True)

        labels = [labels[i] for i in order]
        counts_rising = [counts_rising[i] for i in order]
        counts_falling = [counts_falling[i] for i in order]
        dur_rising = [dur_rising[i] for i in order]
        dur_falling = [dur_falling[i] for i in order]

        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=(
                f"Number of detected variations per sensor (ROC threshold={w_roc_min.value} {_display_unit(unit)}/min)",
                "Average variation duration per sensor (min)",
            ),
            vertical_spacing=0.15,
        )

        fig.add_trace(go.Bar(
            name="Rising",
            x=labels, y=counts_rising,
            marker_color="#EF553B",
            text=counts_rising, textposition="outside",
        ), row=1, col=1)

        fig.add_trace(go.Bar(
            name="Falling",
            x=labels, y=counts_falling,
            marker_color="#636EFA",
            text=counts_falling, textposition="outside",
        ), row=1, col=1)

        fig.add_trace(go.Bar(
            name="Rising duration",
            x=labels, y=dur_rising,
            marker_color="#EF553B",
            opacity=0.7,
            text=[f"{v} min" for v in dur_rising],
            textposition="outside",
            showlegend=False,
        ), row=2, col=1)

        fig.add_trace(go.Bar(
            name="Falling duration",
            x=labels, y=dur_falling,
            marker_color="#636EFA",
            opacity=0.7,
            text=[f"{v} min" for v in dur_falling],
            textposition="outside",
            showlegend=False,
        ), row=2, col=1)

        fig.update_layout(
            height=800,
            template="plotly_white",
            barmode="group",
            bargap=0.15,
            xaxis_tickangle=-45,
            xaxis2_tickangle=-45,
            title=f"All sensors analysis — ROC≥{w_roc_min.value} {_display_unit(unit)}/min, Var≥{w_var_min.value} {_display_unit(unit)}",
        )

        fig.update_yaxes(title_text="Count", row=1, col=1)
        fig.update_yaxes(title_text="Duration (min)", row=2, col=1)

        with out:
            out.clear_output(wait=True)
            display(fig)

    for w in [w_roc_min, w_var_min]:
        w.observe(_run, names="value")

    display(VBox([w_roc_min, w_var_min, out]))
    _run()


def launch_roc_compare_thresholds(df: pd.DataFrame, unit: str | None = None) -> None:
    unit = _resolve_unit(unit)
    sensor_cols = [c for c in df.columns if c != "time"]

    w_sensor = Dropdown(
        options=sensor_cols,
        value=sensor_cols[0],
        description="Sensor"
    )

    w_var_min = FloatSlider(
        value=2.0, min=0.5, max=50.0, step=0.5,
        description=f"Min var. ({_display_unit(unit)})",
        continuous_update=False
    )

    w_roc_1 = FloatSlider(
        value=0.5, min=0.1, max=10.0, step=0.1,
        description="Threshold 1",
        continuous_update=False
    )
    w_roc_2 = FloatSlider(
        value=1.0, min=0.1, max=10.0, step=0.1,
        description="Threshold 2",
        continuous_update=False
    )
    w_roc_3 = FloatSlider(
        value=2.0, min=0.1, max=10.0, step=0.1,
        description="Threshold 3",
        continuous_update=False
    )

    btn_run = Button(description="Compare", button_style="primary")
    status = HTML("<b>Status:</b> ready")
    out = Output()

    state = {"running": False}

    def _run(_=None):
        if state["running"]:
            return

        state["running"] = True
        btn_run.disabled = True
        btn_run.description = "Computing..."
        status.value = "<b>Status:</b> comparison in progress..."

        with out:
            out.clear_output(wait=True)
            print(f"Comparison in progress for {w_sensor.value}...")

        try:
            sensor = w_sensor.value
            thresholds = [w_roc_1.value, w_roc_2.value, w_roc_3.value]
            var_min = w_var_min.value

            df_clean = compute_roc_series(df, sensor)

            if df_clean.empty:
                with out:
                    out.clear_output(wait=True)
                    print("No usable data for this sensor.")
                status.value = "<b>Status:</b> no usable data"
                return

            results = []
            for thr in thresholds:
                df_res = detect_variations_cross_zero_from_clean(
                    df_clean=df_clean,
                    sensor_name=sensor,
                    roc_min=thr,
                    variation_min=var_min
                )
                results.append(df_res)

            fig = make_subplots(
                rows=3, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.06,
                subplot_titles=(
                    f"ROC threshold = {thresholds[0]:.1f} {_display_unit(unit)}/min",
                    f"ROC threshold = {thresholds[1]:.1f} {_display_unit(unit)}/min",
                    f"ROC threshold = {thresholds[2]:.1f} {_display_unit(unit)}/min",
                )
            )

            val_min = df_clean["Value"].min()
            val_max = df_clean["Value"].max()

            for idx, (thr, df_res) in enumerate(zip(thresholds, results), start=1):
                fig.add_trace(go.Scattergl(
                    x=df_clean["time"],
                    y=df_clean["Value"],
                    line=dict(color="rgba(180,180,180,0.6)", width=1),
                    name="Raw signal" if idx == 1 else None,
                    showlegend=(idx == 1)
                ), row=idx, col=1)

                if not df_res.empty:
                    x_up, y_up = [], []
                    x_down, y_down = [], []

                    for row in df_res.itertuples(index=False):
                        segment = df_clean.loc[
                            (df_clean["time"] >= row.Start) &
                            (df_clean["time"] <= row.End),
                            ["time", "Value"]
                        ]

                        if row.Type == "Montée":
                            x_up.extend(segment["time"].tolist())
                            y_up.extend(segment["Value"].tolist())
                            x_up.append(None)
                            y_up.append(None)
                        else:
                            x_down.extend(segment["time"].tolist())
                            y_down.extend(segment["Value"].tolist())
                            x_down.append(None)
                            y_down.append(None)

                    if x_up:
                        fig.add_trace(go.Scattergl(
                            x=x_up,
                            y=y_up,
                            line=dict(color="#EF553B", width=2.5),
                            name="Rising" if idx == 1 else None,
                            showlegend=(idx == 1)
                        ), row=idx, col=1)

                    if x_down:
                        fig.add_trace(go.Scattergl(
                            x=x_down,
                            y=y_down,
                            line=dict(color="#636EFA", width=2.5),
                            name="Falling" if idx == 1 else None,
                            showlegend=(idx == 1)
                        ), row=idx, col=1)

                fig.update_yaxes(range=[val_min, val_max], row=idx, col=1)

            fig.update_layout(
                height=850,
                template="plotly_white",
                title=f"ROC threshold comparison — {sensor} (Min variation = {var_min} {_display_unit(unit)})",
                margin=dict(t=70, b=20)
            )

            fig.update_yaxes(title_text=_unit_label("Temperature", unit), row=1, col=1)
            fig.update_yaxes(title_text=_unit_label("Temperature", unit), row=2, col=1)
            fig.update_yaxes(title_text=_unit_label("Temperature", unit), row=3, col=1)
            fig.update_xaxes(title_text="Time", row=3, col=1)

            fig.update_yaxes(matches='y', row=2, col=1)
            fig.update_yaxes(matches='y', row=3, col=1)

            with out:
                out.clear_output(wait=True)
                display(fig)

                print("── Detailed comparison summary ──")
                for thr, df_res in zip(thresholds, results):
                    stats = _summarize_variations(df_res)

                    if stats["n_total"] == 0:
                        print(f"Threshold {thr:.1f} {_display_unit(unit)}/min -> no variation detected")
                    else:
                        print(
                            f"Threshold {thr:.1f} {_display_unit(unit)}/min -> "
                            f"{stats['n_mont']} rising, {stats['n_desc']} falling, total={stats['n_total']}"
                        )
                        print(
                            f"   Amplitude : mean={stats['amp_mean']:.2f} {_display_unit(unit)} | max={stats['amp_max']:.2f} {_display_unit(unit)}"
                        )
                        print(
                            f"   Duration  : mean={stats['dur_mean']:.2f} min | max={stats['dur_max']:.2f} min"
                        )
                        print(
                            f"   Speed     : mean={stats['vmax_mean']:.2f} {_display_unit(unit)}/min | max={stats['vmax_max']:.2f} {_display_unit(unit)}/min"
                        )

            status.value = "<b>Status:</b> comparison complete"

        except Exception as e:
            with out:
                out.clear_output(wait=True)
                print(f"Error during comparison: {e}")
            status.value = "<b>Status:</b> error during comparison"

        finally:
            state["running"] = False
            btn_run.disabled = False
            btn_run.description = "Compare"

    btn_run.on_click(_run)

    display(VBox([
        w_sensor,
        w_var_min,
        HBox([w_roc_1, w_roc_2, w_roc_3]),
        HBox([btn_run, status]),
        out
    ]))


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS — COINCIDENCE
# ─────────────────────────────────────────────────────────────────────────────

def _event_start_times(df_res: pd.DataFrame) -> np.ndarray:
    if df_res.empty:
        return np.array([], dtype="datetime64[ns]")
    return pd.to_datetime(df_res["Start"]).values.astype("datetime64[ns]")


# ─────────────────────────────────────────────────────────────────────────────
# PURE ANALYSIS — SENSOR COINCIDENCE
# ─────────────────────────────────────────────────────────────────────────────

def detect_events_for_sensors(
    df: pd.DataFrame,
    sensor_names: list[str],
    roc_min: float = 1.0,
    variation_min: float = 2.0,
    apply_iqr_filter: bool = True,
) -> dict[str, pd.DataFrame]:
    results = {}

    for sensor in sensor_names:
        df_res, _ = detect_variations_cross_zero(
            df=df,
            sensor_name=sensor,
            roc_min=roc_min,
            variation_min=variation_min,
            apply_iqr_filter=apply_iqr_filter,
        )
        results[sensor] = df_res

    return results


def compute_event_coincidence_matrix(
    events_dict: dict[str, pd.DataFrame],
    tol_min: float = 5.0,
) -> pd.DataFrame:
    sensors = list(events_dict.keys())
    starts = {sensor: _event_start_times(df_res) for sensor, df_res in events_dict.items()}

    tol_ns = np.timedelta64(int(tol_min * 60), "s")
    matrix = pd.DataFrame(index=sensors, columns=sensors, dtype=float)

    for s1 in sensors:
        t1 = starts[s1]

        for s2 in sensors:
            t2 = starts[s2]

            if len(t1) == 0:
                matrix.loc[s1, s2] = np.nan
                continue

            if len(t2) == 0:
                matrix.loc[s1, s2] = 0.0
                continue

            count_match = 0

            for tt in t1:
                if np.any(np.abs(t2 - tt) <= tol_ns):
                    count_match += 1

            matrix.loc[s1, s2] = 100.0 * count_match / len(t1)

    return matrix


# ─────────────────────────────────────────────────────────────────────────────
# VISUALIZATIONS — COINCIDENCE
# ─────────────────────────────────────────────────────────────────────────────

def plot_event_coincidence_matrix(
    coincidence_df: pd.DataFrame,
    title: str = "Event coincidence matrix"
) -> go.Figure:
    fig = go.Figure(data=go.Heatmap(
        z=coincidence_df.values,
        x=coincidence_df.columns,
        y=coincidence_df.index,
        text=np.round(coincidence_df.values, 1),
        texttemplate="%{text}%",
        textfont={"size": 11},
        colorscale="Blues",
        zmin=0,
        zmax=100,
        colorbar=dict(title="Coincidence (%)")
    ))

    fig.update_layout(
        title=title,
        template="plotly_white",
        height=650,
        xaxis_title="Target sensor",
        yaxis_title="Reference sensor"
    )

    return fig


# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARDS — COINCIDENCE
# ─────────────────────────────────────────────────────────────────────────────

def launch_event_coincidence_heatmap(
    df: pd.DataFrame,
    sensor_names: list[str],
    unit: str | None = None,
) -> None:
    unit = _resolve_unit(unit)

    w_roc_min = FloatSlider(
        value=1.0, min=0.1, max=10.0, step=0.1,
        description=f"ROC ({_display_unit(unit)}/min)",
        continuous_update=False
    )

    w_var_min = FloatSlider(
        value=2.0, min=0.5, max=50.0, step=0.5,
        description=f"Min var. ({_display_unit(unit)})",
        continuous_update=False
    )

    w_tol = FloatSlider(
        value=5.0, min=1.0, max=30.0, step=1.0,
        description="Tol (min)",
        continuous_update=False
    )

    btn_run = Button(description="Analyze", button_style="primary")
    out = Output()
    status = HTML("<b>Status:</b> ready")
    state = {"running": False}

    def _run(_=None):
        if state["running"]:
            return

        state["running"] = True
        btn_run.disabled = True
        btn_run.description = "Computing..."
        status.value = "<b>Status:</b> analysis in progress..."

        try:
            with out:
                out.clear_output(wait=True)
                print("Computing event coincidence matrix...")

            events_dict = detect_events_for_sensors(
                df=df,
                sensor_names=sensor_names,
                roc_min=w_roc_min.value,
                variation_min=w_var_min.value,
            )

            coincidence_df = compute_event_coincidence_matrix(
                events_dict=events_dict,
                tol_min=w_tol.value
            )

            fig = plot_event_coincidence_matrix(
                coincidence_df,
                title=(
                    f"Event coincidence — ROC≥{w_roc_min.value} {_display_unit(unit)}/min, "
                    f"Var≥{w_var_min.value} {_display_unit(unit)}, tolerance ±{w_tol.value} min"
                )
            )

            with out:
                out.clear_output(wait=True)
                display(fig)

                print("── Number of events per sensor ──")
                for sensor in sensor_names:
                    n_evt = len(events_dict[sensor])
                    print(f"{sensor}: {n_evt}")

                print("\n── Quick summary ──")
                for sensor in sensor_names:
                    stats = _summarize_variations(events_dict[sensor])
                    print(
                        f"{sensor} -> total={stats['n_total']}, "
                        f"mean amp={stats['amp_mean']:.2f} {_display_unit(unit)}, "
                        f"mean dur={stats['dur_mean']:.2f} min"
                    )

                print("\n── Matrix reading ──")
                print("Row A / column B = % of A events whose start is also found on B within the selected window.")

            status.value = "<b>Status:</b> analysis complete"

        except Exception as e:
            with out:
                out.clear_output(wait=True)
                print(f"Error during analysis: {e}")
            status.value = "<b>Status:</b> error"

        finally:
            state["running"] = False
            btn_run.disabled = False
            btn_run.description = "Analyze"

    btn_run.on_click(_run)

    display(VBox([
        HTML(f"<b>Analyzed sensors:</b> {', '.join(sensor_names)}"),
        HBox([w_roc_min, w_var_min, w_tol]),
        HBox([btn_run, status]),
        out
    ]))