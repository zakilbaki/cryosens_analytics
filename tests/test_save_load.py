from pathlib import Path

import pandas as pd

from cryosens import save_load


def test_dataframe_round_trip(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(save_load, "_get_project_root", lambda: tmp_path)
    expected = pd.DataFrame({"temperature": [20.0, 21.5]})

    path = save_load.save_dataframe(expected, "sample.parquet")
    actual = save_load.load_dataframe("sample.parquet")

    assert path == tmp_path / "exports" / "sample.parquet"
    pd.testing.assert_frame_equal(actual, expected)
