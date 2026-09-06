// M2: native regressions for malformed, delayed, duplicate and wrapped-clock frames.
#include <assert.h>
#include <string>
#include "status_protocol.h"

using status_display::Receiver;

int main() {
    Receiver r;
    assert(!r.fresh(0));
    r.request(100, 1, 1);
    const std::string frame = std::string("TRUSS1 ") + r.nonce() + " live leased 5000 4900 900 online";
    assert(r.accept(frame.c_str(), 200));
    assert(r.frame.cap == 5000 && r.frame.observed == 4900);
    assert(r.fresh(2599));
    assert(!r.accept(frame.c_str(), 2200)); // A duplicate cannot refresh the display.
    r.tick(2600);
    assert(!r.fresh(2600));
    assert(!r.fresh(100)); // Expiry latches even after clock wrap.

    r.request(3000, 1, 2);
    assert(!r.accept(frame.c_str(), 3100)); // Previous poll's reply.
    const std::string prefix = std::string("TRUSS1 ") + r.nonce();
    assert(!r.accept((prefix + " live leased -5 100 900 online").c_str(), 3200));
    assert(!r.accept((prefix + " live leased 5000 -2 900 online").c_str(), 3200));
    assert(!r.accept((prefix + " live leased 5000 1e3 900 online").c_str(), 3200));
    assert(!r.accept((prefix + " live leased 1000000 0 900 online").c_str(), 3200));
    assert(!r.accept((prefix + " live safe 5000 0 900 online").c_str(), 3200));
    assert(!r.accept((prefix + " live leased 5000 0 900 online extra").c_str(), 3200));
    assert(!r.accept((prefix + std::string(150, 'x')).c_str(), 3200));
    assert(r.accept((prefix + " mock unverified 5000 -1 900 unknown").c_str(), 3300));
    assert(r.frame.observed == -1 && strcmp(r.frame.source, "mock") == 0);

    r.request(6000, 1, 3);
    const std::string late = std::string("TRUSS1 ") + r.nonce() + " live leased 5000 4900 900 online";
    assert(!r.accept(late.c_str(), 8500)); // Receipt cannot start a new freshness window.

    Receiver wrap;
    wrap.request(UINT32_MAX - 999, 1, 1);
    assert(wrap.accept(frame.c_str(), UINT32_MAX - 900));
    wrap.tick(1499);
    assert(wrap.fresh(1499));
    wrap.tick(1500);
    assert(!wrap.fresh(1500));

    Receiver newBoot;
    newBoot.request(100, 2, 1);
    assert(!newBoot.accept(frame.c_str(), 200)); // Prior boot's buffered reply.
}
