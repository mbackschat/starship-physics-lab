---
type: Payload
title: Starlink V3
description: The satellite whose unit mass converts an observed count into a payload figure.
tags: [starlink, spacex, payload, derived]

sources:
  - id: wiki-f12
    resource: ../../../raw/2026-08-16-wikipedia-starship-flight-12.md
    title: Starship flight test 12
    last_modified: 2026-08-16
  - id: wiki-f13
    resource: ../../../raw/2026-08-16-wikipedia-starship-flight-13.md
    title: Starship flight test 13
    last_modified: 2026-08-16

generated: { by: claude-opus-5, at: 2026-08-16T00:00:00Z }

status: stable
stale_after: 2026-10-31

provenance: derived
feeds:
  - target: data/flights.yaml#12
    asserts: {payload_t: 37.5}
  - target: data/flights.yaml#13
    asserts: {payload_t: 34.1}
---

# Starlink V3

The satellite Starship exists to launch, and the unit that makes its payload measurable from the outside.

## The unit mass is derived, not published

**1.705 t per satellite.** SpaceX has not published a figure, so this comes from division:

| Flight | Units | Total mass | Implied unit mass |
|---|---:|---:|---:|
| [13](../flights/flight-13.md) | 20 operational | 34,100 kg | **1.705 t** |
| [12](../flights/flight-12.md) | 22 (20 simulators + 2 working) | 37,500 kg | 1.705 t |

The two agree to four significant figures. Neither flight published a unit mass, so two independent totals landing on the same quotient is the only corroboration available, and it is reasonably strong: 22 × 1.705 = 37.51 t against a stated 37.5 t.

Marked `derived` rather than `published` for exactly this reason. It is arithmetic on published totals, not a specification.

## Why it matters more than it looks

Flight 14 is the first orbital attempt. What will be reported from it is a **satellite count**, not a payload mass. This number is what converts one into the other, and therefore what makes the [pre-registered prediction](../../../studies/flight-14-prediction/finding.md) checkable at all.

At 1.705 t, the model's range of predictions spans 22 satellites (if the ship weighs 220 t) to 116 (if it weighs 85 t). That is a wide enough spread that a satellite count alone will discriminate between the estimates.

## What would weaken this

**A change in the satellite itself.** If V3 is revised between flights, or if Flight 14 carries a different variant, this figure silently stops applying and every payload derived from a count is wrong. The two flights agreeing tells us the mass was stable across May and July 2026; it says nothing about later.

Recheck the moment a flight reports a count and a mass that do not divide to 1.705.

## A source disagreement worth knowing

Wikipedia's Flight 12 article calls the two working satellites modified Starlink **V2**; its List of Starship launches calls them **V3**. The count and total mass agree in both, so nothing here changes, but if it were V2 then the 22-unit corroboration above is really 20 V3 simulators plus 2 of something else, and it is weaker than it looks. Recorded rather than resolved.
