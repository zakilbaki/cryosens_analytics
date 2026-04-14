import pandas as pd
import numpy as np
from scipy.signal import find_peaks
import plotly.graph_objects as go
import plotly.express as px
from ipywidgets import IntSlider, FloatSlider, Dropdown, Output, VBox
from IPython.display import display


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _safe_display(df: pd.DataFrame) -> None:
    try:
        display(df)  # noqa: F821
    except NameError:
        print(df.to_string())


def _get_series(df: pd.DataFrame, sensor_name: str) -> pd.Series:
    """Force l'index sur la colonne 'time' — seule source de vérité temporelle."""
    series = df[sensor_name].copy()
    if "time" in df.columns:
        series.index = pd.to_datetime(df["time"])
    return series


def _widgets(df: pd.DataFrame):
    """Retourne les widgets communs aux dashboards."""
    temp_cols = [c for c in df.columns if c != "time"]
    return (
        temp_cols,
        Dropdown(options=temp_cols, value=temp_cols[0], description="Capteur"),
        IntSlider(value=24,  min=1,   max=168, step=1,   description="Fenêtre IQR (h)"),
        FloatSlider(value=1.0, min=0.1, max=2.5, step=0.1, description="Sensibilité"),
        IntSlider(value=10,  min=1,   max=100, step=1,   description="Amp Min (°C)"),
    )


# ─────────────────────────────────────────────────────────────────────────────
# ANALYSE
# ─────────────────────────────────────────────────────────────────────────────

def analyze_thermal_cycles(
    series: pd.Series,
    window_h: int = 24,
    prom_factor: float = 0.5,
    min_amp: float = 10,
):
    """Détecte des cycles thermiques sur un signal temporel avec seuil IQR local adaptatif."""

    # 1. Nettoyage
    s_raw = pd.to_numeric(series, errors="coerce").dropna()
    if not isinstance(s_raw.index, pd.DatetimeIndex):
        try:
            s_raw.index = pd.to_datetime(s_raw.index, errors="coerce")
            if s_raw.index.isna().any():
                s_raw.index = pd.to_timedelta(np.arange(len(s_raw)), unit="s")
        except Exception:
            s_raw.index = pd.to_timedelta(np.arange(len(s_raw)), unit="s")

    if len(s_raw) < 30:
        return pd.DataFrame(), s_raw, pd.Series(dtype=float), pd.Series(dtype=float)

    # 2. Paramètres de segmentation
    time_deltas = s_raw.index.to_series().diff().dropna()
    if time_deltas.empty or not isinstance(time_deltas.iloc[0], pd.Timedelta):
        dt_min = 1.0
    else:
        dt_min = time_deltas.median().total_seconds() / 60
        if dt_min <= 0 or np.isnan(dt_min):
            dt_min = 1.0

    win_points = max(5, int((window_h * 60) / dt_min))

    # 3. IQR local par fenêtre glissante
    q1 = s_raw.rolling(window=win_points, center=True, min_periods=1).quantile(0.25)
    q3 = s_raw.rolling(window=win_points, center=True, min_periods=1).quantile(0.75)
    local_iqr = q3 - q1
    local_iqr[local_iqr <= 0] = s_raw.std() * 0.01

    # 4. Détection des pics et creux par segments
    peaks, valleys = [], []
    n    = len(s_raw)
    step = win_points // 2

    for start in range(0, n, step):
        end     = min(start + win_points, n)
        segment = s_raw.iloc[start:end]
        seg_iqr = local_iqr.iloc[start:end].median() * prom_factor

        seg_peaks,   _ = find_peaks( segment.values, prominence=seg_iqr)
        seg_valleys, _ = find_peaks(-segment.values, prominence=seg_iqr)

        peaks.extend(segment.index[seg_peaks])
        valleys.extend(segment.index[seg_valleys])

    peaks   = pd.Index(sorted(set(peaks)))
    valleys = pd.Index(sorted(set(valleys)))

    # 5. Extraction des cycles
    peaks_idx   = [s_raw.index.get_loc(p) for p in peaks]
    valleys_idx = [s_raw.index.get_loc(v) for v in valleys]

    cycles      = []
    valid_p_idx = []
    valid_v_idx = []

    for i in range(len(peaks_idx) - 1):
        p1, p2    = peaks_idx[i], peaks_idx[i + 1]
        v_between = [v for v in valleys_idx if p1 < v < p2]
        if not v_between:
            continue

        v = min(v_between, key=lambda x: s_raw.values[x])

        t_p1, t_v, t_p2         = s_raw.index[p1], s_raw.index[v], s_raw.index[p2]
        temp_p1, temp_v, temp_p2 = s_raw.values[p1], s_raw.values[v], s_raw.values[p2]
        amp                      = max(temp_p1 - temp_v, temp_p2 - temp_v)

        if amp >= min_amp:
            dur_total_min = (t_p2 - t_p1).total_seconds() / 60
            dur_cool_min  = (t_v  - t_p1).total_seconds() / 60
            dur_heat_min  = (t_p2 - t_v ).total_seconds() / 60

            roc_c = (temp_v  - temp_p1) / dur_cool_min if dur_cool_min > 0 else np.nan
            roc_h = (temp_p2 - temp_v)  / dur_heat_min if dur_heat_min > 0 else np.nan

            cycles.append({
                "Capteur"    : series.name,
                "Début"      : t_p1,
                "Point_Bas"  : t_v,
                "Fin"        : t_p2,
                "Amplitude_C": round(amp, 2),
                "Durée_min"  : round(dur_total_min, 1),
                "ROC_Cooling": round(roc_c, 4) if not np.isnan(roc_c) else np.nan,
                "ROC_Heating": round(roc_h, 4) if not np.isnan(roc_h) else np.nan,
            })

            valid_p_idx.extend([p1, p2])
            valid_v_idx.append(v)

    seen = set()
    valid_p_idx_ordered = []
    for idx in valid_p_idx:
        if idx not in seen:
            seen.add(idx)
            valid_p_idx_ordered.append(idx)

    return (
        pd.DataFrame(cycles),
        s_raw,
        s_raw.iloc[valid_p_idx_ordered],
        s_raw.iloc[valid_v_idx],
    )


# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARDS — pattern observe() : widgets affichés UNE seule fois via VBox
# ─────────────────────────────────────────────────────────────────────────────

def launch_cycle_dashboard(df: pd.DataFrame) -> None:
    """Signal brut + cycles détectés + tableau."""
    _, w_sensor, w_window, w_prom, w_amp = _widgets(df)
    out = Output()

    fig = go.FigureWidget()
    fig.add_trace(go.Scatter(name="Signal",           line=dict(color="#CFD8DC", width=1)))
    fig.add_trace(go.Scatter(name="Pics Validés",     mode="markers", marker=dict(color="red",  size=8, symbol="triangle-up")))
    fig.add_trace(go.Scatter(name="Vallées Validées", mode="markers", marker=dict(color="blue", size=8, symbol="triangle-down")))
    fig.update_layout(template="plotly_white", height=600, xaxis_title="Temps", yaxis_title="Température (°C)")

    def _run(_=None):
        series = _get_series(df, w_sensor.value)
        df_c, s_final, pks, vls = analyze_thermal_cycles(
            series, w_window.value, w_prom.value, w_amp.value
        )
        with fig.batch_update():
            fig.data[0].x, fig.data[0].y = s_final.index, s_final.values
            fig.data[1].x, fig.data[1].y = (pks.index, pks.values) if not pks.empty else ([], [])
            fig.data[2].x, fig.data[2].y = (vls.index, vls.values) if not vls.empty else ([], [])
            fig.layout.title.text = f"Analyse CryoSens — {w_sensor.value} ({len(df_c)} cycles)"

        out.clear_output(wait=True)
        with out:
            if not df_c.empty:
                print(f"✅ {len(df_c)} cycles détectés")
                _safe_display(df_c.sort_values("Début"))

    for w in [w_sensor, w_window, w_prom, w_amp]:
        w.observe(_run, names="value")

    display(VBox([w_sensor, w_window, w_prom, w_amp, fig, out]))
    _run()


def launch_cycle_histogramme(df: pd.DataFrame) -> None:
    """Distribution des amplitudes des cycles."""
    _, w_sensor, w_window, w_prom, w_amp = _widgets(df)
    out = Output()

    def _run(_=None):
        series = _get_series(df, w_sensor.value)
        df_c, _, _, _ = analyze_thermal_cycles(
            series, w_window.value, w_prom.value, w_amp.value
        )
        out.clear_output(wait=True)
        with out:
            if df_c.empty:
                print("Aucun cycle détecté avec ces paramètres.")
                return
            fig = px.histogram(
                df_c, x="Amplitude_C", nbins=30,
                title=f"Distribution des Amplitudes — {w_sensor.value} ({len(df_c)} cycles)",
                labels={"Amplitude_C": "Amplitude du Cycle (°C)"},
                color_discrete_sequence=["#636EFA"],
                marginal="rug",
            )
            fig.update_layout(template="plotly_white", yaxis_title="Nombre de cycles", bargap=0.1)
            fig.show()

    for w in [w_sensor, w_window, w_prom, w_amp]:
        w.observe(_run, names="value")

    display(VBox([w_sensor, w_window, w_prom, w_amp, out]))
    _run()


def launch_cycle_sensitivity(df: pd.DataFrame) -> None:
    """Nombre de cycles détectés vs prom_factor."""
    _, w_sensor, w_window, _, w_amp = _widgets(df)
    out = Output()

    def _run(_=None):
        series  = _get_series(df, w_sensor.value)
        series  = pd.to_numeric(series, errors="coerce").dropna()
        factors = np.arange(0.1, 3.1, 0.2)
        counts  = []

        out.clear_output(wait=True)
        with out:
            print(f"⏳ Calcul en cours pour {w_sensor.value}...")
            for f in factors:
                df_c, _, _, _ = analyze_thermal_cycles(
                    series, window_h=w_window.value, prom_factor=f, min_amp=w_amp.value
                )
                counts.append(len(df_c))

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=factors, y=counts, mode="lines+markers", name="Nb Cycles"))
            fig.update_layout(
                title=f"Sensibilité IQR — {w_sensor.value} (Amp Min = {w_amp.value}°C, Window = {w_window.value}h)",
                xaxis_title="prom_factor",
                yaxis_title="Nombre de cycles détectés",
                template="plotly_white",
            )
            fig.show()

    for w in [w_sensor, w_window, w_amp]:
        w.observe(_run, names="value")

    display(VBox([w_sensor, w_window, w_amp, out]))
    _run()