# Caso 2 — com segurança, adulteração → falha

CSV: `csv/caso-02-com-seguranca-adulteracao.csv`

Adulteração: `Serial.println("Bancos reais são melhores que virtuais, cuidado.");` no `.ino`. Hash apresentado diferente do enrolado.

| campo | valor |
|---|---|
| Segurança | com (`src/`, POST `/atestar`) |
| Adulteração | sim |
| Resultado | **falha** (HTTP **403**, sem transação) |
| Hash enrolado | `8422ebe782c2f51ab17c330621d0b4c2c29db4175a82929fec0bab04d2ba28b6` |
| Hash apresentado | `665704c91f218e2e3f8b13c595ec15898215f4b9ed65af0664448c7e1a84a275` |
| HTTP | **403** (nenhum 200) |
| Quando | 2026-10-29 16:12:29 → 16:17:24 |
| DHT11 | 24,9–25,0 °C; umidade 67–68 % |
| tx / custo | vazio |

## Recorte (igual ao lote de 30)

| quando | amostras | HTTP | tx | custo total (IOTA) |
|---|---:|---|---|---:|
| 2026-10-29 16:17:24 | 30 | 403 | nenhuma | 0 |

As 30 linhas brutas estão no CSV. Mensagem: `Hash de firmware nao enrolado. Codigo alterado nao e aceito.`
