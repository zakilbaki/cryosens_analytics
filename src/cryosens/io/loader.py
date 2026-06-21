import polars as pl
import pandas as pd
from pathlib import Path


def select_file() -> str:
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.attributes("-topmost", True)
    root.withdraw()

    try:
        path = filedialog.askopenfilename(
            title="Select a sensor data file",
            filetypes=[("Data Files", "*.xlsx *.xls *.csv")]
        )
        return path
    finally:
        root.destroy()


def load_data(path: str | Path) -> pd.DataFrame:
    """Load a CSV or Excel sensor export into a pandas DataFrame."""
    data_path = Path(path)
    suffix = data_path.suffix.lower()

    if suffix == ".csv":
        frame = pl.read_csv(data_path, infer_schema_length=10000, ignore_errors=True)
    elif suffix in {".xlsx", ".xls"}:
        frame = pl.read_excel(data_path)
    else:
        raise ValueError(f"Unsupported file format: {suffix or '<none>'}")

    return frame.to_pandas()


def load_raw_data() -> pd.DataFrame | None:
    """Open a file picker and load the selected sensor export."""
    path_str = select_file()

    if not path_str:
        print("No file selected.")
        return None

    path = Path(path_str)

    try:
        df_pandas = load_data(path)

        print(f"Loaded file: {path.name} ({len(df_pandas)} rows)")
        return df_pandas

    except Exception as e:
        print(f"Error while loading file: {e}")
        return None
