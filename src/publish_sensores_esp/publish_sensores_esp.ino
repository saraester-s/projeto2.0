#include <WiFi.h>
#include <HTTPClient.h>
#include "DHT.h"

#define DHTPIN 4
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

const char* ssid = "Sara";
const char* senhas[] = {"Sara@2026", "Sara@2026 "};
const int numSenhas = sizeof(senhas) / sizeof(senhas[0]);

const char* relayHost = "192.168.18.6";
const uint16_t relayPorta = 5000;
const char* relayCaminho = "/atestar";
// Hash canônico do .ino (firmware.py zera este campo na medição). Para o teste:
// altere o código, rode python src/teste_manual_hash.py, cole o hash novo aqui
// e NÃO atualize FIRMWARE_HASH_ESPERADO_HEX — o relay deve recusar.
const char* firmwareHash = "8422ebe782c2f51ab17c330621d0b4c2c29db4175a82929fec0bab04d2ba28b6";

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

bool postarRelay(const char* payload) {
  WiFiClient cliente;
  HTTPClient http;
  Serial.print("POST http://");
  Serial.print(relayHost);
  Serial.print(":");
  Serial.print(relayPorta);
  Serial.println(relayCaminho);

  if (!http.begin(cliente, relayHost, relayPorta, relayCaminho)) {
    Serial.println("http.begin falhou");
    return false;
  }

  http.addHeader("Content-Type", "application/json");
  http.setTimeout(60000);
  int codigo = http.POST(payload);
  String corpo = http.getString();
  String erro = (codigo <= 0) ? http.errorToString(codigo) : "";
  http.end();

  Serial.print("HTTP ");
  Serial.println(codigo);
  if (codigo > 0) {
    Serial.println(corpo);
  } else {
    Serial.println(erro);
  }
  return codigo == 200;
}

void setup() {
  Serial.begin(115200);
  delay(800);
  Serial.println();
  Serial.println("=== FW-ATESTACAO (hash de firmware no POST /atestar) ===");
  Serial.print("firmwareHash=");
  Serial.println(firmwareHash);
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

  char payload[320];
  snprintf(
    payload,
    sizeof(payload),
    "{\"origem\":\"esp32\",\"temperature\":%.2f,\"humidity\":%.2f,\"status\":true,\"firmware_hash\":\"%s\"}",
    temp,
    umid,
    firmwareHash
  );
  Serial.print("JSON len=");
  Serial.print(strlen(payload));
  Serial.print(" hash_len=");
  Serial.println(strlen(firmwareHash));

  if (!postarRelay(payload)) {
    Serial.println("Relay nao aceitou o POST. Confira o IPv4 192.168.18.6:5000/atestar e o servidor no ar.");
  }

  delay(10000);
}
