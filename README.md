GTA VI trophy rarity forecast

The model converts printed rates back to rounded tracked-player counts, applies half-count binomial smoothing, and estimates trophy levels in logit space with tier-level empirical-Bayes pooling. Recent trends use Theil-Sen slopes, pooled within tier, and a capped saturating projection (2.8-day time constant). Target spread combines robust residual noise and horizon-dependent model uncertainty. Flat histories intentionally have essentially no movement and a small band. Five quantiles are inverse-logit transforms.

Practice histories contain only 7-8 flat reads over a short launch-night interval. The graded history has hundreds of reads and a roughly 4.5-day horizon, making robust trend estimation and saturation central.

Self-test mean logit pinball loss (lower is better):

| Synthetic tau (days) | Gain | Model | House baseline |
|---:|---:|---:|---:|
| 1.2 | 1.0 | 0.224505 | 0.233060 |
| 2.0 | 1.6 | 0.247738 | 0.279932 |
| 3.5 | 2.2 | 0.300320 | 0.360997 |

Run `python3 main.py --self-test`; results are written to `out/`. Standard library only.
