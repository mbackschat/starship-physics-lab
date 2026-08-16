---
description: Audit the physics core in src/rocketry for correctness, calibration and honesty about its limits.
argument-hint: "[module or topic, e.g. staging, reuse, ascent]"
---

# Review the physics engine

Audit `src/rocketry/`$ARGUMENTS.

This is not a general code review. The physics core is the one part of this project that other people's arguments will be built on, and a plausible-looking wrong number here is worse than a crash: it propagates into every chapter, every study and every claim the app makes, silently and with a confident badge next to it.

**Read [docs/physics-reference.md](../../docs/physics-reference.md) first.** It is the source of truth. Section 2 derives the physics, section 3 is the claim-by-claim verification log, section 4 records known corrections, section 6 specifies the models the app must implement, and section 7 holds the golden numbers. A finding that contradicts that document is either a real defect or a misreading of it, and you must say which.

## What to check, hardest first

### 1. Does it still reproduce reality?

The single question that matters. Run it, do not reason about it:

```sh
uv run pytest -m golden          # the documented numbers
uv run pytest tests/test_library_calibration.py
uv run pytest tests/test_properties.py
```

`test_library_calibration.py` is the one that decides whether anything else can be believed: the model must recover each vehicle's *published* payload. Vehicles that do not are on an excused list with a stated reason each, and the test fails if a vehicle is quietly left out of both lists, or if an excuse stops being needed. **Read those lists in the file rather than assuming who is on them**; which vehicles are excused, and how many, is exactly the sort of thing that changes between one review and the next.

**If you change a golden number, you are either fixing a bug or breaking the model. Say which, explicitly.** There is no third option and no "small drift".

### 2. Is a limit being hidden rather than stated?

The project's credibility comes from admitting what it cannot do. Look for anywhere the code produces a confident number for a case it does not really model:

- **Parallel burns are not modelled.** A serial walk over strap-on boosters always *flatters* the vehicle, because it lets the core burn propellant at the low mass it only reaches after separation. Vehicles excused for this are named in `tests/test_library_calibration.py`. Any vehicle with parallel stages that is *not* on that list is a defect. If the list is empty, the limit has been fixed and this bullet should go.
- Extrapolation past the range a correlation was fitted on.
- A default that quietly decides something the caller should have chosen.

A number with an unstated limit is the worst defect available here. Rank it above ordinary bugs.

### 3. Are the two questions still separate?

`Scenario.at_payload()` answers *what velocity does this produce carrying this payload*. `Scenario.solve_payload()` answers *what payload can it carry on this mission*. They are deliberately separate methods rather than one function with a flag, because confusing them produces answers that look entirely plausible.

Check that no caller has collapsed them, and that `solve_payload` returning a **negative** value is still passed through rather than clamped. Negative means "short by this much", which is a real answer worth showing.

### 4. Are the invariants still invariant?

Golden numbers pin known points; properties cover everywhere else. Look for invariants that hold but are untested:

- Monotonicity: more propellant never reduces Δv; a heavier stage never increases payload.
- Conservation: mass in equals mass out, and losses decompose by an exact identity rather than a residual.
- Inverses round-trip: every `tsiolkovsky` forward form against its inverse.
- Boundaries: zero, negative and absurd inputs raise with a message naming the values, rather than returning a plausible number.

### 5. The two rules that do not bend

- `src/rocketry/` imports nothing from Streamlit, Plotly, pandas or `labbook`. Verify by reading imports, not by assuming.
- SI throughout: tonnes, m/s, seconds, tonnes-force. Any unit conversion inside the core is a defect, even a correct one, because conversion belongs once at the presentation edge.

### 6. Clean code, last

Only after the above. Duplicated formulae that could drift apart, magic numbers that should be named constants in `constants.py`, docstrings that no longer describe what the function does, and comments explaining *what* where they should explain *why*.

## How to report

Rank by consequence, not by how interesting the code is:

1. **Wrong numbers** that would reach a reader.
2. **Unstated limits**, where a confident answer is produced for an unmodelled case.
3. **Untested invariants** that currently hold, since those are the next silent regression.
4. Everything else.

For each finding give the exact location, the invariant it breaks, and **a concrete input that demonstrates it**. A finding without a reproducing case is a hypothesis; say so rather than presenting it as a defect.

If a change is warranted, follow the project's red/green discipline: write the failing test first, and if the fix moves a golden number, update `docs/physics-reference.md` in the same change so the document and the code never disagree.
