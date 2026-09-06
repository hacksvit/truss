# 14 — Competition rules

## The constraint

Code2Create requires projects to be built **during** the event, from scratch,
with no pre-built projects, no prior commits and no reused project code.
Organiser sources also state that AI tool use is permitted and that hardware is
allowed but self-supplied. [S17][S18]

## What that forbids

- Carrying implementation code, prior commits, or reusable project modules into
  the event.
- Creating the competition repository before the clock starts.
- Any `git` history that predates the official start.

## What it does not forbid

- **Deciding what to build.** The idea, the boundary and the rejections are
  thinking, not code.
- **Freezing interfaces on paper.** These plans specify six message schemas.
  Writing them down is design; committing them as code before the start is not.
- **Learning the tools.** Disposable exercises against Mosquitto, paho-mqtt,
  Pydantic, OR-Tools and Hypothesis, deleted before the event.
- **Brand and pitch material.** The name, the mark, the demo script.
- **Rehearsal.** Running cold-start passes of an idea is preparation; the
  artefact you rehearse with does not travel.

## How this repository stays compliant

- **No implementation code lives here.** Plans, brand, protocol specification
  and research only.
- Any practice code goes in a scratch directory outside this tree and is deleted
  before check-in.
- The competition repository is created **after** the official start, and the
  first commit is an empty scaffold with a timestamp.
- If organisers rule that even written schemas are too much preparation, we
  retype them from these documents inside the first hour and lose nothing that
  matters. The value here is the decisions, not the keystrokes.

## Open items to confirm directly with organisers

These were unresolved in the source research and **must** be confirmed rather
than inferred:

1. **The event dates.** The official graVITas page and ACM-VIT's promotional
   material disagreed (6–8 vs 7–9 September). Confirm through the participant
   portal or by messaging the organiser. [S17][S19]
2. **Idea submission state and deadline.** Sources gave conflicting internal and
   external deadlines. If registered, submit through the participant portal
   immediately. [S18][S19]
3. **What "from scratch" permits.** Ask explicitly at the opening ceremony
   whether written interface specifications prepared in advance are acceptable.
   Until answered, assume the strictest reading.
4. **Judging weights.** The official page listed criteria as TBD. Ask whether
   weights exist and what they are.

Do not infer any of these four. Ask, and write down the answer with who gave it.
