# Physics Core: Open Findings

From an independent review on 16 August 2026, run through the [review-physics](../.claude/skills/review-physics/SKILL.md) skill. Every claim below was reproduced before being written down.

**Completed items are deleted from this file, not ticked and kept.** Git history is the record of what was fixed. When this file is empty, delete it.

The headline calculations were not affected. Falcon 9 and Starship both still reproduce, golden numbers did not move, and no finding changes the payload argument.

---

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

## 7. Reuse costs the model almost nothing

Not from the review. Found while fixing finding 1, which had been hiding it: the fairing error flattered Falcon 9 by 1.7 t of payload, and removing it left the calibration reference 1.2 t *over* its published figure instead of 0.5 t under.

The model says a droneship recovery costs Falcon 9 **7.1 %** of its payload, 20.10 t against 18.68 t. The published payloads say **23.2 %**, 22.8 t against 17.5 t, and that figure is verified in [docs/physics-reference.md](physics-reference.md) section 3.4 as one the article got right.

The mechanism is not the size of the reserve. `_analyse_stages()` burns every stage to depletion less its reserve, so holding propellant back is the *only* thing a recovery profile can cost. In reality most of what recovery costs is **staging early**: a Falcon 9 that means to land separates at 8,000 km/h where an expendable one goes to 10,800. Both numbers are already in `data/vehicles.yaml` as `staging_speed_kmh`, and the stage walk never reads them. It is chart annotation only.

So the two vehicles differ in the model by 10.15 t of held-back propellant, 2.6 % of the first stage's load, and by nothing else.

- [ ] Decide whether the analytic walk should honour `staging_speed_kmh`, or whether the two Falcon 9 entries should stop pretending to be the same stage flown differently. The first is a real modelling change; the second is a data change.
- [ ] `tests/test_scenarios.py::test_droneship_recovery_costs_falcon9_about_a_fifth_of_its_orbital_mass` reads as the guard for exactly this and is not one. It compares `analyse()` results, whose `payload_t` is the *published claim* copied out of the YAML, so it asserts 22.8 / 17.5 ≈ 1.30 and would pass against any physics at all.

---

## Fixed already

Removed as they land. See git history.

- **A user-facing crash the review did not name.** Picking the Space Shuttle in the Launch chapter raised a `ValueError` and showed the reader a traceback, breaking the rule that an impossible configuration is explained. `5087496`, with a test that every vehicle on offer can be selected without raising.
- **Scenario overrides bypassed validation.** `model_copy` wrote fields blind, so a negative dry mass gave a confident answer and a misspelled field was silently ignored. Stages are now rebuilt and revalidated. `20dc38d`.
- **Recovery burns could create propellant.** `Burn` now rejects negative delta-v and non-positive Isp, with a property test that the reserve is never negative. `661a77c`.
- **`mass_to_orbit_t` omitted the recovery reserve**, and the case study had routed around it, leaving one idea implemented twice with the wrong copy public. Fixed at that root: the property counts the reserve and `payload_curve` now reads it. `0aac35f`.
- **The core was not uniform in its units.** `orbital_velocity` took kilometres and `StagingModel` took km/h, so `payload_at(1666.7)` returned −84.8 t where the same speed as 6,000 km/h returned 56.7 t. Both now take m/s and metres, the app and the study cross the boundary through `labbook.units.from_kmh` / `to_kmh`, and `tests/test_units.py` walks the core so the next one cannot be added quietly. It found a third the review had not: `Engine.mass_kg`, which is allowlisted because nothing calculates with it. CLAUDE.md rule 2 now states the split between computation and recorded source figures.
- **The fairing was carried to orbit.** It is now released when the last stage ignites, which is where the three-stage vehicles here really shed theirs and 35 s early for Falcon 9, worth 0.16 % of payload. Falcon 9 moved from 16.96 t to 18.68 t and `falcon9_expendable` stopped needing an excuse, so it moved to `MUST_REPRODUCE`. What that exposed is finding 7.
