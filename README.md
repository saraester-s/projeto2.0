# projeto2.0 — IoT e atestação na IOTA EVM Testnet

ESP32 + DHT11, contrato Vyper e um relay Flask que publica atestações na [IOTA EVM Testnet](https://wiki.iota.org/).

A documentação completa (o que é atestação, como ela é feita, cada parte do repositório, métricas e limites) está em **[RESUMO.md](RESUMO.md)**.

## Atalhos

```text
pytest
python src/novo_servidor_relay.py
# página: http://127.0.0.1:5000/atestar
```

O ESP32 deve apontar para o IPv4 do PC na mesma Wi-Fi 2.4 GHz, não para `127.0.0.1`.
