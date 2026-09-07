# Explaining and demonstrating Truss

Introduce the idea on the website, then use Console Live runtime for process behaviour. The three-home Example is an illustration; the live console runs five virtual homes. Always identify the source on screen.

## A short introduction

“Several homes can share a limited power supply. Truss gives each home an agreed basic allowance, then shares spare capacity. Each home chooses its own appliances. Extra permission expires if it is not renewed, and we keep counting earlier promises before making new ones. We demonstrate this with virtual appliances and real communicating processes.”

## Before presenting

Follow [operations](operations.md), choose Live runtime in Console, wait through recovery and check fresh observations. Keep a labelled recording as fallback. Run disruptive tests separately from the presentation. The supplied site has five homes, 900 W of floors, 100 W reserve and a 5,000 W cap. Whole appliances can leave permission unused, so observed watts need not equal cap minus reserve.

## A three-minute route

1. **Home, about 25 seconds.** Introduce the problem and scroll through a few cards. “We share an allowance; each home still makes local choices.”
2. **Info or Example, about 35 seconds.** Show the agent and coordinator. “The coordinator receives aggregate demand. This three-home scene explains the rule; it is not a live reading.”
3. **Console, about 70 seconds.** Identify proposed, issued, reserved and observed watts. Run **Coordinator stops**. “The coordinator process stops while the independent virtual plants remain alive. We wait for their fresh readings to show what happened.” Inspect the report and recovery.
4. **Console, about 25 seconds.** Show **Minimums do not fit**, or a recorded result. “The system reports a shortage when supply cannot cover approved minimums. It cannot create electricity.”
5. **Lab and Credits, about 25 seconds.** Show a completed benchmark and the team. “This larger group tests allocation only. The current live runtime has five virtual homes.”

Do not rush a drill to match this timing. Skip a visual beat if recovery is still running. An inconclusive result needs investigation, not a new label.

## Simple answers to likely questions

| Question | Answer |
| --- | --- |
| What is a member agent? | A small program that chooses appliances inside one home's allowance. A room could become a member later. |
| Why not just use priorities? | Priorities choose preferences. They do not account for permissions another home may still hold. |
| Why start the timer at the request? | Travel time must consume the lease's life. A delayed reply must not create a fresh six seconds. |
| Why wait 6.4 seconds on restart? | Earlier authority must become unusable before more is issued, allowing for declared clock and enforcement bounds. |
| Does the coordinator know the appliances? | It uses household offers. The separate demo observer can inspect fictional device details. |
| Why are some watts unused? | A whole on/off appliance may not fit. The model skips it instead of pretending it can run partly. |
| Do credits guarantee repayment? | No. They give bounded weight for withheld authorisation, not an energy refund or completion guarantee. |
| Is the 3D scene the backend? | It illustrates the tested rule for three homes. Console Live runtime shows the separate five-home process system. |
| Are real appliances controlled? | No. Appliances and readings are virtual. The optional physical screen only displays status. |
| Why was software the main work? | Delays, overlapping promises, restarts and missing evidence require a protocol. A switch alone does not handle them. |
| Is the mechanism entirely new? | Its components have prior art. Our contribution is this implemented, tested and explainable combination. |
| Can it run thousands of homes? | We benchmark thousands of synthetic allocation inputs. Full-system scaling still needs measurement. |
| What happens on Heroku? | One web dyno hosts one shared virtual run. Visitor controls affect that run; restart loses temporary runtime files. |

## Explain the difficult case with two homes

Use a simplified 1,000 W site with no reserve. Old permissions are A=800 W and B=200 W. New desired shares are A=200 W and B=800 W. Both plans total 1,000 W, but delivering only B's increase could allow 1,600 W. The gate prevents spending A's still-outstanding permission twice.

This explains the software responsibility better than simply calling the algorithm complicated.

## If the live demonstration fails

Keep the actual error or missing-data state visible. Use a saved, labelled recording for the explanation, or explicitly choose Mock preview to demonstrate the interface. Do not narrate a mock action as a real process kill.

Preserve the failed run. Investigate source mode, process health, sample freshness and the operation record. Never erase authority storage to dismiss recovery. Do not publish credentials with evidence.

The [project report](project-report.md) contains the longer explanation and team contributions; [verification](verification.md) records the checks.
