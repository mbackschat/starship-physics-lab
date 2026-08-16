"""Independent verification of every number in starship-article.md.

Convention: mass in tonnes, velocity in m/s, ISP in seconds.
"""
from math import exp, log, log2, sqrt, cos, sin, radians, pi

G0 = 9.81          # article uses 9.81, not 9.80665
KMH = 1 / 3.6      # km/h -> m/s


def ve(isp):
    return isp * G0


def dv(m0, mf, isp):
    return ve(isp) * log(m0 / mf)


def mf_after(m0, dv_, isp):
    return m0 / exp(dv_ / ve(isp))


def prop_for(mf, dv_, isp):
    """Propellant needed to give final mass mf a delta-v (burn ends at mf)."""
    return mf * (exp(dv_ / ve(isp)) - 1)


def chk(label, claimed, computed, tol=0.02, unit=""):
    if claimed is None:
        print(f"  ·  {label:<58} = {computed:>10.4g} {unit}")
        return
    rel = abs(computed - claimed) / abs(claimed) if claimed else abs(computed)
    mark = "OK " if rel <= tol else "XX "
    print(f"{mark}  {label:<58} claim {claimed:>9.4g} | calc {computed:>9.4g} {unit}  ({rel*100:.1f}%)")


print("=" * 100)
print("1. ENGINE / ISP BASICS")
print("=" * 100)
chk("Raptor3 SL flow: 250 tf / 327 s", 0.764, 250 / 327, unit="t/s")
chk("throttle vs announced 280 tf", 0.11, 1 - 250 / 280, unit="frac")
chk("ve at ISP 327", None, ve(327), unit="m/s")
chk("ve at ISP 350 (article: 3433)", 3433, ve(350), unit="m/s")
chk("ve at ISP 380", None, ve(380), unit="m/s")
chk("ve at ISP 348 (MVac)", None, ve(348), unit="m/s")
chk("ve at ISP 365 (SS avg)", None, ve(365), unit="m/s")
chk("ve at ISP 340 (SH avg)", None, ve(340), unit="m/s")

print("\n-- footnote: 'binary' velocity V for mass ratio 2, Raptor vac --")
chk("V = ve(350)*ln2  [article: 2428 m/s]", 2428, ve(350) * log(2), unit="m/s")
chk("constant g0*ln2  [article: 6.937]", 6.937, G0 * log(2), unit="m/s^2")
print(f"     -> article's 2428 implies ve = {2428/log(2):.0f} m/s = ISP {2428/log(2)/G0:.0f} s")

print("\n-- doubling-ladder example (1 t dry) --")
for n in range(1, 5):
    mr = 2 ** n
    print(f"     {n}xV -> mass ratio {mr:>3}, propellant {mr-1:>3} t  (article: 1,3,7,15)")

print("\n" + "=" * 100)
print("2. WEIGHING THE STARSHIP FROM THE 14 s DEORBIT-DEMO BURN")
print("=" * 100)
flow = 250 / 327
chk("14 s burn propellant", 10.7, 14 * flow, unit="t")
dV = 500 * KMH
chk("500 km/h in m/s", 139, dV, unit="m/s")
chk("prop / INITIAL mass  = 1-exp(-dv/ve)", 0.04, 1 - exp(-dV / ve(350)), unit="frac")
chk("prop / FINAL mass    = exp(dv/ve)-1", 0.04, exp(dV / ve(350)) - 1, unit="frac")
f_final = exp(dV / ve(350)) - 1
print(f"     -> with 10.0 t: final mass {10/f_final:6.1f} t, initial {10/f_final*(1+f_final):6.1f} t")
print(f"     -> with 10.7 t: final mass {10.7/f_final:6.1f} t, initial {10.7/f_final*(1+f_final):6.1f} t")
print("     article claims 240-257 t 'before reentry' -> matches FINAL-mass reading (242-259)")

print("\n-- Starship landing burn --")
chk("gravity loss 20 s", 200, 20 * G0, unit="m/s")
for isp in (327, 300, 280, 250):
    p = prop_for(220, 300, isp)
    print(f"     dv=300 m/s on 220 t dry at ISP {isp}: {p:5.1f} t = {p/220*100:4.1f}% of dry mass")
print("     article claims 'over 10%' -> ~30 t; straight calc gives 22-26 t (30 t needs ISP~240 s)")

print("\n" + "=" * 100)
print("3. THE PLAUSIBLE MODEL: STARSHIP + SUPER HEAVY")
print("=" * 100)
SS_ORBIT = 300.0     # mass in orbit incl. payload + landing prop
SS_PROP = 1600.0
SS_ISP = 365.0
SH_DRY = 300.0
SH_PROP = 3650.0
SH_BURN = 3320.0
SH_ISP = 340.0
GLOW = SH_PROP + SH_DRY + SS_PROP + SS_ORBIT
chk("stack liftoff mass", 5850, GLOW, unit="t")
dv_ss = dv(SS_ORBIT + SS_PROP, SS_ORBIT, SS_ISP)
chk("Starship ideal dv", 6609, dv_ss, unit="m/s")
dv_sh = dv(GLOW, GLOW - SH_BURN, SH_ISP)
chk("Super Heavy ideal dv", 2795, dv_sh, unit="m/s")
chk("total ideal dv", 9404, dv_ss + dv_sh, unit="m/s")
chk("SH share of total dv", 0.30, dv_sh / (dv_ss + dv_sh), unit="frac")

print("\n-- Super Heavy return budget --")
boost = 1800.0
land = 600.0
for isp_b, isp_l in ((350, 327), (340, 327), (330, 330)):
    ratio = exp(boost / ve(isp_b)) * exp(land / ve(isp_l))
    print(f"     boostback ISP {isp_b} + landing ISP {isp_l}: {ratio-1:.3f} t prop per t dry"
          f"  -> {(ratio-1)*300:5.0f} t for 300 t dry")
print("     article: 'at least 1.1 t/t = 330 t'  -> reproduces with ~330 s average ISP")
chk("boostback dv = (5400+1000) km/h", 1800, (5400 + 1000) * KMH, unit="m/s")
chk("landing: 27 s grav loss + 300 m/s residual", 600, 27 * G0 + 300, unit="m/s", tol=0.10)
chk("SH prop kept back (3650-3320)", 330, SH_PROP - SH_BURN, unit="t")

print("\n" + "=" * 100)
print("4. FALCON 9 CROSS-CHECK")
print("=" * 100)
F9_S2_DRY, F9_S2_PROP, F9_S2_ISP = 4.0, 107.0, 348.0
PAY = 17.5
chk("F9 S2 ideal dv (17.5 t payload)", 6100, dv(PAY + F9_S2_DRY + F9_S2_PROP, PAY + F9_S2_DRY, F9_S2_ISP), unit="m/s")
chk("F9 S2 dv minus 0.5 t deorbit prop", 6025, dv(PAY + F9_S2_DRY + F9_S2_PROP, PAY + F9_S2_DRY + 0.5, F9_S2_ISP), unit="m/s")
print("\n-- F9 stage 1: reverse-engineer the 3233 m/s claim --")
for s1_dry in (25.6, 22.2):
    for isp1 in (282, 297, 301, 311):
        glow = s1_dry + 385 + F9_S2_DRY + F9_S2_PROP + 1.9 + PAY
        burn = 385 - 25
        d = dv(glow, glow - burn, isp1)
        flag = "  <== matches 3233" if abs(d - 3233) < 40 else ""
        print(f"     dry {s1_dry:5.1f} t, ISP {isp1}: GLOW {glow:6.1f} t, dv {d:7.0f} m/s{flag}")
chk("dv gap SH vs F9-S1", 438, 3233 - dv_sh, unit="m/s")
chk("F9 staging speed advantage 2000 km/h", 570, 2000 * KMH, unit="m/s")
chk("F9 stage-1 share of total dv", None, 3233 / (3233 + 6025), unit="frac")

print("\n-- liftoff thrust/weight and the '40 s' comparison --")
F9_T = 7607e3 / (G0 * 1000)      # tf
F9_GLOW = 549.0
SS_T = 33 * 250.0
chk("F9 liftoff TWR", 1.4, F9_T / F9_GLOW)
chk("Starship liftoff TWR", 1.4, SS_T / GLOW)
chk("F9 net accel at liftoff", 0.4, F9_T / F9_GLOW - 1, unit="g")
chk("SS net accel at liftoff", 0.4, SS_T / GLOW - 1, unit="g")
chk("frac of thrust eaten by gravity at liftoff (SS)", 0.70, GLOW / SS_T, unit="frac")
f9_flow = 9 * 845e3 / (G0 * 282) / 1000
ss_flow = 33 * flow
chk("F9 propellant/s as % of GLOW", 0.005, f9_flow / F9_GLOW, unit="frac")
chk("SS propellant/s as % of GLOW", 0.0043, ss_flow / GLOW, unit="frac")
for name, T, M, fl, claim in (("F9", F9_T, F9_GLOW, f9_flow, 0.875), ("Starship", SS_T, GLOW, ss_flow, 0.69)):
    m40 = M - 40 * fl
    a40 = T / m40 - 1
    print(f"     {name:9} after 40 s: mass {m40:6.1f} t, net accel {a40:5.3f} g "
          f"(article {claim}), gravity eats {m40/T*100:4.1f}% (article: 53/59%)")
print("     -> Starship 0.69 g reproduces with TWR0=1.40; F9 0.875 g needs TWR0=1.51, not 1.41")
chk("Raptor vs Merlin flow saving (327 vs 282 s)", 0.14, 1 - 282 / 327, unit="frac")

print("\n" + "=" * 100)
print("5. DRY-MASS FRACTIONS AND THE ARIANE 6 ARGUMENT")
print("=" * 100)
chk("Starship dry fraction 220/(220+1600)", 0.12, 220 / (220 + 1600), unit="frac")
chk("F9 S2 + fairing fraction 6/(6+107)", 0.06, 6 / (6 + 107), unit="frac", tol=0.15)
chk("Ariane6 ULPM fraction 6/(6+32)", None, 6 / (6 + 32), unit="frac")
chk("Ariane6 ULPM scaled to 1600 t prop", 300, 6 * 1600 / 32, unit="t")
chk("Ariane6 payload / dry mass", 3.67, 22 / 6)
chk("SH dry scaled from F9 S1 (3250 t prop)", 215, 25.6 * 3250 / 385, unit="t")
chk("SH dry scaled from F9 S1 (3650 t prop)", 240, 25.6 * 3650 / 385, unit="t")
chk("SH cross-section vs F9 (9 m / 3.66 m)^2", 6, (9 / 3.66) ** 2)
chk("SH dry mass vs F9 S1", 12, 300 / 25.6, tol=0.05)
chk("diameter for equal ballistic loading", 12.5, 3.66 * sqrt(12), unit="m")
chk("Shuttle payload fraction 27.5/2000", None, 27.5 / 2000, unit="frac")
chk("Starship payload fraction 37.5/5850", None, 37.5 / 5850, unit="frac")
chk("ratio of the two payload fractions", 2.0, (27.5 / 2000) / (37.5 / 5850), tol=0.10)
chk("F9 reuse penalty on payload 22.8->17.5", 0.25, 1 - 17.5 / 22.8, unit="frac", tol=0.10)
chk("F9 reuse penalty on orbital mass", 0.20, 1 - 21.5 / 26.8, unit="frac", tol=0.10)

print("\n" + "=" * 100)
print("6. INCLINATION / ROTATION PENALTIES")
print("=" * 100)
V_ROT = 465.1
for lat, inc in ((28.5, 28.5), (28.5, 53.0), (28.5, 90.0), (28.5, 97.4)):
    if abs(cos(radians(inc))) > cos(radians(lat)):
        continue
    sin_az = cos(radians(inc)) / cos(radians(lat))
    help_ = V_ROT * cos(radians(lat)) * sin_az
    print(f"     lat {lat}° -> inc {inc:5.1f}°: azimuth sin {sin_az:+.3f}, rotation bonus {help_:+6.0f} m/s"
          f", penalty vs due-east {V_ROT*cos(radians(lat))-help_:6.0f} m/s")
print("     article: 53° costs ~1500 km/h (417 m/s) and polar ~600 m/s extra")
print("     -> polar ~420-480 m/s is the clean number; the 53° figure looks ~300 m/s too high")
chk("orbital-mass loss for +600 m/s at ISP 348", 0.15, 1 - 1 / exp(600 / ve(348)), unit="frac", tol=0.20)
chk("F9 implied dv 28.5->53 deg (21.5 -> 19.5 t)", None, dv(21.5, 19.5, 348), unit="m/s")
chk("F9 implied dv 28.5->polar (21.5 -> 17.5 t)", None, dv(21.5, 17.5, 348), unit="m/s")

print("\n-- payload leverage: 20 % less orbital mass --")
print(f"     300 t in orbit, 200 t of it structure+prop -> payload 100 t")
print(f"     240 t in orbit                              -> payload {240-200:.0f} t "
      f"({(240-200)/240*100:.0f} % of orbital mass, article: 13 %)")
print(f"     real model: 260 t non-payload, 300 t in orbit -> payload 40 t")
for pen, lbl in ((330, "53 deg"), (600, "polar")):
    m = mf_after(300, pen, SS_ISP)
    print(f"     with +{pen} m/s ({lbl}): orbital mass {m:5.1f} t -> payload {m-260:+6.1f} t")

print("\n" + "=" * 100)
print("7. THOUGHT EXPERIMENT: RAPTOR 33 / RAPTOR 4  (staging at 10 000 km/h)")
print("=" * 100)
GLOW2 = 5850.0
dv1 = dv_sh + (10000 - 6000) * KMH
chk("R33 ascent dv (SH dv + 4000 km/h)", 3920, dv1, unit="m/s")
burn_frac = 1 - exp(-dv1 / ve(340))
chk("burned fraction of GLOW", 0.691, burn_frac, unit="frac")
rest = GLOW2 * (1 - burn_frac)
chk("mass left at staging", 1806, rest, unit="t")
land_frac = exp(500 / ve(327)) - 1
chk("landing prop / dry mass (500 m/s @327 s)", 0.17, land_frac, unit="frac")
brake_dv = (10000 - 5300) * KMH
brake_frac = exp(brake_dv / ve(350)) - 1
chk("braking prop fraction (10000->5300 km/h @350 s)", 0.46, brake_frac, unit="frac")
r33_sep = 300 * (1 + land_frac) * (1 + brake_frac)
chk("R33 mass at separation", 513, r33_sep, unit="t")
chk("  as % of dry mass", 1.71, r33_sep / 300)
r4_total = rest - r33_sep
chk("mass available for R4 + payload", 1293, r4_total, unit="t")
dv2 = 5600.0
r4_orbit = mf_after(r4_total, dv2, SS_ISP)
chk("R4 mass reaching orbit", 271, r4_orbit, unit="t")
chk("R4 propellant burned", 1022, r4_total - r4_orbit, unit="t")
print(f"     consistency: article's own budget 9404 - 3920 = {9404-dv1:.0f} m/s, they used {dv2:.0f} (conservative)")
r4_stage = 160.0
chk("R4 stage mass scaled linearly from 250 t / 1600 t", 160, 250 * (r4_total - r4_orbit) / 1600, unit="t", tol=0.05)
chk("R4 payload", 110, r4_orbit - r4_stage, unit="t")
chk("orbital mass vs Starship", -0.10, r4_orbit / 300 - 1, unit="frac", tol=0.10)
for pen, claim, lbl in ((330, 87, "53 deg"), (600, 68, "polar")):
    m = mf_after(r4_orbit, pen, SS_ISP)
    print(f"     +{pen} m/s ({lbl}): orbital mass {m:5.1f} t -> payload {m-r4_stage:5.1f} t (article ~{claim})")

print("\n-- expendable upper stage on the same booster --")
chk("payload with 40 t expendable stage", 230, r4_orbit - 40, unit="t")
for isp_m in (365, 380):
    m_tmi = mf_after(r4_orbit, 3600, isp_m)
    print(f"     +3600 m/s TMI at ISP {isp_m}: {m_tmi:5.1f} t -> {m_tmi-40:5.1f} t to Mars (article: >50 t)")

print("\n" + "=" * 100)
print("8. THOUGHT EXPERIMENT: STAGING AT 12 000 km/h  (Raptor 3 upper stage)")
print("=" * 100)
dv1b = dv1 + (12000 - 10000) * KMH
chk("R33 ascent dv", None, dv1b, unit="m/s")
rest_b = GLOW2 * exp(-dv1b / ve(340))
chk("mass left at staging", None, rest_b, unit="t")
brake_b = exp((12000 - 5300) * KMH / ve(350)) - 1
s1_sep = 300 * (1 + land_frac) * (1 + brake_b)
chk("stage-1 mass at separation", None, s1_sep, unit="t")
chk("stage-1 return propellant", 300, s1_sep - 300, unit="t", tol=0.10)
us_total = rest_b - s1_sep
chk("upper stage total mass (article: 942 t)", 942, us_total, unit="t", tol=0.05)
dv2b = dv2 - (12000 - 10000) * KMH
chk("upper stage dv", None, dv2b, unit="m/s")
orb_b = mf_after(942, dv2b, SS_ISP)
chk("mass to orbit from 942 t", 231, orb_b, unit="t")
chk("propellant burned", 711, 942 - orb_b, unit="t")
chk("stage mass scaled linearly (160 t * 711/1022)", 111, 160 * 711 / 1022, unit="t")
chk("payload", 120, orb_b - 111, unit="t")
chk("full stage-1 mass (5850-942)", 4908, GLOW2 - 942, unit="t")
print("\n-- sensitivity: stage 1 dry 400 t --")
chk("mass left for upper stage (article: 742 t)", 742, rest_b - 400 * (1 + land_frac) * (1 + brake_b), unit="t", tol=0.10)
orb_c = mf_after(742, dv2b, SS_ISP)
chk("mass to orbit", 182, orb_c, unit="t")
chk("propellant", 560, 742 - orb_c, unit="t")
chk("stage mass scaled", None, 160 * (742 - orb_c) / 1022, unit="t")
chk("payload", 94, orb_c - 160 * (742 - orb_c) / 1022, unit="t")

print("\n" + "=" * 100)
print("9. INDEPENDENT CHECK: IS THE ARTICLE'S THESIS RIGHT? SWEEP THE STAGING SPEED")
print("=" * 100)
print("Model: GLOW 5850 t, stage-1 dry 300 t fixed, stage-2 dry+landing prop scales")
print("linearly with its propellant (250 t per 1600 t), stage-1 brakes to 5300 km/h")
print("and lands with 500 m/s. Ascent dv = SH's 2795 m/s + (v_stage - 6000 km/h).")
print(f"{'v_stage':>9} {'dv1':>7} {'dv2':>7} {'m_sep':>8} {'s1_ret':>8} {'m_orbit':>8} {'stage2':>8} {'payload':>8}")
best = None
for v_kmh in range(6000, 16001, 500):
    d1 = dv_sh + (v_kmh - 6000) * KMH
    d2 = 9404.0 - d1                      # keep the total mission budget constant
    m_after = GLOW2 * exp(-d1 / ve(340))
    bf = exp(max(0.0, (v_kmh - 5300) * KMH) / ve(350)) - 1
    s1 = 300 * (1 + land_frac) * (1 + bf)
    avail = m_after - s1
    if avail <= 0:
        break
    orb = mf_after(avail, d2, SS_ISP)
    stage2 = 250 * (avail - orb) / 1600
    pay = orb - stage2
    star = ""
    if best is None or pay > best[1]:
        best, star = (v_kmh, pay), ""
    print(f"{v_kmh:>9} {d1:>7.0f} {d2:>7.0f} {m_after:>8.0f} {s1-300:>8.0f} {orb:>8.0f} {stage2:>8.0f} {pay:>8.1f}{star}")
print(f"\n  optimum in this model: staging at {best[0]} km/h -> {best[1]:.0f} t payload")
print(f"  actual Starship (6000 km/h) in the same model gives the ~40 t the article computes")

print("\n" + "=" * 100)
print("10. CLASSICAL OPTIMAL STAGING (equal ISP, equal structural coefficient)")
print("=" * 100)
print("For two stages with the same ve and the same structural coefficient eps,")
print("maximum payload is at an EQUAL dv split. Numeric proof for total dv 9404 m/s:")
eps, isp_e = 0.08, 350.0
total = 9404.0
best2 = (0, 0)
for share in [i / 100 for i in range(20, 81, 5)]:
    d1, d2 = total * share, total * (1 - share)
    # work backwards from 1 t payload
    def stage_back(m_top, d):
        r = exp(d / ve(isp_e))
        # m_top + m_struct + m_prop, m_struct = eps*(m_struct+m_prop)
        return m_top * r * (1 - eps) / (1 - eps * r) if (1 - eps * r) > 0 else float("inf")
    m1 = stage_back(1.0, d2)
    m0 = stage_back(m1, d1)
    pay_frac = 1 / m0 if m0 != float("inf") else 0
    if pay_frac > best2[1]:
        best2 = (share, pay_frac)
    print(f"     stage-1 share {share:.0%}: payload fraction {pay_frac*100:6.3f} %")
print(f"  -> optimum at stage-1 share {best2[0]:.0%}  (theory says 50 %)")
