# Stage1 Performance Report

## Scope

This report evaluates the current Stage1 method: Rolling DPGMM + KMeans scenario reduction.
It reuses existing Stage1 outputs and existing downstream reports to avoid rerunning expensive stages.

## 1. Distribution Fit

- `wind` typical-weighted vs history: KS=0.066309, Wasserstein=0.012129.
- `pv` typical-weighted vs history: KS=0.509791, Wasserstein=0.068310.

## 2. Wind-PV Joint Relation

- History correlation: -0.087943; typical weighted correlation: -0.068513; error: 0.019430.
- Joint distribution JS divergence: sampled=0.030294, typical=0.103914.

## 3. Time Continuity

- `wind` lag-1 ACF: history=0.976477, typical=0.938682; ACF MAE(1-24)=0.085662; ramp Wasserstein=0.011290.
- `pv` lag-1 ACF: history=0.939235, typical=0.583800; ACF MAE(1-24)=0.191048; ramp Wasserstein=0.063932.

## 4. Extreme Coverage

- Low total renewable threshold (P10)=0.040373; history low-rate=0.100182; typical low-rate=0.028743.
- Longest low-renewable spell: history=14h; typical mean=9.13h.
- High absolute ramp threshold (P95)=0.220300; history high-ramp rate=0.050097; typical high-ramp rate=0.202137.

## 5. Downstream Snapshot

- Stage4 best policy by critical served ratio: `priority_with_reserve`, critical_served_ratio=0.669147, expected_total_shed=58.495836.
- Stage7 contextual dispatch: total_cost=25878.062086, EENS=18.849255, reliability_score=0.360511.

## 6. Existing Method Context

The existing Stage1 method-comparison artifacts show the following method context:

| method | elapsed_sec | wind_90pct_coverage | pv_90pct_coverage | wind_pv_corr | correlation_error |
|---|---|---|---|---|---|
| DPGMM | 401.263793 | 0.955260 | 0.995788 | -0.078554 | 0.009389 |
| ARIMA | 16327.843394 | 0.550205 | 0.369877 | 0.116324 | 0.204267 |
| LSTM | 611.431155 | 0.311248 | 0.454121 | -0.016709 | 0.071234 |
| Copula | 3.208915 | 0.964367 | 0.996699 | -0.073933 | 0.014010 |

## Caveat

Downstream metrics are reused from existing formal2024 Stage4/5/7 runs driven by the same DPGMM-style uncertainty outputs. They show task usefulness, but they are not yet a full end-to-end re-run against alternative Stage1 methods.