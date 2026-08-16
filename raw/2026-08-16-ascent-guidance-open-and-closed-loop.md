---
resource: https://www.orbiterwiki.org/wiki/Powered_Explicit_Guidance
title: Ascent guidance, open loop and closed loop
retrieved: 2026-08-16
---

# How launch vehicles are actually steered

Reduced from several sources retrieved on 16 August 2026, listed at the bottom. Captured because this project's ascent simulation modelled only the first half of the scheme and produced a ballistic arc as a result.

## The two-phase scheme

Launch vehicles do not steer the same way for the whole flight. They use **open-loop control during the atmospheric first stage** and **closed-loop guidance for the exoatmospheric portion**.

> Most modern multi-staged space launch vehicles adopt closed-loop guidance laws for the exoatmospheric trajectory, although open-loop ascent guidance is effective enough for the first stage maneuver against the atmospheric loads.

The reason for the split is aerodynamic, not computational. Inside the atmosphere the vehicle must fly close to zero angle of attack or the structural loads become unsurvivable, so the pitch attitude is commanded from a stored program and is not free to chase a target. Above the atmosphere that constraint disappears and the guidance can steer at whatever attitude the target orbit requires.

> Unlike the first stage pitch program, the second stage guidance program is continually modified by the guidance system.

> Second stage guidance functions very differently from first stage guidance in that second stage guidance is closed loop. It solves equations of motion for the guidance program parameters, and hands those parameters to the control system to fly for a short distance.

## When the handover happens

As early as the flight allows, because closed-loop guidance is what corrects whatever the open-loop phase got wrong:

> In the first phase of core stage flight, Powered Explicit Guidance (PEG) begins to steer the vehicle to the ascent target and must compensate for trajectory errors that may have accumulated during boost. This mode is engaged as early in core stage flight as possible in order to minimize propellant reserves required to achieve the target orbit.

Shuttle engaged PEG shortly after solid rocket booster separation. Saturn V's Iterative Guidance Mode engaged shortly after S-II ignition, once the launch escape system and the interstage were gone.

## What the closed loop is aiming at

An orbit is a position *and* a velocity, so the guidance targets both: the specified cutoff altitude and a flight path angle of zero, reached at the same moment the propellant runs out. The classical solutions (IGM on Saturn V, PEG on Shuttle, and their descendants) all reduce to a **linear tangent steering law**, in which the tangent of the pitch angle varies linearly with time.

## Reference trajectory markers

Rough figures for checking a simulation against reality.

| Vehicle | Event | Time | Altitude | Speed |
|---|---|---|---|---|
| Falcon 9 | MECO | ~T+2:30 | ~80 km | ~Mach 10 |
| Falcon 9 | SECO-1 | ~T+8:40 | ~200 km | orbital |
| Saturn V | Centre engine cutoff | T+135 s | 44 km | |
| Saturn V | S-IC cutoff | T+162 s | 68 km | |
| Saturn V | S-II cutoff | ~T+9:12 | 185 km (115 mi) | 7,018 m/s (15,700 mph) |

Falcon 9 MECO speed is quoted inconsistently across secondary sources, from 6,000 km/h to Mach 10, and varies by mission profile in any case: a droneship landing stages considerably earlier than an expendable flight. Treat the altitude as the firmer of the two numbers.

## Sources

- [Powered Explicit Guidance, OrbiterWiki](https://www.orbiterwiki.org/wiki/Powered_Explicit_Guidance)
- [Shuttle ascent guidance (PEG), FlightGear wiki](https://wiki.flightgear.org/Shuttle_guidance_-_Ascent_guidance_Powered_Explicit_Guidance_(PEG))
- [Space Launch System Ascent Flight Control Design, AAS 14-038](https://scispace.com/pdf/space-launch-system-ascent-flight-control-design-4x7ednv4p7.pdf)
- [A comparison of iterative explicit guidance algorithms for space launch vehicles](https://www.sciencedirect.com/science/article/abs/pii/S0273117714005900)
- [S-IC, Wikipedia](https://en.wikipedia.org/wiki/S-IC)
- [S-II, Wikipedia](https://en.wikipedia.org/wiki/S-II)
- [Falcon 9 Block 5, Wikipedia](https://en.wikipedia.org/wiki/Falcon_9_Block_5)
