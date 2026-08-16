# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

An interactive rocket physics explorer, served as a static site that runs Python in the reader's browser. [README.md](README.md) is the human-facing pitch; this file is the working brief.

## Commands

```sh
uv sync                                          # install, including the dev group
uv run pytest                                    # 332 tests
uv run pytest tests/test_golden.py               # one file
uv run pytest tests/test_golden.py::test_name    # one test
uv run pytest -k staging                         # by name
uv run pytest -m golden                          # only the documented-number tests
uv run ruff check . && uv run mypy               # lint and types, both must be clean
uv run streamlit run app/Home.py                 # the app, locally

uv run python studies/staging-split/run.py       # answer a question
uv run python deploy/build.py                    # build the static site into deploy/site/
uv run playwright install chromium               # once, for the browser checks
uv run python deploy/acceptance.py --local       # drive the built site in a real browser
uv run python deploy/screenshot.py               # refresh the README images
```

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
2. **`src/rocketry/` is SI throughout** (tonnes, m/s, seconds, tonnes-force). Units convert exactly once, at the presentation edge, in `labbook.units`. A unit bug can then change a label but never a result. Specific impulse stays in seconds in both systems and is deliberately never converted.

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

### Provenance is load-bearing

Every library entry carries a `Provenance`: `PUBLISHED`, `ESTIMATED`, `CONTESTED`, `DERIVED`, `ANNOUNCED`. This is not decoration. The project's central argument rests on one number SpaceX has not published, and a model that could not tell a measurement from a guess would hide exactly the thing that matters. Never present a contested estimate as a measurement; route it through `shell.provenance_badge()`.

The project's stance is physics first, verdict last. Chapters 1 to 5 teach mechanics with no agenda; the case study shows its uncertainty and hands the reader a slider rather than a conclusion. Preserve that when editing copy.

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

## Reference

[docs/physics-reference.md](docs/physics-reference.md) is the source of truth for the physics: section 2 derives it, section 3 is the claim-by-claim verification log, section 4 records corrections, section 6 specifies the models the app implements, section 7 holds the golden numbers. Module docstrings cite it by section; keep those citations accurate when changing a model.

The source article is copyrighted and deliberately not in the repo. It is cited by URL only.
