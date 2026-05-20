# Plano — Termômetro Climático da Bahia

Solução para o desafio **"Resiliência Climática e Cidades Inteligentes na Bahia: Antecipando o
Futuro com IA"**.

---

## 1. O Problema

A Bahia vive dois extremos climáticos opostos ao mesmo tempo: **secas devastadoras no semiárido**
e **enchentes urbanas** que atingem comunidades inteiras. O estado tem orçamento limitado de
resiliência climática e precisa decidir **onde investir cada real** para reduzir o máximo de risco
humano possível.

Hoje essa decisão é política e pouco baseada em dados. E a maioria das soluções de IA para clima
para num "vai chover amanhã?" — uma previsão genérica que já existe (INMET, apps de tempo) e não
diz o que fazer com a informação.

**Nossa pergunta é outra: dado um orçamento, quais municípios são mais vulneráveis e merecem
prioridade?**

---

## 2. A Solução

Um **índice de vulnerabilidade climática para os 417 municípios da Bahia** e uma **calculadora de
alocação orçamentária** que distribui qualquer orçamento proporcionalmente ao risco de cada
município.

O produto é um app web (Streamlit) com três telas:

1. **Mapa de risco** — coroplético dos 417 municípios, com camadas por categoria (geral, seca,
   enchente, calor) e a **projeção 2030**. Clicar/selecionar um município mostra a decomposição
   do risco e uma explicação gerada por IA.
2. **Calculadora de orçamento** — o usuário digita o orçamento total (R$); o app devolve uma
   **tabela município por município com o valor destinado**, exportável em CSV. Sliders permitem
   priorizar seca, enchente ou calor e ver a verba se redistribuir em tempo real.
3. **Arquétipos & Projeção** — agrupamento não-supervisionado dos municípios em tipologias de
   vulnerabilidade e a tendência histórica projetada (agravando/estável/melhorando).

**Quem usa:** governo estadual (onde alocar verba), defesa civil (onde está pior), iniciativa
privada e ONGs (onde investir).

---

## 3. Por que é IA de verdade (não-supervisionada)

Não existe um "score verdadeiro" rotulado para treinar um modelo supervisionado. Por isso o motor
é **100% não-supervisionado** — o sinal emerge da estrutura dos dados, não de pesos chutados:

- **PCA (Análise de Componentes Principais)** aprende os pesos da ameaça composta a partir da
  variância dos dados. Não dizemos "seca vale 1/3"; a 1ª componente principal define o peso de
  cada risco. Pitch: *os pesos não foram arbitrados, emergiram dos dados*.
- **KMeans** agrupa os 417 municípios em arquétipos de vulnerabilidade sem rótulos prévios
  (ex.: "seca crônica do sertão", "enchente/chuva extrema litorânea").
- **Projeção temporal**: para cada estação, ajustamos a tendência de uma proxy de ameaça sobre
  21 anos (2000-2021) e projetamos para 2030. É o "antecipando o futuro" do desafio.
- **Claude (Haiku)** traduz os números em linguagem natural e recomenda prioridade de gasto.
  Importante: a IA de linguagem **não calcula o score** (isso é estatística reprodutível); ela só
  explica. Honesto e auditável.

Evitamos deliberadamente "IA falsa" (slider rotulado IA, análise de sentimento de notícia,
chatbot que alucina).

---

## 4. Metodologia do Score

Framework de vulnerabilidade do **IPCC**: risco = ameaça climática moderada pela (falta de)
capacidade de resposta do município.

### 4.1 Sub-índices climáticos por estação (45 estações INMET, 2000-2021)
Calculados a partir de 5,2 milhões de medições horárias. Tratamento: sentinela `-9999` vira NaN;
exige ≥55% de dias válidos por ano; janela temporal comum; estações em pane filtradas.

- **Seca**: aridez (chuva anual baixa) + dias secos consecutivos (CDD) + déficit de chuva
  década-a-década (2000-2010 vs 2011-2021).
- **Enchente**: Rx1day (máxima chuva diária anual, padrão ETCCDI) + nº de dias/ano com chuva
  ≥ 50 mm.
- **Calor**: TX90p (% de dias acima do percentil 90 do período-base — sinal real de aquecimento)
  + tendência da temperatura média.

Cada sub-índice é normalizado para [0,1] por percentil robusto (p5–p95).

### 4.2 Ameaça composta (PCA)
PCA sobre os 3 sub-índices padronizados → 1ª componente principal = ameaça, normalizada a [0,1].

### 4.3 Interpolação espacial (45 → 417)
As 45 estações não cobrem os 417 municípios. Usamos **IDW** (inverse distance weighting, k=5
estações mais próximas, potência=2) sobre os centroides municipais (malha IBGE). A incerteza é
maior no oeste do sertão, sub-amostrado — declarado abertamente.

### 4.4 Capacidade adaptativa e peso final (per capita)
- Capacidade = `1 − IDHM` (IDHM do Atlas Brasil/PNUD, cobre os 417).
- **Peso per capita**: `peso_i = (ameaça_i / (1 + capacidade_i))` normalizado para **somar 1**.
- Decisão de design: **sem população crua no numerador**. Salvador tem população enorme, mas
  baixo risco climático e alta capacidade de se defender sozinha → peso baixíssimo. O sertão pobre
  e seco → peso alto. A verba segue a gravidade do problema, não o tamanho da cidade.

### 4.5 Calculadora
`R$_município = orçamento_total × peso_município`. A soma sempre fecha no orçamento.

### Validação (casos reais do nosso pipeline)
- **Salvador**: ameaça ≈ 0,00, peso ≈ 0 (litoral chuvoso, IDHM alto). Confere com o esperado.
- **Irecê / Juazeiro / Serrinha** (sertão): ameaça > 0,9, entre os maiores pesos.
- Foco SECA via slider → topo: Irecê, Sobradinho, Uibaí. Foco ENCHENTE → Salvador, Lauro de
  Freitas, Camaçari. A geografia bate.

---

## 5. Dados (todos públicos, sem login)

| Fonte | Uso | Acesso |
| --- | --- | --- |
| INMET (histórico horário) | sub-índices climáticos | `data/raw/clima_bahia.csv` (Drive, 549 MB) |
| IBGE Malhas (GeoJSON) | polígonos dos 417 municípios | API v3, chave `codarea` |
| IBGE SIDRA | população 2021 | API v3 agregado 6579 |
| Atlas Brasil / PNUD | IDHM por município | CSV (`Codmun7`) |
| Open-Meteo | alerta de chuva 7-16 dias (opcional) | API sem chave |

---

## 6. Arquitetura

```
INMET CSV + IBGE/IDHM
        |
        v
indices.py  -> sub-indices por estacao (-9999 -> NaN, ETCCDI)
score.py    -> PCA (ameaca) + IDW (45->417) + capacidade + peso per-capita (soma=1)
cluster.py  -> KMeans (arquetipos)
forecast.py -> projecao temporal 2026-2030
ai.py       -> Claude explica/recomenda (fallback offline)
        |
        v
data/processed/scores.csv
        |
        v
app.py (Streamlit) -> mapa + calculadora + arquetipos  -> deploy Streamlit Cloud
```

Reproduzir: `uv run python scripts/baixar_municipios_ibge.py` e
`uv run python scripts/build_scores.py` geram tudo; `uv run streamlit run app.py` sobe o app.

---

## 7. Pitch (1 frase)

> "Não prevemos se vai chover. Usamos 21 anos de dados do INMET, aprendizado não-supervisionado
> (PCA + clustering) e projeção temporal para dizer ONDE o estado deve investir cada real do
> orçamento de resiliência climática — priorizando os municípios mais vulneráveis e com menor
> capacidade de se defenderem sozinhos."

---

## 8. Limitações e próximos passos (honestidade técnica)

- IDHM é de 2010 (último censo municipal oficial). A camada de **capacidade adaptativa é
  extensível**: pode incorporar desemprego, cobertura de saúde e PIB per capita sem mudar a
  fórmula (basta compor um índice de capacidade).
- 45 estações para 417 municípios: IDW é defensável, mas o sertão oeste tem incerteza maior.
  Kriging seria o próximo passo.
- A projeção é uma tendência linear honesta, não um modelo climático físico.
- Camada de validação externa: cruzar com registros de desastres (S2iD/Atlas) e Monitor de Secas
  da ANA confirmaria os scores contra eventos reais.
