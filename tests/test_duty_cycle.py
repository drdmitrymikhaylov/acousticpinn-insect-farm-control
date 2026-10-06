"""Pin the duty-cycle section of the page to results/duty_cycle_check.json,
and recompute from results/song_measurements.json whatever can be recomputed
without the audio or the private pipeline.

Run: python -m pytest tests/   (numpy, scipy)
"""
import json
import math
import os

import numpy as np
from scipy.stats import spearmanr

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")

TABLE_TAXA = ["Acheta domesticus", "Gryllus bimaculatus", "Gryllus campestris",
              "Oecanthus fultoni", "Oecanthus pellucens", "Neocurtilla hexadactyla"]


def load(name):
    with open(os.path.join(RES, name)) as f:
        return json.load(f)


def readme():
    with open(os.path.join(ROOT, "README.md"), encoding="utf-8") as f:
        return " ".join(f.read().split())


def close(a, b, tol=1e-9):
    assert abs(a - b) <= tol, (a, b, tol)


def used_rows():
    """The recordings chorus.py takes its duty cycle from."""
    return [r for r in load("song_measurements.json")
            if r.get("carrier_snr_db", 0) >= 10.0 and r.get("duty_cycle")]


def pct(x, nd=1):
    return "%.*f %%" % (nd, 100 * x)


def taxon_row(name, t):
    return "| *%s* | %d | %.3f | %.3f – %.3f | %.2f |" % (
        name, t["n"], t["median"], t["q25"], t["q75"], t["reading_at_median"])


def mixed_row(pub, mix):
    return "| %d | %s | **%s** | %s | %s |" % (
        mix["n_males"], pct(pub["silence_rel_sd"]), pct(mix["silence_rel_sd_pooled_duty"]),
        pct(pub["energy_rel_sd"]), pct(mix["energy_rel_sd"]))


def test_pool_median_interval_and_quartiles_recomputed():
    c = load("duty_cycle_check.json")
    rows = used_rows()
    d = np.array([r["duty_cycle"] for r in rows])
    ref = load("chorus.json")["duty_cycle"]
    close(c["duty_cycle_assumed"], ref)
    close(float(np.median(d)), ref)
    p = c["pool"]
    assert p["n"] == len(rows) == 316 == load("chorus.json")["n_recordings"]
    frog = [r for r in rows if r["taxon"] == "Acris gryllus"]
    assert p["n_frog"] == len(frog) == 6
    close(p["median_orthoptera_only"], float(np.median([r["duty_cycle"] for r in rows
                                                        if r["taxon"] != "Acris gryllus"])))
    s = np.sort(d)
    lo = int(math.floor(316 / 2 - 1.96 * math.sqrt(316) / 2))
    hi = int(math.ceil(316 / 2 + 1.96 * math.sqrt(316) / 2))
    close(p["median_ci95_order_stat"][0], float(s[lo - 1]))
    close(p["median_ci95_order_stat"][1], float(s[hi - 1]))
    read = lambda x: math.log(1 - x) / math.log(1 - ref)
    close(p["reading_at_q25"], read(float(np.percentile(d, 25))))
    close(p["reading_at_q75"], read(float(np.percentile(d, 75))))
    close(p["reading_at_median_ci"][0], read(float(s[lo - 1])))
    close(p["reading_at_median_ci"][1], read(float(s[hi - 1])))
    close(p["count_change_per_duty_point"], 0.01 / ((1 - ref) * abs(math.log(1 - ref))))
    text = readme()
    for phrase in (
        "median of 316 recordings",
        "Without them it is %.3f" % p["median_orthoptera_only"],
        "%.3f to %.3f, which is already %.2f to %.2f of the true count" % (
            *p["median_ci95_order_stat"], *p["reading_at_median_ci"]),
        "quartiles are %.2f and %.2f" % (p["q25"], p["q75"]),
        "reads **%.2f** of its males" % p["reading_at_q25"],
        "upper quartile **%.2f**" % p["reading_at_q75"],
        "is **%s** of the count" % pct(p["count_change_per_duty_point"]),
        "needs *d* to ± %.3f" % p["duty_tolerance_for_5pct_count"],
    ):
        assert phrase in text, phrase


def test_taxon_rows_recomputed_and_on_the_page():
    c = load("duty_cycle_check.json")
    rows = used_rows()
    ref = c["duty_cycle_assumed"]
    text = readme()
    for name in TABLE_TAXA:
        v = np.array([r["duty_cycle"] for r in rows if r["taxon"] == name])
        t = c["taxa"][name]
        assert t["n"] == v.size
        close(t["median"], float(np.median(v)))
        close(t["q25"], float(np.percentile(v, 25)))
        close(t["q75"], float(np.percentile(v, 75)))
        close(t["reading_at_median"], math.log(1 - np.median(v)) / math.log(1 - ref))
        L = np.log(1 - v)
        close(t["reading_mixed_bin"], float(L.mean() / math.log(1 - ref)))
        assert taxon_row(name, t) in text, taxon_row(name, t)
    farmed = c["taxa"]["Acheta domesticus"]
    assert round(100 * (1 - farmed["reading_at_median"])) == 11
    assert "reads 11 % low on its own median" in text
    assert round(100 * (1 - farmed["reading_mixed_bin"])) == 13
    assert "and 13 % low when the males in the bin differ" in text
    # half the bin male, camera exact: the sex ratio the page quotes
    assert round(100 * 0.5 * farmed["reading_mixed_bin"]) == 44
    assert "reads as 44 % male" in text


def test_duty_cycle_follows_signal_to_noise():
    c = load("duty_cycle_check.json")["snr"]
    rows = used_rows()
    d = np.array([r["duty_cycle"] for r in rows])
    snr = np.array([r["carrier_snr_db"] for r in rows])
    rho, p = spearmanr(d, snr)
    close(c["spearman_rho"], float(rho), 1e-9)
    assert p < 1e-15
    f = np.array([r["taxon"] == "Acheta domesticus" for r in rows])
    rho_f, p_f = spearmanr(d[f], snr[f])
    close(c["farmed_species"]["spearman_rho"], float(rho_f), 1e-9)
    assert 0.0005 < p_f < 0.0015
    terc = np.array_split(np.argsort(snr, kind="stable"), 3)
    med = [float(np.median(d[ix])) for ix in terc]
    for got, want in zip(c["terciles"], med):
        close(got["median_duty"], want)
    assert med[0] < med[1] < med[2]
    text = readme()
    for phrase in (
        "ρ = **%.2f**" % c["spearman_rho"],
        "and %.2f within the 50 *Acheta domesticus* recordings" % c["farmed_species"]["spearman_rho"],
        "the median is %.2f, %.2f and %.2f" % tuple(med),
        "which is %.2f, %.2f and %.2f of the count" % tuple(t["reading_at_median"] for t in c["terciles"]),
    ):
        assert phrase in text, phrase


def test_measure_floor_and_ceiling():
    c = load("duty_cycle_check.json")["measure_floor"]
    d = np.array([r["duty_cycle"] for r in used_rows()])
    noise = c["band_noise_only"]["mean"]
    assert round(noise, 2) == 0.03 and round(c["continuous_tone_in_noise"]["mean"], 2) == 0.02
    assert c["n_recordings_below_twice_noise_floor"] == int((d <= 2 * noise).sum()) == 27
    assert d.max() < c["ceiling_by_construction"] == 0.5
    text = readme()
    assert "returns 0.03 on band noise with no song in it and 0.02 on an uninterrupted tone" in text
    assert "27 of the 316 recordings sit below twice the noise value" in text


def test_mixed_bin_table_on_the_page():
    c = load("duty_cycle_check.json")["mixed_bin"]
    pub = {r["n_males"]: r for r in load("chorus.json")["counts"]}
    mix = {r["n_males"]: r for r in c["counts"]}
    assert c["n_recordings"] == 50 and c["windows"] == 200
    text = readme()
    for n in (5, 12, 30):
        assert mixed_row(pub[n], mix[n]) in text, mixed_row(pub[n], mix[n])
    # still ahead of the energy estimator at every count, by 1.2 to 1.5 and not by ten
    ratios = [r["energy_rel_sd"] / r["silence_rel_sd_pooled_duty"] for r in c["counts"]]
    assert 1.15 < min(ratios) and max(ratios) < 1.55
    assert pub[5]["energy_rel_sd"] / pub[5]["silence_rel_sd"] > 10
    assert "by a factor of 1.2 to 1.5, not ten" in text
    # the biases quoted under the table, over all eight counts
    def span(key):
        v = [abs(r[key]) for r in c["counts"]]
        assert all(r[key] < 0 for r in c["counts"])
        return round(100 * min(v)), round(100 * max(v))
    assert span("silence_rel_bias_pooled_duty") == (13, 17)
    assert span("silence_rel_bias_species_duty") == (2, 7)
    assert span("energy_rel_bias") == (19, 26)
    assert "reads 13 to 17 % low" in text and "it reads 2 to 7 % low" in text
    assert "The energy estimator, calibrated at 0.188, reads 19 to 26 % low" in text
    # the spread is set by who is in the bin: prediction from the recordings alone
    for n, want in ((5, 21), (12, 14), (30, 9)):
        assert round(100 * mix[n]["silence_rel_sd_predicted"]) == want
    assert "21 %, 14 % and 9 %" in text


def test_energy_bias_is_the_calibration_draw():
    c = load("duty_cycle_check.json")["energy_calibration"]
    ch = load("chorus.json")
    close(c["expected"], ch["duty_cycle"])
    close(c["ratio"], c["constant"] / c["expected"])
    big = [r for r in ch["counts"] if r["n_males"] == 120][0]
    # at 120 males the level average is exact to 0.4 %, so the bias left is the constant
    close(c["implied_energy_bias"], big["energy_rel_bias"], 0.003)
    assert round(100 * (c["ratio"] - 1), 1) == 8.6
    assert round(c["z"], 1) == 2.0
    assert round(100 * c["bias_sd_if_calibrated_on_k_males"]["1"]) == 60
    assert round(100 * c["bias_sd_if_calibrated_on_k_males"]["10"]) == 19
    text = readme()
    for phrase in ("averaged 8.6 % above", "2.0 standard errors",
                   "one known male carries a constant error with a standard deviation of 60 %",
                   "ten males 19 %"):
        assert phrase in text, phrase
