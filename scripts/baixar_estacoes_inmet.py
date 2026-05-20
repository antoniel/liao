"""Baixa o catálogo de estações automáticas do INMET e filtra BA."""
import csv
import json
import urllib.request
from pathlib import Path

URL = "https://apitempo.inmet.gov.br/estacoes/T"
ROOT = Path(__file__).resolve().parents[1]
RAW_CSV = ROOT / "data" / "raw" / "clima_bahia.csv"
OUT = ROOT / "data" / "processed" / "estacoes.csv"


def main() -> None:
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as r:
        data = json.load(r)

    ba = {e["CD_ESTACAO"]: e for e in data if e["SG_ESTADO"] == "BA"}
    codes = sorted({l.split(",")[0] for l in RAW_CSV.read_text().splitlines()[1:] if l})

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["codigo", "nome", "latitude", "longitude", "altitude_m", "situacao"])
        for c in codes:
            e = ba.get(c)
            if e:
                w.writerow([c, e["DC_NOME"], e["VL_LATITUDE"], e["VL_LONGITUDE"], e["VL_ALTITUDE"], e["CD_SITUACAO"]])
            else:
                w.writerow([c, "?", "", "", "", ""])
    print(f"{len(codes)} estações salvas em {OUT}")


if __name__ == "__main__":
    main()
