from pathlib import Path
import pandas as pd


def _get_project_root() -> Path:
    """Retourne la racine du projet (dossier parent de src)."""
    return Path(__file__).resolve().parent.parent.parent


def save_dataframe(df: pd.DataFrame, filename: str) -> Path:
    """
    Sauvegarde un DataFrame en parquet dans exports/.

    Args:
        df: DataFrame à sauvegarder
        filename: nom du fichier (ex: 'df_ti.parquet')

    Returns:
        Chemin du fichier sauvegardé
    """
    if not filename.endswith(".parquet"):
        raise ValueError("Le fichier doit être au format .parquet")

    root = _get_project_root()
    output_dir = root / "exports"
    output_dir.mkdir(parents=True, exist_ok=True)

    path = output_dir / filename
    df.to_parquet(path, index=False)

    print(f"Saved → {path}")
    return path


def load_dataframe(filename: str) -> pd.DataFrame:
    """
    Charge un DataFrame depuis exports/.

    Args:
        filename: nom du fichier (ex: 'df_ti.parquet')

    Returns:
        DataFrame chargé
    """
    root = _get_project_root()
    path = root / "exports" / filename

    if not path.exists():
        raise FileNotFoundError(f"Fichier non trouvé : {path}")

    df = pd.read_parquet(path)
    print(f"Loaded ← {path} | shape={df.shape}")
    return df