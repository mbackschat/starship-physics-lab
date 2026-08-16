# Physics Core: Open Findings

From an independent review on 16 August 2026, run through the [review-physics](../.claude/skills/review-physics/SKILL.md) skill. Every claim below was reproduced before being written down.

**Completed items are deleted from this file, not ticked and kept.** Git history is the record of what was fixed. When this file is empty, delete it.

The headline calculations were not affected. Falcon 9 and Starship both still reproduce, golden numbers did not move, and no finding changes the payload argument.

---

## 1. The fairing is carried to orbit

`_analyse_stages()` in `src/rocketry/vehicle.py` adds `vehicle.fairing_t` to the mass above **every** stage, including the last. There is no jettison event, so Falcon 9's 1.9 t fairing is modelled as reaching orbit.

Falcon 9's upper stage gets 5,790 m/s where the documented calculation without an orbit-bound fairing gives 6,025 m/s. Solved payload is 16.96 t; dropping the fairing entirely gives 18.86 t. The truth is between them, because a real fairing is jettisoned partway through the second stage burn.

This matters more than its size suggests, because Falcon 9 is the calibration reference that makes the whole method credible.

- [ ] Add a mass-jettison event rather than tuning the data around it. `test_the_calibration_reference_is_the_tightest` should get tighter, not looser.

`tests/test_scenarios.py::test_the_fairing_is_not_counted_as_arriving` pins the gap meanwhile: `burnout_mass_t` exceeds `mass_to_orbit_t` by exactly the fairing, because the model still has it attached at engine cutoff. When this finding is fixed the two converge and that test should become an equality.

## 2. Unsupported configurations are analysed anyway

`Stage` can name only one engine type, `_analyse_stages()` assumes serial burns, and `ascent._plan()` builds one homogeneous burn per stage. Nothing refuses a vehicle that violates those assumptions.

Three reproductions, in descending severity:

- **The Space Shuttle is in `MUST_REPRODUCE` and its boosters are modelled with RS-25 engines.** It passes calibration at 29.1 t against a published 27.5 t, while `simulate()` refuses it at a thrust-to-weight of 0.19. It passes the test that is supposed to decide whether it can be believed, and is nonsense underneath.
- **Ariane 64** solves to 32.2 t against 21.6 t. Its exception says so, but the generic Launch and Stages views still offer it.
- **Starship's upper stage** has three sea-level and three vacuum Raptors; ascent simulates six identical `raptor_3`. Simulated and analytic budgets differ by 215 m/s at the claimed payload.

The reviewer recommended moving the Shuttle to the excused list. **That would fail the suite**, because `test_excused_vehicles_really_do_miss` requires an excused vehicle to miss by more than tolerance and the Shuttle is within 5.9 %. The framework has one axis where the problem has two.

- [ ] Separate *reproduces its published payload* from *is honestly modelled*. A vehicle can do the first without the second, and today nothing records that.
- [ ] Replace the Shuttle's RS-25 placeholder, or mark the stage as not simulatable.
- [ ] Decide whether mixed engine types within a stage should be representable, or rejected at load time.

## 6. The core is not uniform in its units

The stated non-negotiable rule is SI throughout, conversion only at the presentation edge. Two functions take other units:

- `orbital_velocity(altitude_km)` takes kilometres. `orbital_velocity(200_000)` returns 1,390 m/s.
- `StagingModel` takes km/h. `payload_at(1666.7)` returns −84.8 t where the equivalent 6,000 km/h returns 56.7 t.

**Rated lower than the reviewer did.** Both parameters are named for their units, so nothing computes wrong for a caller who reads the signature, and the data models legitimately store what sources publish. This is a footgun and an inconsistency with a stated rule, not a defect producing wrong numbers today.

- [ ] Decide between converting these to SI at the boundary, or amending the rule in CLAUDE.md to say the core is SI except where a parameter name says otherwise. Either is defensible; the present state, where the rule and the code disagree, is not.

---

## Fixed already

Removed as they land. See git history.

- **A user-facing crash the review did not name.** Picking the Space Shuttle in the Launch chapter raised a `ValueError` and showed the reader a traceback, breaking the rule that an impossible configuration is explained. `5087496`, with a test that every vehicle on offer can be selected without raising.
- **Scenario overrides bypassed validation.** `model_copy` wrote fields blind, so a negative dry mass gave a confident answer and a misspelled field was silently ignored. Stages are now rebuilt and revalidated. `20dc38d`.
- **Recovery burns could create propellant.** `Burn` now rejects negative delta-v and non-positive Isp, with a property test that the reserve is never negative. `661a77c`.
- **`mass_to_orbit_t` omitted the recovery reserve**, and the case study had routed around it, leaving one idea implemented twice with the wrong copy public. Fixed at that root: the property counts the reserve and `payload_curve` now reads it. `0aac35f`.
