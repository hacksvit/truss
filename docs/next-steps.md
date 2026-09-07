# What comes next

Truss demonstrates coordination across independently failing virtual processes. The next work should test whether those behaviours survive realistic devices, additional hosts and sustained load. These are proposed extensions, not delivered capabilities or promised dates.

## Start with the people who would use it

Interview a hostel operator and residents. Establish who approves minimum allowances, which loads genuinely tolerate interruption and how disputes would be reviewed. Record actual supply constraints and outage procedures with appropriate expertise. A pilot should establish whether the policy is useful and understandable; a polished website and a mathematically defined allocation rule do not prove acceptance or demand.

## Improve the virtual model

| Extension | Why it matters | Required evidence |
| --- | --- | --- |
| Changing household demand | Current profiles largely ask for their configured maxima. | Reproducible traces with low, bursty and sustained demand. |
| Reclaim binary leftovers | A whole appliance may not fit its allowance. | Admission-aware second-pass tests that improve useful draw without double-spending old authority. |
| Non-interruptible jobs | A running cycle may need a sustained commitment. | A local job model with authority reserved for the entire accepted commitment. |
| Deadline scheduling | Watts now do not establish completion later. | Energy-over-time tests, explicit missed deadlines and a measured baseline comparison. |
| Policy evaluation | Bounded weights do not guarantee repayment or resist inflated demand. | Long traces separating authorisation, actual virtual service, repeated shortfalls and dishonest offers. |

Richer offers may reveal more information. Keep appliance scheduling local where possible. Any optimiser needs validation, admission, a bounded runtime and a documented fallback. An AI classifier is not needed to decide which loads are protected.

## Test the whole system at larger sizes

The 5,000-member Lab limit describes synthetic allocator input. Increase live member count in stages and measure:

- CPU and memory across the broker, coordinator, observer, members and plants.
- Messages and bytes per second, queue pressure, observation gaps and reconnect behaviour.
- Request-to-grant and grant-to-plant acknowledgement latency.
- Independent expiry lateness under load and during failures.
- SQLite commit cost, recording growth, snapshot size and browser responsiveness.

Preserve raw samples, machine details, configuration, source revision and fault windows. Report median, p95 and observed maxima as measurements, not universal timing guarantees. Stop increasing scale when assumptions fail; a faster chart does not repair a late enforcer.

Later architectures could use site coordinators under a building-level envelope or consolidate local processes while retaining isolation. These change authority and recovery obligations. Parent and child coordinators must not both spend the same capacity. Hierarchical coordination is not implemented today.

## Build a narrow hardware experiment

Keep the existing read-only display separate from control. Its serial freshness behaviour is useful but does not make it a meter or appliance enforcer.

A first actuation experiment should be a separately reviewed low-voltage setup with an independent measurement path. Define startup defaults, expiry, communication loss, brownout/restart behaviour and measurable response limits first. A board has its own clock; it cannot interpret the PC's absolute monotonic deadline directly.

Actual household equipment requires appropriate electrical design and validation. Isolation, protection, inrush, phase constraints and physical failure modes are separate obligations from fair allocation. No physical household installation or medical-device application is delivered by this build.

## Strengthen trust and hosting

The plant currently trusts its member to forward genuine authority. A stronger design needs authority the enforcer can verify, bound to site, member, boot/session and expiry semantics. Investigate direct issuer-to-enforcer delivery or signed grants with explicit replay and clock handling. A signature alone does not solve stale authority.

Further work includes operator authentication, per-site isolation, protected broker identities, transport security beyond the host, key rotation and auditable configuration changes. The hosted showcase is one shared virtual run; visitors with control access affect that same run.

Store wanted recordings outside ephemeral dyno storage. Separate public explanation from privileged control, then measure resources before changing worker or dyno count. A database add-on alone would not turn independent coordinators into one correctly coordinated runtime.

## Standards and interoperability

Choose one actual target and version, then map its limits, states, freshness and failure semantics. Matter, OpenADR, EEBus and Home Assistant are possible investigations. Naming them does not establish an implemented adapter or conformance.

Validate an adapter against a real counterpart, including unsupported operations and disconnection. Identify which obligations it preserves and which need a protocol change.

## Product improvements and useful assets

Further website work can focus on loading time, bundle splitting, lower-powered phones and keyboard focus across route changes. Preserve a full static reading path when motion is reduced.

Useful next assets are a recording of an actual failure drill, a clearly labelled photo of the read-only screen, and an operator-approved realistic demand trace. These add evidence without implying an installation that does not exist.

The next success should be a credible experiment: clearer operator decisions, a reproducible failure result or verified integration behaviour. Savings, adoption and certified safety require different evidence and remain open questions.
