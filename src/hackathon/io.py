import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
OUTPUTS = ROOT / "outputs"

CLIMA_CSV = DATA_RAW / "clima_bahia.csv"
NA_SENTINEL = -9999.0

COL_ESTACAO = "ESTACAO"
COL_DATA = "DATA (YYYY-MM-DD)"
COL_PRECIP = "PRECIPITACAO TOTAL HORARIO (mm)"
COL_TEMP = "TEMPERATURA DO AR - BULBO SECO, HORARIA (C)"


def load_clima(usecols: list[str] | None = None) -> pd.DataFrame:
    return pd.read_csv(CLIMA_CSV, usecols=usecols, na_values=[NA_SENTINEL])


def load_estacoes() -> pd.DataFrame:
    return pd.read_csv(DATA_PROCESSED / "estacoes.csv")


def load_municipios() -> pd.DataFrame:
    return pd.read_csv(DATA_PROCESSED / "municipios.csv", dtype={"codigo": str})


def load_malha_geojson() -> dict:
    return json.loads((DATA_PROCESSED / "ba.geojson").read_text())
