# Caso 4 — sem segurança, adulteração → sucesso

CSV: `data/caso-04-sem-seguranca-adulteracao.csv`  
Média do lote 30: `data/caso-04-sem-seguranca-adulteracao-media.csv`

Adulteração: `Serial.println("Bancos reais são melhores que virtuais, cuidado.");` no `.ino` sem atestação. Relay **sem** allowlist — a leitura grava mesmo assim.

| campo | valor |
|---|---|
| Segurança | sem (`sem_atestacao/`, POST `/leitura` :5001) |
| Adulteração | sim |
| Resultado | **sucesso** (HTTP 200 + `tx_hash`) |
| Lote | **30/30** |
| Quando | 2026-10-29 17:02:38 → 17:09:33 |
| Contrato | o mesmo ESDRA `registrar` (`0xDAc95e767da4376456b132F4b78e18C0b8d0C669`) |
| Hash | zeros on-chain; ninguém confere firmware |
| DHT11 | 25,1–25,2 °C; umidade 66 % |

## Média do lote 30

| quando | amostras | tempo médio envio (ms) | tempo médio confirmação (ms) | custo médio (IOTA) | custo médio (wei) | custo total (IOTA) | custo total (wei) |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2026-10-29 17:09:33 | 30 | 1481,69 | 4154,59 | 0,000217 | 217250000000000 | 0,0065175 | 6517500000000000 |
