# Resumo do projeto

O projeto registra dados de um dispositivo IoT na **IOTA EVM Testnet**, para que o histórico fique gravado na blockchain e possa ser consultado depois.

Um **ESP32** lê um sensor **DHT11** (temperatura e umidade no GPIO 4), conecta ao Wi-Fi e, a cada 10 segundos, envia uma transação para o contrato `0x4849b3b059D063aF45d50591086daCB1D821E0C7` usando a biblioteca **Web3E**. A rede está configurada com o chain ID **1076**.

O contrato em Vyper (`sensor.vy`) guarda um histórico por endereço do dispositivo. Cada registro é uma atestação no estilo **ESDRA**: hash do firmware, timestamp da rede e um status de validade (`isValid`). A ideia é deixar um rastro imutável da integridade do dispositivo, e não só a leitura pontual do sensor.

Há também um simulador antigo em Python (`archived/sensor_simulado.py`), que fazia a mesma chamada `registrar` contra uma blockchain local (Ganache), e um patch da Web3E que aponta o chain ID **1075** para o RPC `json-rpc.evm.testnet.iotaledger.net`.
