# Step6 Final Delivery

## 1) Final Conclusion
- 全局推荐策略：`batts__c3po_ref__rr0p3`（`STR_001`）。
- 在 24 个环境场景、48 组 cloud 评估下，该策略平均融合得分 `0.4018`，优于第二名 `schloemer__c3po_ref__rr0p3`（`0.2926`）。
- 最佳单次场景：`S0018 + STR_001`，融合得分 `0.9419`。

## 2) Cloud Core Metrics (48 runs)
| Strategy | Mean Fusion | Mean AUPRC | Mean Recall@Top10 | Mean RR | Mean Priority | Mean Sustainability | Mean Cost |
|---|---:|---:|---:|---:|---:|---:|---:|
| batts__c3po_ref__rr0p3 | 0.4018 | 0.9999 | 0.5860 | 0.3654 | 0.7027 | 0.3576 | 1681.0852 |
| schloemer__c3po_ref__rr0p3 | 0.2926 | 0.9998 | 0.4865 | 0.3591 | 0.6443 | 0.3511 | 1778.1209 |

## 3) Indicator Weights (EWM)
| Indicator | Weight |
|---|---:|
| warning_auprc | 0.4651 |
| warning_recall_top10 | 0.1511 |
| warning_f1_top10 | 0.1511 |
| Robustness | 0.0635 |
| Sustainability | 0.0600 |

## 4) Stratified Findings
- 风光分层：5/5 组合中 `STR_001` 均为最优。
- 负荷分层：4/4 场景中 `STR_001` 均为最优。
- 强度分层：`0.8,1.4` 由 `STR_003` 更优，`1.0,1.2` 由 `STR_001` 更优。

| Intensity | Winner | Mean Fusion | Mean RR | Mean Cost |
|---|---|---:|---:|---:|
| 0.8 | STR_003 | 0.2014 | 0.3559 | 1634.8582 |
| 1.0 | STR_001 | 0.1977 | 0.3778 | 1645.0672 |
| 1.2 | STR_001 | 0.9144 | 0.3630 | 1720.8793 |
| 1.4 | STR_003 | 0.6812 | 0.3545 | 1852.5592 |

## 5) High-Risk Environments (Top-5 by avg_cost)
| Env | Intensity | Wind Variant | Load Scenario | Avg Cost | Avg RR | Best Fusion |
|---|---:|---|---|---:|---:|---:|
| S0023 | 1.4 | high_wind_low_pv | critical_stress | 2028.2778 | 0.3385 | 0.6727 |
| S0020 | 1.4 | baseline_dpgmm | extreme_plus_30pct | 1981.0772 | 0.3659 | 0.6816 |
| S0009 | 1.0 | low_wind_low_pv | extreme_plus_30pct | 1931.4812 | 0.3468 | 0.1790 |
| S0014 | 1.2 | baseline_dpgmm | critical_stress | 1905.7023 | 0.3603 | 0.9091 |
| S0016 | 1.2 | low_wind_high_pv | extreme_plus_30pct | 1905.1377 | 0.3778 | 0.9270 |

## 6) Repro Commands (Fast Path)
```powershell
# Step1 design matrix
python scripts/multiscenario_fusion_experiment.py --config configs/multiscenario_fusion.formal2024.json --phase design --run-tag phase1_design

# Step2 edge evaluation (representative sample)
python scripts/multiscenario_fusion_run.py --design-manifest results/multiscenario_fusion/phase1_design/experiment_manifest.json --output-subdir edge_eval_v2 --env-selection shuffle --min-intensity 1.0 --max-env-cases 6 --max-strategies 3 --n-scenarios 32 --hours 48 --seed 42

# Step3 cloud evaluation (top2 strategies, fast scheduling mode)
python scripts/multiscenario_fusion_run.py --design-manifest results/multiscenario_fusion/phase1_design/experiment_manifest_cloud_top2.json --output-subdir cloud_eval_v1 --env-selection shuffle --max-env-cases 24 --max-strategies 2 --n-scenarios 256 --hours 72 --seed 42 --policy-set priority_only
```

## 7) File Index
- 总报告：`C:\Users\yuhan\Desktop\gridagent1\results\multiscenario_fusion\phase1_design\cloud_eval_v1\fusion_report.json`
- 策略汇总：`C:\Users\yuhan\Desktop\gridagent1\results\multiscenario_fusion\phase1_design\cloud_eval_v1\fusion_strategy_summary.csv`
- 指标权重：`C:\Users\yuhan\Desktop\gridagent1\results\multiscenario_fusion\phase1_design\cloud_eval_v1\fusion_indicator_weights.csv`
- 分层总报告：`C:\Users\yuhan\Desktop\gridagent1\results\multiscenario_fusion\phase1_design\step4_analysis\step4_report.json`
- 强度分层：`C:\Users\yuhan\Desktop\gridagent1\results\multiscenario_fusion\phase1_design\step4_analysis\by_intensity_winner.csv`
- 风光分层：`C:\Users\yuhan\Desktop\gridagent1\results\multiscenario_fusion\phase1_design\step4_analysis\by_wind_variant_winner.csv`
- 负荷分层：`C:\Users\yuhan\Desktop\gridagent1\results\multiscenario_fusion\phase1_design\step4_analysis\by_load_scenario_winner.csv`
- 环境风险视图：`C:\Users\yuhan\Desktop\gridagent1\results\multiscenario_fusion\phase1_design\step4_analysis\environment_risk_view.csv`

## 8) Scope Note
- 本次为快速交付，cloud 阶段采用 `policy_set=priority_only` 以缩短时长；若需完整基线对照，可将 `policy_set` 改回 `all` 重新评估。
- 按用户要求，已跳过第5步敏感性/稳健性补充。