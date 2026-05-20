"""Score de vulnerabilidade climatica por municipio e calculadora de orcamento.

Fluxo: indicadores por estacao -> 3 sub-indices [0,1] -> PCA aprende a ameaca
composta (pesos data-driven) -> IDW interpola os 45 pontos para os 417 centroides
municipais -> capacidade adaptativa (1-IDHM) -> peso per capita (ameaca/(1+AC))
normalizado para somar 1. A calculadora multiplica o orcamento pelo vetor de pesos.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from shapely.geometry import shape
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from . import io

CATEGORIAS = ["seca", "enchente", "calor"]


def normalizar_robusto(s: pd.Series) -> pd.Series:
    """Min-max robusto (p5-p95), maior = pior, recortado em [0,1]."""
    lo, hi = s.quantile(0.05), s.quantile(0.95)
    if hi == lo:
        return pd.Series(0.5, index=s.index)
    return ((s - lo) / (hi - lo)).clip(0, 1)


def subindices_estacao(ind: pd.DataFrame) -> pd.DataFrame:
    """Combina indicadores brutos nos 3 sub-indices climaticos por estacao."""
    aridez = normalizar_robusto(-ind["precip_anual"])  # menos chuva = pior
    cdd = normalizar_robusto(ind["cdd"])
    deficit = normalizar_robusto(ind["deficit_decada"])
    seca = normalizar_robusto(0.5 * aridez + 0.3 * cdd + 0.2 * deficit)

    enchente = normalizar_robusto(
        0.6 * normalizar_robusto(ind["rx1day"]) + 0.4 * normalizar_robusto(ind["dias_chuva_forte"])
    )

    quentes = normalizar_robusto(ind["dias_quentes_pct"])
    trend = normalizar_robusto(ind["temp_trend"].clip(lower=0))
    calor = normalizar_robusto(0.6 * quentes + 0.4 * trend)

    return pd.DataFrame(
        {"estacao": ind["estacao"], "seca": seca, "enchente": enchente, "calor": calor}
    )


def ajustar_ameaca_pca(sub: pd.DataFrame) -> tuple[PCA, StandardScaler]:
    """PCA nos 3 sub-indices: a 1a componente vira a ameaca composta."""
    scaler = StandardScaler()
    x = scaler.fit_transform(sub[CATEGORIAS])
    pca = PCA(n_components=1).fit(x)
    # orienta a componente para que maior valor = maior ameaca
    alto = pd.DataFrame([[1, 1, 1]], columns=CATEGORIAS)
    if pca.transform(scaler.transform(alto))[0, 0] < 0:
        pca.components_ *= -1
    return pca, scaler


def aplicar_ameaca(df: pd.DataFrame, pca: PCA, scaler: StandardScaler) -> pd.Series:
    bruto = pca.transform(scaler.transform(df[CATEGORIAS]))[:, 0]
    return normalizar_robusto(pd.Series(bruto, index=df.index))


def centroides_municipios() -> pd.DataFrame:
    geo = io.load_malha_geojson()
    linhas = []
    for f in geo["features"]:
        c = shape(f["geometry"]).centroid
        linhas.append({"codigo": str(f["properties"]["codarea"]), "lat": c.y, "lon": c.x})
    return pd.DataFrame(linhas)


def idw(
    valores: pd.DataFrame, origem: pd.DataFrame, destino: pd.DataFrame, k: int = 5, power: float = 2.0
) -> pd.DataFrame:
    """Inverse distance weighting de `valores` (em `origem`) para `destino`.

    origem: [estacao, lat, lon]; destino: [codigo, lat, lon]; valores: indexado por estacao.
    """
    o = origem.dropna(subset=["lat", "lon"]).reset_index(drop=True)
    val = valores.loc[o["estacao"]].to_numpy()
    olat, olon = np.radians(o["lat"].to_numpy()), np.radians(o["lon"].to_numpy())
    dlat, dlon = np.radians(destino["lat"].to_numpy()), np.radians(destino["lon"].to_numpy())

    saida = np.zeros((len(destino), val.shape[1]))
    for i in range(len(destino)):
        d = _haversine(dlat[i], dlon[i], olat, olon)
        idx = np.argsort(d)[:k]
        dk = d[idx]
        if dk[0] < 1e-3:
            saida[i] = val[idx[0]]
            continue
        w = 1.0 / dk**power
        saida[i] = (w[:, None] * val[idx]).sum(axis=0) / w.sum()
    out = pd.DataFrame(saida, columns=valores.columns)
    out.insert(0, "codigo", destino["codigo"].to_numpy())
    return out


def _haversine(lat1, lon1, lat2, lon2):
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 6371.0 * 2 * np.arcsin(np.sqrt(a))


def montar_scores() -> pd.DataFrame:
    """Pipeline completo -> df municipios com sub-indices, ameaca, capacidade e peso."""
    ind = pd.read_csv(io.DATA_PROCESSED / "indicadores_estacao.csv")
    estacoes = io.load_estacoes().rename(columns={"latitude": "lat", "longitude": "lon"})

    sub = subindices_estacao(ind).set_index("estacao")
    origem = ind[["estacao"]].merge(
        estacoes[["codigo", "lat", "lon"]], left_on="estacao", right_on="codigo", how="left"
    )[["estacao", "lat", "lon"]]

    munis = io.load_municipios()
    centro = centroides_municipios()
    destino = centro.merge(munis[["codigo"]], on="codigo", how="right")

    interp = idw(sub, origem, destino)  # codigo + seca/enchente/calor por municipio

    pca, scaler = ajustar_ameaca_pca(sub.reset_index())
    interp["ameaca"] = aplicar_ameaca(interp, pca, scaler).to_numpy()

    df = munis.merge(interp, on="codigo", how="left")
    df["capacidade"] = 1 - df["idhm"]  # menor IDHM = menor capacidade = mais vulneravel
    df["peso"] = _peso_per_capita(df["ameaca"], df["capacidade"])
    return df


def peso_per_capita(ameaca: pd.Series, capacidade: pd.Series) -> pd.Series:
    """Peso de alocacao per capita (ameaca / (1+falta de capacidade)), soma = 1."""
    bruto = ameaca / (1 + capacidade)
    return bruto / bruto.sum()


_peso_per_capita = peso_per_capita


def hazard_por_pesos(df: pd.DataFrame, w_seca: float, w_enchente: float, w_calor: float) -> pd.Series:
    """Ameaca alternativa por pesos do usuario (sliders), re-normalizados para somar 1."""
    total = w_seca + w_enchente + w_calor
    if total == 0:
        return df["ameaca"]
    combo = (w_seca * df["seca"] + w_enchente * df["enchente"] + w_calor * df["calor"]) / total
    return normalizar_robusto(combo)


def alocar(df: pd.DataFrame, orcamento: float, coluna_peso: str = "peso") -> pd.DataFrame:
    pesos = df[coluna_peso] / df[coluna_peso].sum()
    out = df[["codigo", "nome", "populacao", "idhm", "ameaca"]].copy()
    out["peso"] = pesos.to_numpy()
    out["valor_rs"] = (pesos * orcamento).to_numpy()
    return out.sort_values("valor_rs", ascending=False).reset_index(drop=True)
