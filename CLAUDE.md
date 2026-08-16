# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

An interactive rocket physics explorer, served as a static site that runs Python in the reader's browser. [README.md](README.md) is the human-facing pitch; this file is the working brief.

## Commands

```sh
uv sync                                          # install, including the dev group
uv run pytest                                    # the whole suite
uv run pytest tests/test_golden.py               # one file
uv run pytest tests/test_golden.py::test_name    # one test
uv run pytest -k staging                         # by name
uv run pytest -m golden                          # only the documented-number tests
uv run pytest -m freshness                       # knowledge pages due a recheck
uv run ruff check . && uv run mypy               # lint and types, both must be clean
uv run streamlit run app/Home.py                 # the app, locally

uv run python studies/staging-split/run.py       # answer a question
uv run python deploy/build.py                    # build the static site into deploy/site/
uv run playwright install chromium               # once, for the browser checks
uv run python deploy/acceptance.py --local       # drive the built site in a real browser
uv run python deploy/screenshot.py               # refresh the README images
```

### When those commands will not run

Start here rather than reviewing by reading. A judgement made without executing anything is worth very little in a repository whose whole claim is that its numbers were checked.

**`Failed to spawn: pytest`, or any console script missing.** The `.venv` was copied, moved or renamed from another path, and every console script still carries an absolute shebang pointing at where it used to live. Venvs are not relocatable. `uv sync` repairs the editable install but **not** the shebangs, so the fix is:

```sh
rm -rf .venv && uv sync
```

`.venv` is gitignored and rebuilds in seconds from `uv.lock`. `uv run python -m pytest` works around it and should not be committed anywhere as though it were the normal form.

**A fresh or sandboxed workspace.** There is no environment until `uv sync` has run, and a sandbox with no access to the global `uv` cache has to build one from `uv.lock` first. Do that before concluding anything is broken.

## Commands and skills

**Never add slash commands.** Reusable agent instructions go in `.claude/skills/<name>/SKILL.md`. Commands are a Claude Code feature that nothing else reads, and this repository is worked by other agents: `AGENTS.md` and `.codex` are symlinks so they see the same instructions.

Two things about skills that break silently, both covered by `tests/test_agent_config.py`:

- A skill is found by **description matching**, so its description must say *when* to use it and list triggers. A description that only says what the skill is will never be reached by the task that needs it.
- Relative links inside a skill sit one level deeper than most files. Nothing about markdown instructions fails loudly, so a rotted link just sends the reader nowhere.

## Committing

**Commit as soon as a piece of work lands. Do not ask first, and do not leave finished work sitting in the working tree.** This overrides the general "only commit when asked" default; in this repository it is standing permission.

"Landed" means verified, not merely written: `ruff`, `mypy` and `pytest` are green, and for anything a reader can see, `deploy/acceptance.py --local` too. A commit that has not been checked is not a landing.

Keep the commits separable. One coherent change per commit, and prefer boundaries where no file straddles two commits, since partial staging is not available here. If a change genuinely spans layers, commit the new modules first and the wiring second: that ordering leaves each commit working on its own.

Conventional Commits, `type(scope): subject`, imperative, lowercase type. Subject line only unless a non-obvious *why* needs one or two sentences of body. No bullet lists, no test counts, no restating the diff.

**Pushing is not automatic.** A push to `main` triggers CI and deploys the live site, so it stays an explicit request. Commit freely; push when asked.

`mypy` is configured to check `src` only and runs `--strict`. `ruff` covers the whole tree with per-directory relaxations already set in `pyproject.toml`; do not add `noqa` where a per-file-ignore already exists.

CI ([.github/workflows/pages.yml](.github/workflows/pages.yml)) runs `ruff`, `mypy` and `pytest` on every push to `main`, and only deploys if all three pass.

`deploy/acceptance.py` is the only check that sees what a reader sees. Unit tests know what the build *writes*; they cannot know whether the browser boots Python, whether a shared link still resolves, or whether an SVG arrived as a drawing rather than as its own source code. A routing bug once lived in exactly that gap with the whole suite green, and so did both traps below. Run it before trusting a green suite about anything user-facing.

## The two rules that do not bend

1. **`src/rocketry/` never imports Streamlit, Plotly, pandas or `labbook`.** The dependency arrow points one way only: `app/` → `labbook/` → `rocketry/`. Breaking this makes the physics untestable without a browser and breaks the scripted-analysis consumer.
2. **`src/rocketry/` is SI throughout** (tonnes, m/s, metres, seconds, tonnes-force). Units convert exactly once, at the presentation edge, in `labbook.units`. A unit bug can then change a label but never a result. Specific impulse stays in seconds in both systems and is deliberately never converted.

   The rule's real content is *one unit per quantity*, which is why tonnes and tonnes-force qualify. It binds anything a calculation reads. Library fields that merely record what a source published may keep that source's unit, and then the name must say so: `staging_speed_kmh`, `max_velocity_kmh`, `mass_kg`. The test is whether a calculation reads it. `tests/test_units.py` walks the core and fails on any other name in a foreign unit, so the allowlist is the only way in and stays reviewed.

   The article speaks km/h and so does chapter 4. Cross that boundary with `labbook.units.from_kmh` / `to_kmh`, never with a bare multiplication in a page.

## Scope and audience

Written for enthusiasts with no physics background. Assume they know that a rocket is and that orbit means going fast sideways. Assume they do **not** know what a logarithm, a mass ratio, a specific impulse or a delta-v is, and that they will not read a wall of text before touching something.

The precision target is **a few percent, not a fraction of a percent**. This is a teaching workbench, not a design tool for professionals.

Deliberately out of scope, and worth pushing back on rather than quietly adding: orbital mechanics beyond circular orbits, inclination and a transfer budget (no n-body, no trajectory optimisation, no rendezvous); 3D of any kind, because well-designed 2D communicates more per pixel here; accounts or persistence beyond a shareable URL.

**The honesty test.** A reader must be able to reach a conclusion the source article would dislike, if their own assumptions support it. Anything that makes that harder is a bug, however well-intentioned.

## Writing a chapter

Each chapter answers one question, has one primary interaction, and ends with one takeaway a reader could restate. The rules below are what make that work, and most already have a helper in `components/shell.py`:

1. **One sentence at the top** saying what the page teaches. No preamble. That is the `teaser` argument to `page()`.
2. **Formulas twice**, once symbolically and once with the reader's own numbers substituted in. This is the single device that stops symbols being frightening. Use `formula_block()`.
3. **Every number carries its unit**, through a `Formatter`, never hand-formatted.
4. **Progressive disclosure.** Prose and one control on the surface; reasoning inside `why()`; maths below that.
5. **No dead ends.** An impossible configuration explains *why* and points at the fix. Never a stack trace, never a silent zero.
6. **Presets before parameters.** Every page opens on a real vehicle with sensible values, via `vehicle_picker()`.
7. **Nudges, not instructions.** `try_this()` beats a paragraph explaining what would have happened.

## Architecture

**`src/rocketry/`** is the physics core. `tsiolkovsky.py` holds the rocket equation and its inverses; everything else builds on it (`staging`, `reuse`, `scaling`, `ascent`, `orbit`, `payload`, `reentry`, `dynamics`, `atmosphere`). `models.py` defines frozen, `extra="forbid"` Pydantic models; `library.py` loads and cross-validates them from YAML.

**`vehicle.py` is the bridge** between the library and the primitives, and holds the seam every "what if" goes through. Two questions get asked of a vehicle and they are not interchangeable, which is why they are separate methods rather than one function with a flag:

- *What velocity does it produce carrying this payload?* → `Scenario.at_payload()`
- *What payload can it carry on this mission?* → `Scenario.solve_payload()`

Use `scenario(lib, key, stage_key={...})` to alter stages without mutating the library, so two scenarios on one page cannot interfere. `solve_payload` returning a negative number is a real answer meaning "short by this much", not an error to clamp.

**`src/labbook/`** is presentation, shared by two consumers that must never disagree: the Streamlit app and scripted analysis in `studies/`. Both import the same formatters and chart builders, so a figure in a script looks like the same figure in the app. This layer may depend on plotly and pandas.

**`app/`** is thin Streamlit glue. Anything with logic in it belongs in `labbook` so it can be tested without a browser. Every page opens the same way: `page()`, then `sidebar()` for the formatter, then `mode()` for the chart surface, then `library()`, and closes with `chapter_footer(n)`. Pages start with a `sys.path.insert` so `components.shell` resolves; this is why `app/*` has an `E402` ignore.

**`labbook/navigation.py` is the single source of truth for the tour.** Chapter numbers, titles, questions and page files all come from `CHAPTERS`, and `Chapter.page_file` is derived rather than stored. Anything that needs to link to a chapter goes through `shell.chapter_link()` or `shell.chapter_card()`; `shell.chapter_pages()` delegates here too. Never hard-code a chapter list or glob `app/pages/` for one: globbing sorts 10 and 11 ahead of 2, and a second list drifts. `tests/test_navigation.py` holds the registry and the directory together in both directions.

Cross-references between chapters are links, not prose. A reference to a chapter on the *same* page (the glossary's "see also") uses a button that rewrites the search box, not a link: navigating would reload the whole browser runtime to arrive back where it started.

**`data/`** is the rocket library as editable YAML. **Adding or changing a rocket is a data change, never a code change.** `Library._check_references()` fails at load time if a stage names an unknown engine or a vehicle names an unknown stage.

That extends to observations. `data/flights.yaml` holds what was measured, the model holds what was predicted, and the app plots one against the other. A flight that has not happened yet sits there as a row of nulls so its absence is visible rather than silently omitted. When a new flight lands, recording it must mean editing one YAML row: **if it means editing Python, the abstraction is wrong and that is the thing to fix.**

### Two modelling limits worth knowing

**Parallel burns are not modelled.** Representing strap-on boosters as a sequence of stages always *flatters* the vehicle, because it lets the core burn propellant at the low mass it only reaches once the boosters are gone. Splitting the core's propellant across both phases recovers most of it. This is why Ariane 64 and the Shuttle sit on the excused list in `tests/test_library_calibration.py`, which fails if a vehicle is quietly left out of both lists or if an excuse stops being needed.

**A smaller stage has to be allowed to be a lighter one.** Shrinking a stage while holding its dry mass fixed makes the rocket worse, so the obvious advice, "cut the upper stage in half", teaches the opposite of the truth. The sandbox scales dry mass with propellant by default and offers a checkbox to turn that off, which turns the trap into the lesson. Two tests hold both directions.

### Provenance is load-bearing

Every library entry carries a `Provenance`: `PUBLISHED`, `ESTIMATED`, `CONTESTED`, `DERIVED`, `ANNOUNCED`. This is not decoration. The project's central argument rests on one number SpaceX has not published, and a model that could not tell a measurement from a guess would hide exactly the thing that matters. Never present a contested estimate as a measurement; route it through `shell.provenance_badge()`.

The project's stance is physics first, verdict last. Chapters 1 to 5 teach mechanics with no agenda; the case study shows its uncertainty and hands the reader a slider rather than a conclusion. Preserve that when editing copy, which has three concrete consequences beyond tone:

- A payload result is shown as a **range across the plausible dry-mass span**, never as a single number, with both the article's estimate and the operator's claim marked on it.
- The fact-check chapter reports the article's **errors as well as its confirmations**, by name.
- **No loaded language in any string.** "Starship's dry mass is disputed" ships; "Starship is objectively bad" does not.

### Two Streamlit traps that unit tests cannot see

Both of these produce a page that runs perfectly, passes every test, and is visibly wrong. Only `deploy/acceptance.py` catches them, which is why it exists.

**Multi-line HTML becomes a code block.** `st.markdown` parses markdown *before* it honours `unsafe_allow_html`, and markdown claims any line indented four spaces or more. Hand-formatted SVG therefore lands on the page as its own source code. Everything drawn goes through `labbook.visuals.inline()`, which flattens markup to one line and drops comments. Never pass multi-line markup to `st.markdown` directly. `st.html` is not an escape route: it renders nothing here.

**A bare string expression is rendered to the reader.** Streamlit's magic writes any top-level expression to the page, and an attribute docstring is an expression statement. The `CONSTANT = value` followed by `"""docs"""` convention that the rest of the project uses will print that paragraph at the reader. Inside `app/`, document module-level constants with `#` comments. `tests/test_app.py` walks the AST of every page to enforce this.

**Drawn components take a `uid`.** Two drawings on one page otherwise share CSS class names and fight over each other's keyframes and dimensions.

### Why it runs in a browser, and what that costs

GitHub Pages serves static files; browsers run only JS and WebAssembly. [Pyodide](https://pyodide.org) is CPython compiled to WebAssembly and [stlite](https://github.com/whitphx/stlite) packages Streamlit for it, so the browser downloads an interpreter once and then runs the very same `.py` files. Two consequences:

**Every runtime dependency is a wheel the reader downloads.** Runtime deps are deliberately four (`pydantic`, `pyyaml`, `streamlit`, `plotly`) and mirrored in `REQUIREMENTS` in [deploy/build.py](deploy/build.py). `scipy` and `ambiance` were dropped for a forty-line standard atmosphere and a hand-written RK4 integrator, saving ~15 MB. Adding a runtime dependency is a significant decision; dev-only tools belong in the `dev` dependency group.

**Chapter URLs need a routing hack.** Streamlit writes the current chapter into the address bar, a static host has no route for that path, and the browser runtime never shows the path to Python (it reports its own mount point and forwards only the query string). So the build writes the same page as both `index.html` and `404.html`, and a small inline script moves the chapter from the path into the query string before Python starts. `Home.py` then reads it via `route_for()` and forwards, carrying settings by hand because Streamlit drops the query string on a page switch. `deploy/build.py::CHAPTER_PARAM` and `labbook.sharing.CHAPTER_PARAM` must stay equal; `tests/test_deploy.py` holds them together. Without this every link the app produces answers with GitHub's error page.

URL input is treated as hostile: `labbook.sharing.read_number`/`read_choice` fall back and clamp rather than raise. It is the one input a reader can hand-edit.

`deploy/site/` is generated and gitignored. Never edit it; rebuild it.

**`assets/logo.svg` is the project mark**, and a plain hand-editable file rather than markup generated in Python. It is inlined three ways: into the app by `labbook.logo.mark()`, and into the built page twice by `deploy/build.py`, as the favicon data URI and as the boot screen's artwork. It paints its body in `currentColor` so it follows the reader's theme with no Python deciding anything, and takes the surrounding paper colour through a `--ship-gap` custom property. The app cannot fetch it by URL, because stlite serves from a virtual filesystem with no HTTP origin, which is the only reason the loader exists.

## Tests

- `test_golden.py` pins numbers recomputed independently during the article verification, tied to [docs/physics-reference.md](docs/physics-reference.md) section 7, default tolerance 1 %. If one moves, either the model changed on purpose and this file is updated deliberately, or something broke. There is no third option.
- `test_library_calibration.py` decides whether anything else can be believed: the model must recover each rocket's known published payload.
- `test_properties.py` uses Hypothesis for invariants that hold everywhere, not just at the pinned points.
- `test_app.py` executes every Streamlit page top to bottom through `streamlit.testing.v1.AppTest`.
- `test_charts.py` and `test_teaching_charts.py` lock the visual language in both light and dark, and pin the *shapes* of chapter 1's paired curves: the burn steepens, the loading sweep flattens. They are a pair, and if one stops bending the right way the pair starts actively misleading.
- `test_navigation.py` holds the chapter registry against the files on disk.
- `test_visuals.py` covers the drawn components, including that nothing reaches the page on more than one line.

Follow red/green TDD for new physics or fixes. A new documented number gets a golden test; a new invariant gets a property test.

The palette in `labbook/palette.py` is validated, not chosen by taste: propellant, structure and payload wear the same colour in every chart on every page. Light mode fails contrast on two slots, which obligates direct labels or a table view. Every chart carries direct labels and every study emits a markdown table beside its figure. Keep that.

## Studies

One folder per question under `studies/<name>/`: `run.py`, `finding.md`, and a gitignored `out/`. See [studies/README.md](studies/README.md). If a finding cannot be reproduced by running one command, it is not a finding yet. Never hard-code a rocket in a study; load it from `data/` and add missing numbers to the library with their provenance. Write output with `beside(__file__)`. Every `finding.md` needs its assumptions section, which is the section that matters most.

## Knowledge base

Reference material the project has *looked up*, as opposed to `studies/` which holds what it has *worked out*. `raw/` holds immutable captured sources, `docs/knowledge/` holds compiled pages, and this file is the schema. The design and its reasoning are in [docs/knowledge-base.md](docs/knowledge-base.md); open work is in [docs/knowledge-base-plan.md](docs/knowledge-base-plan.md).

Pages are markdown with YAML front matter in [Open Knowledge Format v0.2](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md). Only `type` is required; OKF mandates that unknown keys be preserved, which is what makes this project's two extensions legal rather than a private fork.

```yaml
---
type: Vehicle                     # OKF's one required field
title: Starship / Super Heavy V3
description: One sentence.
tags: [starship, spacex]

sources:                          # every page cites at least one, dated
  - id: wiki-f13
    resource: ../../../raw/2026-08-16-wikipedia-starship-flight-13.md
    title: Starship flight test 13
    last_modified: 2026-08-16

generated: { by: claude-opus-5, at: 2026-08-16T00:00:00Z }
verified:                         # optional; its absence is itself the signal
  - { by: 'human:mbackschat', at: 2026-08-16T11:00:00Z }

status: stable                    # draft | stable | deprecated
stale_after: 2026-09-30           # absolute date, not a TTL

provenance: contested             # extension: the Provenance vocabulary
feeds:                            # extension: entries this page is evidence for
  - target: data/stages.yaml#starship_v3
    asserts: {dry_mass_t: 220.0}  # held to this; see below
  - data/vehicles.yaml#starship_v3   # bare form: existence only
---
```

**Trust and provenance are different axes and both are needed.** `verified` answers *did a person check this page*, and its tier is derived rather than stored: no `verified` key means unverified, machine actors only means machine-confirmed, any `human:` actor means human-reviewed. `provenance` answers *how much weight can this number bear*. A human-reviewed page can describe a contested number. Never collapse them into one field, and never replace either with a numeric score.

**`feeds:` is the load-bearing extension, and `asserts` is what makes it bite.** A bare reference only claims the entry exists. A `target` with `asserts` states the values the page stands behind, and `tests/test_knowledge.py` fails if the library disagrees, naming the field and both values. That is the whole reason the corpus is worth keeping rather than bookmarking things: if an operator restates a figure and only one of the two places is updated, the suite goes red.

Prose is deliberately never scanned for numbers. It is unreliable and it fails silently, so a page states what it stands behind explicitly. The corollary is that `asserts` should carry every value a page displays in a table, because anything left out is unguarded.

There is no separate lint step. The checks are tests, so `uv run pytest` and therefore CI already run them.

**Except freshness, which runs on its own schedule.** Every page carries a `stale_after` date. That check is kept out of the default run because it fails as a *date* passes rather than as a *change* lands, and a check that reddens an unrelated commit on a Monday morning is one people learn to ignore.

Instead [.github/workflows/freshness.yml](.github/workflows/freshness.yml) runs weekly, and turns expiry into a tracked work item: one GitHub issue, rewritten while pages are due and **closed automatically** when none are. `uv run python -m knowledge` produces the report it files and exits non-zero when anything is due; `uv run pytest -m freshness` is the same check as a test. Renaming that entry point without updating the workflow would silently stop the corpus being maintained, so `tests/test_knowledge.py` holds the two together.

`src/knowledge.py` reads and validates pages. It is authoring tooling, deliberately outside both shipped packages and outside `deploy/build.py`'s trees so it never becomes a wheel the reader downloads; a test in `tests/test_deploy.py` holds that. `raw/` is text only, never binaries, because the point of keeping a source is being able to diff it when it is recaptured.

## Reference

[docs/physics-reference.md](docs/physics-reference.md) is the source of truth for the physics: section 2 derives it, section 3 is the claim-by-claim verification log, section 4 records corrections, section 6 specifies the models the app implements, section 7 holds the golden numbers. Module docstrings cite it by section; keep those citations accurate when changing a model.

The source article is copyrighted and deliberately not in the repo. It is cited by URL only.
