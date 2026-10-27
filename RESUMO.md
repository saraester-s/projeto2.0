# Documentação do projeto

Este documento descreve o trabalho de ponta a ponta: o que é atestação, como ela é feita aqui, e cada parte do repositório.

Índice:

1. [O que é atestação](#1-o-que-é-atestação)
2. [Como a atestação é feita neste projeto](#2-como-a-atestação-é-feita-neste-projeto)
3. [Arquitetura](#3-arquitetura)
4. [Contrato `sensor.vy`](#4-contrato-sensorvy)
5. [Firmware ESP32](#5-firmware-esp32)
6. [Relay Flask](#6-relay-flask)
7. [Testes](#7-testes)
8. [Desempenho medido](#8-desempenho-medido)
9. [Como rodar](#9-como-rodar)
10. [Limites e o que ainda não está atestado](#10-limites-e-o-que-ainda-não-está-atestado)
11. [Mapa de arquivos](#11-mapa-de-arquivos)

---

## 1. O que é atestação

**Atestação** (em inglês, *attestation*), no contexto de IoT e blockchain, é o ato de um dispositivo **declarar um fato sobre si mesmo** de forma que um terceiro consiga conferir depois, sem precisar estar ao lado da placa.

Não é a mesma coisa que “enviar a temperatura”. Enviar a temperatura é telemetria. Atestar é dizer, por exemplo:

- “o firmware que estou rodando tem este hash”;
- “neste instante da rede, considero o hardware válido”;
- “esta declaração foi assinada pela identidade desta placa”.

Em **atestação remota de firmware** (*remote attestation*), o fluxo clássico é:

1. Alguém (ou o próprio dispositivo) **mede** o software — em geral um hash criptográfico do binário.
2. Essa medida vai acompanhada de um **status** (íntegro / comprometido) e de uma **identidade** (chave, endereço EVM, certificado).
3. O resultado é **publicado** num lugar difícil de apagar — aqui, um contrato na IOTA EVM Testnet.
4. Depois, um auditor consulta o histórico: “naquele bloco, este endereço afirmou este hash”.

O nome **ESDRA** no código antigo (simulador, script de deploy, ABI `registrar(bytes32, bool)`) é exatamente esse molde: guardar, por dispositivo, um `firmwareHash`, um `isValid`/`status` e o `timestamp` do bloco.

O que a blockchain **garante** nesse modelo:

- que a transação existiu;
- que foi assinada por quem controla a chave de `msg.sender`;
- que o registro não some nem é reescrito sem outra transação.

O que ela **não garante** sozinha:

- que o hash foi calculado de verdade a partir da flash;
- que o DHT11 existia e mediu aqueles números;
- que ninguém copiou a chave privada do firmware.

Essa diferença é o coração da pesquisa deste repositório.

---

## 2. Como a atestação é feita neste projeto

Hoje existem **dois desenhos** que convivem. Vale lê-los juntos, não misturados.

### 2.1 Caminho que roda no laboratório (atestação on-chain de firmware)

Este é o circuito que o hardware usa quando o relay está no ar.

```
DHT11 → ESP32 → HTTP POST /atestar → Flask no PC → transação EVM → IOTA Testnet
                                                      ↓
                                        CSV + página localhost
```

Passo a passo:

1. **Leitura.** O ESP32 (`src/publish_sensores_esp/publish_sensores_esp.ino`) lê temperatura e umidade no GPIO 4. Se o DHT11 devolve NaN, **não há atestação**: não há POST, não há transação, espera 2 segundos e tenta de novo.

2. **Pacote.** Com leitura válida, o sketch monta um JSON com `snprintf` (origem, temperatura, umidade, `status`, `firmware_hash` de 64 hex). O hash é o SHA-256 canônico do `.ino` (`src/firmware.py` zera o campo `firmwareHash` na medição). Não é medido na flash do chip.

3. **Transporte.** A cada 10 segundos o ESP32 faz POST para `http://<IPv4-do-PC>:5000/atestar` na mesma rede Wi-Fi 2.4 GHz. `127.0.0.1` no chip é o próprio ESP, não o computador.

4. **Filtro no relay.** `src/novo_servidor_relay.py` só segue se temperatura e umidade forem numéricas e plausíveis (cerca de −20 a 80 °C e 0 a 100 % de umidade). JSON inválido ou sem `firmware_hash` vira erro. Leitura ruim vira `ignored` e **não entra na média**.

5. **Allowlist.** Só aceita exatamente 64 hex iguais a `FIRMWARE_HASH_ESPERADO`. Hash curto, lixo ou código alterado → HTTP 403, sem transação.

6. **Assinatura.** O PC (não o ESP) monta a chamada `registrar(firmwareHash, status)` no contrato implantado na testnet, com `gasPrice` legado (a IOTA EVM deste ambiente rejeita EIP-1559). Tenta o `chainId` que o RPC reporta e, se vier *chain ID mismatch*, tenta 1075 e 1076.

7. **Publicação.** `send_raw_transaction` + espera do recibo (até 120 s). A identidade on-chain desta atestação é a **carteira do relay**, porque é ela que assina.

8. **Consulta humana.** GET em `http://127.0.0.1:5000/atestar` mostra hash, status, tx, tempo e custo. Os CSVs em `data/` guardam o mesmo para o relatório.

Em uma frase: **atestamos que “esta conta EVM, neste bloco, registrou este hash de firmware e este booleano”.** Temperatura e umidade viajam no JSON para validar o hardware e medir desempenho; **não entram no `registrar` atual**.

Contrato usado nesse caminho: `0xDAc95e767da4376456b132F4b78e18C0b8d0C669`, função `registrar(bytes32 firmwareHash, bool status)`. É o molde ESDRA, não o `registrar_leitura` do `sensor.vy`.

### 2.2 Caminho desenhado para o contrato novo (leitura IoT on-chain)

`src/sensor.vy` descreve o próximo passo: gravar **a leitura** (temp, umidade, `hardwareValido`) por endereço da placa, com allowlist e faixa 0–100.

Aí a “atestação” muda de objeto: em vez do hash do firmware, o fato declarado é **a amostra do sensor**, carimbada com `block.timestamp`. Continua sendo uma declaração assinada, não uma prova física do DHT11.

`src/firmware.py` hoje só mede e enrola o hash do `.ino`. O sketch de laboratório só decide “NaN → não posta”; faixa 0–100 e `hardwareValido` só existem de fato em `sensor.vy` / `contract_logic.py`. A tabela abaixo é o desenho do contrato novo:

| Situação | Camada | Subcategoria | O que acontece |
|---|---|---|---|
| DHT devolve NaN | Off-chain | `DHT11_NAN` | Não envia transação; tenta de novo |
| Temperatura > 100 | On-chain | `FAIXA_TEMPERATURA` | Envia; o contrato recusa pelo assert de temp |
| Umidade > 100 | On-chain | `FAIXA_UMIDADE` | Envia; o contrato recusa pelo assert de umidade |
| Hardware marcado inválido | On-chain | `HARDWARE_INVALID` | Envia; grava o status |
| Leitura ok | On-chain | `DHT11_OK` | Envia; grava registro completo |

A subcategoria existe para as etapas seguintes não “adivinhar”: mesma camada on-chain, regras diferentes (campo de temperatura vs campo de umidade, gravar tudo vs só recusar).

### 2.3 Como conferir uma atestação depois

1. Abrir a página do relay ou o CSV e copiar o `tx_hash`.
2. Procurar o hash no explorador da IOTA EVM Testnet.
3. No contrato ESDRA, o estado fica indexado pelo endereço que assinou (`msg.sender`) e pelo índice da atestação.
4. No `sensor.vy` (quando implantado e usado), a consulta é `historico[endereço][índice]` e `contagem_leituras[endereço]`.

---

## 3. Arquitetura

```
                    Wi-Fi 2.4 GHz
  [DHT11]--GPIO4--[ESP32]----POST JSON---->[PC: Flask :5000]
                                                 |
                                                 | Web3.py, chave do PC
                                                 v
                                         [IOTA EVM Testnet]
                                                 |
                          +----------------------+----------------------+
                          |                                             |
                   contrato ESDRA                                (alvo futuro)
              registrar(hash, status)                         sensor.vy
                                                                registrar_leitura
```

Histórico do desenho:

- Primeiro o ESP falava direto com a cadeia (Web3E, patch de nós IOTA, chain ID 1075/1076). Isso exigia chave na placa e lutava com RPC.
- O simulador `archived/sensor_simulado.py` fazia o mesmo `registrar` contra Ganache.
- O laboratório atual coloca o PC no meio: mais fácil de medir, de depurar Wi-Fi e de não estourar gas no chip — com o custo de a assinatura on-chain ser do relay.

---

## 4. Contrato `sensor.vy`

Arquivo: `src/sensor.vy` (Vyper ^0.4.0). ABI em `abi.json`.

Estrutura `RegistroIoT`: temperatura, umidade, `hardwareValido`, timestamp.

Armazenamento:

- `historico[placa][índice]` — gaveta infinita por dispositivo;
- `contagem_leituras[placa]` — próximo índice;
- `dispositivos_autorizados` — quem pode chamar `registrar_leitura`;
- `owner` — quem autoriza e revoga.

Regras de `registrar_leitura(_temp, _umid, _status)`:

1. `msg.sender` precisa estar autorizado.
2. `_temp <= 100` e `_umid <= 100`.
3. Grava o pacote com `block.timestamp`.
4. Incrementa o contador daquela placa.
5. Emite `LeituraRegistrada`.

`src/contract_logic.py` é um espelho em Python das mesmas regras, para pytest sem compilador Vyper.

Contratos velhos (`mycontract.vy`, `mycontact.vy` — typo de uma cópia de `sensor.vy` —, `sensor.vy` na raiz) estão no `.gitignore`. O script `src/publish_sensores_esp/python_script_vincula_a_RPC.py` ainda faz deploy do bytecode ESDRA antigo (e ainda carrega a mesma chave do relay em texto claro).

---

## 5. Firmware ESP32

Arquivo: `src/publish_sensores_esp/publish_sensores_esp.ino`.

O que ele faz hoje:

- biblioteca DHT + HTTPClient (não Web3E neste sketch);
- Wi-Fi STA direto no SSID de laboratório (`Sara`), sem scan;
- JSON com `snprintf` e POST em host/porta/caminho explícitos (`192.168.18.6:5000/atestar`);
- intervalo de 10 s após leitura válida.

O modelo testável em `src/firmware.py` mede o SHA-256 do `.ino` e compara com o hash enrolado. O sketch que está na placa **não** chama Web3E.

**Atenção operacional:** SSID, senha e URL do relay são locais. Trocar de rede exige atualizar os três. Não commitar senha nova em texto claro se for possível evitar; o sketch atual ainda traz credenciais de laboratório.

---

## 6. Relay Flask

Arquivo: `src/novo_servidor_relay.py`.

- Sobe em `0.0.0.0:5000` (acessível na LAN).
- Tenta RPCs `json-rpc.evm.testnet.iota.cafe` e `json-rpc.evm.testnet.iotaledger.net`.
- GET `/` devolve JSON de status; GET `/atestar` é a página que recarrega a cada 5 s; POST `/atestar` é o hardware.
- Lote de desempenho: 30 envios **reais** (DHT válido + tx confirmada).
- Média acumulada reescrita em `data/performance_media_total.csv`.

A chave EVM e o `WALLET_ADDRESS` (`0x316e45d3…874Ef6`) usados para assinar estão no código do relay, não no `.ino`. Para qualquer uso fora do laboratório, isso deveria ir para variável de ambiente (o `.env` já está no `.gitignore`).

---

## 7. Testes

`pytest` (`pytest.ini` aponta `tests/`, `pythonpath = .`). Dependências em `requirements.txt`: pytest, Flask e web3.

Só há o teste de hash de firmware:

- com atestação: `tests/test_firmware_hash.py` — código alterado muda o hash e a atestação é recusada;
- sem atestação: `sem_atestacao/tests/sem_atestacao_test_firmware_hash.py` — o hash muda e a leitura mesmo assim grava;
- manual: `python src/teste_manual_hash.py` (opcional `--hash` e `--enviar`).

---

## 8. Desempenho medido

Coletado em 17 de outubro de 2026, só com DHT válido:

| Conjunto | Amostras | Tempo médio até envio | Tempo médio até confirmação | Custo médio | Custo total |
|---|---|---|---|---|---|
| Lote (`performance_resumo.csv`) | 30 | ~1616 ms | ~4057 ms | ~0,000851 IOTA | ~0,0255 IOTA |
| Série 45 (`performance_media_45.csv` / `performance_media_total.csv`) | 45 | ~1586 ms | ~4030 ms | ~0,000851 IOTA | ~0,0383 IOTA |

Cada linha bruta está em `data/performance_atestacoes.csv` (hash da tx, gas, temp, umidade).

---

## 9. Como rodar

1. Python 3 e `pip install -r requirements.txt` (pytest, Flask, web3).
2. `python src/novo_servidor_relay.py`
3. No navegador: `http://127.0.0.1:5000/atestar`
4. No `.ino`, IPv4 atual do PC (`ipconfig`) e a mesma Wi-Fi 2.4 GHz do ESP32.
5. Gravar o sketch e abrir o Serial (115200).
6. Testes: `pytest` na raiz do repositório.

Mudança de rede: atualizar SSID/senha no firmware e a URL `http://NOVO_IP:5000/atestar`. O Flask não precisa mudar de porta.

---

## 10. Limites e o que ainda não está atestado

Funciona hoje: sensor → JSON com hash enrolado → relay (403 se o código mudou) → testnet → CSV/página; números de latência e custo com hardware real.

Ainda **não** é atestação forte:

- o hash é do **arquivo-fonte** `.ino`, não da imagem na flash;
- quem assina na cadeia é o PC, não um elemento seguro no ESP32;
- o contrato novo acredita no booleano que o remetente manda;
- temperatura/umidade do laboratório não estão no storage do contrato ESDRA que o relay chama;
- `sensor.vy` ainda não é o destino das transações do relay.

O contraste experimental está no clone `sem_atestacao/`: a leitura grava mesmo com o sketch alterado.

---

## 11. Mapa de arquivos

| Caminho | Papel |
|---|---|
| `src/sensor.vy` | Contrato de leituras IoT (alvo do desenho novo) |
| `src/contract_logic.py` | Espelho Python do contrato |
| `src/firmware.py` | Medição SHA-256 e hash enrolado |
| `src/teste_manual_hash.py` | Teste manual do hash (local ou POST no relay) |
| `src/novo_servidor_relay.py` | Relay + atestação ESDRA + métricas |
| `src/publish_sensores_esp/publish_sensores_esp.ino` | Firmware do laboratório |
| `src/publish_sensores_esp/python_script_vincula_a_RPC.py` | Deploy do bytecode ESDRA |
| `abi.json` | ABI do `sensor.vy` |
| `tests/` | Teste: código alterado → hash recusado |
| `data/` | CSVs de desempenho |
| `archived/sensor_simulado.py` | Simulador antigo (Ganache + `registrar`) |
| `patch_nodes_iota.txt` | Patch Web3E (nós IOTA / chain ID) |
| `docs/search_strings.md` | Strings de busca bibliográfica |
| `README.md` | Porta de entrada no GitHub; aponta para este arquivo |
| `RESUMO.md` | Esta documentação |
| `requirements.txt` | pytest, Flask, web3 |
| `mycontact.vy` | Cópia local (typo) de `sensor.vy`; ignorada pelo Git |
| `Web3E-master.zip` | Biblioteca do desenho antigo (ESP falando direto com a EVM) |

Em uma frase: **atestação, aqui, é publicar na testnet uma declaração assinada sobre o dispositivo; o laboratório já faz isso com hash de firmware via relay, e o contrato novo prepara o mesmo gesto para a leitura do sensor.**
