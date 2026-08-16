---
name: review-physics
description: Audit the physics core for correctness, calibration and honesty about its limits. Use before trusting a change to src/rocketry, when a golden number or a calibration test moves, when adding a vehicle or stage that might not be modelled honestly, when asked to review the physics or the model, and before publishing any number the app will show a reader. Also use when a result looks plausible but unverified.
---

# Review the physics engine

Audit `src/rocketry/`. If a module or topic was named, scope the audit to it and say so; otherwise cover the whole core.

This is not a general code review. The physics core is the one part of this project that other people's arguments will be built on, and a plausible-looking wrong number here is worse than a crash: it propagates into every chapter, every study and every claim the app makes, silently and with a confident badge next to it.

**Read [docs/physics-reference.md](../../../docs/physics-reference.md) first.** It is the source of truth. Section 2 derives the physics, section 3 is the claim-by-claim verification log, section 4 records known corrections, section 6 specifies the models the app must implement, and section 7 holds the golden numbers. A finding that contradicts that document is either a real defect or a misreading of it, and you must say which.

## What to check, hardest first

### 1. Does it still reproduce reality?

The single question that matters. Run it, do not reason about it:

```sh
uv sync                          # a fresh workspace has no environment yet
uv run pytest -m golden          # the documented numbers
uv run pytest tests/test_library_calibration.py
uv run pytest tests/test_properties.py
```

**If those will not run, stop and say so rather than reviewing by reading.** An environment that cannot be built is itself a finding, and a review of the physics that never executed the physics is worth very little. Two failures are worth recognising: a sandbox with no access to the global `uv` cache, and a `.venv` copied or moved from another path, whose console scripts still carry absolute shebangs pointing at where it used to live. The second is repaired by deleting `.venv` and running `uv sync` again, not by `uv sync` alone.

`test_library_calibration.py` is the one that decides whether anything else can be believed: the model must recover each vehicle's *published* payload. It splits the library three ways. Vehicles declaring a `modelling_limits` entry that distorts payload are not asked to mean anything, because agreement from a model that misrepresents the vehicle is a coincidence. Vehicles excused by name must actually miss. Everything else must reproduce. **Read the file rather than assuming who is in which group**; that is exactly the sort of thing that changes between one review and the next, and the first two groups answer different questions.

**If you change a golden number, you are either fixing a bug or breaking the model. Say which, explicitly.** There is no third option and no "small drift".

### 2. Is a limit being hidden rather than stated?

The project's credibility comes from admitting what it cannot do. Look for anywhere the code produces a confident number for a case it does not really model:

- **Parallel burns are not modelled.** A serial walk over strap-on boosters always *flatters* the vehicle, because it lets the core burn propellant at the low mass it only reaches after separation. A vehicle this applies to declares `modelling_limits: [parallel_burn]` in `data/vehicles.yaml`; one with parallel stages that does not is a defect. Read `src/rocketry/limits.py` for the vocabulary and what each entry claims about the direction of the error.
- Extrapolation past the range a correlation was fitted on.
- A default that quietly decides something the caller should have chosen.

A number with an unstated limit is the worst defect available here. Rank it above ordinary bugs.

### 3. Is a number being compared with something that measures a different thing?

Ask of any figure the library holds against a published one: **measured against what?** Two numbers can look comparable and not be, and a model tuned to close a gap that was never real is worse than one that leaves it open.

- **A payload figure carries a reference orbit and inclination**, usually unstated. Falcon 9's 22.8 t and 17.5 t are both for 28.5°, which is the only reason their difference is the cost of recovery rather than an inclination penalty.
- **A velocity carries a frame.** Ground-relative and inertial differ by up to 465 m/s, and a non-rotating simulation reports neither exactly.
- **A manoeuvre's Δv may be what the engines produced or what the vehicle lost.** Most of a Falcon 9 entry burn's deceleration is atmosphere; charging propellant for the whole velocity change double-counts the air.
- **A mass carries a moment**: ignition, separation, burnout, with or without residuals.

Then check *how* a number was confirmed. **Arithmetic on a claim's own figures is not a check of it.** "Reuse costs 25 %" was recorded as verified because `1 − 17.5 / 22.8 = 23.2 %`, which tests the division and would pass against any physics; the same mistake appeared as a test asserting `analyse()` payloads, which are the published claims copied out of the YAML. A claim compared against a restatement of itself is unchecked. Say so when you find one.

Where a number matters, **cross-check along routes that do not share an assumption**. Falcon 9's recovery reserve is settled three ways: a Δv budget, a share of the propellant load, and engine mass flow times observed burn duration. The last two quote no velocity at all, which is what makes the first trustworthy. Corroboration from two sources that inherit the same frame is not corroboration.

When the model and a source disagree, **suspect the implementation first**. The library once said reuse cost 7 % where the source article said 25 %; the article was right.

### 4. Are the two questions still separate?

`Scenario.at_payload()` answers *what velocity does this produce carrying this payload*. `Scenario.solve_payload()` answers *what payload can it carry on this mission*. They are deliberately separate methods rather than one function with a flag, because confusing them produces answers that look entirely plausible.

Check that no caller has collapsed them, and that `solve_payload` returning a **negative** value is still passed through rather than clamped. Negative means "short by this much", which is a real answer worth showing.

### 5. Are the invariants still invariant?

Golden numbers pin known points; properties cover everywhere else. Look for invariants that hold but are untested:

- Monotonicity: more propellant never reduces Δv; a heavier stage never increases payload.
- Conservation: mass in equals mass out, and losses decompose by an exact identity rather than a residual.
- Inverses round-trip: every `tsiolkovsky` forward form against its inverse.
- Boundaries: zero, negative and absurd inputs raise with a message naming the values, rather than returning a plausible number.

### 6. The two rules that do not bend

- `src/rocketry/` imports nothing from Streamlit, Plotly, pandas or `labbook`. Verify by reading imports, not by assuming.
- SI throughout: tonnes, m/s, metres, seconds, tonnes-force. The rule's content is *one unit per quantity*, and it binds anything a calculation reads. Library fields that only record what a source published may keep that unit and must name it; the allowlist in `tests/test_units.py` is the only way in, and that test walks the core so a new offender cannot arrive quietly. Readers' km/h crosses the boundary through `labbook.units.from_kmh` / `to_kmh`, never a bare multiplication in a page.

### 7. Clean code, last

Only after the above. Duplicated formulae that could drift apart, magic numbers that should be named constants in `constants.py`, docstrings that no longer describe what the function does, and comments explaining *what* where they should explain *why*.

## How to report

Rank by consequence, not by how interesting the code is:

1. **Wrong numbers** that would reach a reader.
2. **Unstated limits**, where a confident answer is produced for an unmodelled case.
3. **Untested invariants** that currently hold, since those are the next silent regression.
4. Everything else.

For each finding give the exact location, the invariant it breaks, and **a concrete input that demonstrates it**. A finding without a reproducing case is a hypothesis; say so rather than presenting it as a defect.

If a change is warranted, follow the project's red/green discipline: write the failing test first, and if the fix moves a golden number, update `docs/physics-reference.md` in the same change so the document and the code never disagree.
