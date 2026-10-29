# Caso 3 — sem segurança, sem adulteração → sucesso

CSV: `csv/caso-03-sem-seguranca-sem-adulteracao.csv`  
Média do lote 30: `csv/caso-03-sem-seguranca-sem-adulteracao-media.csv`  
Média histórica de 45: `csv/caso-03-sem-seguranca-sem-adulteracao-media-45.csv`

| campo | valor |
|---|---|
| Segurança | sem (`sem_atestacao/`, POST `/leitura` :5001) |
| Adulteração | não |
| Resultado | **sucesso** (HTTP 200 + `tx_hash`) |
| Lote | **30/30** |
| Quando | 2026-10-29 16:42:11 → 16:49:23 |
| Contrato | o mesmo ESDRA `registrar` (`0xDAc95e767da4376456b132F4b78e18C0b8d0C669`) |
| Hash | zeros on-chain (`HASH_SEM_ATESTACAO`); relay **sem** allowlist |
| DHT11 | 25,2–25,3 °C; umidade 66 % |

## Média do lote 30

| quando | amostras | tempo médio envio (ms) | tempo médio confirmação (ms) | custo médio (IOTA) | custo médio (wei) | custo total (IOTA) | custo total (wei) |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2026-10-29 16:49:23 | 30 | 1664,76 | 4384,17 | 0,000217 | 217250000000000 | 0,0065175 | 6517500000000000 |

## Média histórica de 45 amostras

| quando | amostras | tempo médio envio (ms) | tempo médio confirmação (ms) | custo médio (IOTA) | custo total (IOTA) |
|---|---:|---:|---:|---:|---:|
| 2026-10-19 16:49:51 | 45 | 1378,17 | 3644,64 | 0,000216 | 0,0097119 |
