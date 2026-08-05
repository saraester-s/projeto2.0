#include <WiFi.h>
#include <Web3.h>
#include <Contract.h>
#include <Util.h>
#include "DHT.h"

// 1. CONFIGURAÇÃO DO SENSOR DHT
#define DHTPIN 21       // Pino digital conectado ao sensor DHT
#define DHTTYPE DHT11   // Tipo do sensor DHT
DHT dht(DHTPIN, DHTTYPE);

// 2. DADOS DA REDE WI-FI
const char* ssid = "Valter Cel 2.4G";   
const char* password = "91346879vl";

// 3. DADOS DA BLOCKCHAIN
String rpc_url = "http://192.168.1.126:7545";     //endereço do wifi
const char* private_key = "0x0f380022f81f21f85815cc175c05dbeb0e8a11d264b64d34d2524b14fb570621"; 
const char* contract_address = "0x6D201D58155Cfb654d4D995e28da74217Af920F2"; 
string minha_carteira = "0xC766B9536918CE7bAAB94BbA1333E48565B7e922"; 

Web3 web3(1337); // Chain ID do Ganache

void setup() {
  Serial.begin(115200);
  dht.begin();
  delay(1000);

  Serial.println("\n=== INICIANDO MODULO ESP32 + DHT11 + WEB3 ===");
  Serial.print("\n[REDE] Conectando ao Wi-Fi: ");
  Serial.println(ssid);
  
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("");
  Serial.println("Wi-Fi conectado com sucesso!");
  Serial.print("Endereço IP da Bancada: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    
    // =========================================================
    // INÍCIO DO MODO DE TESTE (IGNORANDO O SENSOR FÍSICO)
    // =========================================================
    
    // Lendo o sensor (COMENTADO)
    // float temp = dht.readTemperature();
    // float umid = dht.readHumidity();

    // Inserindo dados manuais (FALSOS) para testar a Blockchain
    float temp = 28.5;
    float umid = 65.0;
    bool status_hardware = true;

    // =========================================================
    // FIM DO MODO DE TESTE
    // =========================================================

    Serial.printf("Lido -> Temp: %.2f *C | Umid: %.2f %%\n", temp, umid);

    // Preparando a conexão com o Contrato
    Contract contrato(&web3, contract_address);
    contrato.SetPrivateKey(private_key);

    // Convertendo os dados lidos para o formato numérico da EVM
    uint256_t tempUint = (uint32_t)temp;
    uint256_t umidUint = (uint32_t)umid;
    uint256_t statusUint = status_hardware ? 1 : 0;

    Serial.println("Buscando nonce atual...");
    uint32_t nonce = web3.EthGetTransactionCount(&minha_carteira);

    unsigned long long gasPrice = 20000000000ULL; 
    uint32_t gasLimit = 3000000; 
    string toAddress = contract_address; 
    uint256_t valorWei = 0; 

    Serial.println("Enviando transacao para o Ganache...");
    
    // Atenção: Certificar que o nome da função no Smart Contract é exatamente "registrar"
    string param = contrato.SetupContractData("registrar(uint256,uint256,bool)", &tempUint, &umidUint, &statusUint); 
    
    string tx_hash = contrato.SendTransaction(nonce, gasPrice, gasLimit, &toAddress, &valorWei, &param);

    if (tx_hash == "") {
      Serial.println("Erro: Falha ao enviar transacao (Verifique se o Ganache esta rodando).");
    } else {
      Serial.print("Sucesso! Transacao confirmada. Hash: ");
      Serial.println(tx_hash.c_str());
    }

  } else {
    Serial.println("Wi-Fi desconectado... Tentando reconectar.");
    WiFi.reconnect();
  }
  
  delay(10000);
}