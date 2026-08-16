# Operating log

Append-only. One entry per ingest, query or lint pass, newest last.

Format: `## [YYYY-MM-DD] <operation> | <subject>`, so entries can be found by grep without parsing anything.

This is not a changelog for the pages themselves. Git already holds that. It is the record of *what was done to the knowledge base and why*, which git does not hold.

---

## [2026-08-16] ingest | Starship flights 12 and 13, Flight 14 plans

Captured three sources into `raw/`: Wikipedia's flight 12 and flight 13 articles, and reporting on Flight 14's planned mission, cross-checked against SpaceX's August earnings call.

Compiled four pages: `vehicles/starship-v3.md`, `engines/raptor-3.md`, `flights/flight-12.md`, `flights/flight-13.md`. The vehicle and engine pages were migrated from `docs/physics-reference.md` section 5 rather than researched fresh, to prove the format carries existing content before more is gathered.

**Found and corrected a real error.** `data/flights.yaml` recorded Flight 12 as `2026-05-01` with month precision. It flew 22 May 2026. The payload description said "22 Starlink V3 mass simulators"; it was 20 simulators plus 2 working satellites, which matters because it was the first Starship to deploy working hardware. Corrected in `3cf3139`.

**Recorded an unresolved source conflict.** Wikipedia's flight 12 article calls the two working satellites modified Starlink V2; its launch list calls them V3. Mass and count agree, so nothing computed here changes. Left as a disagreement in both the page and the library note rather than silently picking one.

**Noted a discrepancy already known but not written down.** Raptor 3 sea-level Isp is 327 s in the library, following the source article, against Wikipedia's 330 s for the Block 3 stack. About 1 %, inside the project's precision target, but it propagates into every delta-v from that engine.

## [2026-08-16] ingest | Flight 14 pre-registration

Pre-registered the model's Flight 14 prediction in `studies/flight-14-prediction/` before the flight, committed as `6d6acb4`. The falsifiable claim is the 296 to 298 t total reaching orbit, which moves by 0.8 % across a 135 t range of dry-mass assumptions, not the payload split, which moves by a factor of five.
