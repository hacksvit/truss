# 22 — Protected overnight loads

Current decision, 6 September 2026: the user removed AI and SGLang from scope. The project uses deterministic coordination and explicit protected-load policy only. The user’s own PC remains the intended host.

## The important answer: protection does not need AI

A user-declared breathing-support requirement must not enter the pool of interruptible demand. That is an explicit local policy and capacity reservation, not an inference from appliance name, time of day, power trace or a model's confidence score. Different breathing-related devices and uses have different requirements; this prototype does not classify clinical necessity or infer safe interruption times.

The medical-device power-loss issue is real: FDA guidance advises users to plan for power outages with their care/device support teams and keep device-specific emergency information. That supports the need for explicit continuity planning, **not** a claim that Truss can supply it. [FDA power-outage preparation](https://www.fda.gov/media/80782/download), [FDA medical-device disaster guidance](https://www.fda.gov/medical-devices/emergency-situations-medical-devices/fda-offers-tips-about-medical-devices-and-natural-disasters).

For Truss's fictional demo, reserve the declared protected requirement for the **entire run**, including daytime. Do not add a night schedule that can switch it off at dawn, depend on timezone, misread a clock, or assume the user has finished. This deliberately costs daytime utilisation and avoids another safety-critical state machine. A real product would need a device-specific assessment and independent power continuity; we build neither here.

### Required amendment to the local policy and plant contract

- Add `control_policy: protected|flexible|unclassified` to DeviceDiscovery and private profiles. `flexibility` remains the demand-description field; `control_policy` decides eligibility for automated curtailment.
- **Protected:** registry baseline for that device covers its full admitted maximum draw; member baseline covers the sum. Local planner cannot generate an off/defer command for it. Plant rejects such a command with `policy_conflict`, including on lease expiry. The plant's expiry target includes this protected baseline.
- **Flexible:** only these admitted loads participate in ordinary deferral; their local commands remain bounded by aggregate ceiling.
- **Unclassified:** no automated curtailment decision is permitted. Before a run, resolve policy or conservatively reserve full admitted maximum as baseline; otherwise refuse that configuration. Do not silently treat uncertainty as “safe to cut”. This does not authorise an unregistered load to exceed available capacity.
- No runtime command or AI result may downgrade protected/unclassified to flexible. Policy changes require stopping the fictional scenario and reviewing/revalidating the registry before a new run. The existing Protect control can reorder eligible flexible priorities only; its label/tooltip must say so.
- DeviceView adds `control_policy` and `curtailment_eligible: boolean`; for protected/unclassified the latter is false. The drawer says **“Excluded from automated curtailment”**, not “medically safe”. Add `protected_baseline_w` to the local private policy explanation, not to the coordinator offer as medical detail.
- The central coordinator sees the same aggregate floor/envelope. It does not need the protected device's name, diagnosis, night schedule or room occupant identity. Demo observer may show an anonymised “protected load” and the explicit observer boundary.

Example **fictional watts only**: a household has 180 W registered baseline, of which a 120 W protected virtual load and 60 W other fixed load are reserved. On coordinator loss, flexible output stops while the 180 W entitlement remains. No claim that 120 W describes any particular medical device. If all households' protected/fixed baselines plus reserve exceed the site cap, Truss shows deficit and INFEASIBLE; it neither chooses whose breathing support loses power nor displays success. Power cannot be created by priority or AI.

This strengthens I2/I8. It does not guarantee physical continuity through a failed power source, broken plant/enforcer, real device fault or incorrect registered maximum. No real medical equipment is connected to this prototype.

## Scope decision

The previously explored optional SGLang incident explainer is cut at the user’s request. There is no model-serving branch, AI classification, runtime dependency or helper endpoint to implement. Deterministic event references and arithmetic explain decisions. Protected-load tests remain mandatory: reject off/defer, preserve baseline on expiry, keep unclassified devices out of curtailment, and report infeasible floors honestly.
