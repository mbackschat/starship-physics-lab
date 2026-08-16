---
type: Flight
title: Starship Flight 13
description: First operational satellite deployment, and the relight that weighs the ship.
tags: [starship, flight-test, block-3, starlink]

sources:
  - id: wiki-f13
    resource: ../../../raw/2026-08-16-wikipedia-starship-flight-13.md
    title: Starship flight test 13
    last_modified: 2026-08-16

generated: { by: claude-opus-5, at: 2026-08-16T00:00:00Z }

status: stable
stale_after: 2027-01-31

provenance: published
feeds:
  - target: data/flights.yaml#13
    asserts:
      date: 2026-07-24
      payload_t: 34.1
      reached_orbit: false
---

# Flight 13

24 July 2026, 22:51 UTC. Booster 20 and Ship 40, both Block 3.

The most informative flight so far, for two unrelated reasons.

## What happened

| Event | Time |
|---|---|
| Max q | T+0:58 |
| Hot-staging and separation | T+2:21 |
| Ship engine cutoff | T+8:05 |
| Satellite deployment | T+16:40 to T+27:39 |
| Raptor in-space relight | T+38:58 |
| Splashdown | T+1:05:21 |

**Booster:** lost. Only 10 of its 13 engines relit for the landing burn, and it was destroyed on impact in the Gulf of Mexico.

**Ship:** recovered. It splashed down in the Indian Ocean and stayed intact and operational after tipping over, a first, which let the heat shield and engines be inspected by drone afterwards.

## Why it matters: the relight weighs the ship

The in-space relight at T+38:58 lasted about 14 seconds. That is enough to weigh a vehicle nobody outside SpaceX has access to.

A burn of known duration, from an engine of known thrust and specific impulse, consumes a calculable mass of propellant and produces an observable change in velocity. The rocket equation then gives the vehicle's mass. No access required, which is what makes the method interesting.

It gives a total of **242 to 259 t** for the ship at that moment. Turning that into a dry mass needs one further assumption, how much propellant remained aboard, and that is precisely where measurement stops and argument begins. See [physics-reference.md](../../physics-reference.md) section 3.2 and the [Starship V3 page](../vehicles/starship-v3.md).

## Why it matters: the satellite unit mass

20 operational Starlink V3 satellites massing 34,100 kg gives **1.705 t per unit**.

That figure reproduces [Flight 12](flight-12.md)'s 37,500 kg for 22 units exactly, which is the only corroboration available, since no unit mass has been published. It is what converts an observed satellite count on a future flight into a payload mass, and therefore what makes Flight 14 measurable at all.

## Still not orbit

Like every flight before it, this one was placed deliberately short of orbital velocity, about 500 km/h below. No Starship has yet delivered a payload to a real orbit, which is why the payload question remains open.
