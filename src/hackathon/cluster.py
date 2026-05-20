"""Arquetipos de vulnerabilidade (KMeans nao-supervisionado) sobre os municipios."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

FEATURES = ["seca", "enchente", "calor", "capacidade"]


_DOMINANTE = {"seca": "Seca (sertao)", "enchente": "Enchente / chuva extrema", "calor": "Calor extremo"}
_TIER = {0: "baixa", 1: "moderada", 2: "alta"}


def _perfil(centro: dict) -> tuple[str, float]:
    risco = {c: centro[c] for c in ("seca", "enchente", "calor")}
    dominante = max(risco, key=risco.get)
    return dominante, max(risco.values())


def classificar(df: pd.DataFrame, k: int = 4, seed: int = 42) -> pd.DataFrame:
    """Adiciona `cluster` (id) e `arquetipo` (rotulo unico) ao df de scores."""
    x = StandardScaler().fit_transform(df[FEATURES])
    km = KMeans(n_clusters=k, random_state=seed, n_init=10).fit(x)
    df = df.copy()
    df["cluster"] = km.labels_

    perfis = {
        i: _perfil(df[df["cluster"] == i][["seca", "enchente", "calor"]].mean().to_dict())
        for i in range(k)
    }
    nomes: dict[int, str] = {}
    for dom in set(d for d, _ in perfis.values()):
        ids = sorted([i for i, (d, _) in perfis.items() if d == dom], key=lambda i: perfis[i][1])
        for posicao, i in enumerate(ids):
            base = _DOMINANTE[dom]
            if perfis[i][1] < 0.35:
                nomes[i] = "Baixo risco"
            elif len(ids) == 1:
                nomes[i] = base
            else:
                tier = _TIER[min(posicao, 2)] if len(ids) <= 3 else f"nivel {posicao + 1}"
                nomes[i] = f"{base} ({tier})"
    df["arquetipo"] = df["cluster"].map(nomes)
    return df
