#include <WiFi.h>
#include <HTTPClient.h>
#include "DHT.h"

#define DHTPIN 4
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

const char* ssid = "Sara";
const char* senhas[] = {"Sara@2026", "Sara@2026 "};
const int numSenhas = sizeof(senhas) / sizeof(senhas[0]);

const char* serverUrl = "http://192.168.18.6:5001/leitura";

const char* wifiStatusTexto(int status) {
  switch (status) {
    case WL_IDLE_STATUS: return "IDLE";
    case WL_NO_SSID_AVAIL: return "SSID nao encontrada (rede 2.4GHz / nome)";
    case WL_SCAN_COMPLETED: return "SCAN_OK";
    case WL_CONNECTED: return "CONNECTED";
    case WL_CONNECT_FAILED: return "senha ou autenticacao recusada";
    case WL_CONNECTION_LOST: return "CONNECTION_LOST";
    case WL_DISCONNECTED: return "DISCONNECTED";
    default: return "DESCONHECIDO";
  }
}

bool tentarWifi(const char* senha) {
  WiFi.disconnect(true, true);
  delay(300);
  Serial.print("WiFi.begin SSID=\"");
  Serial.print(ssid);
  Serial.print("\" senha_len=");
  Serial.println(strlen(senha));
  WiFi.begin(ssid, senha);

  int tentativas = 0;
  while (WiFi.status() != WL_CONNECTED && tentativas < 40) {
    delay(500);
    Serial.print(".");
    tentativas++;
  }
  Serial.println();
  Serial.print("Status: ");
  Serial.println(wifiStatusTexto(WiFi.status()));
  return WiFi.status() == WL_CONNECTED;
}

bool conectarWifi() {
  WiFi.persistent(false);
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);

  for (int i = 0; i < numSenhas; i++) {
    if (tentarWifi(senhas[i])) {
      Serial.println("Wi-Fi conectado.");
      Serial.print("IP do ESP32: ");
      Serial.println(WiFi.localIP());
      Serial.print("Gateway: ");
      Serial.println(WiFi.gatewayIP());
      return true;
    }
  }

  Serial.println("Falha Wi-Fi. Nova tentativa em 8s.");
  return false;
}

bool postarRelay(const char* url, const String& payload) {
  HTTPClient http;
  Serial.print("POST ");
  Serial.println(url);

  if (!http.begin(url)) {
    Serial.println("http.begin falhou");
    return false;
  }

  http.addHeader("Content-Type", "application/json");
  http.setTimeout(60000);
  int codigo = http.POST(payload);
  String corpo = http.getString();
  http.end();

  Serial.print("HTTP ");
  Serial.println(codigo);
  if (codigo > 0) {
    Serial.println(corpo);
  } else {
    Serial.println(http.errorToString(codigo));
  }
  return codigo == 200;
}

void setup() {
  Serial.begin(115200);
  delay(800);
  Serial.println();
  Serial.println("=== FW-SEM-ATESTACAO (so temperatura e umidade) ===");
  dht.begin();
  conectarWifi();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    conectarWifi();
    delay(8000);
    return;
  }

  float temp = dht.readTemperature();
  float umid = dht.readHumidity();
  if (isnan(temp) || isnan(umid)) {
    Serial.println("DHT11 nao inicializado/leitura invalida. Sem POST e sem contar lote.");
    delay(2000);
    return;
  }

  Serial.print("Temperatura: ");
  Serial.print(temp, 2);
  Serial.print(" *C | Umidade: ");
  Serial.print(umid, 2);
  Serial.println(" %");

  String payload = "{\"origem\":\"esp32\"";
  payload += ",\"temperature\":";
  payload += String(temp, 2);
  payload += ",\"humidity\":";
  payload += String(umid, 2);
  payload += ",\"status\":true}";

  if (!postarRelay(serverUrl, payload)) {
    Serial.println("Relay nao aceitou o POST. Confira o IPv4 192.168.18.6:5001 e o servidor no ar.");
  }

  delay(10000);
}
