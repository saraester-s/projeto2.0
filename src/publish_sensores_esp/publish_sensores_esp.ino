#include <WiFi.h>
#include <HTTPClient.h>
#include "DHT.h"

// 1. CONFIGURAÇÃO DO SENSOR DHT11
#define DHTPIN 4       // Pino DATA do DHT11 conectado ao GPIO 4
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

// 2. DADOS DA REDE WI-FI ATUAL
const char* ssid = "Sara";
const char* password = "Sara@2026";

// 3. ENDEREÇO DO SERVIDOR RELAY PYTHON (Flask na sua rede local)
const char* serverUrl = "http://192.168.18.6:5000/atestar";

void setup() {
  Serial.begin(115200); // Ajustado para 115200 baud
  dht.begin();
  delay(1000);

  Serial.println("\nA conectar ao Wi-Fi...");
  WiFi.begin(ssid, password);

  int tentativas = 0;
  while (WiFi.status() != WL_CONNECTED && tentativas < 20) {
    delay(500);
    Serial.print(".");
    tentativas++;
  }

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("\nFalha ao conectar. A reiniciar o hardware...");
    ESP.restart();
  }

  Serial.println("\nWi-Fi conectado com sucesso!");
  Serial.print("Endereço IP do ESP32: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {

    // =========================================================
    // LEITURA DO SENSOR DHT11
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

    Serial.print("Temperatura: ");
    Serial.print(temp);
    Serial.print(" *C | Umidade: ");
    Serial.print(umid);
    Serial.println(" %");

    // =========================================================
    // ENVIO VIA HTTP POST PARA O RELAY PYTHON (IOTA EVM TESTNET)
    // =========================================================
    HTTPClient http;
    
    if (http.begin(serverUrl)) {
      http.addHeader("Content-Type", "application/json");
      http.setTimeout(10000); // Timeout de 10 segundos

      // Hash de firmware em formato bytes32 válido (64 caracteres hexadecimais sem '0x')
      String firmwareHashHex = "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef";

      // Monta o payload JSON idêntico ao que o request.get_json() espera no Python
      String payload = "{\"temperature\": " + String(temp) + 
                       ", \"humidity\": " + String(umid) + 
                       ", \"status\": " + (status_hardware ? "true" : "false") + 
                       ", \"firmware_hash\": \"" + firmwareHashHex + "\"}";

      int httpResponseCode = http.POST(payload);

      if (httpResponseCode > 0) {
        String response = http.getString();
        Serial.println("Sucesso! Resposta do Relay:");
        Serial.println(response);
      } else {
        Serial.print("Erro HTTP ao contatar o servidor relay: ");
        Serial.print(httpResponseCode);
        Serial.print(" (");
        Serial.print(http.errorToString(httpResponseCode));
        Serial.println(")");
      }
      http.end();
    } else {
      Serial.println("Erro crítico: Não foi possível inicializar a conexão HTTPClient.");
    }

  } else {
    Serial.println("Wi-Fi desconectado... A tentar reconectar.");
    WiFi.reconnect();
  }

  delay(10000); // Aguarda 10 segundos para o próximo ciclo
}