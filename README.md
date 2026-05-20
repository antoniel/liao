# Termômetro Climático da Bahia

Índice de vulnerabilidade climática dos **417 municípios da Bahia** + calculadora que distribui um
orçamento público proporcionalmente ao risco de cada um. Hackathon "Resiliência Climática e
Cidades Inteligentes na Bahia".

Não prevemos o tempo. Dizemos **onde investir a verba**. Veja [`Plano.md`](Plano.md) para a ideia
completa e a metodologia.

## Como funciona

INMET (21 anos, horário) → sub-índices seca/enchente/calor → **PCA** (ameaça) → **IDW** (45
estações → 417 municípios) → capacidade adaptativa (IDHM) → **peso per capita que soma 1**.
Mais **KMeans** (arquétipos), **projeção 2030** e **Claude** (explica o score). Tudo não-supervisionado.

## Rodar

```bash
uv sync
uv run python scripts/baixar_municipios_ibge.py   # baixa IBGE + IDHM (uma vez)
uv run python scripts/build_scores.py             # gera data/processed/scores.csv
uv run streamlit run app.py                       # sobe o app
```

O CSV bruto do INMET (`data/raw/clima_bahia.csv`, 549 MB) não vai no git. Baixar do Drive:
```bash
uv run --with gdown python -c "import gdown; gdown.download_folder('https://drive.google.com/drive/folders/1DruOvNchljoSbAJyzR4TP6pTmVzLjQr8', output='data/raw')"
mv "data/raw/clima_bahia_hackathon(1).csv" data/raw/clima_bahia.csv
```

(opcional) `export ANTHROPIC_API_KEY=...` ativa as explicações via Claude; sem a key, usa fallback offline.

## Estrutura

```
src/hackathon/
  indices.py    sub-indices climaticos por estacao (ETCCDI, -9999 -> NaN)
  score.py      PCA + IDW + capacidade + peso per-capita + calculadora
  cluster.py    KMeans (arquetipos de vulnerabilidade)
  forecast.py   projecao temporal 2026-2030
  ai.py         Claude explica/recomenda (fallback offline)
scripts/        baixar_municipios_ibge.py, build_scores.py
app.py          app Streamlit (mapa, calculadora, arquetipos)
```

## Dicionário do dataset INMET

| Coluna | Descrição | Unidade |
| --- | --- | --- |
| ESTACAO | Código da estação (ex.: A401 = Salvador) | ID |
| DATA / HORA | Registro da medição (UTC) | Data/Hora |
| PRECIPITACAO TOTAL | Chuva acumulada na última hora | mm |
| PRESSAO ATMOSFERICA | Pressão do ar na estação | mB |
| RADIACAO GLOBAL | Energia solar | W/m² |
| TEMPERATURA DO AR | Bulbo seco (ambiente) | °C |
| UMIDADE RELATIVA | Vapor de água no ar | % |
| VENTO (RAJADA) | Maior velocidade do vento na hora | m/s |

Valores faltantes vêm como `-9999` (sentinela INMET) — sempre tratar como NaN.
