"""Projecao temporal nao-supervisionada da ameaca climatica (2026-2030).

Para cada estacao, monta uma proxy anual de ameaca (chuva invertida + chuva
extrema + temperatura, padronizadas) e ajusta uma tendencia linear sobre 2000-2021.
A tendencia e interpolada (IDW) para os municipios e somada a ameaca atual,
gerando `ameaca_futura` e um rotulo de tendencia. Sem rotulos humanos: o sinal
vem so da dinamica temporal dos dados.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import io, score

ANO_ALVO = 2030
LIMIAR_TENDENCIA = 0.03  # variacao por ano na proxy padronizada


def _proxy_anual(anual: pd.DataFrame) -> pd.DataFrame:
    """Proxy de ameaca por estacao-ano, padronizada entre estacoes."""
    df = anual.copy()
    df["aridez"] = -df["precip_total"]
    for col in ("aridez", "rx1day", "tmax_media"):
        mu, sd = df[col].mean(), df[col].std(ddof=0)
        df[col + "_z"] = (df[col] - mu) / (sd or 1)
    df["proxy"] = df[["aridez_z", "rx1day_z", "tmax_media_z"]].mean(axis=1)
    return df


def _tendencia_estacao(proxy: pd.DataFrame) -> pd.DataFrame:
    linhas = []
    for estacao, g in proxy.groupby("estacao"):
        g = g.dropna(subset=["proxy"])
        if len(g) < 5:
            slope, delta = 0.0, 0.0
        else:
            slope = np.polyfit(g["ano"], g["proxy"], 1)[0]
            proj = np.polyval(np.polyfit(g["ano"], g["proxy"], 1), ANO_ALVO)
            delta = proj - g[g["ano"] >= g["ano"].max() - 2]["proxy"].mean()
        linhas.append({"estacao": estacao, "slope": slope, "delta": delta})
    return pd.DataFrame(linhas)


def _rotulo(slope: float) -> str:
    if slope > LIMIAR_TENDENCIA:
        return "Agravando"
    if slope < -LIMIAR_TENDENCIA:
        return "Melhorando"
    return "Estavel"


def projetar(df_scores: pd.DataFrame) -> pd.DataFrame:
    """Adiciona `ameaca_futura` e `tendencia` ao df de scores."""
    anual = pd.read_csv(io.DATA_PROCESSED / "indicadores_anuais.csv")
    estacoes = io.load_estacoes().rename(columns={"latitude": "lat", "longitude": "lon"})

    tend = _tendencia_estacao(_proxy_anual(anual)).set_index("estacao")
    origem = (
        tend.reset_index()[["estacao"]]
        .merge(estacoes[["codigo", "lat", "lon"]], left_on="estacao", right_on="codigo", how="left")
        [["estacao", "lat", "lon"]]
    )
    destino = score.centroides_municipios().merge(df_scores[["codigo"]], on="codigo", how="right")
    interp = score.idw(tend[["slope", "delta"]], origem, destino)

    df = df_scores.merge(interp, on="codigo", how="left")
    delta_norm = score.normalizar_robusto(df["delta"]) - 0.5  # centrado em 0
    df["ameaca_futura"] = (df["ameaca"] + 0.6 * delta_norm).clip(0, 1)
    df["tendencia"] = df["slope"].apply(_rotulo)
    return df.drop(columns=["slope", "delta"])
