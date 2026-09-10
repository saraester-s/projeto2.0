#include <WiFi.h>
#include <Web3.h>
#include <Contract.h>
#include <Util.h>
#include "DHT.h" // Biblioteca oficial Adafruit

// 1. CONFIGURAÇÃO DO SENSOR DHT
#define DHTPIN 4       // Pino DATA do DHT11 conectado ao GPIO 4
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

// 2. DADOS DA REDE WI-FI 
const char* ssid = "SargonDrase.2.4Ghz";
const char* password = "Yeezus050494";

// 3. DADOS DA BLOCKCHAIN — IOTA EVM TESTNET
const char* private_key = "0x0f380022f81f21f85815cc175c05dbeb0e8a11d264b64d34d2524b14fb570621";
const char* contract_address = "0xa0ff6cbadb6fd4f3dda790e3e529fa8e3c32c5db"; // ATUALIZADO: contrato real deployado na testnet
string minha_carteira = "0x316e45d3A5DF8AfE6091a746522db3b670874Ef6";

Web3 web3(1076);  // IOTA EVM Testnet

void setup() {
  Serial.begin(115200);
  dht.begin();
  delay(1000);  

  Serial.println("Conectando ao Wi-Fi...");
  WiFi.begin(ssid, password);

  int tentativas = 0;
  while (WiFi.status() != WL_CONNECTED && tentativas < 20) {
    delay(500);
    Serial.print(".");
    tentativas++;
  }

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("\nFalha ao conectar. Reiniciando o hardware de forma segura...");
    ESP.restart(); 
  }

  Serial.println("");
  Serial.println("Wi-Fi conectado com sucesso!");
  Serial.print("Endereço IP do ESP32: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {

    // =========================================================
    // LEITURA REAL DHT11
    // =========================================================
    float temp = dht.readTemperature();
    float umid = dht.readHumidity();
    bool status_hardware = true;

    if (isnan(temp) || isnan(umid)) {
      Serial.println("Erro: Falha ao ler o sensor DHT11! Verifique a fiação no pino 4.");
      status_hardware = false;
      delay(2000);
      return; 
    }
    // =========================================================

    Serial.print("Temperatura: ");
    Serial.print(temp);
    Serial.print(" *C | Umidade: ");
    Serial.print(umid);
    Serial.println(" %");

    Contract contrato(&web3, contract_address);
    contrato.SetPrivateKey(private_key);

    uint256_t tempUint = (uint32_t)temp;
    uint256_t umidUint = (uint32_t)umid;
    uint256_t statusUint = status_hardware ? 1 : 0;

    Serial.println("Buscando nonce atual...");
    uint32_t nonce = web3.EthGetTransactionCount(&minha_carteira);

    long long int gasPrice = web3.EthGasPrice();
    Serial.print("Gas Price atual da rede: ");
    Serial.println((long)gasPrice);

    uint32_t gasLimit = 3000000;
    string toAddress = contract_address;
    uint256_t valorWei = 0;

    Serial.println("Enviando transacao para a IOTA EVM Testnet...");

    string param = contrato.SetupContractData("registrar_leitura(uint256,uint256,bool)", &tempUint, &umidUint, &statusUint);

    string tx_hash = contrato.SendTransaction(nonce, gasPrice, gasLimit, &toAddress, &valorWei, &param);

    if (tx_hash == "") {
      Serial.println("Erro: Falha ao enviar transacao.");
    } else {
      Serial.print("Sucesso! Hash da Transacao: ");
      Serial.println(tx_hash.c_str());
    }

  } else {
    Serial.println("Wi-Fi desconectado... Tentando reconectar.");
    WiFi.reconnect();
  }

  delay(10000);
}