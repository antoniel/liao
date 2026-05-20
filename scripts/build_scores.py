"""Orquestra o pipeline completo e gera data/processed/scores.csv.

Etapas: indicadores por estacao -> score (PCA+IDW+peso) -> clusters -> projecao.
Pre-requisitos: data/raw/clima_bahia.csv e scripts/baixar_municipios_ibge.py ja rodado.
"""
from pathlib import Path

from hackathon import cluster, forecast, indices, io, score

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    ind_path = io.DATA_PROCESSED / "indicadores_estacao.csv"
    if not ind_path.exists():
        print("computando indicadores por estacao (CSV horario)...")
        ind, anual = indices.construir()
        ind.to_csv(ind_path, index=False)
        anual.to_csv(io.DATA_PROCESSED / "indicadores_anuais.csv", index=False)

    df = score.montar_scores()
    df = cluster.classificar(df, k=4)
    df = forecast.projetar(df)
    df.to_csv(io.DATA_PROCESSED / "scores.csv", index=False)

    assert abs(df["peso"].sum() - 1.0) < 1e-9, "pesos nao somam 1"
    assert len(df) == 417, f"esperado 417 municipios, veio {len(df)}"
    print(f"OK: {len(df)} municipios, soma pesos = {df['peso'].sum():.6f}")
    print("arquetipos:", df["arquetipo"].value_counts().to_dict())
    print("tendencia:", df["tendencia"].value_counts().to_dict())


if __name__ == "__main__":
    main()
