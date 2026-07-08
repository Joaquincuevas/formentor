/*
 * Controlador de Casilleros — Firmware ESP32-CAM
 * -----------------------------------------------
 * Responsabilidades del controlador (segun el enunciado):
 *   - Abrir/cerrar hasta 4 casilleros validando una clave de 4 gestos.
 *   - Funcionar de forma AUTONOMA (la apertura no depende de Internet: las claves
 *     estan cacheadas localmente).
 *   - Mantener las claves actualizadas via MQTT (latencia < 5 min).
 *   - Informar al Sistema de Administracion cada apertura/cierre.
 *   - Actualizar el modelo de gestos de forma remota.
 *   - Indicadores visuales (LEDs).
 *
 * Estado de este archivo:
 *   - WiFi + MQTT + contrato de topicos: IMPLEMENTADO y funcional.
 *   - Actuadores + LEDs + sensores: IMPLEMENTADO (requieren el hardware conectado).
 *   - Inferencia de gestos on-device: STUB documentado (ver readGestureSequence()).
 *     El pipeline real (captura de camara -> MediaPipe/landmarks -> TFLite Micro)
 *     se integra cuando el modelo este exportado (ver gesture-model/export_tflite.py).
 *
 * Sin el actuador fisico igual puedes flashear esto: conecta WiFi, sincroniza con
 * el admin y veras las claves llegar por serial. La "apertura" se simula por serial.
 */
#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "config.h"

WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);

// clave cacheada localmente por casillero (indices de gesto, -1 = sin asignar)
int lockerKeys[4][4];
bool lockerOpen[4] = {false, false, false, false};
int modelVersion = -1;
unsigned long lastHeartbeat = 0;

// ---- helpers de topicos ----
String topic(const char *suffix) {
  return String("casilleros/") + CONTROLLER_ID + "/" + suffix;
}

// ---- indicadores visuales ----
void setStatusLed(bool on) { digitalWrite(PIN_LED_STATUS, on ? HIGH : LOW); }

void blink(int times) {
  for (int i = 0; i < times; i++) {
    setStatusLed(true); delay(120);
    setStatusLed(false); delay(120);
  }
}

// ---- actuador ----
void driveActuator(int lockerIdx, bool open) {
  // pulso al rele/solenoide. Ajustar la logica segun tu cerradura (pulso vs nivel).
  digitalWrite(ACTUATOR_PINS[lockerIdx], open ? HIGH : LOW);
  lockerOpen[lockerIdx] = open;
}

// ---- publicar evento de apertura/cierre ----
void publishEvent(int lockerNumber, const char *action) {
  StaticJsonDocument<128> doc;
  doc["locker"] = lockerNumber;
  doc["action"] = action;
  doc["ts"] = "";  // idealmente hora NTP; el admin usa su hora si viene vacio
  char buf[128];
  size_t n = serializeJson(doc, buf);
  mqtt.publish(topic("event").c_str(), buf, n);
}

/*
 * Captura la secuencia de 4 gestos del usuario frente a la camara.
 *
 * STUB: por ahora lee 4 numeros por el monitor serial para poder probar la logica
 * de validacion sin la camara. La implementacion real debe:
 *   1. Capturar frames con esp_camera_fb_get().
 *   2. Extraer landmarks de la mano (o correr un detector ligero).
 *   3. Normalizar igual que gesture-model/landmarks.py.
 *   4. Invocar el modelo TFLite Micro (gesture_model.cc) por cada gesto estable.
 * Devuelve true si logro leer 4 gestos.
 */
bool readGestureSequence(int outKey[4]) {
  Serial.println("[gesto] STUB: ingresa 4 indices de gesto (0-5) separados por espacio:");
  for (int i = 0; i < 4; i++) {
    while (!Serial.available()) delay(10);
    outKey[i] = Serial.parseInt();
  }
  return true;
}

// intenta abrir un casillero validando la clave capturada
void attemptOpen(int lockerIdx) {
  int lockerNumber = lockerIdx + 1;
  if (lockerKeys[lockerIdx][0] < 0) {
    Serial.printf("[casillero %d] sin clave asignada\n", lockerNumber);
    return;
  }
  setStatusLed(true);  // "capturando"
  int attempt[4];
  readGestureSequence(attempt);
  setStatusLed(false);

  bool ok = true;
  for (int i = 0; i < 4; i++)
    if (attempt[i] != lockerKeys[lockerIdx][i]) ok = false;

  if (ok) {
    driveActuator(lockerIdx, true);
    publishEvent(lockerNumber, "open");
    blink(2);
    Serial.printf("[casillero %d] ABIERTO\n", lockerNumber);
  } else {
    publishEvent(lockerNumber, "denied");
    blink(5);
    Serial.printf("[casillero %d] clave incorrecta\n", lockerNumber);
  }
}

// ---- MQTT: aplicar mensajes entrantes ----
void applyKey(JsonDocument &doc) {
  int locker = doc["locker"];
  JsonArray key = doc["key"].as<JsonArray>();
  if (locker < 1 || locker > 4) return;
  for (int i = 0; i < 4 && i < (int)key.size(); i++)
    lockerKeys[locker - 1][i] = key[i];
  Serial.printf("[mqtt] clave del casillero %d actualizada\n", locker);
}

void applySyncResponse(JsonDocument &doc) {
  modelVersion = doc["model_version"] | -1;
  for (JsonObject lk : doc["lockers"].as<JsonArray>()) {
    int locker = lk["locker"];
    JsonArray key = lk["key"].as<JsonArray>();
    if (locker >= 1 && locker <= 4)
      for (int i = 0; i < 4 && i < (int)key.size(); i++)
        lockerKeys[locker - 1][i] = key[i];
  }
  Serial.printf("[mqtt] sincronizado. modelo v%d\n", modelVersion);
}

void onMessage(char *t, byte *payload, unsigned int len) {
  StaticJsonDocument<512> doc;
  if (deserializeJson(doc, payload, len)) return;
  String ts(t);
  if (ts.endsWith("/keys")) applyKey(doc);
  else if (ts.endsWith("/sync/response")) applySyncResponse(doc);
  else if (ts.endsWith("/model")) {
    modelVersion = doc["model_version"] | modelVersion;
    Serial.printf("[mqtt] nuevo modelo v%d: %s\n",
                  modelVersion, (const char *)(doc["model_url"] | ""));
    // TODO: descargar doc["model_url"] por HTTP y reemplazar el modelo en flash.
  }
}

void announce() {
  StaticJsonDocument<128> doc;
  doc["controller_id"] = CONTROLLER_ID;
  doc["active_lockers"] = ACTIVE_LOCKERS;
  doc["firmware"] = FIRMWARE_VER;
  char buf[128];
  size_t n = serializeJson(doc, buf);
  mqtt.publish(topic("sync/request").c_str(), buf, n);
}

void reconnectMqtt() {
  while (!mqtt.connected()) {
    Serial.print("[mqtt] conectando...");
    if (mqtt.connect(CONTROLLER_ID)) {
      Serial.println(" ok");
      mqtt.subscribe(topic("keys").c_str());
      mqtt.subscribe(topic("model").c_str());
      mqtt.subscribe(topic("sync/response").c_str());
      announce();
    } else {
      Serial.printf(" falla rc=%d, reintento en 2s\n", mqtt.state());
      delay(2000);
    }
  }
}

void sendHeartbeat() {
  StaticJsonDocument<96> doc;
  doc["ts"] = "";
  doc["rssi"] = WiFi.RSSI();
  char buf[96];
  size_t n = serializeJson(doc, buf);
  mqtt.publish(topic("heartbeat").c_str(), buf, n);
}

void setup() {
  Serial.begin(115200);
  for (int i = 0; i < 4; i++) {
    pinMode(ACTUATOR_PINS[i], OUTPUT);
    digitalWrite(ACTUATOR_PINS[i], LOW);
    for (int j = 0; j < 4; j++) lockerKeys[i][j] = -1;  // sin clave hasta sincronizar
  }
  pinMode(PIN_LED_STATUS, OUTPUT);

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("[wifi] conectando");
  while (WiFi.status() != WL_CONNECTED) { delay(400); Serial.print("."); }
  Serial.printf("\n[wifi] IP %s\n", WiFi.localIP().toString().c_str());

  mqtt.setServer(MQTT_BROKER, MQTT_PORT);
  mqtt.setCallback(onMessage);
  mqtt.setBufferSize(1024);
}

void loop() {
  if (!mqtt.connected()) reconnectMqtt();
  mqtt.loop();

  if (millis() - lastHeartbeat > HEARTBEAT_MS) {
    lastHeartbeat = millis();
    sendHeartbeat();
  }

  // demo por serial: escribe "open N" o "close N" (N = numero de casillero)
  if (Serial.available()) {
    String cmd = Serial.readStringUntil(' ');
    if (cmd == "open") {
      int n = Serial.parseInt();
      if (n >= 1 && n <= 4) attemptOpen(n - 1);
    } else if (cmd == "close") {
      int n = Serial.parseInt();
      if (n >= 1 && n <= 4) {
        driveActuator(n - 1, false);
        publishEvent(n, "close");
        Serial.printf("[casillero %d] cerrado\n", n);
      }
    }
  }
}
