

import pandas as pd
import numpy as np
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, Confirm
from rich import box
import ipywidgets as widgets
from IPython.display import display, clear_output

console = Console()

def convert_pressures(df: pd.DataFrame) -> pd.DataFrame:
    """
    Interactive interface to convert pressure units.
    Targets PI columns and automatically excludes PDI columns.
    """
    df = df.copy()
    
    # 1. Automatically identify PI columns, excluding PDI columns
    target_cols = [c for c in df.columns if c.lower() != "time" and "P_" in c.upper() and "PD_" not in c.upper()]
    
    if not target_cols:
        _warn("No PI column detected for conversion.")
        return df

    # 2. Display the selection interface
    console.print(Panel(f"[bold]Pressure Unit Conversion (PI)[/]\nTarget columns: {', '.join(target_cols)}", style="magenta"))
    
    menu_text = "[white]1[/] → Bar\n[white]2[/] → PSI\n[white]3[/] → kPa"
    
    console.print("[bold cyan]INPUT unit (current data unit):[/]")
    console.print(menu_text)
    choice_in = Prompt.ask("Your choice", choices=["1", "2", "3"], default="1")
    
    console.print("\n[bold green]OUTPUT unit (wanted for analysis):[/]")
    console.print(menu_text)
    choice_out = Prompt.ask("Your choice", choices=["1", "2", "3"], default="1")

    # Choice mapping
    mapping = {"1": "BAR", "2": "PSI", "3": "KPA"}
    u_in = mapping[choice_in]
    u_out = mapping[choice_out]

    if u_in == u_out:
        _ok("Same units selected, no change applied.")
        return df

    # 3. Conversion logic using bar as pivot unit
    for col in target_cols:
        
        # Step A: convert input unit to bar
        if u_in == "PSI":
            df[col] = df[col] / 14.5038
        elif u_in == "KPA":
            df[col] = df[col] / 100
            
        # Step B: convert from bar to output unit
        if u_out == "PSI":
            df[col] = df[col] * 14.5038
        elif u_out == "KPA":
            df[col] = df[col] * 100

    _ok(f"Success: conversion {u_in} → {u_out} applied to {len(target_cols)} columns.")
    return df


def convert_pdi(df: pd.DataFrame) -> pd.DataFrame:
    """
    Interactive interface to convert differential pressure units.
    Targets only PDI columns.
    """
    df = df.copy()
    
    # 1. Automatically identify PDI columns
    target_cols = [c for c in df.columns if c.lower() != "time" and "PD_" in c.upper()]
    
    if not target_cols:
        _warn("No PD_ column detected for conversion.")
        return df

    # 2. Display the selection interface
    console.print(Panel(f"[bold]Differential Pressure Unit Conversion (PD_)[/]\nTarget columns: {', '.join(target_cols)}", style="magenta"))
    
    menu_text = "[white]1[/] → milliBar (mbar)\n[white]2[/] → Inches of Water (inH2O)\n[white]3[/] → Pascal (Pa)"
    
    console.print("[bold cyan]INPUT unit (current data unit):[/]")
    console.print(menu_text)
    choice_in = Prompt.ask("Your choice", choices=["1", "2", "3"], default="1")
    
    console.print("\n[bold green]OUTPUT unit (wanted for analysis):[/]")
    console.print(menu_text)
    choice_out = Prompt.ask("Your choice", choices=["1", "2", "3"], default="1")

    # Choice mapping
    mapping = {"1": "MBAR", "2": "INH2O", "3": "PA"}
    u_in = mapping[choice_in]
    u_out = mapping[choice_out]

    if u_in == u_out:
        _ok("Same units selected, no change applied.")
        return df

    # 3. Conversion logic using mbar as pivot unit
    for col in target_cols:
        
        # Step A: convert input unit to mbar
        if u_in == "INH2O":
            df[col] = df[col] * 2.49089
        elif u_in == "PA":
            df[col] = df[col] / 100
            
        # Step B: convert from mbar to output unit
        if u_out == "INH2O":
            df[col] = df[col] / 2.49089
        elif u_out == "PA":
            df[col] = df[col] * 100

    _ok(f"Success: conversion {u_in} → {u_out} applied to {len(target_cols)} columns.")
    return df



def convert_temperatures(df: pd.DataFrame) -> pd.DataFrame:
    """
    Interactive interface to convert temperature units.
    Takes only the DataFrame as input.
    """
    df = df.copy()
    
    # 1. Automatically identify TI columns
    target_cols = [c for c in df.columns if c.lower() != "time" and "T_" in c.upper()]
    
    if not target_cols:
        _warn("No T_ column detected for conversion.")
        return df

    # 2. Display the selection interface
    console.print(Panel(f"[bold]Unit Conversion[/]\nTarget columns: {', '.join(target_cols)}", style="magenta"))
    
    # Tip: create the menu text only once to keep choices consistent
    menu_text = "[white]1[/] → Celsius (°C)\n[white]2[/] → Fahrenheit (°F)\n[white]3[/] → Kelvin (K)"
    
    console.print("[bold cyan]INPUT unit (current data unit):[/]")
    console.print(menu_text)
    choice_in = Prompt.ask("Your choice", choices=["1", "2", "3"], default="2")
    
    console.print("\n[bold green]OUTPUT unit (wanted for analysis):[/]")
    console.print(menu_text)
    choice_out = Prompt.ask("Your choice", choices=["1", "2", "3"], default="1")

    # Choice mapping, now perfectly aligned with menu_text
    mapping = {"1": "C", "2": "F", "3": "K"}
    u_in = mapping[choice_in]
    u_out = mapping[choice_out]

    if u_in == u_out:
        _ok("Same units selected, no change applied.")
        return df

    # 3. Conversion logic using Celsius as pivot unit
    for col in target_cols:
        
        # Step A: convert input unit to Celsius
        if u_in == "F":
            df[col] = (df[col] - 32) * 5 / 9
        elif u_in == "K":
            df[col] = df[col] - 273.15
            
        # Step B: convert from Celsius to output unit
        if u_out == "F":
            df[col] = (df[col] * 9 / 5) + 32
        elif u_out == "K":
            df[col] = df[col] + 273.15

    _ok(f"Success: conversion {u_in} → {u_out} applied to {len(target_cols)} columns.")
    return df
# ─────────────────────────────────────────────────────────────────────────────
# VISUAL HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def split_df_by_sensor_types(df: pd.DataFrame):
    if "time" not in df.columns:
        raise ValueError("The DataFrame must contain a 'time' column.")

    t_cols  = ["time"] + [c for c in df.columns if c != "time" and c.upper().startswith("T_")]
    dp_cols = ["time"] + [c for c in df.columns if c != "time" and c.upper().startswith("DP_")]
    p_cols  = ["time"] + [c for c in df.columns if c != "time" and c.upper().startswith("P_") and not c.upper().startswith("DP_")]

    df_t = df[t_cols].copy() if len(t_cols) > 1 else None
    df_dp = df[dp_cols].copy() if len(dp_cols) > 1 else None
    df_p = df[p_cols].copy() if len(p_cols) > 1 else None

    table = Table(title="Split by sensor type", box=box.SIMPLE_HEAVY)
    table.add_column("Label", style="bold cyan")
    table.add_column("Columns", style="white")
    table.add_column("Shape", style="yellow")

    for label, sub_df in [("T_", df_t), ("DP_", df_dp), ("P_", df_p)]:
        if sub_df is not None:
            table.add_row(label, ", ".join([c for c in sub_df.columns if c != "time"]), str(sub_df.shape))

    console.print(table)
    return df_t, df_dp, df_p

def _show_columns_table(df: pd.DataFrame, title: str = "Available columns") -> None:
    table = Table(title=title, box=box.SIMPLE_HEAVY, show_lines=False)
    table.add_column("#",      style="dim cyan",   justify="right", no_wrap=True)
    table.add_column("Name",   style="bold white",  no_wrap=False)
    table.add_column("Type",   style="yellow",      no_wrap=True)
    table.add_column("NaN %",  style="red",         justify="right", no_wrap=True)
    table.add_column("Preview", style="dim",        no_wrap=True)

    for i, col in enumerate(df.columns):
        nan_pct = df[col].isna().mean() * 100
        nan_str = f"{nan_pct:.1f}%" if nan_pct > 0 else "—"
        preview = str(df[col].dropna().iloc[0]) if df[col].dropna().shape[0] > 0 else "∅"
        dtype   = str(df[col].dtype)
        table.add_row(str(i), str(col), dtype, nan_str, preview[:40])

    console.print(table)


def _show_data_preview(df: pd.DataFrame, n_rows: int = 5, title: str = "Data preview") -> None:
    
    if df.empty:
        _warn("The DataFrame is empty, nothing to display.")
        return

    max_cols = 10
    cols_to_show = df.columns[:max_cols]
    
    table = Table(
        title=f"[bold cyan]{title}[/] [dim]({len(df)} rows x {len(df.columns)} cols)[/]", 
        box=box.ROUNDED, 
        header_style="bold magenta",
        border_style="dim blue",
        show_lines=True
    )

    # Regular columns only
    for col in cols_to_show:
        table.add_column(str(col), justify="center", no_wrap=True)
    
    if len(df.columns) > max_cols:
        table.add_column("...", justify="center")

    # Rows
    for i in range(min(n_rows, len(df))):
        row_data = [str(val)[:20] for val in df.iloc[i, :max_cols].values]
        if len(df.columns) > max_cols:
            row_data.append("...")
        table.add_row(*row_data)

    console.print(table)

def _ok(msg: str):   console.print(f"[bold green]✔[/]  {msg}")
def _warn(msg: str): console.print(f"[bold yellow]⚠[/]  {msg}")
def _err(msg: str):  console.print(f"[bold red]✘[/]  {msg}")

def _parse_index_list(raw: str, max_idx: int) -> list[int]:
    indices = []
    for token in raw.split(","):
        token = token.strip()
        if "-" in token and not token.startswith("-"):
            parts = token.split("-")
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                indices.extend(range(int(parts[0]), int(parts[1]) + 1))
        elif token.isdigit():
            indices.append(int(token))
    return [i for i in indices if 0 <= i < max_idx]

# ─────────────────────────────────────────────────────────────────────────────
# TRANSFORMATION FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def crop_top_rows(df: pd.DataFrame, start_row: int) -> pd.DataFrame:
    if not (0 <= start_row < len(df)):
        _warn(f"Invalid start_row={start_row} (0–{len(df)-1}), no rows removed.")
        return df.copy()
    cropped = df.iloc[start_row:].reset_index(drop=True)
    _ok(f"{start_row} rows removed → {len(cropped)} rows remaining.")
    return cropped

def promote_row_to_header(df: pd.DataFrame, row_index: int = 0) -> pd.DataFrame:
    if not (0 <= row_index < len(df)):
        _err(f"Invalid row_index={row_index}.")
        return df
    new_cols = df.iloc[row_index].fillna("unnamed").astype(str).tolist()
    seen = {}
    deduped = []
    for c in new_cols:
        count = seen.get(c, 0)
        deduped.append(f"{c}.{count}" if count > 0 else c)
        seen[c] = count + 1
    df = df.iloc[row_index + 1:].reset_index(drop=True)
    df.columns = deduped
    _ok(f"Row {row_index} promoted to header ({len(df.columns)} columns).")
    return df

def choose_and_rename_time_column(df: pd.DataFrame) -> pd.DataFrame:
    console.print(Panel("[bold]Time column selection[/]", style="cyan"))
    _show_columns_table(df)
    while True:
        raw = Prompt.ask("[cyan]Time column number[/]")
        if raw.isdigit() and 0 <= (idx := int(raw)) < len(df.columns): break
        _warn(f"Enter an integer between 0 and {len(df.columns) - 1}.")
    old_name = df.columns[idx]
    df.rename(columns={old_name: "time"}, inplace=True)
    _ok(f"Column '[italic]{old_name}[/italic]' (index {idx}) renamed to 'time'.")
    return df

def drop_columns_interactive(df: pd.DataFrame) -> pd.DataFrame:
    console.print(Panel("[bold]Column deletion[/]", style="cyan"))
    _show_columns_table(df)
    raw = Prompt.ask("[cyan]Columns to delete[/] (indices/names, empty for none)", default="")
    if not raw.strip():
        _ok("No column deleted.")
        return df
    idx_list = _parse_index_list(raw, len(df.columns))
    cols_to_drop = list(dict.fromkeys([df.columns[i] for i in idx_list] + [t.strip() for t in raw.split(",") if t.strip() in df.columns]))
    if not cols_to_drop:
        _warn("No valid identifier found.")
        return df
    console.print(f"[red]Columns that will be deleted:[/] {cols_to_drop}")
    if Confirm.ask("Confirm deletion?", default=True):
        df.drop(columns=cols_to_drop, inplace=True)
        _ok(f"{len(cols_to_drop)} column(s) deleted.")
    return df

# ─────────────────────────────────────────────────────────────────────────────
# COLUMN RENAMING UI
# ─────────────────────────────────────────────────────────────────────────────

def rename_columns_ui(df: pd.DataFrame) -> None:
    header = widgets.HTML(value="""
    <h3>📝 Column renaming</h3>
    <p>Edit the names on the right. Leave them unchanged if no change is needed.</p>

    <div style="
        padding: 12px;
        margin: 10px 0 15px 0;
        border: 1px solid #d0d7de;
        border-radius: 8px;
        background-color: #f6f8fa;
        line-height: 1.6;
    ">
        <b>Renaming rules:</b><br>
        • The time column must be named: <code>time</code><br>
        • Temperature sensors must start with: <code>T_</code><br>
        • Pressure sensors must start with: <code>P_</code><br>
        • Differential pressure sensors must start with: <code>DP_</code><br><br>

        <b>Examples:</b><br>
        <code>time</code><br>
        <code>T_FEED_IN</code><br>
        <code>P_OUTLET</code><br>
        <code>DP_PASS_A</code><br><br>

        <span style="color:#555;">
        These prefixes allow the toolbox to automatically identify sensor families.
        </span>
    </div>
    """)

    rows = []
    text_boxes = {}
    label_layout = widgets.Layout(width='300px')
    input_layout = widgets.Layout(width='300px')

    for col in df.columns:
        label = widgets.Label(value=str(col), layout=label_layout)
        text_box = widgets.Text(value=str(col), layout=input_layout)
        text_boxes[col] = text_box
        rows.append(widgets.HBox([label, widgets.Label(value=" ➡️ "), text_box]))

    button = widgets.Button(
        description="✅ Validate renaming",
        button_style='success',
        layout=widgets.Layout(width='250px', margin='20px 0 0 0'),
        icon='check'
    )
    output = widgets.Output()

    def on_button_click(b):
        with output:
            clear_output()
            new_names_map = {old: box.value.strip() for old, box in text_boxes.items()}
            new_names = list(new_names_map.values())

            if len(new_names) != len(set(new_names)):
                print("❌ Error: two columns cannot have the same name.")
                return

            changes = {k: v for k, v in new_names_map.items() if k != v}

            if not changes:
                print("ℹ️ No change applied.")
            else:
                df.rename(columns=new_names_map, inplace=True)
                print(f"✨ Success! {len(changes)} column(s) renamed.")
                print(f"New names: {list(changes.values())}")

    button.on_click(on_button_click)
    ui_container = widgets.VBox([header] + rows + [button, output])
    display(ui_container)
# ─────────────────────────────────────────────────────────────────────────────
# CLEANING & NaN
# ─────────────────────────────────────────────────────────────────────────────

def convert_columns_to_float(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.columns:
        if col != "time":
            df[col] = pd.to_numeric(df[col], errors='coerce')
    _ok("All columns except time converted to float.")
    return df

def handle_nans(df: pd.DataFrame) -> pd.DataFrame:
    console.print(Panel("[bold]NaN handling[/]", style="cyan"))
    _show_columns_table(df, "NaN status")
    
    # Suggested strategy: automatically remove columns with too many missing values
    num_cols = [col for col in df.columns if col != "time"]
    threshold = 0.8  # 80% missing values
    
    cols_to_drop = [c for c in num_cols if df[c].isna().mean() > threshold]
    if cols_to_drop:
        _warn(f"Columns excluded because they are too empty (>80%): {cols_to_drop}")
        df = df.drop(columns=cols_to_drop)
        num_cols = [c for c in num_cols if c not in cols_to_drop]

    console.print("\n[bold]Strategies:[/]\n[cyan]1[/] → Drop rows (risky: may remove everything)"
                  "\n[cyan]2[/] → Mean\n[cyan]3[/] → Median\n[cyan]4[/] → Interpolation (recommended)")
    
    c = Prompt.ask("Your choice", choices=["1","2","3","4"], default="4")
    
    if c == "1":
        before = len(df)
        df = df.dropna(subset=num_cols).reset_index(drop=True)
        _ok(f"Rows deleted: {before - len(df)}")
        
    elif c in ["2", "3"]:
        for col in num_cols:
            val = df[col].mean() if c == "2" else df[col].median()
            df[col] = df[col].fillna(val)
        _ok(f"NaN values replaced by the {'mean' if c=='2' else 'median'}")
        
    elif c == "4":
        # Limit interpolation to 5 consecutive points to keep physical meaning
        df[num_cols] = df[num_cols].interpolate(method='linear', limit=5, limit_area='inside')
        # Fill remaining small NaN gaps with a short ffill/bfill
        df[num_cols] = df[num_cols].ffill(limit=2).bfill(limit=2)
        _ok("Linear interpolation applied (max 5 consecutive points).")
        
    return df
# ─────────────────────────────────────────────────────────────────────────────
# PIPELINE ORCHESTRATOR
# ─────────────────────────────────────────────────────────────────────────────
def run_preprocessing_pipeline(df: pd.DataFrame) -> pd.DataFrame:
    console.print(Panel(
        "[bold white]Preprocessing Pipeline[/]\n"
        "[dim]Active preview after each step.[/]",
        style="bold blue", expand=False
    ))

    # --- Step 1: Crop top rows ---
    console.rule("[bold cyan]Step 1/6 — Crop top rows[/]")
    _show_data_preview(df, title="State BEFORE cropping")
    if Confirm.ask("Run: [bold]Crop rows[/]?", default=True):
        start_row = IntPrompt.ask("Number of the first useful row", default=0)
        df = crop_top_rows(df, start_row - 1)
        _show_data_preview(df, title="State AFTER cropping")

    # --- Step 2: Promote row to header ---
    console.rule("[bold cyan]Step 2/6 — Promote row to header[/]")
    if not df.empty:
        console.print(f"[yellow]Current row 0 (future header):[/] {df.iloc[0].values.tolist()}")
        if Confirm.ask("Promote row 0 to header?", default=True):
            df = promote_row_to_header(df, 0)
            _show_data_preview(df, title="State AFTER header promotion")

    # --- Step 3: Time column ---
    console.rule("[bold cyan]Step 3/6 — Choose the time column[/]")
    if Confirm.ask("Run: [bold]Define the TIME column[/]?", default=True):
        df = choose_and_rename_time_column(df)

        if "time" in df.columns:
            if not pd.api.types.is_datetime64_any_dtype(df["time"]):
                df["time"] = pd.to_datetime(df["time"], errors="coerce")
                _ok("Column 'time' converted to datetime.")
            else:
                _ok("Column 'time' is already in datetime format.")

        _ok("Column 'time' configured.")

    # --- Step 4: Column deletion ---
    console.rule("[bold cyan]Step 4/6 — Delete columns[/]")
    if Confirm.ask("Run: [bold]Interactive deletion[/]?", default=True):
        df = drop_columns_interactive(df)
        _show_columns_table(df, "Remaining columns")

    # --- Step 5: Float conversion ---
    console.rule("[bold cyan]Step 5/6 — Convert columns to float[/]")
    if Confirm.ask("Run: [bold]Float conversion[/]?", default=True):
        df = convert_columns_to_float(df)

    # --- Step 6: NaN handling ---
    console.rule("[bold cyan]Step 6/6 — Handle NaN values[/]")

    nan_ratio = df.isna().mean() * 100
    has_nans = (nan_ratio > 0).any()

    if not has_nans:
        _ok("No NaN detected.")
        _show_data_preview(df, title="Final cleaned dataset")
        return df

    _show_columns_table(df, "Detected NaN summary")

    # Sub-step A: delete columns with too many missing values
    if Confirm.ask("Delete columns with many NaN values?", default=True):
        threshold_pct = IntPrompt.ask(
            "Threshold (%) above which a column is deleted",
            default=50
        )

        cols_to_drop = nan_ratio[nan_ratio >= threshold_pct].index.tolist()

        if cols_to_drop:
            df = df.drop(columns=cols_to_drop)
            _ok(f"Deleted columns: {cols_to_drop}")
            _show_columns_table(df, "Remaining columns after NaN deletion")
        else:
            console.print("[yellow]No column above the threshold.[/]")

    remaining_nans = int(df.isna().sum().sum())

    if remaining_nans == 0:
        _ok("No NaN values remain after column deletion.")
        _show_data_preview(df, title="Final cleaned dataset")
        return df

    # Sub-step B: optional additional NaN handling
    if Confirm.ask("Apply additional NaN handling afterwards?", default=False):
        df = handle_nans(df)
        _show_data_preview(df, title="Final cleaned dataset")
    else:
        _ok("No additional NaN handling applied.")
        _show_data_preview(df, title="Dataset after simple NaN handling")

    return df