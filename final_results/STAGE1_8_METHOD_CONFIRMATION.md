# Stage1-8 方法确认

生成时间：2026-04-27

## 总体流程

GridAgent1 当前主流程是：

`Stage1 风光不确定性 -> Stage2 组件故障概率 -> Stage3 时空故障场景 -> Stage4 负荷优先级调度 -> Stage5 韧性评估 -> Stage6 GNN 预警 -> Stage7 上下文调度优化 -> Stage8 稳态物理闭环`

## 方法清单

| Stage | 模块/脚本 | 方法 | 主要输入 | 主要输出 |
|---|---|---|---|---|
| Stage1 | `scripts/wind_pv_uncertainty_modeling.py` | 风光出力不确定性建模，使用 DPGMM 生成典型风光场景和场景概率。 | `DPGMM_input.csv`、`TRIM_input.csv` | `typical_scenarios.npy`、`scenario_probabilities.csv`、`history_series.csv`、`uncertainty_report.json` |
| Stage2 | `scripts/component_failure_probability.py` | 台风风场驱动的输电线路故障概率计算，配置中默认使用 Schloemer/Batts 类风场与脆弱性模型。 | `grid_topology.json`、台风轨迹/强度参数 | `line_failure_timeseries_schloemer.csv` 或 `line_failure_timeseries_batts.csv`、`failure_probability_report.json` |
| Stage3 | `scripts/spatiotemporal_contingency_generator.py` | 基于线路故障概率生成时空故障场景，支持 Wang MC/QMC、C3PO reference、TRIM reference 等方法。 | Stage2 故障概率、`grid_topology.json` | `contingency_tensor_*.npy`、`contingency_scenarios_*.csv`、`state_summary_*.csv`、`method_comparison.csv`、`contingency_report.json` |
| Stage4 | `scripts/load_prioritization_scheduling.py` | 负荷优先级与灾前调度/切负荷策略评估，比较 priority/uniform 与 reserve/no-reserve 策略。 | Stage1 场景、Stage2 概率、Stage3 张量、`TRIM_input.csv` | `policy_comparison.csv`、`scenario_metrics.csv`、`pre_disaster_dispatch_schedule.csv`、`worst_scenario_shedding_detail.csv`、`load_bus_priority_profile.csv` |
| Stage5 | `scripts/multi_criteria_resilience_assessment.py` | 多指标韧性评估，使用 EWM 熵权法 + TOPSIS 排序。 | Stage4 `policy_comparison.csv`、`worst_scenario_shedding_detail.csv` | `indicator_table.csv`、`single_indicator_ranking.csv`、`ewm_topsis_result.csv`、`multi_criteria_report.json` |
| Stage6 | `scripts/gnn_warning_module.py` | 线路级 GNN 风险预警，当前重点方法为 Baseline GNN + MetaPath V1 语义增强、注意力解释、残差门控和概率校准。 | `grid_topology.json`、`aligned_merged.csv`、Stage2 概率、Stage3 张量、Stage4 负荷优先级 | `line_risk_prediction.csv`、`calibrated_hourly_line_probability.csv`、`nk_failure_risk.csv`、`critical_load_risk.csv`、`metapath_attention_summary.csv`、`warning_report.json` |
| Stage7 | `scripts/dispatch_optimization_module.py` | 上下文调度优化，先求 SCUC、Stochastic UC、Robust UC，再按风险/不确定性规则逐小时选择策略。 | `grid_topology.json`、`TRIM_input.csv`、Stage1 场景、Stage2 概率、Stage6 风险结果 | `dispatch_strategy_selection.csv`、`contextual_dispatch_unit_schedule.csv`、`contextual_dispatch_load_shedding.csv`、`contextual_dispatch_hourly_cost.csv`、`line_flow.csv`、`dispatch_optimization_report.json` |
| Stage8 | `scripts/steady_state_physics_module.py` | 稳态物理可行性校核与规则闭环修正，检查负荷、机组、线路约束，生成对象级诊断、规则动作和修正后方案。 | Stage7 调度输出、`grid_topology.json` | `feasibility_summary.json`、`physics_violations.csv`、`critical_lines_hourly.csv`、`vulnerable_buses_hourly.csv`、`rule_based_actions_hourly.csv`、`rule_corrected_*`、`rule_closure_summary.json` |

## 当前正式配置口径

配置文件：`configs/gridagent_framework.formal2024.json`

- Stage1：`n_typical_scenarios=10`，`max_components=8`。
- Stage2：从 `2024-09-01 00:00:00` 起 72 小时台风窗口。
- Stage3：`repair_hours=12`，`high_risk_quantile=0.9`。
- Stage6：启用 `metapath_v1_enabled=true`，`horizon_hours=24`，`train_ratio=0.7`。
- Stage7：启用 `strategy_mode=contextual`，24 小时调度窗口，SCUC/Stochastic/Robust 按阈值切换。
- Stage8：启用 `steady_state_physics.enabled=true`，`auto_correct=true`，输出目录名为 `stage8_steady_state_physics`。
