from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
OUTPUTS = ROOT / "outputs"


def load_clima() -> pd.DataFrame:
    return pd.read_csv(DATA_RAW / "clima_bahia.csv")


def load_estacoes() -> pd.DataFrame:
    return pd.read_csv(DATA_PROCESSED / "estacoes.csv")
