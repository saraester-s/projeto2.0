#include <WiFi.h>
#include <HTTPClient.h>
#include "DHT.h"

#define DHTPIN 4
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

const char* ssid = "SargonDrase.2.4Ghz";
const char* password = "Yeezus050494";

// IPv4 do PC nesta LAN. 127.0.0.1 no ESP e o proprio chip.
const char* serverUrls[] = {
  "http://192.168.1.120:5000/atestar"
};
const int numServerUrls = sizeof(serverUrls) / sizeof(serverUrls[0]);

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

void listarRedes() {
  Serial.println("Varrendo Wi-Fi 2.4 GHz...");
  int n = WiFi.scanNetworks(/*async=*/false, /*hidden=*/true);
  Serial.print("Redes visiveis: ");
  Serial.println(n);
  bool achouSsid = false;
  for (int i = 0; i < n; i++) {
    String nome = WiFi.SSID(i);
    Serial.print("  [");
    Serial.print(i);
    Serial.print("] ");
    Serial.print(nome);
    Serial.print(" RSSI=");
    Serial.print(WiFi.RSSI(i));
    Serial.println();
    if (nome == ssid) {
      achouSsid = true;
    }
  }
  if (!achouSsid) {
    Serial.print("SSID \"");
    Serial.print(ssid);
    Serial.println("\" NAO apareceu no scan. Troque ssid/password ou use a rede 2.4 GHz.");
  }
}

bool conectarWifi() {
  WiFi.persistent(false);
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);
  WiFi.disconnect(true, true);
  delay(200);
  listarRedes();

  Serial.print("[FW-NOVO] A conectar ao Wi-Fi SSID=\"");
  Serial.print(ssid);
  Serial.println("\" (so 2.4 GHz)...");
  WiFi.begin(ssid, password);

  int tentativas = 0;
  while (WiFi.status() != WL_CONNECTED && tentativas < 40) {
    delay(500);
    Serial.print(".");
    tentativas++;
  }
  Serial.println();

  if (WiFi.status() != WL_CONNECTED) {
    Serial.print("Falha Wi-Fi: ");
    Serial.println(wifiStatusTexto(WiFi.status()));
    Serial.println("Nao vou reiniciar o chip. Nova tentativa em 8s.");
    return false;
  }

  Serial.println("Wi-Fi conectado.");
  Serial.print("IP do ESP32: ");
  Serial.println(WiFi.localIP());
  Serial.print("Gateway: ");
  Serial.println(WiFi.gatewayIP());
  return true;
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
  Serial.println("=== FW-NOVO publish_sensores_esp (sem ESP.restart) ===");
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

  String firmwareHashHex = "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef";
  String payload = "{\"origem\":\"esp32\"";
  payload += ",\"temperature\":";
  payload += String(temp, 2);
  payload += ",\"humidity\":";
  payload += String(umid, 2);
  payload += ",\"status\":true";
  payload += ",\"firmware_hash\":\"";
  payload += firmwareHashHex;
  payload += "\"}";

  bool ok = false;
  for (int i = 0; i < numServerUrls && !ok; i++) {
    ok = postarRelay(serverUrls[i], payload);
  }
  if (!ok) {
    Serial.println("Nenhum IPv4 do PC aceitou o POST. Confira o IPv4 atual com ipconfig e o relay no ar.");
  }

  delay(10000);
}
