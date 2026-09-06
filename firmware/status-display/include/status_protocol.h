// M2: bounded display-only parser and request-anchored freshness. No authority.
#pragma once

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

namespace status_display {
constexpr uint32_t FRESH_MS = 2500;

struct Frame {
    char source[7] = "";
    char state[15] = "";
    int32_t cap = 0;
    int32_t observed = -1;
    int32_t baseline = 0;
    char coordinator[11] = "";
};

inline bool oneOf(const char* value, const char* const* choices, unsigned count) {
    for (unsigned i = 0; i < count; ++i) {
        if (strcmp(value, choices[i]) == 0) return true;
    }
    return false;
}

inline bool watts(const char* value, int32_t& result, bool unknown = false) {
    if (unknown && strcmp(value, "-1") == 0) { result = -1; return true; }
    const size_t n = strlen(value);
    if (n == 0 || n > 6) return false;
    for (size_t i = 0; i < n; ++i) if (value[i] < '0' || value[i] > '9') return false;
    result = static_cast<int32_t>(strtol(value, nullptr, 10));
    return true;
}

class Receiver {
public:
    Frame frame;

    void request(uint32_t now, uint32_t boot, uint32_t sequence) {
        snprintf(nonce_, sizeof(nonce_), "%08lx%08lx",
                 static_cast<unsigned long>(boot), static_cast<unsigned long>(sequence));
        requestedAt_ = now;
        pending_ = true;
    }
    const char* nonce() const { return nonce_; }
    bool fresh(uint32_t now) const {
        return valid_ && static_cast<uint32_t>(now - sampledAt_) < FRESH_MS;
    }
    void tick(uint32_t now) {
        // Latch expiry so a millis() rollover cannot revive a days-old frame.
        if (!fresh(now)) valid_ = false;
        if (pending_ && static_cast<uint32_t>(now - requestedAt_) >= FRESH_MS) pending_ = false;
    }
    bool accept(const char* line, uint32_t now) {
        tick(now);
        if (!pending_ || strlen(line) >= 128) return false;
        char copy[128];
        strcpy(copy, line);
        char* parts[9] = {};
        char* save = nullptr;
        unsigned count = 0;
        for (char* part = strtok_r(copy, " ", &save); part; part = strtok_r(nullptr, " ", &save)) {
            if (count == 9) return false;
            parts[count++] = part;
        }
        if (count != 8 || strcmp(parts[0], "TRUSS1") || strcmp(parts[1], nonce_)) return false;
        const char* sources[] = {"live", "mock", "replay"};
        const char* states[] = {"starting", "recovering", "leased", "cap_transition", "infeasible", "unverified"};
        const char* coordinators[] = {"online", "recovering", "offline", "unknown"};
        if (!oneOf(parts[2], sources, 3) || !oneOf(parts[3], states, 6) ||
            !oneOf(parts[7], coordinators, 4)) return false;
        Frame next;
        if (!watts(parts[4], next.cap) || !watts(parts[5], next.observed, true) ||
            !watts(parts[6], next.baseline)) return false;
        strcpy(next.source, parts[2]);
        strcpy(next.state, parts[3]);
        strcpy(next.coordinator, parts[7]);
        frame = next;
        sampledAt_ = requestedAt_; // Receipt and duplicates cannot extend this.
        valid_ = true;
        pending_ = false;
        return true;
    }

private:
    char nonce_[17] = "";
    uint32_t requestedAt_ = 0;
    uint32_t sampledAt_ = 0;
    bool pending_ = false;
    bool valid_ = false;
};
} // namespace status_display
