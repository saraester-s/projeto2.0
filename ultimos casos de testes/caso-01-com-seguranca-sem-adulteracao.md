# Caso 1 — com segurança, sem adulteração → sucesso

CSV: `csv/caso-01-com-seguranca-sem-adulteracao.csv`  
Média do lote 30: `csv/caso-01-com-seguranca-sem-adulteracao-media.csv`  
Média histórica de 45: `csv/caso-01-com-seguranca-sem-adulteracao-media-45.csv`

| campo | valor |
|---|---|
| Segurança | com (`src/`, POST `/atestar`) |
| Adulteração | não |
| Resultado | **sucesso** (HTTP 200 + `tx_hash`) |
| Lote | **30/30** |
| Quando | 2026-10-27 17:05:53 → 2026-10-29 15:56:14 |
| Hash enrolado | `8422ebe782c2f51ab17c330621d0b4c2c29db4175a82929fec0bab04d2ba28b6` |

## Média do lote 30

| quando | amostras | tempo médio envio (ms) | tempo médio confirmação (ms) | custo médio (IOTA) | custo médio (wei) | custo total (IOTA) | custo total (wei) |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2026-10-29 15:56:14 | 30 | 1638,23 | 4673,75 | 0,000221 | 221090000000000 | 0,0066327 | 6632700000000000 |
