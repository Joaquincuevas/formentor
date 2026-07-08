// PLANTILLA de configuracion. Copiala a `config.h` y pon tus valores reales.
// `config.h` esta en .gitignore para NO subir credenciales (repo publico).
//
//     cp config.example.h config.h
//
#pragma once

// --- Identidad del controlador (debe coincidir con el creado en el admin) ---
#define CONTROLLER_ID   "ctrl-demo1"
#define ACTIVE_LOCKERS  3          // casilleros fisicos conectados (1..4)
#define FIRMWARE_VER    "0.1.0"

// --- WiFi ---  (OJO: el ESP32 solo soporta 2.4GHz, no 5GHz)
#define WIFI_SSID       "TU_WIFI"
#define WIFI_PASSWORD   "TU_PASSWORD"

// --- MQTT ---
#define MQTT_BROKER     "192.168.1.100"   // IP del computador con Mosquitto
#define MQTT_PORT       1883

// --- Pines (ajustar segun tu cableado; la ESP32-CAM deja pocos GPIO libres) ---
#define PIN_ACTUATOR_1  12   // rele/transistor del casillero 1
#define PIN_ACTUATOR_2  13
#define PIN_ACTUATOR_3  15
#define PIN_ACTUATOR_4  14
#define PIN_LED_STATUS  2    // LED indicador (listo/capturando)
#define PIN_REED_1      16   // sensor magnetico casillero 1 (opcional)
#define PIN_SELECTOR    3    // boton/selector para elegir casillero

#define HEARTBEAT_MS    60000UL   // latido cada 60 s

static const int ACTUATOR_PINS[4] = {
    PIN_ACTUATOR_1, PIN_ACTUATOR_2, PIN_ACTUATOR_3, PIN_ACTUATOR_4
};
