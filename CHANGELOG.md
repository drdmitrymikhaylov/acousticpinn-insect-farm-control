# Changelog

## 2026-10-06

- The silence estimator's duty cycle, taken apart
  (`results/duty_cycle_check.json`). The published 2.4 % at five males came
  from a simulation in which every male shares one duty cycle and the
  estimator is told it. With duty cycles drawn from the 50 *Acheta domesticus*
  recordings the spread is 19.2 % (14.1 % at 12, 10.5 % at 30) and the reading
  is 13 to 17 % low; the lead over the energy estimator is 1.2 to 1.5, not
  tenfold. One point of duty cycle is 5.9 % of the count; the recordings'
  quartiles (0.10, 0.26) read 0.52 and 1.43 of the true count.
- The measured duty cycle rises with the recording's signal-to-noise ratio
  (Spearman 0.49 over 316 recordings, 0.45 within the farmed species); the
  measure returns 0.03 on band noise with no song.
- Corrections: "needs no calibration at all" now says what it needs. The
  energy estimator's 8 % low reading is the calibration sample (200
  single-male runs that averaged 8.6 % above their expectation, 2.0 standard
  errors), not "a loud tail pulling the mean above the median".
- `tests/test_duty_cycle.py` (6 tests) pins the new section; three stray
  `._*` files removed from the repository.

## 2026-09-21

- Carrier column re-read as a mixture: 27/50 *Acheta domesticus* recordings
  sit at 4.53 ± 0.34 kHz (published 4.8), 19 lock below 2.5 kHz; the quoted
  3.73 ± 1.93 averages two clusters. Medians and in-band means added for all
  six taxa; the "indoor, at a distance" explanation corrected to "the peak
  picker cannot reject a non-cricket tone".
- Policy differences now carry 95 % intervals (300 runs/arm): on setpoint the
  sensors are +8 ± 14 g and +2 ± 14 g (zero) but camera + mic costs FCR
  +0.14 ± 0.01 — "worth nothing" was too kind; cold +354 ± 12 g; warm camera
  alone +153 ± 12 g (+10 %, not stated before), camera + mic +207 ± 13 g.
- Energy estimator bias stated: reads 8 % low at every count (−7.6 to −10.9 %).
- Results files published in `results/`; `tests/test_readme_numbers.py`
  (6 tests) pins every number on the page to them.
