# VisionX — Execution Rules

**Status:** Binding. These rules govern every change made to this repository.
**Owner:** Whoever is at the keyboard (human or agent).
**Companion document:** [EXECUTION_TRACKER.md](EXECUTION_TRACKER.md) — the living record of what was actually done.

> These rules exist because this repo has already been burned once by the gap
> between what the docs claimed and what the code did (see
> [ENGINEERING_REVIEW.md](ENGINEERING_REVIEW.md) §21: *"the architecture is
> complete because the classes exist"*). Every rule below closes one specific
> way that gap reopens.

---

## R0 — The definition of Done

A change is **Done** only when all five hold. There is no partial Done.

1. **Reachable** — the code is invoked by something a user or another module can actually call. An unmounted router, an unregistered action, or an unreferenced manager is *not* done.
2. **Correct** — it does what its docstring says, including on the failure path.
3. **Tested** — covered by a test that exercises it through its real interface (HTTP for endpoints, a real socket for WebSockets, a real call for actions).
4. **Gated** — all four quality gates (R3) pass.
5. **Recorded** — README, the tracker, and git all reflect it (R1, R2).

---

## R1 — Always update the README

**Any** improvement, modification, creation, edit, or fix must be reflected in
`README.md` in the same change, if it alters any of:

- what the system can do (feature table, roadmap table),
- how to run, build, test, or deploy it (Quick Start, Testing),
- the project structure tree,
- the tech stack, dependencies, or licensing position,
- test counts, status claims, or maturity claims.

**Never** let the README describe a capability that fails R0. If a fix narrows
a claim, narrow the README claim in the same edit. A README that overstates the
system is treated as a **defect**, logged in the tracker like any other.

---

## R2 — Always update GitHub

Every change lands in git, and git lands on GitHub:

1. Work on a branch — never commit directly to `main` unless explicitly asked.
2. One logical change per commit. Conventional prefixes: `feat:` `fix:` `perf:` `refactor:` `test:` `docs:` `chore:` `security:`.
3. Commit messages state **what changed and why**, and cite the tracker ID (`DEF-012`) where one exists.
4. Push after the gates pass — never push a red tree.
5. Open a PR when the change is non-trivial; the PR body lists the tracker IDs it closes.
6. If CI fails after a push, fixing it is the **immediate next task** — no new work stacks on a red pipeline.

---

## R3 — The four gates

All four must pass before any commit. No exceptions, no "I'll fix it next commit."

```bash
python -m pytest tests/ -q                    # backend tests
ruff check . --select E,W,F --ignore E501     # backend lint
cd client && npx tsc --noEmit                 # frontend types
cd client && npm run build                    # production build
```

If a gate cannot be run in the current environment, say so explicitly in the
tracker entry. **Never report a gate as passing when it was not executed.**

---

## R4 — Tracker discipline

[EXECUTION_TRACKER.md](EXECUTION_TRACKER.md) is updated in the same change, not afterwards.

- Every defect found gets a `DEF-nnn` row **the moment it is found**, even if it will not be fixed now.
- Every defect fixed gets its status, the fixing commit, and the verification method recorded.
- Every execution run (audit, fix batch, refactor) gets a Run Log entry with date, scope, and outcome.
- A defect is only marked `Fixed` when it satisfies R0. Otherwise it stays `Open`, `In progress`, or `Deferred` — with a reason.
- **Nothing is deleted from the tracker.** Superseded entries are struck through and annotated, so the history of what was believed and when stays readable.

---

## R5 — Findings are logged, not silently fixed

When you find something broken, odd, or misengineered **while doing something
else**, you must log it (R4) before deciding what to do with it. Then choose one:

- **Fix now** if it is in scope and small.
- **Defer** with an explicit reason and a tracker row.
- **Never** silently leave it — an unlogged defect is a defect that will be rediscovered at the worst possible time.

---

## R6 — Security changes are never "done later"

Findings in these classes are fixed before any feature work continues:

- authentication or authorization gaps,
- credential handling (storage, comparison, transport, logging),
- anything that fails **open** rather than closed,
- SSRF, injection, or unvalidated user-supplied URLs and paths.

Every new endpoint declares its auth posture explicitly. A route with no
`Depends(...)` auth dependency is a **public** route, and making a route public
is a deliberate, documented decision — never an omission.

---

## R7 — Fail loud, not silent

This is an *alerting* product. A silent failure is worse than a crash.

- An action that does not execute must **not** be recorded as a success.
- Swallowing an exception requires a comment explaining why the failure is safe to ignore.
- A stub that returns a fake success value must be named as such and raise or warn unless explicitly opted into (`allow_stub=True` or equivalent).
- Never let a dropped alert be indistinguishable from a delivered one.

---

## R8 — No unbounded growth

Anything that accumulates per-request, per-IP, per-connection, or per-event must
have a bound: a max size, a TTL, an eviction policy, or all three. In-memory
maps keyed by client IP are the standard way this repo leaks memory — cap them.

---

## R9 — Docs must not outrun the code

`implementation_plan.md` and `MASTER_BLUEPRINT.md` are **vision documents, not
commitments**. They do not define Done; R0 does. Never cite them as evidence
that something is built. When plan and code disagree, the code is the truth and
the plan gets a correction note.

---

## R10 — Honest reporting

- If a test fails, say so, and paste the output.
- If a step was skipped, say which and why.
- If a fix is partial, say what remains and log it as a tracker row.
- Never describe work as complete and verified unless it was executed and verified.

---

## Change log for this file

| Date | Change |
|---|---|
| 2026-08-02 | Created. Rules R0–R10 established during the first tracked execution run. |
