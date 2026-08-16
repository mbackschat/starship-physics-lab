# The Knowledge Base

How this project stores what it has *looked up*, as opposed to what it has *worked out*.

This document describes the design and the reasoning behind it. The open work is tracked separately in [knowledge-base-plan.md](knowledge-base-plan.md).

## The problem it solves

The repository already holds two kinds of knowledge and handles both well.

[physics-reference.md](physics-reference.md) holds verified physics, with a claim-by-claim log of what was checked against what. `data/*.yaml` holds the numbers, each carrying its provenance. [`studies/`](../studies/) holds investigations, each a script plus the finding it produced.

What is missing is everything in between: the reference material that explains *why* an entry in `data/` says what it says, where a figure was published, which source disagrees with which, and what changed when an operator restated a number. Today that lives in chat logs and browser tabs, which is to say it does not live anywhere.

The obvious fix, a folder of notes pulled from the web, would quietly wreck the thing that makes this project worth anything. Its credibility rests on one sentence: every number is recomputed independently and labelled published, estimated or contested. A pile of unverified notes sitting beside `data/` is an invitation for an agent to grep it, find a plausible figure, and put a number on a page that never went through verification. The provenance badges would become decoration.

So the knowledge base has to inherit the verification discipline, not sit next to it.

## The pattern

This follows the **LLM wiki** pattern, published by Andrej Karpathy in April 2026. Three layers and three operations.

| Layer | Owner | Role |
|---|---|---|
| `raw/` | human | Immutable captured sources. The model reads them and never edits them. |
| `docs/knowledge/` | model | Compiled, interlinked pages. The model owns these. |
| [CLAUDE.md](../CLAUDE.md) | human | The schema: conventions, rules, workflow. |

**Ingest.** A source arrives, is captured into `raw/`, and the model writes or revises the pages it touches, updates the index, and appends to the log.

**Query.** Questions are answered from the compiled pages rather than by re-reading sources. A good answer becomes a page, so exploration compounds.

**Lint.** Periodic health check: contradictions, stale pages, orphans, and the domain-specific rule below.

The point is that this is *not* retrieval-augmented generation. RAG re-derives an answer from raw documents on every question. Here the synthesis cost is paid once, so cross-references and contradictions are already resolved when a question arrives.

### Why the pattern was hand-rolled rather than installed

Several packaged implementations exist. All of them impose their own directory layout, typically `wiki/entities/`, `wiki/concepts/` and `wiki/syntheses/`, which would duplicate `studies/` and `physics-reference.md` and leave the repository with two competing knowledge layers.

More to the point, the consistent finding across independent reviews of these tools is that **the schema is most of the product**, and that implementations enforcing strict domain rules produced knowledge bases people trusted while fully automated ones produced output that always needed double-checking. This project's schema is already stricter than anything the generic tools ship, because `Provenance` is enforced by a Pydantic model and the verification log is claim by claim. Adopting a package would have meant adopting a weaker schema.

## The format: OKF v0.2

Pages use **[Open Knowledge Format](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md) v0.2**, Google Cloud's vendor-neutral specification for exactly this pattern, published June 2026. It is a directory of markdown files with YAML frontmatter, no registry, no required tooling.

Only `type` is required. Everything else is optional, and the specification requires consumers to preserve unknown keys and never reject a document for having them, which is what makes the project's own fields legal rather than merely tolerated.

Four things it gives us that would otherwise have been invented here, worse:

- **`generated` and `verified` kept distinct**, because the author and the checker are different parties. That is this project's central discipline expressed as a field.
- **`status: draft | stable | deprecated`**, which gives supersession without machinery. A deprecated page stays for its links and its history.
- **`stale_after`**, an absolute date rather than a time-to-live, so a staleness check is a plain comparison.
- **`sources[].id`**, which enables per-claim attribution through markdown footnotes, the thing [physics-reference.md](physics-reference.md) already does by hand.

### Trust and provenance are two different axes

This is the part worth reading twice, because conflating them would lose information.

| | Question it answers | Field | Values |
|---|---|---|---|
| **OKF trust** | Did a human check *this page* against its sources? | `verified` | Derived: unverified, machine-confirmed, human-reviewed |
| **Project provenance** | How much weight can *this number* bear? | `provenance` | `published`, `estimated`, `contested`, `derived`, `announced` |

A page can be human-reviewed and still describe a contested number, and an unreviewed page can quote a published one. Neither implies the other, so both are recorded.

OKF's trust tiers are categorical and derived rather than stored, and the specification is explicit that it records signals rather than scores. That is the same position this project takes, which is why the two compose instead of fighting. A numeric confidence value between 0 and 1 was considered and rejected: it implies a precision nobody can audit, and "contested, because these two sources disagree by a factor of two" is a claim a reader can check in a way that "0.62" is not.

## Layout

```
raw/                                    captured sources, never edited
  2026-08-16-wikipedia-starship-launches.md
docs/knowledge/
  index.md                              catalog, one line per page
  log.md                                append-only ingest / query / lint record
  engines/raptor-3.md
  vehicles/starship-v3.md
  flights/flight-13.md
```

**`raw/` holds text, never binaries.** A source is captured as its markdown conversion plus the URL and the date it was retrieved. No PDFs, no page archives, no video. This keeps the repository small and, more importantly, keeps a capture diffable: seeing what changed in a source between two retrievals is the whole point of keeping it. Anything that cannot be reduced to text is cited by URL instead.

## Page format

```yaml
---
# OKF v0.2 core
type: Vehicle
title: Starship V3
description: SpaceX's two-stage reusable launch vehicle, as flown from Flight 12.
tags: [starship, spacex, block-3]

sources:
  - id: wiki-launches
    resource: https://en.wikipedia.org/wiki/List_of_Starship_launches
    title: List of Starship launches
    last_modified: 2026-08-14

generated: { by: claude-opus-5, at: 2026-08-16T10:00:00Z }
verified:
  - { by: human:mbackschat, at: 2026-08-16T11:00:00Z }

status: stable
stale_after: 2026-09-15

# project extensions, explicitly legal under OKF
provenance: contested
feeds: [data/vehicles.yaml#starship_v3]
---
```

`feeds:` is the load-bearing extension. It names the library entries this page is the evidence for, and it is what turns a folder of notes into something with a guarantee attached.

## Lint

Ordinary checks: every page has `type`, every source carries a retrieval date, `stale_after` has not passed, `feeds:` targets exist, deprecated pages are marked rather than deleted, no orphans.

Then the one that matters:

> **Every numeric claim on a page whose `feeds:` names a library entry must still agree with that entry.**

This is a contradiction detector specialised to this repository, and it is the reason the knowledge base is worth building rather than just bookmarking things. It means the prose and the numbers cannot drift apart silently. If an operator restates a figure and the page is updated, lint fails until `data/` is updated too, or until the disagreement is recorded deliberately as `contested`.

## Deliberate deviations from the canonical pattern

**The model does not own the numbers.** The pattern gives the model ownership of the wiki layer. Here that holds for prose, but any value that becomes a number in `data/` still passes through human verification. Without that, the 61-of-64 claim stops being true.

**No vector or graph retrieval.** Later extensions of the pattern add BM25 plus embeddings plus graph traversal, on the grounds that flat indexing degrades somewhere past 200 to 500 pages. This corpus will be far smaller, grep is exact and free, and fuzzy retrieval is a poor fit for a project whose entire point is an exact number with a citation. Revisit if the page count approaches 200.

**No attested computations, yet.** OKF defines an `Attested Computation` type, with a deterministic attester confirming that a value came from the sanctioned computation. The golden numbers in [physics-reference.md](physics-reference.md) section 7 are exactly this, and `tests/test_golden.py` is already the attester. The mapping is close enough to be worth doing eventually, but it is the most elaborate part of a 0.2 specification and it buys nothing the golden tests do not already deliver. Revisit if OKF reaches 1.0.

**One repository, not a submodule.** Splitting the knowledge base into its own repository was considered. It breaks the guarantee above: a submodule pins a commit, so the wiki and the library can diverge while CI stays green, which is precisely the failure the lint exists to prevent. It also breaks the promise that recording a new flight is one edit. If a second consumer ever appears, `git subtree split` extracts the directory with its history intact, so nothing is lost by waiting.

## The loop this is for

The knowledge base earns its keep when reality arrives and disagrees with the model.

The model currently predicts a specific figure for what Starship delivers to orbit. Flight 14 will measure it. The sequence is:

1. **Predict, and commit the prediction, before the flight.** Once telemetry exists it becomes impossible to prove the model was not adjusted to fit. Pre-registration is what keeps "verified independently" defensible.
2. Capture the sources into `raw/` and compile the flight page.
3. Record the observation as **one row** in `data/flights.yaml`. If this needs a Python change, the abstraction is wrong and that is the thing to fix.
4. Run the calibration and golden tests. They either pass or they name the number reality disagrees with.
5. Record the comparison as a study: predicted, observed, and the gap.

If the measurement contradicts the case study, that gets said in public. It is a better outcome than being right.

## Sources

- Karpathy, `llm-wiki`, April 2026: <https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f>
- Open Knowledge Format v0.2 specification: <https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md>
- OKF v0.2 trust signals: <https://cloud.google.com/blog/products/data-analytics/okf-v0-2-adds-trust-signals/>
