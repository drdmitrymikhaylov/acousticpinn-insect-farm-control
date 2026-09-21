"""Pin every number on the project page to the files in results/.

Run: python -m pytest tests/   (numpy only)
"""
import json
import os

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")


def load(name):
    with open(os.path.join(RES, name)) as f:
        return json.load(f)


def close(a, b, tol):
    assert abs(a - b) <= tol, (a, b, tol)


# ------------------------------------------------------------ song measurements

def test_recording_counts_319_313_311_89():
    s = load("song_summary.json")
    assert (s["n_downloaded"], s["n_orthoptera"], s["n_carrier"], s["n_pulse_resolved"]) == (319, 313, 311, 89)
    assert s["dropped_non_orthoptera"] == ["Acris gryllus"]
    m = load("song_measurements.json")
    assert len(m) == 319
    assert sum(1 for r in m if r["taxon"] == "Acris gryllus") == 319 - 313
    orth = [r for r in m if r["taxon"] != "Acris gryllus"]
    assert sum(1 for r in orth if r.get("carrier_snr_db") is not None and r["carrier_snr_db"] >= s["snr_min_db"]) == 311


def test_song_table_mean_sd_per_taxon():
    s = load("song_summary.json")["taxa"]
    want = {  # taxon: n, carrier mean, sd, pulse n, pulse mean, sd, duty
        "Gryllus bimaculatus": (50, 4.75, 1.09, 3, 132.8, 19.8, 0.23),
        "Gryllus campestris": (50, 4.47, 0.94, 4, 45.0, 23.4, 0.21),
        "Acheta domesticus": (50, 3.73, 1.93, 5, 74.9, 34.2, 0.16),
        "Oecanthus fultoni": (49, 2.62, 1.35, 9, 52.0, 18.7, 0.17),
        "Neocurtilla hexadactyla": (39, 3.02, 2.50, 37, 74.2, 25.6, 0.23),
        "Oecanthus pellucens": (27, 2.86, 1.31, 20, 32.2, 8.4, 0.16),
    }
    for tax, (n, cm, cs, pn, pm, ps, duty) in want.items():
        t = s[tax]
        assert t["n_carrier"] == n and t["n_pulse"] == pn
        close(t["carrier_khz"][0], cm, 0.005); close(t["carrier_khz"][1], cs, 0.005)
        close(t["pulse_rate_hz"][0], pm, 0.05); close(t["pulse_rate_hz"][1], ps, 0.05)
        close(t["duty_cycle"][0], duty, 0.005)


def test_carrier_clusters_match_measurements():
    """The mixture table: medians, in-band counts and means recomputed from the rows."""
    m = load("song_measurements.json")
    c = load("carrier_clusters.json")
    want = {  # taxon: median, in-band n, in-band mean, in-band sd, below 2.5, above 6
        "Acheta domesticus": (4.28, 27, 4.53, 0.34, 19, 3),
        "Gryllus bimaculatus": (4.84, 45, 4.83, 0.38, 1, 1),
        "Gryllus campestris": (4.71, 43, 4.75, 0.27, 4, 1),
        "Oecanthus fultoni": (2.24, 45, 2.25, 0.36, 34, 3),
        "Oecanthus pellucens": (2.69, 26, 2.62, 0.42, 8, 1),
        "Neocurtilla hexadactyla": (1.85, 32, 1.89, 0.33, 30, 7),
    }
    for tax, (med, nb, bm, bs, lo, hi) in want.items():
        r = c["taxa"][tax]
        v = np.array([x["carrier_hz"] for x in m if x["taxon"] == tax
                      and x.get("carrier_snr_db") is not None and x["carrier_snr_db"] >= 10]) / 1000
        close(float(np.median(v)), med, 0.005)
        b0, b1 = r["band_khz"]
        band = (v >= b0) & (v <= b1)
        assert int(band.sum()) == nb == r["n_in_band"]
        close(float(v[band].mean()), bm, 0.005); close(float(v[band].std(ddof=1)), bs, 0.005)
        assert int((v < 2.5).sum()) == lo == r["n_below_2p5"]
        assert int((v > 6).sum()) == hi == r["n_above_6"]


# ------------------------------------------------------------ chorus

def test_chorus_table_and_energy_bias():
    c = load("chorus.json")
    close(c["duty_cycle"], 0.19, 0.005)
    rows = {r["n_males"]: r for r in c["counts"]}
    for n, sil, en in ((5, 0.024, 0.245), (12, 0.025, 0.161), (30, 0.084, 0.106)):
        close(rows[n]["silence_rel_sd"], sil, 0.0006); close(rows[n]["energy_rel_sd"], en, 0.0006)
    for n, en in ((50, 0.080), (120, 0.053)):
        assert rows[n]["silence_usable"] < 0.1
        close(rows[n]["energy_rel_sd"], en, 0.0006)
    bias = [r["energy_rel_bias"] for r in c["counts"]]
    assert min(bias) > -0.11 and max(bias) < -0.075          # 8 % low at every count
    assert all(abs(r["silence_rel_bias"]) < 0.005 for r in c["counts"] if r["n_males"] <= 20)


# ------------------------------------------------------------ policies

TABLE = {  # (condition, policy): harvest g, sd, FCR, day
    ("on setpoint", "calendar"): (1619, 85, 1.94, 52.0),
    ("on setpoint", "camera"): (1627, 90, 1.99, 52.0),
    ("on setpoint", "full"): (1621, 89, 2.07, 52.5),
    ("1.5 C cold", "calendar"): (1203, 77, 1.77, 52.0),
    ("1.5 C cold", "camera"): (1199, 75, 1.77, 52.0),
    ("1.5 C cold", "full"): (1557, 79, 2.07, 58.2),
    ("1.5 C warm", "calendar"): (1472, 59, 2.21, 52.0),
    ("1.5 C warm", "camera"): (1625, 90, 2.81, 52.0),
    ("1.5 C warm", "full"): (1678, 98, 2.11, 47.9),
}


def test_policy_table():
    p = load("policies.json")
    for (cond, pol), (g, sd, fcr, day) in TABLE.items():
        q = p[cond][pol]
        assert q["n"] == 300
        close(q["biomass_g"]["mean"], g, 0.5); close(q["biomass_g"]["sd"], sd, 0.5)
        close(q["fcr"]["mean"], fcr, 0.005); close(q["harvest_day"]["mean"], day, 0.05)
    assert p["1.5 C cold"]["calendar"]["fraction_harvested_as_adults"] == 0.0
    assert p["1.5 C cold"]["camera"]["fraction_harvested_as_adults"] == 0.0
    assert p["1.5 C cold"]["full"]["fraction_harvested_as_adults"] == 1.0


def test_policy_differences_with_intervals():
    p = load("policies.json")
    d = load("policy_differences.json")
    want = {  # (cond, pol): biomass diff, ci, fcr diff, ci
        ("on setpoint", "camera"): (8, 14, 0.06, 0.01),
        ("on setpoint", "full"): (2, 14, 0.14, 0.01),
        ("1.5 C cold", "full"): (354, 12, 0.30, 0.01),
        ("1.5 C warm", "camera"): (153, 12, 0.60, 0.01),
        ("1.5 C warm", "full"): (207, 13, -0.10, 0.01),
    }
    for (cond, pol), (bd, bci, fd, fci) in want.items():
        r = d[cond][pol]
        cal, q = p[cond]["calendar"], p[cond][pol]
        diff = q["biomass_g"]["mean"] - cal["biomass_g"]["mean"]
        se = np.sqrt(q["biomass_g"]["sd"] ** 2 / 300 + cal["biomass_g"]["sd"] ** 2 / 300)
        close(r["biomass_g"]["diff_vs_calendar"], diff, 1e-9)
        close(r["biomass_g"]["ci95_half"], 1.96 * se, 1e-9)
        close(diff, bd, 0.5); close(1.96 * se, bci, 0.5)
        close(r["fcr"]["diff_vs_calendar"], fd, 0.005); close(r["fcr"]["ci95_half"], fci, 0.005)
    assert not d["on setpoint"]["camera"]["biomass_g"]["excludes_zero"]
    assert not d["on setpoint"]["full"]["biomass_g"]["excludes_zero"]
    assert d["on setpoint"]["full"]["fcr"]["excludes_zero"]
    close(d["1.5 C cold"]["full"]["biomass_g"]["rel_pct"], 29.4, 0.05)
    close(d["1.5 C warm"]["camera"]["biomass_g"]["rel_pct"], 10.4, 0.05)
    close(d["1.5 C warm"]["full"]["biomass_g"]["rel_pct"], 14.0, 0.05)
