# Build Plan: Interactive Rocket Physics Explorer

Companion to [physics-reference.md](physics-reference.md), which holds the verified physics, the reference data and the golden numbers this app must reproduce.

**Timing note.** The source article was published 14 August 2026 and Starship Flight 14 is expected before the end of that month: first orbital attempt, first ship tower catch, booster returning to the launch site, operational Starlink V3 satellites. It will produce the first real measurement of Starship's orbital payload, which is exactly the number the app's central chapter is about. **Design for that as a data update, not a code change.** See [physics-reference section 9](physics-reference.md#9-live-context-as-of-16-august-2026).

---

## 1. What we are building

A Python web application that lets a curious beginner **understand why rockets perform the way they do**, by playing with them.

Not a slideshow with sliders bolted on. The user should be able to grab any number in the model, move it, and watch the consequences propagate through a real physics engine. The article's Starship analysis is the worked example that gives the whole thing a spine, but the app teaches the physics, not the polemic.

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

**The hard rule: `src/rocketry/` never imports Streamlit, Plotly or pandas.** It is a library that happens to have a web front end. This keeps the physics testable, keeps the app thin, and means a different front end is a weekend, not a rewrite.

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

### M0: Scaffold
`uv` project, dependency set, `ruff` and `mypy` clean, `pytest` running, directory skeleton. Verification script from the analysis phase moved into `tests/` as the seed.
**Done when:** `uv run pytest` runs and reports the golden-number tests as failing for the right reason.

### M1: Physics core
`tsiolkovsky.py`, `models.py`, `vehicle.py`, `payload.py`, `reuse.py`, `orbit.py`. No UI.
**Done when:** every fixture in physics-reference section 7 passes except the ascent-simulation and optimiser ones, plus hypothesis properties hold (delta-v monotonic in mass ratio and in Isp; payload solver inverts the forward model to within 1e-6; propellant forms agree).

### M2: Data library
All five YAML files populated from physics-reference section 5, each entry validating against the pydantic models, each carrying provenance.
**Done when:** loading the library and running Starship, Falcon 9, Ariane 6 and the Shuttle through the core reproduces their published payloads within the stated tolerance.

### M3: App shell plus chapters 1 and 2
Streamlit multipage app, shared components, the formula renderer, the three-colour mass visual language, the glossary stub.
**Done when:** a beginner can move the mass-ratio slider and see delta-v respond, and can compare Falcon 9 and Starship side by side to scale.

### M4: Ascent simulation and chapter 3
`ascent.py` with loss accounting, cached, plus the animated flight page.
**Done when:** simulating Falcon 9 to orbit produces a gravity loss between 1000 and 1600 m/s and a total delta-v within 150 m/s of the analytic budget, and the flight page scrubs smoothly.

### M5: Staging and chapters 4 and 5
`staging.py` sweep and optimum, `reuse.py` surfaced in the UI.
**Done when:** the sweep reproduces the curve in physics-reference section 3.7, with the optimum at 11 500 ± 1000 km/h, and the real rockets land on the curve where expected.

### M6: The case study, chapters 6, 7 and 7b
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

### D5: Deployment — local first

`uv run streamlit run app/Home.py`. Add an `stlite` static export in M8 if a shareable link is wanted. Streamlit Community Cloud is the middle option for a hosted URL without a build step.

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

Nothing is blocked. Start at step 1.

1. **M0 scaffold.** `uv init`, dependency set from section 2, `ruff` and `mypy` configured, `pytest` wired up.
2. **Write `tests/test_golden.py`** from [physics-reference section 7](physics-reference.md#7-golden-numbers-test-fixtures). All red.
3. **Build `src/rocketry/`** until they are green. This is M1 and it is the foundation everything else stands on.
4. **M2 data library**, then M3 app shell with chapters 1 and 2.

`analysis/verify_article.py` and `analysis/verify_v4_scaling.py` already compute most of the golden numbers with dependency-free code. They are the reference implementation to port and test against, not code to import.
