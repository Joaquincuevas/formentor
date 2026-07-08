/*
 * Firmware de STREAMING para la ESP32-CAM (AI-Thinker).
 * -----------------------------------------------------
 * Modo de demostracion del reconocimiento de gestos con IA en el COMPUTADOR:
 * la cam solo transmite video MJPEG por WiFi; el PC (MediaPipe) hace la IA.
 *
 * Al arrancar imprime por serial la URL del stream, por ejemplo:
 *     http://192.168.1.99/stream
 *
 * Este .cpp se compila en el entorno [env:esp32cam_stream] (ver platformio.ini).
 * El firmware del controlador MQTT vive en main.cpp (entorno [env:esp32cam]).
 */
#include <Arduino.h>
#include <WiFi.h>
#include "esp_camera.h"
#include "esp_http_server.h"
#include "config.h"

// --- Pines de la camara para AI-Thinker ESP32-CAM ---
#define PWDN_GPIO_NUM   32
#define RESET_GPIO_NUM  -1
#define XCLK_GPIO_NUM    0
#define SIOD_GPIO_NUM   26
#define SIOC_GPIO_NUM   27
#define Y9_GPIO_NUM     35
#define Y8_GPIO_NUM     34
#define Y7_GPIO_NUM     39
#define Y6_GPIO_NUM     36
#define Y5_GPIO_NUM     21
#define Y4_GPIO_NUM     19
#define Y3_GPIO_NUM     18
#define Y2_GPIO_NUM      5
#define VSYNC_GPIO_NUM  25
#define HREF_GPIO_NUM   23
#define PCLK_GPIO_NUM   22

httpd_handle_t server = NULL;
static const char *STREAM_CT = "multipart/x-mixed-replace;boundary=frame";

// Handler del stream MJPEG: envia frames JPEG uno tras otro.
static esp_err_t stream_handler(httpd_req_t *req) {
  httpd_resp_set_type(req, STREAM_CT);
  httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
  char part[64];
  while (true) {
    camera_fb_t *fb = esp_camera_fb_get();
    if (!fb) { continue; }
    if (httpd_resp_send_chunk(req, "\r\n--frame\r\n", 10) != ESP_OK) {
      esp_camera_fb_return(fb); break;
    }
    int len = snprintf(part, sizeof(part),
        "Content-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n", fb->len);
    if (httpd_resp_send_chunk(req, part, len) != ESP_OK ||
        httpd_resp_send_chunk(req, (const char *)fb->buf, fb->len) != ESP_OK) {
      esp_camera_fb_return(fb); break;
    }
    esp_camera_fb_return(fb);
  }
  return ESP_OK;
}

// Pagina raiz simple con el video embebido.
static esp_err_t index_handler(httpd_req_t *req) {
  static const char html[] =
    "<html><body style='margin:0;background:#111;text-align:center'>"
    "<h3 style='color:#fff;font-family:sans-serif'>ESP32-CAM Casilleros</h3>"
    "<img src='/stream' style='max-width:100%'></body></html>";
  httpd_resp_set_type(req, "text/html");
  return httpd_resp_send(req, html, strlen(html));
}

void startCameraServer() {
  httpd_config_t cfg = HTTPD_DEFAULT_CONFIG();
  cfg.server_port = 80;
  if (httpd_start(&server, &cfg) == ESP_OK) {
    httpd_uri_t idx = {"/", HTTP_GET, index_handler, NULL};
    httpd_uri_t st  = {"/stream", HTTP_GET, stream_handler, NULL};
    httpd_register_uri_handler(server, &idx);
    httpd_register_uri_handler(server, &st);
  }
}

void setup() {
  Serial.begin(115200);
  Serial.println();

  camera_config_t config = {};
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;   config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM; config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM; config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;   config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  // QVGA + compresion alta: frames livianos para un enlace WiFi debil.
  // (MediaPipe funciona bien a 320x240; subir resolucion solo si el WiFi es bueno.)
  config.frame_size = FRAMESIZE_QVGA;    // 320x240
  config.jpeg_quality = 16;              // mayor numero = mas compresion
  config.fb_count = psramFound() ? 2 : 1;

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("[cam] fallo init 0x%x (revisa el modulo de camara)\n", err);
    return;
  }

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("[wifi] conectando");
  while (WiFi.status() != WL_CONNECTED) { delay(400); Serial.print("."); }
  Serial.println();

  startCameraServer();
  Serial.printf("[stream] listo -> http://%s/stream\n",
                WiFi.localIP().toString().c_str());
}

void loop() {
  delay(10000);
}
