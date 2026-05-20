"""Baixa malha, populacao e IDHM dos 417 municipios da Bahia (UF 29).

Gera:
- data/processed/ba.geojson  (malha municipal, chave `codarea` = codigo IBGE 7 digitos)
- data/processed/municipios.csv  (codigo, nome, populacao, idhm, rdpc)
"""
import io
import json
from pathlib import Path

import pandas as pd
import requests

UF_BA = 29
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "processed"

MALHA_URL = (
    "https://servicodados.ibge.gov.br/api/v3/malhas/estados/29"
    "?formato=application/vnd.geo+json&intrarregiao=municipio&qualidade=intermediaria"
)
LOCALIDADES_URL = "https://servicodados.ibge.gov.br/api/v1/localidades/estados/BA/municipios"
POP_URL = (
    "https://servicodados.ibge.gov.br/api/v3/agregados/6579/periodos/2021"
    "/variaveis/9324?localidades=N6[N3[29]]"
)
IDHM_URL = "https://raw.githubusercontent.com/mauriciocramos/IDHM/master/municipal.csv"


def _get(url: str, **kw) -> requests.Response:
    r = requests.get(url, timeout=60, headers={"User-Agent": "Mozilla/5.0"}, **kw)
    r.raise_for_status()
    return r


def baixar_malha() -> dict:
    geo = _get(MALHA_URL).json()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "ba.geojson").write_text(json.dumps(geo))
    return geo


def baixar_nomes() -> pd.DataFrame:
    data = _get(LOCALIDADES_URL).json()
    return pd.DataFrame(
        {"codigo": str(m["id"]), "nome": m["nome"]} for m in data
    )


def baixar_populacao() -> pd.DataFrame:
    data = _get(POP_URL).json()
    series = data[0]["resultados"][0]["series"]
    ano = next(iter(series[0]["serie"]))
    rows = [
        {"codigo": s["localidade"]["id"], "populacao": int(s["serie"][ano])}
        for s in series
    ]
    return pd.DataFrame(rows)


def baixar_idhm() -> pd.DataFrame:
    txt = _get(IDHM_URL).text
    df = pd.read_csv(io.StringIO(txt), sep=";", low_memory=False)
    ba = df[(df["UF"] == UF_BA) & (df["ANO"] == 2010)].copy()
    ba["codigo"] = ba["Codmun7"].astype(str)
    for col in ("IDHM", "RDPC"):
        ba[col] = ba[col].astype(str).str.replace(",", ".").astype(float)
    return ba[["codigo", "IDHM", "RDPC"]].rename(columns={"IDHM": "idhm", "RDPC": "rdpc"})


def main() -> None:
    baixar_malha()
    municipios = (
        baixar_nomes()
        .merge(baixar_populacao(), on="codigo", how="left")
        .merge(baixar_idhm(), on="codigo", how="left")
    )
    faltando = municipios[["populacao", "idhm"]].isna().sum()
    municipios.to_csv(OUT / "municipios.csv", index=False)
    print(f"{len(municipios)} municipios -> {OUT / 'municipios.csv'}")
    print(f"sem populacao: {faltando['populacao']} | sem idhm: {faltando['idhm']}")


if __name__ == "__main__":
    main()
