# Six PDF Experiments Results

This package was generated from actual CSV/JSON outputs and dispatch reruns, not from the PDF notes.

## Outputs

- `experiment1_main_risk_probability_estimation.csv`
- `experiment2_metapath_ablation_study.csv`
- `experiment3_high_risk_line_identification.csv`
- `experiment4_risk_aware_dispatch_under_stress.csv`
- `experiment5_dispatch_sensitivity_analysis.csv`
- `experiment6_runtime_scalability_analysis.csv`

## Best Stress-Scenario Dispatch Rows

- S1_load_plus20: no_warning top_k=20 alpha=0.1 beta=1.0 EENS=0.0 critical_supply=1.0 cost=102525.33776001088
- S2_exposure_linecap_minus20: no_warning top_k=20 alpha=0.1 beta=1.0 EENS=0.0 critical_supply=1.0 cost=102002.92014628786
- S3_reserve_minus40: failure_prior top_k=20 alpha=0.1 beta=1.0 EENS=4.108748863281988 critical_supply=0.9094722256187192 cost=108182.85778103878

## Best Sensitivity Setting

- top_k=10, alpha=0.05, beta=0.5, EENS=None, overload=None, critical_supply=None, cost=None
