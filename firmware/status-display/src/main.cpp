// M2: new Truss observer screen, using only the wiring documented in ~/ccode.
#include <Arduino.h>
#include <Arduino_GFX_Library.h>
#include <esp_system.h>
#include "status_protocol.h"

namespace {
Arduino_ESP32SPI bus(13, 10, 12, 11, GFX_NOT_DEFINED); // DC, CS, clock, MOSI, no MISO
Arduino_GC9A01 panel(&bus, 14, 0, true); // Reset, rotation, IPS
Arduino_Canvas screen(240, 240, &panel); // One 115,200-byte buffer avoids erase flicker.
status_display::Receiver receiver;
uint32_t bootToken = 0, sequence = 0, lastPoll = 0, lastPaint = 0;
char input[128];
size_t inputSize = 0;
bool overflow = false, ready = false;
bool paintedFresh = false;
constexpr uint16_t COLOR_BG = RGB565(9, 16, 26);
constexpr uint16_t COLOR_WHITE = RGB565(230, 238, 245);
constexpr uint16_t COLOR_AMBER = RGB565(255, 183, 67);
constexpr uint16_t COLOR_RED = RGB565(255, 96, 96);
constexpr uint16_t COLOR_CYAN = RGB565(55, 214, 224);

void centered(const char* text, int y, int size, uint16_t color) {
    screen.setTextSize(size);
    screen.setTextColor(color, COLOR_BG);
    screen.setCursor((240 - static_cast<int>(strlen(text)) * 6 * size) / 2, y);
    screen.print(text);
}

void paint(uint32_t now) {
    screen.fillScreen(COLOR_BG);
    const bool fresh = receiver.fresh(now);
    if (!fresh && paintedFresh) Serial.println("TRUSS-DISPLAY NO_DATA");
    paintedFresh = fresh;
    const auto& f = receiver.frame;
    const bool issue = fresh && (strcmp(f.state, "infeasible") == 0 ||
                                (f.observed >= 0 && f.observed > f.cap));
    const bool ordinary = fresh && f.observed >= 0 && strcmp(f.state, "leased") == 0 &&
                          strcmp(f.coordinator, "online") == 0;
    const uint16_t color = issue ? COLOR_RED : ordinary ? COLOR_CYAN : COLOR_AMBER;
    screen.drawCircle(120, 120, 116, color);
    centered("TRUSS", 32, 3, COLOR_WHITE);
    if (!fresh) {
        centered("NO DATA", 91, 3, COLOR_AMBER);
        centered("Check USB + bridge", 140, 1, COLOR_WHITE);
        centered("READ-ONLY DISPLAY", 179, 1, COLOR_WHITE);
        screen.flush();
        return;
    }
    centered(strcmp(f.source, "live") == 0 ? "VIRTUAL LIVE" :
             strcmp(f.source, "mock") == 0 ? "MOCK DEMO" : "REPLAY", 62, 1, color);
    char line[40];
    snprintf(line, sizeof(line), "CAP %ld W", static_cast<long>(f.cap));
    centered(line, 84, 2, COLOR_WHITE);
    if (f.observed < 0) strcpy(line, "DRAW UNKNOWN");
    else snprintf(line, sizeof(line), "DRAW %ld W", static_cast<long>(f.observed));
    centered(line, 110, 2, color);
    snprintf(line, sizeof(line), "BASE %ld W", static_cast<long>(f.baseline));
    centered(line, 136, 2, COLOR_WHITE);
    centered(f.state, 165, 1, color);
    snprintf(line, sizeof(line), "COORD %s", f.coordinator);
    centered(line, 181, 1, COLOR_WHITE);
    centered("READ ONLY", 197, 1, COLOR_WHITE);
    screen.flush();
}
} // namespace

void setup() {
    Serial.begin(115200);
    bootToken = esp_random();
    ready = screen.begin(40000000);
    Serial.println(ready ? "TRUSS-DISPLAY READY" : "TRUSS-DISPLAY INIT_FAILED");
    if (ready) { screen.setTextWrap(false); paint(millis()); }
    lastPoll = millis() - 1000;
}

void loop() {
    uint32_t now = millis();
    receiver.tick(now);
    if (static_cast<uint32_t>(now - lastPoll) >= 1000) {
        // A new nonce invalidates any answer to a previous poll, even in a USB backlog.
        if (++sequence == 0) bootToken = esp_random();
        receiver.request(now, bootToken, sequence);
        Serial.printf("TRUSS? %s\n", receiver.nonce());
        lastPoll = now;
    }
    // Bound each iteration so a flood cannot starve local expiry or painting.
    for (unsigned budget = 0; budget < 256 && Serial.available(); ++budget) {
        const char ch = static_cast<char>(Serial.read());
        if (ch == '\n') {
            if (!overflow) {
                input[inputSize] = '\0';
                if (receiver.accept(input, millis())) {
                    Serial.printf("TRUSS-DISPLAY ACCEPT %s\n", receiver.nonce());
                }
            }
            inputSize = 0;
            overflow = false;
        } else if (ch < 32 || ch > 126 || inputSize >= sizeof(input) - 1) {
            overflow = true;
        } else if (!overflow) {
            input[inputSize++] = ch;
        }
    }
    now = millis();
    receiver.tick(now);
    if (ready && static_cast<uint32_t>(now - lastPaint) >= 250) {
        paint(now);
        lastPaint = now;
    }
    delay(2);
}
