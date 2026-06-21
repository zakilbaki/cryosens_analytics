from pathlib import Path

import pandas as pd
import pytest

from cryosens.io.loader import load_data


def test_load_data_reads_csv(tmp_path: Path) -> None:
    path = tmp_path / "sensors.csv"
    path.write_text("time,temperature\n2026-01-01T00:00:00,20.5\n", encoding="utf-8")

    frame = load_data(path)

    assert list(frame.columns) == ["time", "temperature"]
    assert frame.iloc[0]["temperature"] == 20.5


def test_load_data_rejects_unknown_format(tmp_path: Path) -> None:
    path = tmp_path / "sensors.json"
    path.write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported file format"):
        load_data(path)
