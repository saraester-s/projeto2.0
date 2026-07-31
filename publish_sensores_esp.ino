#include <WiFi.h>
#include <Web3.h>
#include <Contract.h>
#include "DHT.h"

// CONFIGURAÇÃO SENSOR
#define DHTPIN 21
#define DHTTYPE DHT11

DHT dht(DHTPIN, DHTTYPE);

// DADOS DA REDE WI-FI (Com aspas!)
const char* ssid = "SargonDrase.2.4Ghz";
const char* password = "Yeezus050494";

// Defina a URL como uma String ou ajuste o construtor para o padrão que a Web3E espera
String rpc_url = "http://192.168.1.15:7545";
const char* private_key = "a7249ee56dc740da48be024a42fe94c384c1b321f1acd7081d646da1149210f0";
const char* contract_address = "0x7216cc37dcdcfc63ae925d8e7e48dd9e41df3838";

Web3 web3(1337);  // 1337 é o Chain ID padrão do Ganache local

void conectarWiFi() {
  Serial.print("\n[REDE] A conectar ao Wi-Fi: ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.print("\n[REDE] Conectado! IP da Bancada: ");
  Serial.println(WiFi.localIP());
}

void setup() {
  Serial.begin(115200);
  dht.begin();
  delay(1000);

  Serial.println("\n=== INICIANDO MODULO ESP32 + DHT11 + WEB3 ===");
  conectarWiFi();
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {

    // Leitura física
    float temp = dht.readTemperature();
    float umid = dht.readHumidity();
    bool status_hardware = true;

    // Validação
    if (isnan(temp) || isnan(umid)) {
      Serial.println("Erro: Falha na leitura do DHT11. Verifique o jumper no pino 21!");
      status_hardware = false;
      delay(2000);
      return;
    }

    Serial.printf("Lido -> Temp: %.2f C | Umid: %.2f %%\n", temp, umid);

    // Preparando a conexão com o Contrato
    Contract contrato(&web3, contract_address);
    contrato.SetPrivateKey(private_key);

    // Convertendo os dados lidos para o formato numérico que a EVM (Blockchain) entende
    uint256_t tempUint = (uint32_t)temp;
    uint256_t umidUint = (uint32_t)umid;
    uint256_t statusUint = status_hardware ? 1 : 0;  // Booleanos entram como 0 ou 1 na EVM

    Serial.println("Enviando transacao para o Ganache...");

    // Configura a chamada da função Vyper com as variáveis convertidas
    string param = contrato.SetupContractData("registrar_leitura(uint256,uint256,bool)", &tempUint, &umidUint, &statusUint);

    // Dispara a transação de fato
    // 1. Configura os parâmetros obrigatórios da Web3E para a transação
    uint32_t nonce = 0;                            // Número da transação (pode precisar de ajuste dinâmico futuramente)
    unsigned long long gasPrice = 20000000000ULL;  // Preço do gás (20 Gwei)
    uint32_t gasLimit = 3000000;                   // Limite de gás para a execução do contrato
    string toAddress = contract_address;           // Endereço de destino
    uint256_t valorWei = 0;                        // Valor em ether a ser transferido (0, pois só queremos salvar dados)

    // 2. Dispara a transação passando os 6 argumentos exatos que a biblioteca exige
    string tx_hash = contrato.SendTransaction(nonce, gasPrice, gasLimit, &toAddress, &valorWei, &param);

    if (tx_hash == "") {
      Serial.println("Erro: Falha ao enviar transacao (Verifique se o Ganache esta rodando).");
    } else {
      Serial.print("Sucesso! Transacao confirmada. Hash: ");
      Serial.println(tx_hash.c_str());
    }

  } else {
    Serial.println("Wi-Fi desconectado. Tentando reconectar...");
    WiFi.reconnect();
  }

  // Espera 10 segundos antes de enviar a próxima leitura
  delay(10000);
}