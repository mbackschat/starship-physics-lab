---
name: knowledge-base
description: Ingest researched material into the knowledge base, or answer a question from it. Use when capturing a source URL or article about rockets, engines, vehicles, flights or launch providers; when adding or revising a page in docs/knowledge/; when updating data/*.yaml from newly published information; or when answering a factual question about Starship, Raptor, Super Heavy, Falcon, Ariane or any vehicle the project models. Also use after a Starship flight to record what happened.
---

# Working the knowledge base

The corpus holds what the project has **looked up**. `studies/` holds what it has **worked out**. If the answer comes from running code, it is a study, not a page.

Design and reasoning: [docs/knowledge-base.md](../../../docs/knowledge-base.md). Schema: [CLAUDE.md](../../../CLAUDE.md), "Knowledge base".

## Ingest

1. **Capture first, compile second.** Write the source into `raw/YYYY-MM-DD-publisher-subject.md`, where the date is when *you* retrieved it. Front matter is `resource`, `title`, `retrieved`. Reduce to text; never commit a PDF or an image. If it will not reduce, cite it by URL from the page instead and capture nothing.

2. **Never overwrite a capture.** Recapturing a source later means a *new* file with the new date. The point of keeping the original is being able to diff what changed.

3. **Compile or revise the pages it touches.** One page per subject, under `vehicles/`, `engines/`, `flights/` or a new folder if the subject genuinely needs one. Cite the capture in `sources`, with `last_modified` set to the retrieval date.

4. **Assert what the page stands behind.** Every value the page displays in a table goes in `feeds[].asserts`. Anything left out is unguarded, and unguarded is the failure this whole thing exists to prevent.

5. **Update [docs/knowledge/index.md](../../../docs/knowledge/index.md)**, including the "Not yet covered" list if the source revealed a gap.

6. **Append to [docs/knowledge/log.md](../../../docs/knowledge/log.md).** Record what was ingested, what it changed, and anything you found and did *not* resolve. The log is for reasoning; git already holds the diffs.

7. **Run the checks.** `uv run pytest tests/test_knowledge.py`

### When a source disagrees with the library

This is the interesting case and the one to get right.

- If the source is better, update `data/*.yaml` **and** the page's `asserts` together. They are checked against each other, so a half-update fails the suite.
- If the sources disagree with *each other*, **record the disagreement rather than picking a winner.** Say who says what, in both the page and the library `note`. Silently choosing is how a project loses the right to claim its numbers were verified.
- If the number is contested, that is what `provenance: contested` is for. Never present it as settled.

### When a flight happens

Recording a flight must be **one row** in `data/flights.yaml`. If it seems to need a Python change, the abstraction is wrong and fixing that comes first. Compile a `flights/flight-NN.md` page beside it, and if a prediction was pre-registered in `studies/`, write a separate study comparing predicted against observed rather than editing the prediction.

## Query

1. Read [docs/knowledge/index.md](../../../docs/knowledge/index.md) first. It lists every page and what it feeds.
2. Answer from the pages. Grep the corpus; it is small and exact search beats guessing.
3. **Cite the page, and check its `status` and `stale_after`.** A `deprecated` page is kept for history and should not be quoted as current. A stale one needs rechecking before it is relied on.
4. If the answer was worth working out, file it as a page so the next question starts from it.
5. If the corpus does not cover it, say so and offer to ingest a source. Do not answer from memory and present it as though it came from the corpus.

## Lint

No skill needed, it is one command:

```sh
uv run pytest tests/test_knowledge.py
```

It checks that pages parse, declare a `type`, cite a dated source, declare a `stale_after`, carry a `provenance`, are listed in the index, point at library entries that exist, and **do not contradict the values they assert**. CI runs it with everything else.

Freshness is separate and deselected by default, because it fails on a date rather than on a change:

```sh
uv run pytest -m freshness
```

Run it when picking up the corpus after a gap. Anything it names needs its sources recaptured and its `asserts` rechecked, then a new `stale_after`.

What no check can catch is whether a page's prose agrees with its own `asserts`. That is why step 4 of ingest matters: the assertion is the contract, so it has to cover every value the page states.
