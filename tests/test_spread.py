"""Pin the section "The first song is the cohort only in the model" (added
2026-11-18) to results/spread_check.json, and the parts of it that have a
closed form to the colony model's constants.  Standard library + pytest.
"""
import json
import math
import os
import re
from statistics import NormalDist

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")

DD_EGG_TO_ADULT, T_BASE, EGG_SHARE, DESIGN_TEMP = 765.0, 15.0, 0.26, 30.0
ROOMS = (("on setpoint", "on setpoint"), ("1.5 C cold", "1.5 °C cold"), ("1.5 C warm", "1.5 °C warm"))
POLICIES = (("calendar", "calendar"), ("camera", "camera"), ("full", "camera + mic, first song"),
            ("count", "camera + mic, male count"), ("thermometer", "camera + thermometer"))


def load(name):
    with open(os.path.join(RES, name)) as f:
        return json.load(f)


def readme():
    with open(os.path.join(ROOT, "README.md"), encoding="utf-8") as f:
        return f.read()


def flat(text):
    return " ".join(text.split())


J = load("spread_check.json")
TEXT = readme()
FLAT = flat(TEXT)


# ------------------------------------------------------------------ formatters

def g(c):
    return "%.0f ± %.0f" % (c["biomass_g"]["mean"], c["biomass_g"]["sd"])


def pct(x):
    v = 100 * x
    return "%.0f %%" % (0 if abs(v) < 0.5 else v)


def row_a(room, label, s):
    c = J["cells"][room]["%.2f" % s]["full"]
    d = c["vs_calendar"]["biomass_g"]
    return "| %s | %.2f | %s | %.1f | %s | %+.0f ± %.0f g |" % (
        label, s, g(c), c["harvest_day"]["mean"], pct(c["fraction_harvested_as_adults"]),
        d["diff"], d["ci95_half"])


def row_b(room, label, pol, plabel):
    c = J["cells"][room]["0.10"][pol]
    return "| %s | %s | %s | %.2f | %.1f | %s |" % (
        label, plabel, g(c), c["fcr"]["mean"], c["harvest_day"]["mean"],
        pct(c["fraction_harvested_as_adults"]))


def row_c(label, c):
    return "| %s | %s | %.2f | %.1f | %s | %d |" % (
        label, g(c), c["fcr"]["mean"], c["harvest_day"]["mean"],
        pct(c["fraction_harvested_as_adults"]), c["never_triggered"])


# ----------------------------------------------------------------------- tests

def test_zero_spread_reproduces_the_policy_table():
    """Spread 0 == policies.json, and the thermometer == the first song, run for run."""
    stored = load("policies.json")
    worst = 0.0
    for room, _ in ROOMS:
        cell = J["cells"][room]["0.00"]
        for pol in ("calendar", "camera", "full"):
            for k in ("biomass_g", "fcr", "harvest_day"):
                worst = max(worst, abs(cell[pol][k]["mean"] - stored[room][pol][k]["mean"]),
                            abs(cell[pol][k]["sd"] - stored[room][pol][k]["sd"]))
            assert cell[pol]["fraction_harvested_as_adults"] == stored[room][pol]["fraction_harvested_as_adults"]
        p = cell["thermometer"]["vs_full_paired"]
        for k in ("biomass_g", "fcr", "harvest_day"):
            assert p[k]["diff"] == 0.0 and p[k]["ci95_half"] == 0.0, (room, k, p[k])
        assert p["biomass_g"]["n"] == 300
    assert worst < 1e-9, worst
    assert "reproduces to 2 × 10⁻¹³ g" in FLAT and worst < 3e-13
    assert "paired difference 0.0 ± 0.0 g, 0.00 days" in FLAT


def test_closed_form_of_the_first_song():
    """Where the fastest of K stratified lognormal classes matures, and what the
    median animal weighs then; recomputed from the model constants."""
    K = J["K"]
    assert K == 40
    z = NormalDist().inv_cdf((K - 0.5) / K)
    rows = {cf["spread"]: cf for cf in J["closed_form"]}
    want = {0.05: (684, 46, 0.89, 67), 0.10: (611, 41, 0.80, 44), 0.15: (547, 36, 0.71, 28)}
    for s, (dd, day, prog, mass) in want.items():
        cf = rows[s]
        r_max = math.exp(s * z)
        dd_first = DD_EGG_TO_ADULT / r_max
        q = (dd_first / DD_EGG_TO_ADULT - EGG_SHARE) / (1 - EGG_SHARE)
        assert abs(cf["fastest_rate"] - r_max) < 1e-9
        assert abs(cf["dd_at_first_song"] - dd_first) < 1e-9
        assert abs(cf["day_at_first_song_30C"] - dd_first / (DESIGN_TEMP - T_BASE)) < 1e-9
        assert abs(cf["median_class_mass_share"] - q ** 2.6) < 1e-9
        assert round(dd_first) == dd and round(dd_first / 15) == day
        assert round(cf["median_class_progress"], 2) == prog and round(100 * q ** 2.6) == mass
        assert cf["first_class_quantile"] == 1 - 0.5 / K
    assert "matures at **684 / 611 / 547** degree-days instead of 765" in FLAT
    assert "day 46 / 41 / 36 instead of 51" in FLAT
    assert "0.89 / 0.80 / 0.71 of its development" in FLAT
    assert "carries **67 / 44 / 28 %** of adult mass" in FLAT
    assert "98.75th percentile" in FLAT
    # the tenths: ratio of the 90th to the 10th percentile rate
    z90 = NormalDist().inv_cdf(0.9)
    tenths = {s: round(100 * (math.exp(2 * z90 * s) - 1)) for s in (0.05, 0.10, 0.15)}
    assert tenths == {0.05: 14, 0.10: 29, 0.15: 47}, tenths
    assert "differ by about 14 % in development rate" in FLAT
    assert "At 0.10 (29 % between the tenths)" in FLAT and "At 0.15 (47 %)" in FLAT


def test_first_song_table_and_prose():
    for room, label in ROOMS:
        for s in J["spreads"]:
            assert row_a(room, label, s) in TEXT, row_a(room, label, s)
    cells = J["cells"]
    # males and adult share at the first song, spread > 0
    males = [cells[r]["%.2f" % s]["full"]["males_at_first_song"] for r, _ in ROOMS for s in (0.05, 0.10, 0.15)]
    adult = [cells[r]["%.2f" % s]["full"]["adult_fraction_at_first_song"] for r, _ in ROOMS for s in (0.05, 0.10, 0.15)]
    assert round(min(males)) == 41 and round(max(males)) == 47, (min(males), max(males))
    assert min(males) > 40
    assert all(abs(a - 1 / 40) < 0.002 for a in adult)
    assert "2.5 % of the bin adult and about 41 to 47 males calling" in FLAT
    # cold room, +354 ± 12 -> +12 ± 12; warm +207 -> -97
    cold0 = cells["1.5 C cold"]["0.00"]["full"]["vs_calendar"]["biomass_g"]
    cold5 = cells["1.5 C cold"]["0.05"]["full"]["vs_calendar"]["biomass_g"]
    assert "%+.0f ± %.0f g to %+.0f ± %.0f g" % (cold0["diff"], cold0["ci95_half"], cold5["diff"], cold5["ci95_half"]) == "+354 ± 12 g to +12 ± 12 g"
    assert "+354 ± 12 g to +12 ± 12 g" in FLAT
    warm0 = cells["1.5 C warm"]["0.00"]["full"]["vs_calendar"]["biomass_g"]["diff"]
    warm5 = cells["1.5 C warm"]["0.05"]["full"]["vs_calendar"]["biomass_g"]["diff"]
    assert (round(warm0), round(warm5)) == (207, -97)
    assert "from +207 to −97 g" in FLAT
    # spread 0.10: behind the calendar in every room by 23 to 33 %, 2 to 3 % adult
    rel = [100 * cells[r]["0.10"]["full"]["vs_calendar"]["biomass_g"]["diff"] / cells[r]["0.10"]["calendar"]["biomass_g"]["mean"]
           for r, _ in ROOMS]
    assert all(v < 0 for v in rel) and (round(-max(rel)), round(-min(rel))) == (23, 33), rel
    ad = [round(100 * cells[r]["0.10"]["full"]["fraction_harvested_as_adults"]) for r, _ in ROOMS]
    assert min(ad) == 2 and max(ad) == 3, ad
    assert "by 23 to 33 %, harvesting a bin that is 2 to 3 % adult" in FLAT
    # spread 0.15: 43 % of the spread-0 harvest in every room
    share = [round(100 * cells[r]["0.15"]["full"]["biomass_g"]["mean"] / cells[r]["0.00"]["full"]["biomass_g"]["mean"]) for r, _ in ROOMS]
    assert share == [43, 43, 44], share
    assert "harvests 43 to 44 % of what it harvests without spread" in FLAT
    assert round(cells["1.5 C cold"]["0.10"]["full"]["fcr"]["mean"], 2) == 1.64
    assert "to 1.64 in the cold room at 0.10" in FLAT


def test_three_triggers_table_and_readings():
    for room, label in ROOMS:
        for pol, plabel in POLICIES:
            assert row_b(room, label, pol, plabel) in TEXT, row_b(room, label, pol, plabel)
    cold = J["cells"]["1.5 C cold"]["0.10"]
    th, ct, fs = cold["thermometer"], cold["count"], cold["full"]
    assert round(th["harvest_day"]["mean"], 1) == round(J["cells"]["1.5 C cold"]["0.00"]["full"]["harvest_day"]["mean"], 1) == 58.2
    p = th["vs_full_paired"]["biomass_g"]
    assert "%.0f ± %.0f g" % (p["diff"], p["ci95_half"]) == "534 ± 3 g"
    w = th["vs_calendar"]["biomass_g"]
    assert "%.0f ± %.0f g" % (w["diff"], w["ci95_half"]) == "264 ± 12 g"
    assert "**534 ± 3 g** ahead of the first-song arm in the same runs and 264 ± 12 g ahead of the calendar" in FLAT
    # the count trigger: most grams and >= 95 % adults in every room; 11 days past the median moult in the cold room
    best = []
    for room, _ in ROOMS:
        c = J["cells"][room]["0.10"]
        best.append(c["count"]["biomass_g"]["mean"] == max(c[p]["biomass_g"]["mean"] for p, _ in POLICIES))
        assert round(100 * c["count"]["fraction_harvested_as_adults"]) == 97
    assert best == [True, True, False], best
    warm = J["cells"]["1.5 C warm"]["0.10"]
    assert round(warm["camera"]["biomass_g"]["mean"] - warm["count"]["biomass_g"]["mean"]) == 32
    assert "the most grams in two of the three (in the warm room the camera arm on the calendar beats it by 32 g)" in FLAT
    assert round(ct["harvest_day"]["mean"] - th["harvest_day"]["mean"]) == 11
    assert round(100 * (ct["fcr"]["mean"] / th["fcr"]["mean"] - 1)) == 58
    assert round(100 * (ct["biomass_g"]["mean"] / th["biomass_g"]["mean"] - 1), 1) == 1.3
    assert "FCR 3.57 against the thermometer's 2.27, which is 58 % more feed for 1.3 % more harvest" in FLAT
    # the silence estimator at the first song
    floor = (1 - 0.188) ** 40
    assert 1.5e-4 < floor < 2.5e-4 and 0.4 < 2400 * floor < 0.7
    assert "(1 − 0.188)⁴⁰ ≈ 2 × 10⁻⁴ of frames or less, about half a frame in a ten-minute window of 2 400" in FLAT
    # the estimator's stored bias and spread, as the caption says
    chorus = load("chorus.json")["counts"]
    bias = sum(r["energy_rel_bias"] for r in chorus) / len(chorus)
    assert abs(J["energy_bias_used"] - bias) < 1e-12 and round(100 * bias, 1) == -8.6
    assert round(100 * [r for r in chorus if r["n_males"] == 120][0]["energy_rel_sd"], 1) == 5.3
    assert J["count_threshold"] == 0.45
    assert "stored bias (−8.6 %, the mean over the rows of `chorus.json`) and its stored spread (5.3 % at 120 males" in FLAT


def test_sensitivity_table_and_readings():
    cb = J["count_bias_sweep"]["1.5 C cold"]
    tb = J["thermometer_bias_sweep"]["1.5 C cold"]
    rows = [
        row_c("male count, estimator reads 20 % low", cb["-0.20"]),
        row_c("male count, estimator reads 8.6 % low (as calibrated)", cb["stored"]),
        row_c("male count, estimator unbiased", cb["+0.00"]),
        row_c("male count, estimator reads 20 % high", cb["+0.20"]),
        row_c("thermometer reads −1.0 °C", tb["-1.0"]),
        row_c("thermometer reads −0.5 °C", tb["-0.5"]),
        row_c("thermometer, true temperature", tb["+0.0"]),
        row_c("thermometer reads +0.5 °C", tb["+0.5"]),
        row_c("thermometer reads +1.0 °C", tb["+1.0"]),
    ]
    for r in rows:
        assert r in TEXT, r
    assert cb["stored"]["count_bias"] == J["energy_bias_used"]
    assert cb["-0.20"]["never_triggered"] == 59 and all(cb[k]["never_triggered"] == 0 for k in ("stored", "+0.00", "+0.20"))
    assert "in **59 of 300** runs the bin waits out all 90 days and the arm averages 1358 g at FCR 5.35" in FLAT
    assert round(100 * cb["+0.20"]["fraction_harvested_as_adults"]) == 82 and "fires at 82 % adult" in FLAT
    assert round(cb["stored"]["harvest_day"]["mean"] - cb["+0.00"]["harvest_day"]["mean"]) == 3
    assert round(cb["stored"]["fcr"]["mean"] - cb["+0.00"]["fcr"]["mean"], 2) == 0.44
    assert "costs 3 days and 0.44 of FCR against an unbiased estimator" in FLAT
    t0 = tb["+0.0"]
    days = [abs(tb[k]["harvest_day"]["mean"] - t0["harvest_day"]["mean"]) for k in ("-0.5", "+0.5")]
    pts = [abs(100 * (tb[k]["fraction_harvested_as_adults"] - t0["fraction_harvested_as_adults"])) for k in ("-0.5", "+0.5")]
    assert [round(d) for d in days] == [2, 2] and sorted(round(p) for p in pts) == [13, 14], (days, pts)
    assert "half a degree either way is about two days and 13 to 14 points of adult share" in FLAT
    fs = J["cells"]["1.5 C cold"]["0.10"]["full"]["biomass_g"]["mean"]
    assert round(100 * tb["+1.0"]["fraction_harvested_as_adults"]) == 33
    assert round(tb["+1.0"]["biomass_g"]["mean"]) == 1305 and round(tb["+1.0"]["biomass_g"]["mean"] - fs) == 411
    assert "harvests at 33 % adult and 1305 g, still **411 g** ahead of the first song" in FLAT
    # the thermometer bias sweep is monotone in day and adult share in every room
    for room, _ in ROOMS:
        t = J["thermometer_bias_sweep"][room]
        seq = [t[k] for k in ("-1.0", "-0.5", "+0.0", "+0.5", "+1.0")]
        assert all(a["harvest_day"]["mean"] > b["harvest_day"]["mean"] for a, b in zip(seq, seq[1:]))
        assert all(a["fraction_harvested_as_adults"] > b["fraction_harvested_as_adults"] for a, b in zip(seq, seq[1:]))


def test_pointers_and_known_gap():
    assert "if the cohort matures as one" in FLAT
    assert "Every number in this section is for a colony with no spread of development" in FLAT
    assert "harvests nymphs (2 to 3 % adult at a log-sd of 0.10)" in FLAT
    assert "The fourth was the policy table itself, on 18 November 2026." in FLAT
    assert "`spread_check.json`" in TEXT and "`tests/test_spread.py`" in TEXT
    assert J["n_runs"] == 300 and J["spreads"] == [0.0, 0.05, 0.10, 0.15]
    assert re.search(r"300 runs per cell", FLAT)
