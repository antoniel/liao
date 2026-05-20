"""Indicadores climaticos brutos por estacao INMET (seca, enchente, calor).

Le o CSV horario, agrega para diario/anual e extrai indicadores padrao
(WMO/ETCCDI): chuva anual, dias secos consecutivos, Rx1day, dias de chuva
forte, dias quentes e tendencia de temperatura. Sentinela -9999 ja vira NaN
em io.load_clima. A normalizacao [0,1] e a composicao do score ficam em score.py.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import io

DRY_DAY_MM = 1.0
HEAVY_RAIN_MM = 50.0
MIN_DIAS_VALIDOS = 200  # exige ~55% do ano para o ano contar
MIN_ANOS = 5


def _max_dias_secos(precip_diaria: pd.Series) -> int:
    seco = (precip_diaria < DRY_DAY_MM).to_numpy()
    melhor = atual = 0
    for s in seco:
        atual = atual + 1 if s else 0
        melhor = max(melhor, atual)
    return melhor


def carregar_diario() -> pd.DataFrame:
    """Agrega o horario para diario por estacao (chuva somada, temp max/media)."""
    bruto = io.load_clima(usecols=[io.COL_ESTACAO, io.COL_DATA, io.COL_PRECIP, io.COL_TEMP])
    bruto = bruto.rename(
        columns={
            io.COL_ESTACAO: "estacao",
            io.COL_DATA: "data",
            io.COL_PRECIP: "precip",
            io.COL_TEMP: "temp",
        }
    )
    bruto["data"] = pd.to_datetime(bruto["data"], errors="coerce")
    bruto = bruto.dropna(subset=["data"])
    g = bruto.groupby(["estacao", "data"])
    diario = g.agg(
        precip=("precip", "sum"),
        tmax=("temp", "max"),
        tmedia=("temp", "mean"),
        horas=("precip", "count"),
    ).reset_index()
    diario["ano"] = diario["data"].dt.year
    return diario


def tabela_anual(diario: pd.DataFrame) -> pd.DataFrame:
    """Indicadores por estacao-ano (base da projecao temporal)."""
    linhas = []
    for (estacao, ano), g in diario.groupby(["estacao", "ano"]):
        if len(g) < MIN_DIAS_VALIDOS:
            continue
        tmax = g["tmax"].dropna()
        linhas.append(
            {
                "estacao": estacao,
                "ano": ano,
                "precip_total": g["precip"].sum(),
                "rx1day": g["precip"].max(),
                "dias_chuva_forte": int((g["precip"] >= HEAVY_RAIN_MM).sum()),
                "cdd": _max_dias_secos(g.sort_values("data")["precip"]),
                "tmax_media": tmax.mean() if len(tmax) else np.nan,
            }
        )
    return pd.DataFrame(linhas)


def indicadores_estacao(diario: pd.DataFrame, anual: pd.DataFrame) -> pd.DataFrame:
    """Colapsa a tabela anual num indicador por estacao + tendencia/dias quentes."""
    anual = anual[anual.groupby("estacao")["ano"].transform("size") >= MIN_ANOS]
    base = (
        anual.groupby("estacao")
        .agg(
            precip_anual=("precip_total", "mean"),
            rx1day=("rx1day", "mean"),
            dias_chuva_forte=("dias_chuva_forte", "mean"),
            cdd=("cdd", "mean"),
            tmax_media=("tmax_media", "mean"),
            n_anos=("ano", "size"),
        )
        .reset_index()
    )
    base = base.merge(_deficit_decada(anual), on="estacao", how="left")
    base = base.merge(_tendencia_temp(anual), on="estacao", how="left")
    base = base.merge(_dias_quentes(diario), on="estacao", how="left")
    return base


def _deficit_decada(anual: pd.DataFrame) -> pd.DataFrame:
    linhas = []
    for estacao, g in anual.groupby("estacao"):
        cedo = g[g["ano"] <= 2010]["precip_total"].mean()
        tarde = g[g["ano"] >= 2011]["precip_total"].mean()
        deficit = max(0.0, (cedo - tarde) / cedo) if cedo and not np.isnan(cedo) else 0.0
        linhas.append({"estacao": estacao, "deficit_decada": deficit})
    return pd.DataFrame(linhas)


def _tendencia_temp(anual: pd.DataFrame) -> pd.DataFrame:
    linhas = []
    for estacao, g in anual.groupby("estacao"):
        g = g.dropna(subset=["tmax_media"])
        if len(g) >= MIN_ANOS:
            slope = np.polyfit(g["ano"], g["tmax_media"], 1)[0] * 10  # C por decada
        else:
            slope = np.nan
        linhas.append({"estacao": estacao, "temp_trend": slope})
    return pd.DataFrame(linhas)


def _dias_quentes(diario: pd.DataFrame) -> pd.DataFrame:
    """TX90p: limiar p90 do periodo base (<=2010), excedencia no periodo recente (>=2011).

    Mede aquecimento: ~10% indica clima estavel, >10% indica mais dias quentes que antes.
    Sem periodo base, cai para o p90 global (vira ~0.10, neutro).
    """
    linhas = []
    for estacao, g in diario.groupby("estacao"):
        base = g[g["ano"] <= 2010]["tmax"].dropna()
        recente = g[g["ano"] >= 2011]["tmax"].dropna()
        if len(base) >= MIN_DIAS_VALIDOS and len(recente) >= MIN_DIAS_VALIDOS:
            limiar = base.quantile(0.90)
            pct = float((recente > limiar).mean())
        else:
            tmax = g["tmax"].dropna()
            pct = float((tmax > tmax.quantile(0.90)).mean()) if len(tmax) >= MIN_DIAS_VALIDOS else np.nan
        linhas.append({"estacao": estacao, "dias_quentes_pct": pct})
    return pd.DataFrame(linhas)


def construir() -> tuple[pd.DataFrame, pd.DataFrame]:
    diario = carregar_diario()
    anual = tabela_anual(diario)
    indicadores = indicadores_estacao(diario, anual)
    return indicadores, anual
