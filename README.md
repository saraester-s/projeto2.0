# projeto2.0 — atestação de firmware IoT na IOTA EVM Testnet

ESP32 + DHT11 enviam temperatura, umidade e um **hash SHA-256 do sketch**. O relay Flask no PC só publica a transação se esse hash for o **enrolado**. Caso contrário responde **403** e não chama o contrato.

Documentação longa: **[RESUMO.md](RESUMO.md)**. Clone sem hash: **[sem_atestacao/sem_atestacao_README.md](sem_atestacao/sem_atestacao_README.md)**.

## Estado do laboratório (outubro 2026)

| Peça | Valor atual |
|---|---|
| Wi-Fi 2.4 GHz | SSID `Sara` (credenciais no `.ino`) |
| PC (relay) | `192.168.18.6:5000` |
| ESP32 | `192.168.18.8` (DHCP) |
| POST | `http://192.168.18.6:5000/atestar` |
| Página | [http://127.0.0.1:5000/atestar](http://127.0.0.1:5000/atestar) |
| Hash enrolado | `8422ebe782c2f51ab17c330621d0b4c2c29db4175a82929fec0bab04d2ba28b6` |
| Contrato ESDRA | `0xDAc95e767da4376456b132F4b78e18C0b8d0C669` |
| Função on-chain | `registrar(bytes32 firmwareHash, bool status)` |
| Chain | IOTA EVM Testnet (`1075` / `1076`) |
| DHT11 | GPIO 4; NaN não gera POST |

No Serial, envio aceito parece com isto: `JSON len=152 hash_len=64` e **HTTP 200** com `tx_hash`. `hash_len` diferente de 64 ou **HTTP 403** significam hash incompleto ou código que não está na allowlist. `HTTP -1 connection refused` é rede/firewall, não hash.

O JSON é montado com `snprintf` (não `String +=`): o concatenar do Arduino cortava o último nibble do hash (63 hex) e o relay recusava.

## Como a atestação funciona

1. `src/firmware.py` mede SHA-256 do arquivo `.ino` **depois de zerar** o campo `firmwareHash` (64 zeros). Assim o valor colado no sketch não entra na conta.
2. O resultado vira `FIRMWARE_HASH_ESPERADO_HEX` e a constante `firmwareHash` no `.ino`. Os dois têm de ser iguais para o laboratório aceitar.
3. A cada 10 s, com DHT válido, o ESP faz POST JSON (`origem`, `temperature`, `humidity`, `status`, `firmware_hash`).
4. `src/novo_servidor_relay.py` exige 64 hex e `hash_esta_enrolado`. Match → assina `registrar` com a carteira do PC. Sem match → 403, sem transação.
5. Temperatura e umidade validam o hardware e entram no CSV; **não** vão no `registrar` atual.

Isto prova que o **código-fonte apresentado** é o enrolado. Não prova a imagem na flash nem que o ESP assinou (quem assina é o PC).

## Como rodar

```text
pip install -r requirements.txt
python src/novo_servidor_relay.py
```

Navegador: `http://127.0.0.1:5000/atestar`. O ESP **não** usa `127.0.0.1`.

Arduino IDE: pasta `src/publish_sensores_esp/` (nome da pasta = nome do `.ino`). Serial 115200. Se o IPv4 do PC mudar, atualize `relayHost` no sketch.

```text
pytest
pytest sem_atestacao/tests
python src/teste_manual_hash.py
```

## Teste manual de recusa

1. Altere qualquer linha do `.ino` (um comentário basta).
2. `python src/teste_manual_hash.py` — anote **arquivo agora**.
3. Cole esse hex em `firmwareHash` no `.ino`.
4. **Não** mude `FIRMWARE_HASH_ESPERADO_HEX` em `src/firmware.py`.
5. Grave o chip: POST deve ser **403** (`Hash de firmware nao enrolado`).

Para voltar a aceitar: rode o script de novo e atualize **os dois** campos com o mesmo hex; reinicie o relay (ele lê o enrolado na subida).

## Clone sem atestação

Mesmo hardware, **sem** `firmware_hash`. Porta **5001**, POST `/leitura`, contrato `registrar_leitura`. Código em `sem_atestacao/`.

## Arquivos que importam

| Arquivo | Função |
|---|---|
| `src/publish_sensores_esp/publish_sensores_esp.ino` | Firmware com hash no POST `/atestar` |
| `src/firmware.py` | Medição canônica e allowlist |
| `src/teste_manual_hash.py` | Conferência local (e `--enviar` no relay) |
| `src/novo_servidor_relay.py` | Flask :5000, 403 se hash errado, tx + CSV |
| `src/sensor.vy` | Contrato de leituras (desenho; o relay de lab ainda chama o ESDRA) |
| `tests/test_firmware_hash.py` | Código alterado → hash recusado |
| `data/performance_*.csv` | Tempos e custo das atestações reais |
| `sem_atestacao/` | Pipeline paralelo sem allowlist de firmware |
