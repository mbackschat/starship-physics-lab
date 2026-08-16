# Knowledge Base: Plan

Open work only, for the knowledge base described in [knowledge-base.md](knowledge-base.md).

**Completed items are deleted from this file, not ticked and kept.** The previous build plan died of the opposite habit: it accumulated finished milestones until two thirds of it described a project that no longer existed, and an agent reading it was actively misled. Git history is the record of what was done. This file is only the record of what is not.

When everything here is gone, delete the file.

Phase numbers are stable identifiers, not positions. A completed phase is removed and the rest keep their numbers, so a reference to "Phase 2" elsewhere does not rot.

---

## Maintenance, which nothing currently drives

Every page carries a `stale_after` date and `uv run pytest -m freshness` reports the ones past it, but that check is deselected from the default run on purpose and **nothing runs it automatically**. Left as it is, the corpus rots quietly.

- [ ] **Decide what drives the recheck.** A scheduled agent is the obvious fit and the repository already has the tooling for one. The alternative is a habit, which is not a mechanism.

## Corpus backlog

Pages worth writing are listed in [docs/knowledge/index.md](knowledge/index.md) under "Not yet covered", so the gap list sits beside the pages themselves rather than here.

## Phase 4: close the loop on Flight 14

Blocked until the flight happens.

- [ ] Capture sources, compile `flights/flight-14.md`.
- [ ] Fill the existing Flight 14 row in `data/flights.yaml`. One row. If code has to change, the abstraction is wrong and fixing that comes first.
- [ ] Run the calibration and golden tests, and record what reality said.
- [ ] **Study: predicted against observed.** Cite the pre-registration from Phase 0.
- [ ] If the measurement contradicts chapter 7, revise the chapter and say so plainly.

---

## Decided against, with the condition that would reopen it

Recorded so they are not re-litigated, and so it is clear what would change the answer.

| Rejected | Reopen if |
|---|---|
| Numeric confidence scores, 0.0 to 1.0 | Never. Categorical provenance with a named source is auditable; a float is not. |
| Vector or graph retrieval | The corpus approaches 200 pages and grep starts missing things. |
| OKF `Attested Computation` for golden numbers | OKF reaches 1.0. |
| Separate repository plus git submodule | A second project genuinely needs this knowledge base, or `raw/` exceeds a few hundred megabytes despite the text-only rule. |
| Installing a packaged LLM-wiki plugin | Never, while this project's schema is stricter than the packaged ones. |
| Separate `ingest`, `query` and `lint` skills | Never. They shared one schema, so three skills meant three copies of it. Lint became a single `pytest` invocation and needed no skill at all. One `knowledge-base` skill covers both real operations. |
