# MetaPath Sweep Report (12 Runs)

- Generated on: 2026-04-07
- Experiment dir: `results\early_warning\metapath_tune12_20260407_205845`
- Runs: 12 / 12 succeeded

## Sweep Setup

- Grid/data: `formal_guangdong_2024` + `schloemer` + `wang_qmc` contingency tensor
- Search space: `metapath_topk={3,4,5}`, `lr={0.0045,0.0055}`, `hidden_dim=80`, `epochs=700`, `seed={42,43}`
- Fixed tuned options: `weight_decay=3e-4`, `risk_weight_alpha=1.0`, `risk_weight_beta=2.0`, `risk_weight_on_metapath_only=false`, `metapath_warmup_epochs=12`, `metapath_gate_reg_lambda=2e-4`

## Headline Results

- Mean improvement vs baseline (Val MAE): **+0.012655** (`baseline - metapath`)
- Mean improvement vs baseline (Horizon MAE): **+0.029284**
- Delta Val MAE range: **[0.00925, 0.01593]** (all positive)
- Mean gate value: **0.1356**
- Corr(`metapath_gate_mean`, `delta_val_mae`): **0.9933**

## Best Setting (By Mean Delta Val MAE)

| metapath_topk | lr | runs | delta_val_mae_mean | delta_horizon_mae_mean | val_mae_win_rate | horizon_mae_win_rate |
|---:|---:|---:|---:|---:|---:|---:|
| 3 | 0.0045 | 2 | 0.012917 | 0.02995 | 1.0 | 1.0 |

## Top Individual Runs

| run_name | k | lr | seed | delta_val_mae | delta_horizon_mae | gate_mean |
|---|---:|---:|---:|---:|---:|---:|
| r002_k3_h80_ep700_lr0.0045_wd0.0003_tr0.700_s43 | 3 | 0.0045 | 43 | 0.01593 | 0.038594 | 0.202858 |
| r010_k5_h80_ep700_lr0.0045_wd0.0003_tr0.700_s43 | 5 | 0.0045 | 43 | 0.015926 | 0.038587 | 0.202855 |
| r006_k4_h80_ep700_lr0.0045_wd0.0003_tr0.700_s43 | 4 | 0.0045 | 43 | 0.015925 | 0.038583 | 0.202857 |
| r004_k3_h80_ep700_lr0.0055_wd0.0003_tr0.700_s43 | 3 | 0.0055 | 43 | 0.015542 | 0.036965 | 0.21328 |
| r012_k5_h80_ep700_lr0.0055_wd0.0003_tr0.700_s43 | 5 | 0.0055 | 43 | 0.015539 | 0.036958 | 0.213277 |

## Worst Individual Runs (Still Improved)

| run_name | k | lr | seed | delta_val_mae | delta_horizon_mae | gate_mean |
|---|---:|---:|---:|---:|---:|---:|
| r011_k5_h80_ep700_lr0.0055_wd0.0003_tr0.700_s42 | 5 | 0.0055 | 42 | 0.00925 | 0.020285 | 0.062179 |
| r007_k4_h80_ep700_lr0.0055_wd0.0003_tr0.700_s42 | 4 | 0.0055 | 42 | 0.009251 | 0.020285 | 0.062179 |
| r003_k3_h80_ep700_lr0.0055_wd0.0003_tr0.700_s42 | 3 | 0.0055 | 42 | 0.009251 | 0.020285 | 0.062178 |

## Recommended Next Config

Use this as next default for formal2024 Stage6 warning experiments:

```bash
python scripts/gnn_warning_module.py \
  --run-baseline-comparison \
  --metapath-topk 3 \
  --hidden-dim 80 \
  --epochs 700 \
  --lr 0.0045 \
  --weight-decay 0.0003 \
  --risk-weight-alpha 1.0 \
  --risk-weight-beta 2.0 \
  --risk-weight-threshold 0.10 \
  --no-risk-weight-on-metapath-only \
  --metapath-gate-reg-lambda 0.0002 \
  --metapath-warmup-epochs 12
```

## Output Files

- Raw runs: `results\early_warning\metapath_tune12_20260407_205845/all_runs.csv`
- Group summary: `results\early_warning\metapath_tune12_20260407_205845/summary_by_setting.csv`
- Done marker: `results\early_warning\metapath_tune12_20260407_205845/done.json`
