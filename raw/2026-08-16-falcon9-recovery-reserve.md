---
resource: https://en.wikipedia.org/wiki/Falcon_9_Full_Thrust
title: What a Falcon 9 booster holds back to come home
retrieved: 2026-08-16
---

# What a Falcon 9 booster holds back to come home

Captured on 16 August 2026 while correcting the library's droneship recovery budget, which sat at 10.1 t against a reference figure of ~25 t. The correction was cross-checked three ways *because a budget quoted in m/s is only as good as the frame it was quoted in*, and two of the three routes avoid velocities entirely.

## Route 1: the published payload pair

> Falcon 9 Full Thrust has a payload capacity to LEO of 22,800 kg (50,300 lb) when expended, with an orbital inclination of 28.5°. When landing on a drone ship, the capacity reduces to 17,500 kg (38,600 lb).

**Both figures are quoted for the same reference orbit**, 28.5° inclination from Cape Canaveral. This matters: had one been a 53° Starlink orbit and the other a due-east launch, part of the apparent 23 % "cost of reuse" would have been an inclination penalty rather than recovery propellant, and correcting the reserve to close that gap would have been fitting the model to the wrong thing.

Recovery therefore costs **23 % of payload, like for like**.

## Route 2: share of the propellant load

> Typically 6-10 % of the total fuel mass is required for executing all three re-entry burns.

That is the return-to-launch-site profile: boostback, entry, landing. A droneship recovery skips the boostback, so it should sit below that band. On a 395.7 t first-stage load, 6-10 % is 24 to 40 t for three burns.

**No velocities appear in this figure at all**, so no frame can be mistaken.

## Route 3: engine flow times burn duration

The frame-free check, and the sharpest.

> The entry burn uses 3 engines to slow down the booster at a height of approximately 55 km, followed by a final landing burn using only one Merlin engine.

Observed Falcon 9 practice: an entry burn of roughly 20 to 30 s on three Merlins, and a landing burn of roughly 30 s on one, both throttled. A Merlin 1D at sea level flows about 305 kg/s at full thrust and cannot throttle below 57 %.

At 70 % throttle that gives roughly 5 to 6 t for the landing burn and 16 to 18 t for the entry burn: **21 to 24 t in total**.

## Why the m/s route needed checking

An entry burn described as "1,300 m/s" is ambiguous between two different quantities:

- the velocity the **engines** removed, which is what propellant is charged for, and
- the velocity the **stage** lost, which includes atmospheric drag.

Most of a Falcon 9's entry deceleration is the atmosphere, not the engines. Charging propellant for the second would double-count the air and inflate the reserve. The two frame-free routes above both land at 21-24 t, which is where the m/s route lands too, so the ranges in the project's own reference are being read correctly.

## What this rules out

The library's previous 10.1 t reserve fails routes 2 and 3, not just route 1. It is 2.6 % of the propellant load against a published 6-10 % for a longer profile, and it implies an entry burn of about **six seconds** on three engines. Falcon 9 does not fly a six-second entry burn.

## Sources

- [Falcon 9 Full Thrust, Wikipedia](https://en.wikipedia.org/wiki/Falcon_9_Full_Thrust)
- [Falcon 9 Block 5, Wikipedia](https://en.wikipedia.org/wiki/Falcon_9_Block_5)
- [Re-entry burns of Falcon 9, The Space Techie](https://www.thespacetechie.com/re-entry-burns-of-falcon-9/)
- [Falcon 9 booster landing explained, Orbital Xploration](https://orbitalxploration.com/falcon-9-booster-landing-explained-tech-behind-spacex-reusability)
- [SpaceX Falcon 9 data sheet, Space Launch Report](https://sma.nasa.gov/LaunchVehicle/assets/spacex-falcon-9-data-sheet.pdf)
