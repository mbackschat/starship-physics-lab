---
type: Flight
title: Starship Flight 12
description: First Block 3 flight, and the first to carry working satellites.
tags: [starship, flight-test, block-3, starlink]

sources:
  - id: wiki-f12
    resource: ../../../raw/2026-08-16-wikipedia-starship-flight-12.md
    title: Starship flight test 12
    last_modified: 2026-08-16

generated: { by: claude-opus-5, at: 2026-08-16T00:00:00Z }

status: stable
stale_after: 2027-01-31

provenance: published
feeds:
  - target: data/flights.yaml#12
    asserts:
      date: 2026-05-22
      payload_t: 37.5
      reached_orbit: false
---

# Flight 12

22 May 2026, 22:30:22 UTC. Booster 19 and Ship 39, the first Block 3 pair, and the first launch from Starbase's second pad.

## What happened

**Booster:** lost. It flipped abnormally fast after stage separation and hit the Gulf of Mexico at 1,450 km/h instead of returning to the launch site.

**Ship:** met its objective and splashed down in the Indian Ocean.

The trajectory was suborbital by design, deliberately short of orbital velocity, on a southerly track that would have put any debris over the Caribbean.

## Payload, and a disagreement between sources

Approximately 37,500 kg, deployed through an improved "Pez dispenser" mechanism. It was the first time a Starship released working hardware rather than only simulators.

**Sources disagree on what those working satellites were.** Wikipedia's flight 12 article calls them 2 modified **Starlink V2**; its List of Starship launches calls them **V3**. The count and the total mass agree in both, so the disagreement changes nothing computed here, and it is recorded rather than resolved. Where a source conflict cannot be settled, saying so is more useful than picking one silently.

The composition is therefore best stated as 20 mass simulators plus 2 working satellites, 22 units in total.

## What it contributes

At [Flight 13](flight-13.md)'s unit mass of 1.705 t, 22 units come to 37.51 t, which reproduces the published 37,500 kg exactly. Two flights agreeing on a figure neither of them published is the strongest evidence available for the Starlink V3 unit mass, and that number is what makes Flight 14's payload measurable from a satellite count.
