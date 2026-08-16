# Knowledge Base: Plan

Open work only, for the knowledge base described in [knowledge-base.md](knowledge-base.md).

**Completed items are deleted from this file, not ticked and kept.** The previous build plan died of the opposite habit: it accumulated finished milestones until two thirds of it described a project that no longer existed, and an agent reading it was actively misled. Git history is the record of what was done. This file is only the record of what is not.

When everything here is gone, delete the file.

Phase numbers are stable identifiers, not positions. A completed phase is removed and the rest keep their numbers, so a reference to "Phase 2" elsewhere does not rot.

---

## Phase 2: the guarantee

The reason for building this rather than bookmarking things.

- [ ] **Numeric consistency lint.** Every numeric claim on a page whose `feeds:` names a library entry must still agree with that entry. Decide how claims are marked so they can be extracted: most likely a small table per page rather than free prose, since parsing prose for numbers is a bad idea.
- [ ] **Wire it into CI**, alongside `ruff`, `mypy` and `pytest`.

## Phase 3: the operations

Only worth building once there is a corpus to operate on.

- [ ] **`ingest`** as a skill: capture a source, write or revise pages, update `index.md`, append to `log.md`.
- [ ] **`query`** as a skill: answer from compiled pages, and file good answers back as pages.
- [ ] **`lint`** as a skill: wrap the tests above and report what needs human judgement rather than auto-fixing it.

## Corpus backlog

Pages worth writing, kept in [docs/knowledge/index.md](knowledge/index.md) under "Not yet covered" so the gap list sits beside the pages themselves rather than here. Super Heavy V3 and Falcon 9 are the two that would most improve the app, the first to pair with the ship page and the second because it is the calibration reference the whole model is checked against.

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
