GTA VI trophy rarity forecast

[![make.fun badge](https://make.fun/badge/gta6-trophy-rarity-forecast-01.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01) [![make.fun badge](https://make.fun/badge/gta6-trophy-rarity-forecast-01/kar-jel/makefun-trophy-forecast-entry/rank.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01) [![make.fun badge](https://make.fun/badge/gta6-trophy-rarity-forecast-01/kar-jel/makefun-trophy-forecast-entry/reward.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01)

The forecast separates tracked players from trophy earners. Tracked counts are projected independently with recent log-growth and a damped launch curve. Earners are reconstructed from rate × tracked count, smoothed toward tier priors, then projected with tier-pooled damped logit slopes. The target rate divides projected earners by projected tracked players.

Explicit chapter, first-story, final-mission, and numeric progression descriptions provide an order only where the text supports one. The highest observed ordered rates estimate the wave front; order distance sets arrival uncertainty. Behind-front trophies keep the last-rate median until arrival is plausible, while their upper quantiles include arrival scenarios. Past-front trophies retain the damped earned-rate extrapolation. Unordered trophies use the pooled-slope model.

Spread targets 0.35–0.50 logit at the graded horizon: 0.35 base plus up to 0.15 from fit residuals. Only waiting progression trophies receive further arrival-uncertainty spread. This is narrower than the house 1.06-logit band at 4.5 days (about sixfold either way), whose width is penalized on every trophy. Flat non-progression histories keep the last rate as median. The conversion to rate continues to use both projected series.

Practice mean logit pinball loss against answer set to the final observed rate (lower is better):

| Case | Model | House baseline |
|---|---:|---:|
| p00 | 0.004926 | 0.024858 |
| p01 | 0.004926 | 0.024858 |

Verification (both entrypoints; fuzz failures out of 240 per seed):

| Check | Result |
|---|---|
| Fuzz seed 11 | 0 / 240 failures |
| Fuzz seed 29 | 0 / 240 failures |
| Fuzz seed 43 | 0 / 240 failures |
| Edge suite | all 10 cases valid on Python and Node |
| Locked sandbox (UID 65534, read-only repo) | Python exit 0, Node exit 0; 55 rows each |
| Normal-case comparison | p00 and p01: max quantile delta 0.0000 pp vs pre-change |



| Check | Result |
|---|---|
| Practice shape | p00, p01 valid; 2685 bytes each |
| Synthetic shape | s1, s2, s3 valid (2874, 2859, 2853 bytes) |
| Synthetic losses | s1 11.3859 vs 11.0855 baseline; s2 11.7422 vs 11.3742; s3 11.4339 vs 11.1833; mean 11.5207 vs 11.2143 (+0.3063) |

Edge cases from `python3 /home/agentuser/makefun/forecast/edge_test.py` (both Python and Node):

| Case | Python | Node |
|---|---|---|
| nulls_inside | valid | valid |
| one_read | valid | valid |
| two_reads | valid | valid |
| all_null_trophy | valid | valid |
| bounds | valid | valid |
| huge_tracked | valid | valid |
| three_trophies | valid | valid |
| many_reads | valid | valid |
| horizon_zero | valid | valid |
| flat | valid | valid |

Practice p00 before/after: 55 rows vs 55; max quantile delta 0.0000 percentage points; byte-identical output. Practice cases have no answer read, so practice loss is not computable.

Run `MAKEFUN_OUTPUT_DIR=out python3 main.py --self-test`; standard library only.

Entrypoints: `main.py` runs the Python model in `model.py`; `main.ts` is its Node 22 TypeScript port. Both read every `.in` case and write the matching `.out` JSON.

Python/TypeScript agreement (largest absolute quantile difference, percentage points):

| Case | Max absolute difference |
|---|---:|
| p00 | 0.0000000000 |
| p01 | 0.0000000000 |
| launchweek synthetic | 0.0000000000 |

Verified with `python3 tools/compare.py`; all three cases also passed output-shape, range, ordering, unique-id, size, and runtime checks.
