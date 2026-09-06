# 15 — Risk register

| # | Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|---|
| R1 | **M1 becomes the bottleneck** and four people wait | High | Fatal | Contract frozen at hour 1; everyone builds against fixtures; allocator is a pure function with no infrastructure dependency | M1 |
| R2 | **Distributed integration eats the whole event** — five subsystems that never connect | High | Fatal | Vertical slice by hour 6 is a hard kill point. Three members and two device types is an acceptable retreat; six disconnected demos is not | All |
| R3 | Lease semantics subtly wrong — expiry fires late, or a member over-draws | Medium | Fatal | Hour-12 kill point is exactly this test. Property tests on I3. Monotonic clocks only, never timestamps | M3 |
| R4 | CP-SAT consumes hours and delivers nothing | Medium | High | It is behind an interface and time-boxed. Hour-30 kill point. Cutting it is a defensible answer, not a gap | M1 |
| R5 | Demo laptop cannot join the LAN at the venue | Medium | High | Single-laptop profile rehearsed as often as the distributed one. Own router *and* hotspot. Extension board packed | M5 |
| R6 | ESP32 fails at the venue | Medium | Low | It is bonus only. If it dies mid-demo it becomes beat 3 — a planned failure absorbs an unplanned one | M5 |
| R7 | Console becomes a second project | Medium | Medium | Seven-questions rule; anything that answers none is deleted. Frozen at hour 36 | M4 |
| R8 | Judges read it as "just load shedding" | Medium | High | Beats 5 and 6 exist specifically for this. Lead with the lease and the refusal, not the slider | All |
| R9 | Someone claims Matter/OpenADR compliance under pressure | Low | Fatal to credibility | The boundary is on slide one and in the README. Rehearsed as a scripted sentence, not improvised | All |
| R10 | Scope creep from mentor feedback at Review 1 | High | Medium | Feedback is logged, not implemented. Only changes that fix the core loop are actioned before Review 2 | M1 |
| R11 | Event dates or submission deadline missed | Low | Fatal | [14-rules.md](14-rules.md) open items confirmed directly, today, with a written record of who said what | All |
| R12 | Fatigue-driven breakage in the last six hours | High | High | Hours 42–48 are bug fixes with rollback only. Rest in rotation. Schema and allocator are frozen | All |

## The three that actually decide the outcome

**R2** — if the vertical slice is not alive at hour 6, nothing else in this
document matters. Everything is subordinate to that.

**R3** — the lease mechanism is the difference between this project and a nicer
dashboard. If it does not work, we have an ordinary submission with good
vocabulary.

**R8** — the idea is genuinely distinguishable, but only if we lead with the
distinguishing parts. The slider is the setup; the coordinator kill and the
refusal are the pitch.

## Stop rules

- If the vertical slice is not green at **hour 8**, cut to three members and two
  device types and rebuild it. Do not debug the wide version.
- If leases are not green at **hour 14**, stop all feature work until they are.
- If we cannot complete three cold-start passes by **hour 40**, cut demo beats
  until we can — beat 4 first, then beat 2.
