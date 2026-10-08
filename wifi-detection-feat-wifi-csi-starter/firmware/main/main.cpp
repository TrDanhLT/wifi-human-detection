// ESP-IDF 5.x, original ESP32. Configure Wi-Fi using idf.py menuconfig.
// A computer on the same WLAN sends UDP packets to the printed IP address.
// These AP -> ESP32 packets provide CSI; no internet service is involved.
#include <cstdio>
#include <cstring>
#include <cstdint>
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include "freertos/task.h"
#include "esp_event.h"
#include "esp_log.h"
#include "esp_netif.h"
#include "esp_wifi.h"
#include "nvs_flash.h"
#include "lwip/sockets.h"
#include "sdkconfig.h"

namespace {
constexpr size_t kMaxCsi = 128; // LLTF only: consistent carrier layout.
struct Sample {
    uint32_t sequence;
    uint32_t timestamp;
    int rssi;
    uint16_t length;
    bool invalid_first_word;
    int8_t data[kMaxCsi];
};
QueueHandle_t samples;
uint8_t access_point[6]{};
uint32_t sequence = 0;

void on_csi(void *, wifi_csi_info_t *info) {
    // Wi-Fi task callback: copy only, never block or print here.
    if (!info || !info->buf || std::memcmp(info->mac, access_point, 6) != 0 ||
        info->len != kMaxCsi) return;
    Sample sample{};
    sample.sequence = sequence++; // Gaps expose queue drops to the receiver.
    sample.timestamp = info->rx_ctrl.timestamp;
    sample.rssi = info->rx_ctrl.rssi;
    sample.length = info->len;
    sample.invalid_first_word = info->first_word_invalid;
    std::memcpy(sample.data, info->buf, sample.length);
    xQueueSend(samples, &sample, 0);
}

void on_event(void *, esp_event_base_t base, int32_t id, void *data) {
    if (base == WIFI_EVENT && id == WIFI_EVENT_STA_START) {
        ESP_ERROR_CHECK(esp_wifi_connect());
    } else if (base == WIFI_EVENT && id == WIFI_EVENT_STA_DISCONNECTED) {
        ESP_ERROR_CHECK(esp_wifi_set_csi(false));
        esp_wifi_connect();
    } else if (base == IP_EVENT && id == IP_EVENT_STA_GOT_IP) {
        wifi_ap_record_t ap{};
        ESP_ERROR_CHECK(esp_wifi_sta_get_ap_info(&ap));
        std::memcpy(access_point, ap.bssid, sizeof(access_point));
        auto *event = static_cast<ip_event_got_ip_t *>(data);
        ESP_LOGI("capture", "Send UDP traffic to " IPSTR ":%d", IP2STR(&event->ip_info.ip), CONFIG_PRESENCE_UDP_PORT);
        ESP_ERROR_CHECK(esp_wifi_set_csi(true));
    }
}

void udp_sink(void *) {
    int fd = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (fd < 0) { ESP_LOGE("capture", "UDP socket creation failed"); vTaskDelete(nullptr); return; }
    sockaddr_in address{};
    address.sin_family = AF_INET;
    address.sin_port = htons(CONFIG_PRESENCE_UDP_PORT);
    address.sin_addr.s_addr = htonl(INADDR_ANY);
    if (bind(fd, reinterpret_cast<sockaddr *>(&address), sizeof(address)) < 0) {
        ESP_LOGE("capture", "UDP bind failed");
        close(fd); vTaskDelete(nullptr); return;
    }
    char buffer[512];
    while (recv(fd, buffer, sizeof(buffer), 0) >= 0) {}
    ESP_LOGE("capture", "UDP receive stopped");
    close(fd);
    vTaskDelete(nullptr);
}
}

extern "C" void app_main() {
    if (std::strlen(CONFIG_PRESENCE_SSID) == 0) {
        ESP_LOGE("capture", "Set Wi-Fi credentials in menuconfig before flashing");
        return;
    }
    esp_err_t result = nvs_flash_init();
    if (result == ESP_ERR_NVS_NO_FREE_PAGES || result == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        result = nvs_flash_init();
    }
    ESP_ERROR_CHECK(result);
    samples = xQueueCreate(64, sizeof(Sample));
    configASSERT(samples);
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    configASSERT(esp_netif_create_default_wifi_sta());
    wifi_init_config_t init = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&init));
    ESP_ERROR_CHECK(esp_wifi_set_storage(WIFI_STORAGE_RAM));
    ESP_ERROR_CHECK(esp_event_handler_register(WIFI_EVENT, ESP_EVENT_ANY_ID, on_event, nullptr));
    ESP_ERROR_CHECK(esp_event_handler_register(IP_EVENT, IP_EVENT_STA_GOT_IP, on_event, nullptr));
    wifi_config_t wifi{};
    static_assert(sizeof(CONFIG_PRESENCE_SSID) - 1 <= 32, "SSID too long");
    static_assert(sizeof(CONFIG_PRESENCE_PASSWORD) - 1 <= 64, "Password too long");
    std::memcpy(wifi.sta.ssid, CONFIG_PRESENCE_SSID, sizeof(CONFIG_PRESENCE_SSID) - 1);
    std::memcpy(wifi.sta.password, CONFIG_PRESENCE_PASSWORD, sizeof(CONFIG_PRESENCE_PASSWORD) - 1);
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi));
    ESP_ERROR_CHECK(esp_wifi_start());
    ESP_ERROR_CHECK(esp_wifi_set_ps(WIFI_PS_NONE));
    wifi_csi_config_t csi{};
    csi.lltf_en = true;
    csi.htltf_en = false;
    csi.stbc_htltf2_en = false;
    csi.ltf_merge_en = false;
    csi.channel_filter_en = false;
    csi.manu_scale = false;
    ESP_ERROR_CHECK(esp_wifi_set_csi_config(&csi));
    ESP_ERROR_CHECK(esp_wifi_set_csi_rx_cb(on_csi, nullptr));
    configASSERT(xTaskCreate(udp_sink, "udp_sink", 4096, nullptr, 4, nullptr) == pdPASS);
    Sample sample{};
    while (xQueueReceive(samples, &sample, portMAX_DELAY) == pdTRUE) {
        // One writer for CSI records. Python also tolerates ESP-IDF log lines.
        std::printf("{\"type\":\"csi\",\"seq\":%lu,\"timestamp_us\":%lu,\"rssi\":%d,\"first_word_invalid\":%s,\"iq\":[",
                    static_cast<unsigned long>(sample.sequence), static_cast<unsigned long>(sample.timestamp),
                    sample.rssi, sample.invalid_first_word ? "true" : "false");
        for (size_t i = 0; i < sample.length; ++i) std::printf("%s%d", i ? "," : "", sample.data[i]);
        std::printf("]}\n");
        std::fflush(stdout);
    }
}
