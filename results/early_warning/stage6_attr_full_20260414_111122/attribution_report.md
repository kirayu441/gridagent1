# Stage6 Attribution Report

- Generated at: 2026-04-14T13:09:02
- Experiment directory: `C:\Users\yuhan\Desktop\gridagent1\results\early_warning\stage6_attr_full_20260414_111122`

## Run Summary

- total_runs: 120
- success_runs: 120
- mean_wall_seconds: 0.000

## Block A (Label x Model, strategy OFF)

| label_method | n | delta_val_mae_mean | delta_val_mae_std | delta_val_rmse_mean | delta_best_val_mse_mean | delta_val_high_risk_mae_mean |
| --- | --- | --- | --- | --- | --- | --- |
| c3po_ref | 5 | 0.138442 | 0.0192945 | 0.15562 | 0.0361901 | 0.227764 |
| wang_qmc | 5 | -0.00835856 | 0.0253749 | -0.000414394 | -0.000389829 | -0.0178714 |

Interpretation: positive delta means MetaPath outperforms baseline on the same label regime.

## Block B (Label x Warmup x GateReg x RiskWeight)

Top configurations by val_mae_mean:

| label_method | warmup_on | gate_reg_on | risk_weight_on | n | val_mae_mean | val_mae_std | val_rmse_mean | best_val_mse_mean | val_high_risk_mae_mean | gate_mean_mean | wall_seconds_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| c3po_ref | True | True | False | 5 | 0.0236148 | 0.00739681 | 0.0366467 | 0.0015069 | 0.0836478 | 0.999961 | 0 |
| c3po_ref | True | True | True | 5 | 0.0242388 | 0.00319587 | 0.0353677 | 0.00125605 | 0.0970038 | 0.999954 | 0 |
| c3po_ref | False | True | True | 5 | 0.0246603 | 0.00386683 | 0.0352452 | 0.00127036 | 0.0933249 | 0.999942 | 0 |
| c3po_ref | True | False | False | 5 | 0.0248687 | 0.00756955 | 0.0362804 | 0.00145786 | 0.0763633 | 0.99996 | 0 |
| c3po_ref | False | False | True | 5 | 0.0251553 | 0.00279298 | 0.0345007 | 0.00121438 | 0.0810066 | 0.999942 | 0 |
| c3po_ref | True | False | True | 5 | 0.0254988 | 0.00215633 | 0.0358135 | 0.00129187 | 0.0930723 | 0.999966 | 0 |
| c3po_ref | False | True | False | 5 | 0.027802 | 0.0111595 | 0.0409823 | 0.00216191 | 0.0821442 | 0.999956 | 0 |
| c3po_ref | False | False | False | 5 | 0.0298277 | 0.0155145 | 0.0442716 | 0.00267645 | 0.0820239 | 0.999966 | 0 |

Main effects (off-minus-on gains):

| label_method | factor | n_on | n_off | val_mae_on_mean | val_mae_off_mean | val_mae_gain_off_minus_on | best_val_mse_gain_off_minus_on | high_risk_mae_gain_off_minus_on |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| c3po_ref | warmup_on | 20 | 20 | 0.0245553 | 0.0268613 | 0.00230606 | 0.000452605 | -0.00289691 |
| c3po_ref | gate_reg_on | 20 | 20 | 0.025079 | 0.0263376 | 0.00125864 | 0.000111334 | -0.00591366 |
| c3po_ref | risk_weight_on | 20 | 20 | 0.0248883 | 0.0265283 | 0.00164002 | 0.000692615 | -0.0100571 |
| wang_qmc | warmup_on | 20 | 20 | 0.377865 | 0.37772 | -0.000145069 | 1.70909e-05 | -0.000323644 |
| wang_qmc | gate_reg_on | 20 | 20 | 0.377793 | 0.377793 | -4.42086e-07 | -1.03563e-07 | -8.7209e-07 |
| wang_qmc | risk_weight_on | 20 | 20 | 0.377793 | 0.377793 | 2.34806e-10 | 7.45058e-10 | 3.47694e-10 |

## Block C (Old vs New MetaPath preset)

| label_method | n | delta_val_mae_mean | delta_val_mae_std | delta_best_val_mse_mean | delta_high_risk_mae_mean |
| --- | --- | --- | --- | --- | --- |
| c3po_ref | 5 | -0.00217018 | 0.00652526 | -0.000197921 | -0.022291 |
| wang_qmc | 5 | -0.0145754 | 0.000846087 | 0.00353336 | -0.0318995 |

Interpretation: positive delta means new preset is better than old preset.

## Notes

- This report is descriptive; inferential statistics can be added in a separate step if needed.
- Use per-seed pairwise tables for confidence interval or significance testing.
