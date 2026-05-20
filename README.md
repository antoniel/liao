# Clima Bahia — Hackathon

Dataset com medições horárias de estações meteorológicas da Bahia (fonte: INMET).

Arquivo: `clima_bahia_hackathon(1).csv`

## Dicionário de Dados

| Coluna | Descrição | Unidade |
| --- | --- | --- |
| **ESTACAO** | Código de identificação da estação (ex: `A401` é Salvador). | ID |
| **DATA / HORA** | Registro temporal da medição (UTC). | Data/Hora |
| **PRECIPITACAO TOTAL** | Quantidade de chuva acumulada na última hora. | mm |
| **PRESSAO ATMOSFERICA** | Pressão do ar na estação. Ajuda a prever frentes frias. | mB |
| **RADIACAO GLOBAL** | Intensidade da energia solar. Crucial para modelos de calor. | W/m² |
| **TEMPERATURA DO AR** | Temperatura medida no "bulbo seco" (ambiente). | °C |
| **UMIDADE RELATIVA** | Porcentagem de vapor de água no ar. | % |
| **VENTO (RAJADA)** | A maior velocidade do vento registrada na hora. | m/s |

## Colunas adicionais no CSV

Além das principais acima, o CSV traz variações min/max horárias:

- `PRESSAO ATMOSFERICA MAX./MIN. NA HORA ANT. (mB)`
- `TEMPERATURA MAXIMA/MINIMA NA HORA ANT. (°C)`
- `TEMPERATURA DO PONTO DE ORVALHO` e `ORVALHO MAX./MIN. NA HORA ANT. (°C)`
- `UMIDADE REL. MAX./MIN. NA HORA ANT. (%)`
- `VENTO, DIRECAO HORARIA (gr)` e `VENTO, VELOCIDADE HORARIA (m/s)`
