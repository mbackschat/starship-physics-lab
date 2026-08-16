# Physics Core: Open Findings

From an independent review on 16 August 2026, run through the [review-physics](../.claude/skills/review-physics/SKILL.md) skill. Every claim below was reproduced before being written down.

**Completed items are deleted from this file, not ticked and kept.** Git history is the record of what was fixed. When this file is empty, delete it.

Golden numbers did not move and nothing here changes the payload argument. One finding remains, and it was not in the review: it surfaced only once the errors above it were gone.

---

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
- **Unsupported configurations were analysed anyway.** A vehicle now declares in `data/vehicles.yaml` what the model cannot represent about it, and `tests/test_library_calibration.py` derives its three categories from that instead of a hand-kept list. The Shuttle left `MUST_REPRODUCE`, where its 6 % agreement was a coincidence; Ariane 64 left the excused list, where its excuse was really a modelling limit wearing the wrong label. Its boosters got the real RSRM solid motor, so it flies rather than being refused at a thrust-to-weight of 0.19, and `shell.modelling_note()` tells the reader what is distorted and in which direction. Mixed engine types within a stage stay deliberately unrepresentable, declared instead: engine groups with their own thrust curves would make this a design tool. Decisions recorded in CLAUDE.md.
- **The ascent had no guidance, only a pitch program.** Not from the review either; found because Saturn V and Ariane 64 hit the ground in chapter 3. `_pitch_rad` steered from speed alone with no feedback from altitude, so once the program reached the horizon nothing held the vehicle up: *every* vehicle in the library arced past 200 km and then fell while still burning, Falcon 9 finishing its second stage burn descending through 101 km. Real vehicles fly open loop through the atmosphere and closed loop above it, which is now what this does, aiming at 200 km with no climb rate left. Falcon 9 went from an absurd trajectory that happened to give plausible losses to 7,832 m/s at 200 km, still level, staging at 76 km. Sources captured in [raw/2026-08-16-ascent-guidance-open-and-closed-loop.md](../raw/2026-08-16-ascent-guidance-open-and-closed-loop.md). Every check on the ascent had named Falcon 9 only; there are now parametrised guards over the whole library. `26a9b01`.
- **The fairing was carried to orbit.** It is now released when the last stage ignites, which is where the three-stage vehicles here really shed theirs and 35 s early for Falcon 9, worth 0.16 % of payload. Falcon 9 moved from 16.96 t to 18.68 t and `falcon9_expendable` stopped needing an excuse, so it moved to `MUST_REPRODUCE`. What that exposed is finding 7.
