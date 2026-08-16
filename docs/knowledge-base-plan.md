# Knowledge Base: Plan

Open work only, for the knowledge base described in [knowledge-base.md](knowledge-base.md).

**Completed items are deleted from this file, not ticked and kept.** The previous build plan died of the opposite habit: it accumulated finished milestones until two thirds of it described a project that no longer existed, and an agent reading it was actively misled. Git history is the record of what was done. This file is only the record of what is not.

When everything here is gone, delete the file.

---

## Phase 0: before Flight 14 flies

Time-boxed. Flight 14 is targeting late August 2026 and has not launched, so this window closes in roughly two weeks. Nothing else here depends on Phase 0, and Phase 0 depends on nothing, so it goes first purely because it expires.

- [ ] **Pre-register the payload prediction.** `studies/flight-14-prediction/` with `run.py` and `finding.md`: what the model says Starship delivers to a real orbit, under which dry-mass assumption, with the uncertainty band. Commit before launch. After the flight this cannot be created honestly.
- [ ] **Correct the Flight 12 record.** `data/flights.yaml` says `2026-05-01` with `date_precision: month`; it flew **22 May 2026**. The payload description says "22 Starlink V3 mass simulators"; it was 20 simulators plus 2 functional V3 satellites, which matters because it was the first time a ship deployed working hardware. One YAML edit.

## Phase 1: the schema

Nothing downstream works until pages have a shape and something checks it.

- [ ] **`raw/` and its rule.** Text-only captures, each with source URL and retrieval date. Add to `.gitignore` whatever the rule excludes.
- [ ] **`docs/knowledge/` skeleton.** `index.md` and `log.md`, both with their format documented in place.
- [ ] **Record the frontmatter convention in [CLAUDE.md](../CLAUDE.md).** OKF v0.2 core fields plus the `provenance` and `feeds` extensions. This is the schema layer of the pattern, so it belongs there rather than here.
- [ ] **Two seed pages**, migrated from [physics-reference.md](physics-reference.md) section 5 rather than researched fresh: `engines/raptor-3.md` and `vehicles/starship-v3.md`. Migrating proves the format carries real content before any effort goes into gathering more.
- [ ] **`tests/test_knowledge.py`**: every page parses, has `type`, has at least one dated source, is not past `stale_after`, and every `feeds:` target exists in `data/`.

## Phase 2: the guarantee

The reason for building this rather than bookmarking things.

- [ ] **Numeric consistency lint.** Every numeric claim on a page whose `feeds:` names a library entry must still agree with that entry. Decide how claims are marked so they can be extracted: most likely a small table per page rather than free prose, since parsing prose for numbers is a bad idea.
- [ ] **Wire it into CI**, alongside `ruff`, `mypy` and `pytest`.

## Phase 3: the operations

Only worth building once there is a corpus to operate on.

- [ ] **`ingest`** as a skill: capture a source, write or revise pages, update `index.md`, append to `log.md`.
- [ ] **`query`** as a skill: answer from compiled pages, and file good answers back as pages.
- [ ] **`lint`** as a skill: wrap the tests above and report what needs human judgement rather than auto-fixing it.

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
