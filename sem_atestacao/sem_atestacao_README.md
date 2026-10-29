# Clone sem atestação de firmware

Cópia operacional da main atual, **sem** declarar hash de firmware on-chain.

O que mudou em relação à main:

- o ESP32 envia só temperatura, umidade e `status` (não envia `firmware_hash`);
- o relay recebe POST em `/leitura` (porta **5001**, para coexistir com o relay de atestação na 5000);
- a transação chama o **mesmo** `registrar(firmwareHash, status)` em `0xDAc95e7…` (hash zerado). Não há allowlist: código adulterado também grava.
- CSVs em `data/caso-03-sem-seguranca-*` e log vivo `data/caso-sem-seguranca.csv`.

A carteira, o RPC da IOTA EVM Testnet e a medição de tempo/custo são os mesmos da main.

## Como rodar

Na raiz do repositório:

```text
python sem_atestacao/src/sem_atestacao_novo_servidor_relay.py
# página: http://127.0.0.1:5001/leitura
```

O ESP32 deve apontar para `http://<IPv4-do-PC>:5001/leitura`.

Firmware Arduino: abra a pasta
`sem_atestacao/src/sem_atestacao_publish_sensores_esp/`
(o nome da pasta precisa ser igual ao `.ino`).

```text
pytest sem_atestacao/tests
```
