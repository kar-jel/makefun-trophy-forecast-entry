GTA VI trophy rarity forecast

The forecast separates the two quantities behind each printed rate: tracked players and trophy earners. Tracked counts are read in every history row and projected independently using recent log-growth with a saturating, damped launch curve. Per-trophy earners are reconstructed from rate × tracked count, rounded to counts, smoothed toward their tier's earners-per-thousand prior with stronger evidence from larger counts, and projected with the tier-pooled damped logit slope. The target rate is projected earners divided by projected tracked players.

This matters in a launch surge: the tracked base can expand by hundreds-fold while trophy earners also rise, yet the rate can fall because incoming players are less far along. A rate-only logit trend misses that dilution. The model retains a distinct 100% completion guard, a positive median and upward-reaching band for zero-earner trophies, and ordered quantiles. The practice cases are flat; flat medians match the last printed rate to two decimals.

Practice mean logit pinball loss against answer set to the final observed rate (lower is better):

| Case | Model | House baseline |
|---|---:|---:|
| p00 | 0.004926 | 0.024858 |
| p01 | 0.004926 | 0.024858 |

Synthetic mean logit pinball loss (lower is better):

| Tau (days) | Gain | New two-series | Previous pass | House baseline |
|---:|---:|---:|---:|---:|
| 1.2 | 1.0 | 9.433302 | 9.261571 | 9.261571 |
| 2.0 | 1.6 | 11.209114 | 11.277462 | 11.277462 |
| 3.5 | 2.2 | 11.400847 | 11.594613 | 11.594613 |

The synthetic truths grow tracked players substantially and grow absolute earners while diluting their rate. Results show that the split model is not uniformly better on every synthetic truth; the rapid-growth case remains a limitation.

Run `MAKEFUN_OUTPUT_DIR=out python3 main.py --self-test`; standard library only.
