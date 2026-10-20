# Clone sem atestação de firmware

Cópia operacional da main atual, **sem** declarar hash de firmware on-chain.

O que mudou em relação à main:

- o ESP32 envia só temperatura, umidade e `status` (não envia `firmware_hash`);
- o relay recebe POST em `/leitura` (porta **5001**, para coexistir com o relay de atestação na 5000);
- a transação chama `registrar_leitura(temp, umid, status)` de `sem_atestacao_sensor.vy`, não `registrar(firmwareHash, status)` do ESDRA;
- CSVs em `data/` usam o prefixo `sem_atestacao_` para não misturar com as métricas da atestação.

A carteira, o RPC da IOTA EVM Testnet e a medição de tempo/custo são os mesmos da main.

## Como rodar

Na raiz do repositório:

```text
python sem_atestacao/src/sem_atestacao_novo_servidor_relay.py
# página: http://127.0.0.1:5001/leitura
```

O ESP32 deve apontar para `http://<IPv4-do-PC>:5001/leitura`.

Antes da primeira transação, implante `sem_atestacao_sensor.vy` e cole o endereço em `CONTRACT_ADDRESS` no relay:

```text
python sem_atestacao/src/sem_atestacao_publish_sensores_esp/sem_atestacao_python_script_vincula_a_RPC.py
```

Firmware Arduino: abra a pasta
`sem_atestacao/src/sem_atestacao_publish_sensores_esp/`
(o nome da pasta precisa ser igual ao `.ino`).

```text
pytest sem_atestacao/tests
```
