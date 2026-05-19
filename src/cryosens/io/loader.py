import polars as pl
import pandas as pd
import tkinter as tk
from tkinter import filedialog
from pathlib import Path


def select_file() -> str:
    root = tk.Tk()
    root.attributes("-topmost", True)
    root.withdraw()

    try:
        path = filedialog.askopenfilename(
            title="Select Aramco file",
            filetypes=[("Data Files", "*.xlsx *.xls *.csv")]
        )
        return path
    finally:
        root.destroy()


def load_raw_data() -> pd.DataFrame | None:
    path_str = select_file()

    if not path_str:
        print("No file selected.")
        return None

    path = Path(path_str)

    try:
        if path.suffix.lower() == ".csv":
            pl_df = pl.read_csv(path_str, infer_schema_length=10000, ignore_errors=True)
        else:
            pl_df = pl.read_excel(path_str)

        df_pandas = pl_df.to_pandas()

        print(f"Loaded file: {path.name} ({len(df_pandas)} rows)")
        return df_pandas

    except Exception as e:
        print(f"Error while loading file: {e}")
        return None