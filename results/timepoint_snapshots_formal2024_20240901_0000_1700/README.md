# Formal2024 两个时刻快照输出

时刻：2024-09-01 00:00:00（高风险）与 2024-09-01 17:00:00（风险回落）。

文件说明：
- timepoint_snapshot_summary.csv/json：两时刻关键指标总览
- <timestamp>/warning_dispatch_strategy_selection.csv：预警驱动下的策略选择
- <timestamp>/warning_hourly_line_risk_long.csv：该时刻每条线路风险概率
- <timestamp>/dispatch_generation_schedule.csv：机组出力
- <timestamp>/dispatch_reserve_schedule.csv：备用
- <timestamp>/dispatch_load_shedding_full.csv：节点切负荷明细
- <timestamp>/dispatch_line_flow_full.csv：线路潮流明细
- <timestamp>/scenario_component_failure_prob_full.csv：组件失效概率明细
- <timestamp>/scenario_contingency_scenarios_full.csv：故障场景明细
