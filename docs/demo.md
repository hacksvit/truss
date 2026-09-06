# Three-minute explanation and honest fallback

The backend now supports **real local MQTT with independent virtual-device processes**. The existing frontend still shows mock until the user completes its source-aware handoff. Use the mock script below only with its label. Use the live script after connecting the frontend to source=live and verifying the corresponding controls.

0:00–0:30 — Open `/`. “Five homes share one inverter limit. Each home exposes an aggregate offer; private appliance details stay in the household. We reserve agreed essentials and share the remaining capacity.” Point out that the observer's device detail is fictional and separately privileged.

0:30–1:15 — Open `/console`. Identify proposed watts, retained authority, observed watts and their different meanings. Set the mock cap to 3000 W. Explain why an old permission cannot be erased by changing a dashboard number. Wait for the illustrated transition; do not call it a measured enforcement latency.

1:15–1:50 — Use the mock coordinator-stop button. Explain the request-anchored six-second timer and the local floor. Inspect the protected fictional load: it is excluded from automated curtailment for the entire run, including after expiry. “We do not connect medical equipment. AI is not allowed to decide whether an essential appliance can be interrupted.”

1:50–2:15 — Make member C stale. Show Unknown rather than zero. Then set cap to 500 W: explain infeasible baselines. “The protocol cannot create power when the supply is smaller than our reserved essentials.”

2:15–2:45 — Open `/lab`, run small and larger batches. These points time the actual allocator over synthetic member offers. Report median/p95 and sample count. Do not call this full-system latency, flat scaling, or a live 5000-household demonstration.

2:45–3:00 — Show test results and pending integration gates. Show the actual backend test record separately from this mock illustration. The real process suite covers independent plant fallback; a mock animation itself remains no evidence of that result.

## Live backend script

Use the real chaos endpoint or connected frontend to terminate the owned coordinator while API/member/plant processes stay alive. Record independent member meters and their sample ages; show expiry within the declared timing allowance and baseline preservation. Restart twice inside one TTL; retain old exposure through a cap drop; heal a delayed partition mid-renewal. Show boot/run/request/lease references in the event trace. Capture timings from the shared host domain, not browser animation. Inspect the captured sequence read-only with an explicit gap indicator; interactive replay UI remains optional. If any prerequisite fails, keep the labelled script above.

Explanations use recorded references and deterministic arithmetic. AI and SGLang have been removed from the project scope.
