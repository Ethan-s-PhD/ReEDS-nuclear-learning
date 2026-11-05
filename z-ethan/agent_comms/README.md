# agent_comms: messages between agents on different machines

This folder carries tasks and replies between Claude on Ethan's machine and the agent on the lab machine. Git on branch `paper-AG` is the only channel: each side commits and pushes here, and the other side pulls.

## Rules

1. **One subfolder per task**, named `YYYY-MM-DD_<task>`. Each subfolder holds:
   - `instructions.md`, written by the side that sends the task;
   - `response.md`, written by the side that does the task;
   - optional `scripts/`, `outputs/` and `reference/` (inputs supplied with the task) and `results/` (files returned with the response).

   A follow-up round in the same task uses `instructions_2.md` and `response_2.md`, and so on.
2. **Write only your own files.** The sender never edits `response.md` or `results/`. The receiver never edits `instructions.md`, `scripts/` or `outputs/`. To ask a question or report a problem, write it in `response.md`.
3. **Commit only inside this folder**, except for files that `instructions.md` names explicitly.
4. **Every commit message starts with** `agent_comms: <task> -`.
5. **Before every push, run `git pull --rebase`.** Never force-push.
6. **Decisions belong to Ethan.** When a step needs a choice that `instructions.md` does not cover, stop that step and write the question in `response.md`. Do not choose.
7. **Report observations only.** Give numbers, errors and timings. Do not explain why a result occurs, and do not propose hypotheses or tests.

## Tasks

| Folder | From → to | Status |
|---|---|---|
| `2026-11-05_retail_pilot` | Claude (Ethan's machine) → lab agent | sent 2026-11-05; step 6 failed (fcae372); round 2 (diagnostic) sent 2026-11-05 |
| `2026-11-05_new_runs` | Claude (Ethan's machine) → lab agent | sent 2026-11-05; runs before the retail pilot |
