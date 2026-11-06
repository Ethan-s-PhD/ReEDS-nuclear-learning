# PROJECT_STATUS: paper AG

*Last updated 2026-11-05 by Claude (Ethan's machine). Branch `paper-AG`. This file is a short summary for the project-manager agent. The full status is in `z-ethan/docs/master_plan.md` §2 on Ethan's machine. That file is local only, because Git ignores `z-ethan/docs/`.*

## Bottom line

Paper AG is an exploratory analysis of what policy-driven US nuclear (SMR) deployment does to consumers, markets and the environment. It uses ReEDS runs from paper 1. The ledger of money and emissions is built and closes on all stage-1 and stage-2 runs. The results are on a private review page for Ethan and the coauthors. Retail rates are computed but wait for Ethan's confirmation of protocol amendment A21. The new ReEDS runs are ready on the lab machine but have not been launched.

## Needs Ethan

| # | Action | Where |
|---|---|---|
| 1 | Confirm protocol amendment A21 (how retail rates are computed and reported). Until then no retail number goes on the review page. | Review page, Decisions, card "Protocol amendment A21" |
| 2 | Start the `new_runs` batch on the lab machine (23 runs). The lab agent reports that it has not started, on Ethan's instruction. | `z-ethan/agent_comms/2026-11-05_new_runs/` |
| 3 | H5: a human author checks by hand how `CA_UTILITY_SHARE` = 0.42 was calculated. | Check sheet in `z-ethan/docs/state_allowance_research.md` (local) |
| 4 | Get an answer from Prof. Davies on which actor receives the RPS residual. Until then it stays a named residual. | Review page, Decisions |
| 5 | Decide whether to commit the uncommitted analysis files (notebooks 20–27, `z-ethan/data/external/`, the review template). | Working tree on Ethan's machine |
| 6 | Open decisions with no date: D5 (reporting variants not yet chosen: state allowances, MCPF, horizon, ownership), D6 (whether paper 1's coauthors join). | Review page; `master_plan.md` §6 |

## Waiting on others

- **Lab machine agent.** The `new_runs` batch (RUN-1, RUN-3, stage-2b no-mandate runs, 2 P05 screening runs) waits for launch. Before launch, the agent swaps in paper 1's `Manifest.toml` and runs the PRAS check (M3). All three retail tasks are done and closed.
- **Coauthors (Wesley and others).** H3 review of the stage-2 results on the review page.

## Next for Claude

1. After Ethan confirms A21: add the retail results (notebook 27) to the review page.
2. When `new_runs/response.md` arrives: check it, then add the returned runs to the AG extract spec and run the ledger on them. Check observation O28 (exports to Canada in stress periods).
3. After the two P05 screening runs return: report them for Ethan's decision on the other 10 P05 baselines (amendment A19).

## Where things are

| What | Location |
|---|---|
| Review page (private; decisions are recorded there) | https://claude.ai/artifact/DZo84uXLTzfuCzFu3BHfJQ |
| Hand-off tasks to the lab machine agent | `z-ethan/agent_comms/` (status table in its `README.md`) |
| Casefile for the new runs | `cases_nuclearlearning_ag.csv` |
| Master plan, protocol, observation log, file ledger | `z-ethan/docs/` (local only) |

## Recent milestones

- 2026-11-05: retail rerun from a patched module copy returned (commit 9a58b80); notebook 27 reads it; observation O34.
- 2026-11-05: found that the ReEDS retail module drops capital rows whose technology names differ in case, including all SMR capital (O33); Ethan chose the patched rerun.
- 2026-11-05: retail pilot and stage-1 retail tasks done on the lab machine.
- 2026-11-04: decisions recorded on the review page; RUN-1, RUN-3 and stage-2b run files pushed (25f71ea, 12c893c).
- 2026-10-28 to 10-30: protocol signed (H1), stage-1 ledger approved (H2), stage 2 widened to 308 runs, review page published.

## Rules that bind this project

- Hypotheses and tests come from the human authors. Claude logs observations only.
- Paper decisions go through decision cards on the review page.
- Commit and push only when Ethan asks. Never publish Zenodo.
- Never send messages on Ethan's behalf.
