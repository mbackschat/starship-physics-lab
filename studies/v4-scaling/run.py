"""Does Starship V4 make the staging split worse? The article says yes. Check it."""
from math import log


def brentq(f, a, b, tol=1e-9):
    fa, fb = f(a), f(b)
    if fa * fb > 0:
        raise ValueError("no sign change")
    for _ in range(200):
        m = 0.5 * (a + b)
        fm = f(m)
        if fa * fm <= 0:
            b, fb = m, fm
        else:
            a, fa = m, fm
        if b - a < tol:
            break
    return 0.5 * (a + b)


G0 = 9.81
def ve(isp): return isp * G0

TOTAL_DV = 9404.0          # article's calibrated budget, reproduced in section 3.3
SH_ISP, SS_ISP = 340.0, 365.0
RETURN_RATIO = 1.10        # t propellant per t booster dry mass, RTLS


def solve(sh_prop, sh_dry, ss_prop, ss_dry, label):
    ret = RETURN_RATIO * sh_dry
    burned = sh_prop - ret

    def residual(m_orbit):
        glow = sh_prop + sh_dry + ss_prop + m_orbit
        dv1 = ve(SH_ISP) * log(glow / (glow - burned))
        dv2 = ve(SS_ISP) * log((m_orbit + ss_prop) / m_orbit)
        return dv1 + dv2 - TOTAL_DV

    m_orbit = brentq(residual, 1.0, 3000.0)
    glow = sh_prop + sh_dry + ss_prop + m_orbit
    dv1 = ve(SH_ISP) * log(glow / (glow - burned))
    dv2 = ve(SS_ISP) * log((m_orbit + ss_prop) / m_orbit)
    residual_prop = 40.0 * (ss_prop / 1600.0)     # header tanks scale with the ship
    payload = m_orbit - ss_dry - residual_prop
    print(f"{label}")
    print(f"  stage-1/stage-2 propellant ratio : {sh_prop/ss_prop:6.2f}")
    print(f"  liftoff mass                     : {glow:7.0f} t")
    print(f"  booster return propellant        : {ret:7.0f} t")
    print(f"  booster dv                       : {dv1:7.0f} m/s   ({dv1/TOTAL_DV*100:.0f} % of total)")
    print(f"  ship dv                          : {dv2:7.0f} m/s")
    print(f"  mass in orbit                    : {m_orbit:7.1f} t")
    print(f"  ship dry + residual              : {ss_dry + residual_prop:7.1f} t")
    print(f"  PAYLOAD                          : {payload:7.1f} t")
    print(f"  payload / liftoff mass           : {payload/glow*100:7.2f} %")
    print()
    return payload, glow, dv1 / TOTAL_DV


print("=" * 78)
print("V3 vs V4: does making the ship bigger help?")
print("Ship dry mass scaled linearly from the article's 220 t at 1600 t propellant.")
print("Booster dry mass scaled linearly from 300 t at 3650 t propellant.")
print("=" * 78 + "\n")

solve(3650, 300, 1600, 220, "V3 as flown (article's model)")
solve(4050, 300 * 4050 / 3650, 2300, 220 * 2300 / 1600, "V4 as announced (4050 t booster, 2300 t ship)")
solve(4050, 300 * 4050 / 3650, 1600, 220, "V4 booster + V3-size ship (counterfactual)")
solve(4050, 300 * 4050 / 3650, 1100, 220 * 1100 / 1600, "V4 booster + much smaller ship")

print("=" * 78)
print("Stage propellant ratios for context")
print("=" * 78)
for name, s1, s2 in (("Falcon 9 Block 5", 395.7, 107.0),
                     ("Starship V3", 3650, 1600),
                     ("Starship V4 (announced)", 4050, 2300),
                     ("Article's Raptor 33 / Raptor 4", 4020, 1022),
                     ("Article's Raptor 33 / Raptor 3", 4608, 711)):
    print(f"  {name:32} {s1/s2:5.2f} : 1")

print()
print("=" * 78)
print("Sweep: best ship size on the V4 booster (4050 t, dry 333 t)")
print("=" * 78)
print(f"{'ship prop':>10} {'ratio':>7} {'ship dry':>9} {'dv1 share':>10} {'payload':>9}")
best = (0, -1)
for ss_prop in range(600, 2601, 100):
    ss_dry = 220 * ss_prop / 1600
    ret = RETURN_RATIO * (300 * 4050 / 3650)
    burned = 4050 - ret

    def residual(m_orbit, _sp=ss_prop, _sd=ss_dry, _burned=burned):
        glow = 4050 + 300 * 4050 / 3650 + _sp + m_orbit
        dv1 = ve(SH_ISP) * log(glow / (glow - _burned))
        dv2 = ve(SS_ISP) * log((m_orbit + _sp) / m_orbit)
        return dv1 + dv2 - TOTAL_DV

    m_orbit = brentq(residual, 1.0, 3000.0)
    glow = 4050 + 300 * 4050 / 3650 + ss_prop + m_orbit
    dv1 = ve(SH_ISP) * log(glow / (glow - burned))
    pay = m_orbit - ss_dry - 40.0 * ss_prop / 1600.0
    if pay > best[1]:
        best = (ss_prop, pay)
    print(f"{ss_prop:>10} {4050/ss_prop:>7.2f} {ss_dry:>9.0f} {dv1/TOTAL_DV*100:>9.0f} % {pay:>9.1f}")
print(f"\n  best ship size on this booster: {best[0]} t of propellant -> {best[1]:.0f} t payload")
