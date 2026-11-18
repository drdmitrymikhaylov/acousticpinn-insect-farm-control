# Changelog

## 2026-11-18

- The policy table re-run with a spread of development rates
  (`results/spread_check.json`; 40 lognormal rate classes, log-sd 0 to 0.15,
  same 300 seeds; spread 0 reproduces `policies.json` to 2e-13 g). The
  colony model matures as one, so "harvest at the first song" was scored on
  a cohort whose first song is its last moult. With a log-sd of 0.05 the
  microphone arm's +354 ± 12 g over the calendar in the cold room is
  +12 ± 12 g; at 0.10 it is behind the calendar in every room (23–33 %),
  harvesting a bin 2–3 % adult; at 0.15 it harvests 43–44 % of the
  no-spread figure.
- Two triggers added beside it: a harvest on the acoustic male count over
  the camera count (through the energy estimator with its stored −8.6 % bias
  and spread; the silence estimator is spent on the first singing day) and a
  harvest on a thermometer's degree-day sum. Without spread the thermometer
  reproduces the microphone arm to the gram, run for run; with spread it
  harvests the median animal (cold room, 0.10: 1428 g, 534 ± 3 g ahead of
  the first song). The count trigger gets 97 % adults at FCR 3.57 against
  2.27; an estimator reading 20 % low never fires in 59 of 300 runs.
- In place: fact 1 qualified ("if the cohort matures as one"), a pointer
  under the policy section, a known-gaps bullet, a fourth "second reading".
- `tests/test_spread.py` (6 tests) pins the new section.

## 2026-10-19

- LICENSE now holds the standard CC BY 4.0 legal text, so GitHub recognises the licence (it showed "Other" before). The terms are unchanged; the note on what each licence covers moved to `NOTICE.md`.

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
