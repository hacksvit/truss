# 22 — Protected overnight loads; optional SGLang

Added after the user's clarification: SGLang is desirable **if useful and feasible**, not a mandatory dependency. The user's own PC is the intended host. This supersedes the blanket “no LLM features” exclusion only for the bounded optional use below. It does not weaken any authority or baseline rule.

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

## SGLang feasibility on this host

Read-only host inspection on 6 September 2026 found:

| Item | Observed here |
|---|---|
| CPU | Intel Core i7-13700HX, 24 logical CPUs |
| System RAM | about 15 GiB usable (nominal 16 GB); about 3.6 GiB available at inspection |
| GPU | NVIDIA GeForce RTX 5060 Laptop GPU |
| GPU memory | 8,151 MiB total; 7,511 MiB free at inspection |
| Driver / OS | NVIDIA 610.57.04; Linux 6.18.49-1-lts |

**Verified local observations**, not benchmark results. Assumption H1: the inspected host is the PC the user intends; if different, the hardware conclusion does not transfer. No software was installed, weights downloaded or inference performed.

SGLang is a model-serving/programming runtime, not an electrical allocator. Its official project and documentation expose local serving, OpenAI-compatible endpoints and constrained structured output. These are capability claims, not proof of latency on this PC. [SGLang project](https://github.com/sgl-project/sglang), [installation/platform notes](https://docs.sglang.io/docs/get-started/install), [structured-output source documentation](https://github.com/sgl-project/sglang/blob/main/docs_new/docs/advanced_features/structured_outputs.mdx).

**Strong inference, medium confidence:** a small model is plausible within 8 GB VRAM. A candidate is [Qwen2.5-1.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct), whose card lists 1.54B parameters and a SGLang serving path. Rough half-precision weight storage alone is about 3.08 GB decimal; KV cache, runtime, temporary buffers and display usage are additional. This arithmetic does not verify kernel/driver compatibility, memory peaks or useful answer quality. Current system RAM headroom is narrow, and model setup must be tested alongside the core workload.

Do not pin “latest” documentation examples as a promise of compatibility. At event time choose one tested SGLang/PyTorch/CUDA/model revision, record hashes, use local model/tokenizer paths and short context (target 2,048 tokens, output≤256, one request at a time). No huge model, CPU fallback tuning, multi-GPU serving or cloud endpoint. If weights/dependencies are not already available under the organiser's allowed public-dependency policy, network-free operation is not ready. Do not disguise borrowed project code as a dependency.

## What to integrate, if the gate passes

**Recommended optional feature: a read-only incident explainer inside LoadPath.** It can rephrase the recorded event chain, including “the protected baseline stayed reserved while flexible grants expired.” Deterministic arithmetic and source event references remain the authority. It replaces an optional prose explanation tab, not the numeric inspector and not the planner.

Flow:

```text
Explicit click in inspector
    → API freezes existing incident facts and event IDs
    → optional helper calls local SGLang over loopback
    → schema validation + reference validation
    → labelled draft explanation beside deterministic facts
```

Helper has no MQTT credentials, no live control methods, no authority database write permission and no access to raw device names/medical notes. Its input uses pseudonymous members, aggregate baseline/lease/reservation facts and selected reason codes. It cannot protect/unprotect devices, set cap, issue leases, alter debt, reset state or recommend interrupting treatment. Client-supplied text never becomes a system instruction or a tool invocation.

Structured output constrains format, not truth. A well-formed false explanation is still possible. Validate event IDs against supplied evidence, render quoted facts from deterministic records and label the narrative **“AI explanation — check the event trace”**. If answer conflicts with cap/floor facts or includes unsupported references, discard it. Simple numerical/reference checks are not a complete semantic verifier; that is why the model is not in any safety claim.

For the user's proposed “AI recognises breathing equipment” use: **do not implement automatic criticality classification in the MVP**. A future local intake assistant could ask a person to confirm a protection requirement and produce a draft for human review. It must never decide a device is safe to interrupt, infer a diagnosis, or downgrade existing protection. The mandatory explicit policy selector works without it and is more reliable for this task. False negatives in a model-based safety classifier would undermine the thesis of the whole project.

## Optional files, owners and interfaces

Only add these during the event after the gate; they extend 19, not the core import graph.

| Future file | Owner / purpose | Public interface / dependencies |
|---|---|---|
| `src/truss/explanation.py` | M1, bounded optional service client | `explain(FrozenIncident) → ExplanationResult`; HTTP client and strict Pydantic models only, no coordinator import |
| `src/truss/explanation_models.py` | M1, finite input/output contract | models below; Pydantic + common IDs |
| `web/src/components/IncidentExplanation.tsx` | M4, explicit request and draft display | incident ID props; local pending/result/error state; api client only |
| `tests/test_explanation.py` | M5, invalid-reference/timeout/isolation tests | fake HTTP responses; core invariant comparison with helper off/on |
| `fixtures/explanation-cases.json` | M5, known facts and adversarial text | protected baseline, infeasible floors, lost ack, unknown data, malicious quoted text |
| `docs/sglang.md` | M1, tested local runtime/model manifest | versions, hashes, resource limits, offline readiness, actual timing and kill switch |

Runtime model directory is an external public dependency, never a committed project module. Optional helper service is bound to loopback; frontend reaches only Truss API. Installation/runtime manifest is written during the event; no runnable configuration is included in this plan.

### Exact optional contract

Types use 20's restrictions, extras forbidden, nullable fields required.

**FrozenIncident:** `incident_id: UUID`; `run_id: UUID`; `source: live|mock|replay`; `from_seq: Nat`; `to_seq: Nat`; `facts_hash: Hash`; `facts: list[IncidentFact]` (1–30).

**IncidentFact:** `event_seq: Pos`; `member_id: Maybe(ID)`; `kind: cap|baseline|grant|expiry|observation|unknown|infeasible`; `value_w: Maybe(W)`; `reason: Maybe(Reason)`. No free text, device identifiers, diagnoses or medical schedules enter the model prompt.

**ExplanationResult:** `incident_id`; `facts_hash`; `status: ready|unavailable|timeout|rejected`; `summary: Maybe(string 1–800 chars)`; `cited_event_seqs: list[Pos]` (≤30); `model_revision: Maybe(string≤128)`; `latency_ms: Maybe(nonnegative number)`; `limitations: list[string≤200]` (≤5). Ready requires nonempty summary and all cited seqs from FrozenIncident. Other results have summary=null and an explicit reason in limitations. Store generated result separately from canonical replay facts; do not regenerate it and claim byte-identical replay.

`POST /api/v1/explanations`: `{run_id, source, incident_id, from_seq, to_seq}`; header `Idempotency-Key: UUID`; no control revision required because this is read-only computation. API builds facts server-side; browser cannot inject facts. Synchronous bounded response ≤5 s: 200 ExplanationResult ready; 503 unavailable; 504 timeout; 422 malformed/invalid selection; 429 busy. Error envelopes use 20. Timeout stops client waiting and attempts cancellation; late output is discarded. No automatic retries or background queue. Identical key and facts returns cached result. Maximum one active inference, context≤2,048 tokens, output≤256 tokens; reject rather than truncate away safety-relevant facts. `GET /health` capability `sglang_explanation=false` whenever disabled/unready. Core `/state` shape is unaffected.

No new route or fifth judge-control group. Button sits inside existing LoadPath. Mock provides ready, timeout, unavailable and rejected-reference results, all labelled mock. Core tests require app startup with SGLang absent.

## Gate, cost and failure policy

At hour 24, only if G12/G18/G24 are green: M1 gets at most **two hours total**, including setup, a tiny API adapter and validation; M4 at most one hour by reusing the drawer; M5 at most one hour from optional lab scope. This is an optimistic integration allowance, not a promise. If runtime setup alone consumes one hour, cut it. No new kernel compilation or driver change during the event.

Pass requires: offline cold start; tested model on this exact GPU; repeated 30 incident explanations with recorded median/p95/max; no invalid event references displayed; honest unknown/infeasible answers; five-second timeout; model kill/OOM leaves core running; no protected-policy mutation; no observed violation of the chosen plant timing bound while inference runs. Test both with and without inference under the same scenario. One warmup anecdote is not a benchmark. Empty/incorrect generated output falls back to deterministic LoadPath, without harming the demo.

Protected-load policy tests are **mandatory even if SGLang is cut**: protected off/defer command rejected; expiry preserves protected baseline; AI output cannot access control path; unknown device cannot be auto-classified flexible; cap below baselines remains INFEASIBLE; wall clock crossing night/day changes no protection; stale protected telemetry does not imply zero draw.

Confidence conclusion: SGLang on this hardware is **plausible, not verified**. It can add an optional local explanation feature. It is not needed to preserve breathing-related protected requirements and would be the wrong authority for that decision. The core remains a safety-protocol demonstrator, with no mains switching, no medical-device connection, no certification and no savings claim.
