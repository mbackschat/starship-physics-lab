# Build Plan: Interactive Rocket Physics Explorer

Companion to [physics-reference.md](physics-reference.md), which holds the verified physics, the reference data and the golden numbers this app must reproduce.

**Timing note.** The source article was published 14 August 2026 and Starship Flight 14 is expected before the end of that month: first orbital attempt, first ship tower catch, booster returning to the launch site, operational Starlink V3 satellites. It will produce the first real measurement of Starship's orbital payload, which is exactly the number the app's central chapter is about. **Design for that as a data update, not a code change.** See [physics-reference section 9](physics-reference.md#9-live-context-as-of-16-august-2026).

---

## 1. What we are building

A **physics workbench** with two consumers that must never disagree with each other.

**Consumer 1: the web application.** Lets a curious beginner understand why rockets perform the way they do, by playing with them. Not a slideshow with sliders bolted on. The user grabs any number in the model, moves it, and watches the consequences propagate through a real physics engine.

**Consumer 2: scripted analysis.** A person or a coding agent answers a one-off question by writing a short script against the same tested core, and gets back a markdown table, a chart and a CSV. An investigation leaves a folder in `studies/`, holding the script, the written conclusion and the figures together, so understanding accumulates in the repository rather than evaporating in a chat log.

The two share everything below the presentation layer: the same physics, the same rocket library, the same validated palette, the same unit system. A figure produced in a script is indistinguishable from the same figure in the app, which is the point. If they could drift apart, the app would eventually be showing something the analysis no longer supports.

The article's Starship analysis is the worked example that gives the whole thing a spine, but the project teaches the physics, not the polemic.

### Target audience

Enthusiasts with no physics background. Assume they know what a rocket is and that orbit means going fast sideways. Assume nothing else. Specifically assume they do **not** know what a logarithm, a mass ratio, a specific impulse or a delta-v is, and that they will not read a wall of text before touching something.

### Success criteria

A user who has never heard of the rocket equation should, after 20 minutes, be able to:

1. Explain in their own words why propellant grows exponentially with target speed.
2. Predict, qualitatively, what happens to payload when a stage gets heavier.
3. Explain why rockets have stages and why the split between them matters.
4. Say what reuse costs and why returning to the launch site costs more than landing on a ship.
5. Look up Starship's numbers, see the disputed dry mass, and form their own view on the payload question.

Criterion 5 is the honesty test. The app must make it possible to reach a conclusion the article would dislike, if the user's assumptions support it.

### Non-goals

- Not a launch-vehicle design tool for professionals. Precision target is a few percent, not a fraction of a percent.
- No orbital mechanics beyond circular orbits, inclination and a transfer-injection budget. No n-body, no trajectory optimisation, no rendezvous.
- No 3D. Well-designed 2D communicates more per pixel here.
- No account system, no persistence beyond a shareable URL of the current configuration.

---

## 2. Technology

All Python, per the requirement.

| Layer | Choice | Why |
|---|---|---|
| Physics core | pure Python + `numpy` | No UI dependency, fully unit-testable |
| Integration | `scipy.integrate.solve_ivp` (RK45, event-driven staging) | Standard, handles staging events cleanly |
| Atmosphere | `ambiance` | International Standard Atmosphere to 80 km, saves hand-rolling it |
| Data model | `pydantic` v2 | Validated rocket/stage/engine definitions, free JSON schema for the builder |
| Data files | YAML via `pyyaml` | Human-editable rocket library |
| Web framework | **`streamlit`** | See below |
| Charts | `plotly` | Interactive, animation frames, works natively in Streamlit |
| Tables | `pandas` | Feeds Streamlit dataframes directly |
| Tests | `pytest`, `hypothesis` | Golden numbers plus property tests on the rocket equation |
| Tooling | `uv`, `ruff`, `mypy` | Per project conventions |

### Why Streamlit

The whole physics core runs in single-digit milliseconds, so Streamlit's rerun-on-every-interaction model costs nothing here, and it buys the best widget ergonomics in the Python ecosystem plus effortless interleaving of explanatory prose with controls. That matters more than anything else for a teaching app.

The one real risk is the numerical ascent simulation, which is 10 to 100 ms and would make sliders feel sticky if recomputed blindly. Mitigation is standard: `@st.cache_data` keyed on the parameter tuple.

**Alternatives considered.** `NiceGUI` gives smoother real-time animation and a more app-like feel, at the cost of writing far more layout code for the explanatory chapters. `Dash` is more boilerplate for the same result. `Marimo` is attractive because it exports to a static WASM page, but its layout control is weaker for a long-form multi-chapter app. If we later want a zero-install shareable build, **`stlite`** runs the same Streamlit codebase in the browser via Pyodide, so the Streamlit choice keeps that door open without a rewrite.

For flight animation specifically: a **time scrubber is the primary control, autoplay is secondary**. Scrubbing beats autoplay for learning, because the user controls the pace and can park on the interesting moment.

---

## 3. Architecture

```
starship-viz/
  pyproject.toml              uv-managed, Python 3.12+
  docs/
    physics-reference.md      verified physics, data, golden numbers
    plan.md                   this file
  src/rocketry/               PHYSICS CORE. zero UI imports. 100 % of golden numbers covered.
    models.py                 pydantic: Engine, Stage, Vehicle, Flight, Provenance
    library.py                load() the YAML rocket library, validated and cross-checked
    vehicle.py                stage-by-stage analysis of a whole vehicle
    constants.py              g0, R_earth, mu, v_rot, unit helpers
    tsiolkovsky.py            M1 delta-v and its four inverse forms
    models.py                 pydantic: Engine, Stage, Vehicle, Mission, Recovery
    vehicle.py                stack assembly, per-stage delta-v, mass bookkeeping
    payload.py                M2 payload solver (bisection)
    reuse.py                  M3 recovery propellant budget
    staging.py                M4 staging sweep + optimum
    budget.py                 M5 named delta-v line items
    ascent.py                 M6 2D numerical ascent with loss accounting
    orbit.py                  M7 orbital velocity, inclination, rotation bonus
    reentry.py                M8 ballistic coefficient, optional entry integration
    scaling.py                M9 dry-mass scaling law, exponent 0..1, used by the
                              builder and by the V4 chapter
  data/
    engines.yaml              from physics-reference section 5.1
    stages.yaml               5.2
    vehicles.yaml             5.3
    concepts.yaml             5.4 the article's redesigns, plus a Starship V4 preset
    budgets.yaml              5.5 delta-v budgets
    flights.yaml              observed flight record: payload, achieved velocity,
                              inclination, altitude, outcome. Flight 14 sits here as an
                              empty row until it flies. Model predictions are plotted
                              against these points, so new data never touches code
  src/labbook/                PRESENTATION. may import plotly and pandas; nothing
                              imports it back. Shared by the app and by scripts.
    units.py                  metric / US customary, conversion at the edge only
    palette.py                the validated colour system, one visual language
    tables.py                 markdown tables with per-column units
    charts.py                 plotly builders used by both consumers
    export.py                 save figures as PNG + HTML, tables as MD, data as CSV
  studies/                    one folder per question. method and result together.
    <name>/run.py             the script. imports the same core the app uses
    <name>/finding.md         question, answer, assumptions, how to reproduce
    <name>/out/               generated figures and tables, gitignored
  app/
    Home.py                   entry point, guided tour launcher
    pages/                    one file per chapter, numbered for ordering
    components/
      explain.py              "Why?" expander, formula-with-numbers renderer
      charts.py               all Plotly builders, one shared visual language
      controls.py             reusable slider groups (stage editor, mission editor)
      content.py              all user-facing prose, keyed by ID
  tests/
    test_golden.py            every fixture from physics-reference section 7
    test_properties.py        hypothesis invariants
    test_data.py              every YAML entry validates and round-trips
```

**The hard rule: `src/rocketry/` never imports Streamlit, Plotly, pandas or anything from `labbook`.** It is a library that happens to have a web front end. This keeps the physics testable, keeps the app thin, means a different front end is a weekend rather than a rewrite, and lets a script import the physics without dragging in a charting stack.

**The corollary: `rocketry` is SI throughout, always.** Tonnes, m/s, seconds, metres. Unit conversion happens exactly once, at the edge, in `labbook.units`. A unit bug can therefore change a label but never a result.

### Data model sketch

```python
class Engine(BaseModel):
    name: str
    propellants: str
    thrust_sl_tf: float | None      # None for vacuum-only engines
    thrust_vac_tf: float
    isp_sl_s: float | None
    isp_vac_s: float
    mass_kg: float
    min_throttle: float = 0.4
    source: Literal["published", "estimated", "derived"]
    note: str = ""

class Stage(BaseModel):
    name: str
    dry_mass_t: float
    propellant_t: float
    engine: str                      # key into the engine library
    engine_count: int
    diameter_m: float
    recovery: Recovery | None        # None = expendable
    isp_override_s: float | None     # flight-average, when known better than the engine spec
    confidence: Literal["published", "estimated", "contested"]

class Recovery(BaseModel):
    mode: Literal["rtls", "droneship", "tower_catch", "cable_net"]
    boostback_dv: float
    entry_burn_dv: float
    landing_dv: float
    landing_isp_s: float
```

Every field carries provenance. The UI renders published, estimated and contested values differently. That is a design requirement, not a nicety: the article's whole argument rests on a contested number, and hiding that would make the app dishonest in exactly the way it accuses SpaceX of being.

---

## 4. The chapters

A learning arc, not a dashboard. Each chapter answers one question, has one primary interaction, and ends with one takeaway the user can restate.

| # | Chapter | Question answered | Primary interaction | Takeaway |
|---|---|---|---|---|
| 0 | **Start** | What is this and where do I begin? | Guided tour vs free exploration | You will be moving sliders, not reading |
| 1 | **The rocket equation** | Why is going fast so expensive? | Two sliders: mass ratio, engine efficiency, delta-v updates live. Then the doubling ladder as an interactive | Propellant grows exponentially with speed |
| 2 | **Anatomy of a rocket** | What is a rocket actually made of? | Pick a rocket, see it to scale, see the mass split as propellant / structure / payload | Payload is a sliver, and that is normal |
| 3 | **Launch** | Where does all the speed go? | Fly it. Time scrubber, live altitude, speed, mass, TWR, dynamic pressure, and a stacked live chart of delta-v spent on orbit / gravity / drag | Roughly 1500 m/s is lost before you even start |
| 4 | **Stages** | Why throw half the rocket away? | Drag the staging speed, watch payload move. The sweep curve with real rockets marked on it | The split is worth a factor of two |
| 5 | **Reuse** | What does landing cost? | Toggle expendable / droneship / return-to-launch-site, watch the propellant bar split into "up" and "home" | Coming home is paid for uphill |
| 6 | **Weighing Starship** | How heavy is it really? | Reproduce the article's measurement: burn duration slider, hover-thrust bracket, three independent estimates converging on a range | You can weigh a rocket from a 14-second burn |
| 7 | **The payload question** | Does Starship carry 100 tonnes? | The dry-mass slider against the SpaceX claim, with the 300 t in orbit fixed | The mass in orbit is fixed; only its composition is up for debate |
| 7b | **Bigger is better?** | V4 makes the ship bigger. Does that help? | The dry-mass **scaling exponent** slider, 0 (mass stays fixed) to 1 (mass scales fully with propellant), against the announced V4 configuration | The answer swings from 108 t to 12 t of payload on that one assumption, which is why it is worth arguing about |
| 8 | **Build your own** | Can I do better? | Full sandbox: stages, engines, staging speed, recovery mode, target orbit. Scoreboard against the real rockets | Optimising is a trade, not a free lunch |
| 9 | **Fact check** | Was the article right? | The verification table from physics-reference, with each claim recomputable live | Trust the method, check the inputs |
| 10 | **Glossary** | What did that word mean? | Searchable, every term linked from wherever it first appears | Reference, always one click away |

Chapters 1 to 5 are the physics course. 6 and 7 are the case study. 8 is the payoff. 9 and 10 are support.

### Beginner-facing design rules

Non-negotiable, applied on every page:

1. **One sentence at the top** saying what this page will teach. No preamble.
2. **Formulas twice**: once symbolically, once with the user's current numbers substituted in, side by side. Seeing `Δv = 3581 × ln(1900/300) = 6609 m/s` next to `Δv = v_e · ln(m_0/m_f)` is what makes the symbols stop being scary.
3. **Every number carries its unit and a comparison.** "6609 m/s" means nothing. "6609 m/s, about 24 000 km/h, or Frankfurt to New York in 15 minutes" means something.
4. **Progressive disclosure.** Surface level is prose and one control. Depth lives in "Why does this happen?" expanders. Maths lives one level below that.
5. **No dead ends.** An impossible configuration gets an explanation of *why* it is impossible and a button that fixes it. Never a stack trace, never a silent zero.
6. **Consistent visual language across every chart.** Propellant, structure and payload get the same three colours everywhere, on every page, forever. Load the `dataviz` skill before writing the first chart to fix the palette and the accessibility rules once.
7. **Presets before parameters.** Every page opens on a real rocket with sensible values. Free parameters are opt-in, and a reset button is always visible.
8. **Nudges, not instructions.** "Try dropping the dry mass to 160 t and watch the payload" beats a paragraph explaining what would happen.

---

## 5. Milestones

Red/green TDD throughout: the golden numbers in [physics-reference section 7](physics-reference.md#7-golden-numbers-test-fixtures) are written as failing tests first, then made to pass.

### M0: Scaffold — DONE
`uv` project, dependency set, `ruff` and `mypy` configured, `pytest` running, directory skeleton, public GitHub repository.

### M1: Physics core — DONE
`tsiolkovsky.py`, `dynamics.py`, `orbit.py`, `payload.py`, `reuse.py`, `scaling.py`, `staging.py`, `reentry.py`. No UI.
**Done:** 51 golden-number tests and 20 property tests pass, `ruff` and `mypy --strict` clean. The staging optimiser independently reproduces the article's central claim, finding the payload optimum at 11 480 km/h against the 6 000 km/h Starship actually flies.

### M2: Data library — DONE
YAML files populated from physics-reference section 5, each entry validating against the pydantic models, each carrying provenance and an `in_article` flag.
**Done:** 7 engines, 18 stages, 10 vehicles, 3 flights. `rocketry.vehicle.analyse` reproduces Falcon 9 at 9333 m/s and the Shuttle at 9445 m/s, both in the normal band, and puts Starship at its claimed 100 t payload at 8545 m/s, roughly 850 m/s short of orbit. That gap is the article's argument, arrived at independently.

### M2b: More presets
Add the remaining vehicles the article discusses (Atlas LV-3B, New Glenn, Long March 10B, SLS Block 1, Soyuz-2), then comparison vehicles it does not (Saturn V, Falcon Heavy, Electron, Vulcan Centaur, Neutron). Requires multi-stage support beyond two stages for Saturn V and Ariane 6.
**Done when:** every vehicle in the library reproduces its published payload within 10 %, or carries a note explaining why it cannot.

### M2c: Analysis workbench
`labbook` units, tables, charts and export, plus the `studies/` convention.
**Done:** a question can be answered in a 40-line script that emits a markdown table, a PNG, an interactive HTML chart and a CSV, in either unit system.

### M3: App shell plus chapters 1 and 2 — DONE
Streamlit multipage app, shared components, the formula renderer, the three-colour mass visual language, the glossary stub.
**Done when:** a beginner can move the mass-ratio slider and see delta-v respond, and can compare Falcon 9 and Starship side by side to scale.

### M4: Ascent simulation and chapter 3 — DONE
`ascent.py` with loss accounting, cached, plus the animated flight page.
**Done:** Falcon 9 simulates to 1631 m/s of gravity loss, 34 kPa max q and 7579 m/s at 108 km, all matching real telemetry, and the ideal delta-v lands within 150 m/s of the analytic budget. Losses are decomposed by an exact identity rather than estimated. `ambiance` and `scipy` were replaced by a direct ISA implementation and a hand-written RK4, which removed roughly 15 MB from the browser bundle.

### M5: Staging and chapters 4 and 5 — DONE
`staging.py` sweep and optimum, `reuse.py` surfaced in the UI.
**Done:** the sweep reproduces physics-reference section 3.7 with the optimum at 11 480 km/h, and `rocketry.vehicle.with_stage` gives both chapters a tested seam for asking what if this stage were different, which chapter 7 will reuse for the contested dry mass.

### M6: The case study, chapters 6, 7 and 7b — DONE
The weighing reconstruction, the payload question and the V4 scaling chapter, with contested inputs visibly marked.
**Done when:** a user can set ship dry mass to 160 t, see 100 t of payload appear, read why that number is disputed in both directions, and separately drive the V4 payload from 12 t to 108 t with the scaling-exponent slider. All three must reproduce physics-reference sections 3.8, 4/C15 and 7.

### M7: The sandbox, chapter 8
Free-form builder with validation, scoring and comparison against the library.
**Done when:** a user can build a two-stage vehicle from scratch, fly it, and see where it sits against Falcon 9 and Starship.

### M8: Polish
Fact-check page, glossary complete, guided tour, shareable URL state, responsive layout, light and dark themes, accessibility pass on the palette.
**Done when:** an untrained reader can complete the guided tour without asking a question.

Milestones M0 to M2 are prerequisites for everything. M3 to M5 are the core product. M6 to M8 can be reordered or trimmed if scope pressure appears; the physics core cannot.

---

## 6. Decisions taken

Settled on 16 August 2026.

### D1: UI language — **English** (decided)

All user-facing text in English. The source article stays German and is quoted as a source, not mirrored.

Even with a single language, all prose lives in `app/components/content.py` keyed by ID rather than being inlined in page code. Cost is near zero, it keeps layout code readable, and it leaves a German translation as a drop-in file if the audience turns out to be the article's readership after all. Physics terms get their German equivalent in the glossary, since a reader coming from the Golem piece will arrive with German vocabulary (Raketengleichung, Leermasse, Stufentrennung, Nutzlast).

### D2: Framework — **Streamlit + Plotly** (decided)

As argued in section 2. Keeps the `stlite` WASM export open as a later zero-install shareable build.

### D3: Stance — **physics first, verdict last** (decided)

Chapters 1 to 5 teach mechanics neutrally with no Starship agenda. Chapters 6, 7 and 7b present the case study as a reconstruction with its uncertainty visible, and the user reaches a conclusion by moving the dry-mass and scaling sliders themselves.

Concrete consequences for implementation, not just tone:

- Every input renders its provenance badge: **published**, **estimated**, **contested**. Non-negotiable, enforced by the pydantic model requiring the field.
- The payload result is always shown as a **range across the plausible dry-mass span**, never as a single number, with the article's estimate and SpaceX's claim both marked on it.
- The app states plainly that the pivotal input is unpublished and that the article's estimate is one defensible reading among several.
- Chapter 9 (fact check) reports the article's errors as well as its confirmations. [C1](physics-reference.md#c1-binary-velocity-constant), [C3](physics-reference.md#c3-starships-landing-propellant) and [C4](physics-reference.md#c4-falcon-9-acceleration-at-t40-s) get named.
- No loaded language in any string. "Starship's dry mass is disputed" ships; "Starship is objectively bad" does not.

### D4: Scope of the ascent simulation — build both, analytic first

The analytic delta-v budget (M1) carries chapters 1, 2, 4, 5, 6, 7 and 7b on its own. The numerical 2D simulation (M6) exists for chapter 3, where watching gravity loss accumulate in real time beats any static explanation. Keeping them separate means chapter 3 can slip without blocking anything else.

### D5: Hosting — **GitHub Pages via stlite** (decided)

Repository: [github.com/mbackschat/starship-physics-lab](https://github.com/mbackschat/starship-physics-lab), public.

**Primary: GitHub Pages, serving an [stlite](https://github.com/whitphx/stlite) build.** stlite runs the same Streamlit codebase in the browser on Pyodide. There is no server, so it is free permanently, never sleeps, never cold-starts a container, and scales to any number of readers. For a beginner clicking a link, that last point matters more than anything: a hosted Streamlit app that has gone to sleep costs the reader 30 seconds of blank screen, and most of them will not wait.

This works here because the app is pure computation. No database, no secrets, no server-side state. numpy, scipy, pandas, pydantic and plotly all have Pyodide wheels; `ambiance` is pure Python and installs via micropip. The one dependency that would not survive is `kaleido`, which is why it is already a dev-only dependency: it is used by analysis scripts for PNG export and is never imported by the app.

The cost is a one-time download of roughly 20 to 30 MB of Pyodide on first visit. Mitigate with a splash screen that says what is loading, and preload the rocket library so the first chart appears immediately after.

**Secondary: Streamlit Community Cloud**, for a live URL during development with zero build step. Point it at the repo and it redeploys on push. Free, but apps sleep after inactivity and are capped at 1 GB of RAM.

**Rejected:** Hugging Face Spaces (works, free, but also sleeps and adds a second place to keep in sync); Render, Railway and Fly.io (free tiers now credit-card gated or withdrawn).

Deployment tasks, in M8:

1. `pyproject.toml` already separates runtime from dev dependencies. Keep it that way; every runtime dependency must have a Pyodide wheel.
2. Add `deploy/index.html` with the stlite bootstrap listing the app's requirements.
3. Add a GitHub Actions workflow that builds the static bundle and publishes to Pages on push to `main`.
4. Keep `uv run streamlit run app/Home.py` working locally and identically. If the two ever diverge, the local one is authoritative.

### D6: Units — **switchable, at the presentation edge only** (decided)

Metric and US customary, switchable in the app's sidebar and as one argument to any report or table in `labbook`.

The physics core never sees a unit system. `labbook.units.Formatter` converts once, at the point of display, and `labbook.tables.Col` declares what each column measures so a whole report converts with one argument. Specific impulse is deliberately left in seconds in both systems, which is worth a sentence of explanation in the glossary: it is the same number for everyone, and that is exactly why engineers quote it that way.

### D7: Presets — **every vehicle in the article, plus more, with article ones highlighted** (decided)

Presets are the app's entry point. A beginner should never face an empty form. Every chapter opens on a real vehicle, and every control starts from that preset's values rather than from a default.

The library carries an `in_article` flag and a `category` (`flown`, `announced`, `concept`, `historic`). The UI highlights article-discussed entries, because those are the ones a reader may want to check against the text, and groups the rest as further comparisons.

Loaded so far, all from the article: Starship V3 and V4, Falcon 9 in droneship and expendable configurations, Ariane 64, the Space Shuttle, and the article's four thought experiments (Raptor 33 + Raptor 4, Raptor 33 + Raptor 3, the expendable variant and the pessimistic 400 t booster). Flights 12, 13 and the unflown 14 are in `data/flights.yaml`.

Still to add, all mentioned in the article and all with published data: Atlas LV-3B (John Glenn's, and the article's balloon-tank example), New Glenn, Long March 10B, SLS Block 1, Soyuz-2. Then vehicles not in the article but worth comparing: Saturn V, Falcon Heavy, Electron, Vulcan Centaur, Neutron. Tracked as M2b.

---

## 7. Risks

| Risk | Mitigation |
|---|---|
| Streamlit reruns feel sluggish once the ascent sim is on a page | `@st.cache_data` on every simulation entry point, keyed on the parameter tuple. Budget: no interaction above 200 ms |
| Beginners bounce off the first page | Guided tour with a real rocket preloaded, zero required reading before the first slider |
| The contested dry mass makes the app look like an opinion piece | D3. Provenance rendering on every input, and a payload result that changes with the user's assumption rather than ours |
| Scope sprawl in the sandbox chapter | The sandbox reuses the same models as everything else. If it cannot be built from the existing pydantic models, it is out of scope |
| Physics drift as features accumulate | The golden-number test suite is the guard. It runs on every change, and any milestone that breaks it is not done |
| The article turns out to be wrong somewhere I did not check | Verification is recorded claim by claim in physics-reference section 3. Anything the app asserts must trace to a row there or to a cited source |
| **Flight 14 lands mid-build and invalidates the case study** | This is likely, not hypothetical. `data/flights.yaml` holds observations, the model holds predictions, and the app plots one against the other. Updating after Flight 14 must mean editing one YAML row. If it means editing Python, the abstraction is wrong and needs fixing before M6 |
| Published specs drift (V4, Raptor uprating, payload restatements) | Every data entry carries `source` and a `retrieved` date. Re-check physics-reference section 9 at the start of each session |

---

## 8. Immediate next steps

M0, M1, M2 and M2c are done. Next, in order:

1. **M3 app shell with chapters 1 and 2.** Streamlit multipage skeleton, the unit toggle in the sidebar, the preset picker with article entries highlighted, the formula-with-numbers renderer, the glossary stub.
2. **M4 ascent simulation and chapter 3.** The one genuinely new piece of physics still missing.
3. **M2b more presets**, which can proceed in parallel since it is data entry plus research.
4. **M8 hosting**, which is worth doing early and cheaply so there is a live URL to look at while building.

Each question answered along the way gets a folder in `studies/`.
