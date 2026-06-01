# GridAgent1 项目全量上下文说明（供 GPT/AI 读取）

## 文档元信息
- 项目根目录：`C:\Users\yuhan\Desktop\gridagent1`
- 文档用途：为 GPT/Claude/Codex 等 AI 提供完整、结构化、可复现实验上下文
- 更新时间：2026-03-27
- 建议读取方式：先看“第 1 章概览 + 第 9 章最新结果”，再按问题深入 Stage 细节

---

## 1. 项目定位与研究目标

`GridAgent1` 是一个面向极端天气电网韧性的端到端研究工程，核心目标是把以下环节串成可执行链路：

1. 风光出力不确定性建模（Stage1）
2. 输电线路故障概率计算（Stage2）
3. 时空故障场景生成（Stage3）
4. 负荷优先级与灾前调度（Stage4）
5. 多指标韧性评估（Stage5）
6. GNN 线路风险预警（含 MetaPath V1）（Stage6）
7. 风险上下文驱动的调度优化器切换（Stage7）

本项目当前重点创新在 Stage6：
- 在线路级 GNN 中加入固定元路径语义增强（MetaPath V1）
- 用语义注意力解释“模型更依赖哪种风险传播机制”
- 使用残差门控融合降低语义分支对基线预测的扰动

---

## 2. 当前状态总览（截至 2026-03-27）

## 2.1 最新运行指针
- 文件：`results/gridagent_framework/latest_run.json`
- 指向运行目录：`results/gridagent_framework/ieee118_n60_stagewise_20260324_195044`

## 2.2 当前主实验规模
- 电网拓扑：`data_final/ieee118_n60/grid_topology.json`
- 节点数：60
- 线路数：93
- 发电单元数：24
- 时间窗：72h 台风窗口 + 24h 调度窗口（由配置指定）

## 2.3 已有可并行规模
- `formal_guangdong_2024`：15 节点 / 15 线路
- `ieee118_n60`：60 节点 / 93 线路（当前主线）
- `scaled/g60_n75`：60 节点 / 75 线路（可用于规模/结构敏感性）

---

## 3. 仓库结构与模块职责

## 3.1 顶层目录
- `.venv/`：本地虚拟环境
- `configs/`：实验配置
- `data_final/`：输入数据与拓扑
- `scripts/`：核心算法与流程脚本
- `results/`：实验输出
- `dashboard/`：Streamlit 可视化面板
- `docs/`：文档与报告

## 3.2 关键脚本
- `scripts/gridagent_framework.py`：Stage1~Stage7 总调度器（baseline/adaptive）
- `scripts/wind_pv_uncertainty_modeling.py`：风光不确定性与典型场景
- `scripts/component_failure_probability.py`：线路故障概率
- `scripts/spatiotemporal_contingency_generator.py`：故障场景生成
- `scripts/load_prioritization_scheduling.py`：负荷优先级与调度
- `scripts/multi_criteria_resilience_assessment.py`：EWM+TOPSIS 韧性评估
- `scripts/gnn_warning_module.py`：GNN 预警（Baseline + MetaPath V1）
- `scripts/dispatch_optimization_module.py`：SCUC / Stochastic / Robust + contextual 选模

## 3.3 可视化入口
- `dashboard/gridagent_dashboard.py`
- 页面：`Overview`、`Pipeline View`、`Scenario & Failure`、`Warning`、`Node Weather`、`MetaPath`、`Dispatch`、`Resilience`、`Export`

---

## 4. 数据资产与输入契约

## 4.1 主输入文件（当前主线）
- `data_final/formal_guangdong_2024/aligned_merged.csv`：`(8784, 9)`，对齐后的气象+风光+负荷
- `data_final/formal_guangdong_2024/DPGMM_input.csv`：`(8784, 2)`，风光建模输入
- `data_final/formal_guangdong_2024/TRIM_input.csv`：`(8784, 13)`，调度/场景相关输入
- `data_final/ieee118_n60/grid_topology.json`：60 节点，93 线路，24 发电机

## 4.2 Stage 关键输出字段（用于下游模块）

1. Stage1 `typical_scenarios_long.csv`（`87840 x 5`）
字段：
- `scenario_id`, `timestamp`, `wind`, `pv`, `scenario_probability`

2. Stage2 `line_failure_timeseries_schloemer.csv`（`6696 x 13`）
字段：
- `timestamp`, `model`, `line_id`, `from_bus`, `to_bus`, `v_surface_ms`, `p_tower`, `p_span`, `p_line`, ...

3. Stage3 `contingency_scenarios.csv`（`18432 x 8`）
字段：
- `scenario`, `scenario_id`, `timestamp`, `failed_lines`, `outage_line_count`, `disconnected_load_count`, `probability`, `method`

4. Stage4 `policy_comparison.csv`（`3 x 11`）
字段：
- `policy`, `allow_reserve`, `rr`, `ra`, `expected_total_shed`, `expected_weighted_shed_cost`, `critical_served_ratio`, ...

5. Stage6 `line_risk_prediction.csv`（`93 x 4`）
字段：
- `line_id`, `risk_prob`, `risk_level`, `predicted_fail_hour`

6. Stage6 `calibrated_hourly_line_probability.csv`（`24 x 94`）
字段：
- `timestamp` + 每条线路列（`L0...L92`）

7. Stage7 `dispatch_strategy_selection.csv`（`24 x 9`）
字段：
- `timestamp`, `hour_index`, `hourly_line_risk`, `hourly_uncertainty`, `selected_strategy`, `reason`, ...

---

## 5. 端到端流程（Stage1~Stage7）详细

## Stage1 风光不确定性（wind_pv_uncertainty_modeling）
输入：
- `DPGMM_input.csv`, `TRIM_input.csv`
输出：
- `typical_scenarios.npy`
- `scenario_probabilities.csv`
- `typical_scenarios_long.csv`
- `uncertainty_report.json`

当前 run 指标（`ieee118_n60_stagewise_20260324_195044`）：
- 历史风均值：`0.2199`
- 历史光均值：`0.2025`
- 典型场景数：`10`
- wind 90% 覆盖：`0.9553`
- pv 90% 覆盖：`0.9958`

---

## Stage2 组件故障概率（component_failure_probability）
输入：
- `grid_topology.json`
- 台风轨迹与强度参数（配置）
输出：
- `line_failure_timeseries_schloemer.csv`
- `failure_probability_report.json`

当前 run 指标：
- 时间步：72
- 线路数：93
- 全局 `p_line` 均值：`0.032736`
- 全局 `p_line` 最大值：`0.9999997`
- Top 脆弱线路（按均值）：`L87`, `L76`, `L79`, `L77`, `L78`

---

## Stage3 时空故障场景（spatiotemporal_contingency_generator）
输入：
- Stage2 故障概率时序
- 电网拓扑
输出：
- `contingency_tensor_c3po_ref.npy`
- `contingency_scenarios_c3po_ref.csv`
- `state_summary_c3po_ref.csv`
- `line_probability_summary_c3po_ref.csv`
- `method_comparison.csv`
- `contingency_report.json`

当前 run 指标（c3po_ref）：
- `mae_empirical_vs_input_probability`: `0.002351`
- `high_risk_coverage`: `1.0`
- `risk_lift_ratio`: `226.9996`
- `avg_outage_rate`: `0.03280`
- `multi_line_event_rate_ge2`: `0.30116`

---

## Stage4 负荷优先级调度（load_prioritization_scheduling）
输入：
- Stage1 典型场景
- Stage2 故障概率
- Stage3 故障张量
- `TRIM_input.csv`
输出：
- `policy_comparison.csv`
- `scenario_metrics.csv`
- `pre_disaster_dispatch_schedule.csv`
- `worst_scenario_shedding_detail.csv`
- `load_bus_priority_profile.csv`
- `load_prioritization_report.json`

当前 run（3 个 policy）：
- `priority_with_reserve`: `TOP`（关键负荷服务率最高、综合最好）
- `uniform_with_reserve`: 次优
- `priority_no_reserve`: 第三

关键值（`priority_with_reserve`）：
- `rr`: `0.971354`
- `ra`: `0.978614`
- `expected_total_shed`: `2.5854`
- `expected_weighted_shed_cost`: `55.1557`
- `critical_served_ratio`: `0.986649`

---

## Stage5 韧性评估（multi_criteria_resilience_assessment）
输入：
- Stage4 `policy_comparison.csv`
- Stage4 `worst_scenario_shedding_detail.csv`
输出：
- `indicator_table.csv`
- `single_indicator_ranking.csv`
- `ewm_topsis_result.csv`
- `multi_criteria_report.json`

当前 run TOPSIS：
1. `priority_with_reserve`：`1.0000`
2. `uniform_with_reserve`：`0.4842`
3. `priority_no_reserve`：`0.2995`

---

## Stage6 线路风险预警（gnn_warning_module，含 MetaPath V1）
输入：
- `grid_topology.json`
- `aligned_merged.csv`
- Stage2 `line_failure_timeseries_schloemer.csv`
- Stage3 `contingency_tensor_c3po_ref.npy`
- Stage4 `load_bus_priority_profile.csv`
输出：
- `line_risk_prediction.csv`
- `calibrated_hourly_line_probability.csv`
- `nk_failure_risk.csv`
- `critical_load_risk.csv`
- `metapath_attention_summary.csv`
- `model_comparison.csv`
- `warning_report.json`
- `node_weather_timeseries.csv` / `node_weather_horizon.csv` / `node_weather_summary.csv`

当前 run 训练设置：
- `train_split_count=32`, `val_split_count=40`（总时间步 72）
- 请求 epoch：700，实际早停：286
- `best_val_mse=0.0006605`
- MetaPath: `enabled=True`, `topk=6`

当前 run 对比（核心）：
- `metapath_v1 val_mae = 0.014406`
- `baseline_gnn val_mae = 0.064813`
- `metapath_v1 horizon_mae = 0.021554`
- `baseline_gnn horizon_mae = 0.104650`
- 高风险子集 / top 风险子集指标均由 `metapath_v1` 获胜

元路径语义注意力均值：
- `share_bus`: `0.2606`
- `source_bridge`: `0.2531`
- `primary_load_bridge`: `0.2443`
- `two_hop_topology`: `0.2420`

---

## Stage7 调度优化与上下文选模（dispatch_optimization_module）
输入：
- `grid_topology.json`
- `TRIM_input.csv`
- Stage2 故障概率
- Stage1 不确定性场景
- Stage6 风险结果
输出：
- `dispatch_strategy_selection.csv`
- `dispatch_active_strategy_summary.csv`
- `contextual_dispatch_unit_schedule.csv`
- `contextual_dispatch_load_shedding.csv`
- `contextual_dispatch_hourly_cost.csv`
- `line_flow.csv`
- 各单模型输出（`scuc_*.csv`, `stochastic_uc_*.csv`, `robust_uc_*.csv`）
- `dispatch_optimization_report.json`

当前 run 结果：
- 策略模式：`contextual`
- 24h 选模：`SCUC 16h` + `Stochastic_UC 8h` + `Robust_UC 0h`
- `EENS = 0.0`
- `overload_count = 0`
- `critical_load_supply_rate = 1.0`
- `reliability_score = 1.0`

---

## 6. Stage6 核心算法说明（Baseline GNN + MetaPath V1）

## 6.1 基线 GNN（LineRiskGNN）
- 节点编码：2 层 MLP
- 图消息传递：2 层 `GraphMessageLayer`
- 边级读出：`[h_src, h_dst, edge_dyn, edge_static] -> MLP -> sigmoid`

说明：
- 采用全邻域聚合（不随机采样邻居），目标是降低采样噪声导致的小时级风险波动

## 6.2 固定元路径集合（MetaPath V1）
线路视角定义 4 条语义路径：
- `share_bus`: 共享母线直接耦合（L-B-L）
- `two_hop_topology`: 两跳拓扑传播（L-B-L-B-L）
- `source_bridge`: 电源侧桥接（L-B-source-B-L）
- `primary_load_bridge`: 关键负荷桥接（L-B-primary_load-B-L）

构造方式：
- 基于线路图 + bus-to-line 映射生成候选语义邻居
- 每条元路径按距离排序取 `topk`（当前配置 `topk=6`）

## 6.3 语义注意力与残差门控
对每条线路：
1. 按元路径聚合邻居表示 `path_repr`
2. 计算路径权重 `alpha=softmax(score)`
3. 得到语义上下文 `context = sum(alpha * path_repr)`
4. 预测端使用：
   - `base_logit`（基线）
   - `delta_logit`（语义残差）
   - `gate=sigmoid(gate_head(...))`
   - `out = sigmoid(base_logit + (warmup_scale * gate) * delta_logit)`

## 6.4 训练目标与正则
- 主损失：MSE 或风险加权 MSE（按 `risk_weight_alpha/beta/threshold`）
- 门控正则：`lambda_gate * mean(gate^2)`
- 注意力熵正则：`- lambda_entropy * entropy(alpha)`（鼓励避免单路径塌陷）
- warmup：前 `metapath_warmup_epochs` 线性放大语义残差
- 早停 patience：60

当前有效目标参数（主 run）：
- `risk_weight_alpha=2.0`
- `risk_weight_beta=4.0`
- `risk_weight_threshold=0.1`
- `metapath_gate_reg_lambda=0.0008`
- `metapath_attention_entropy_reg_lambda=0.0005`
- `metapath_warmup_epochs=35`

## 6.5 概率校准
模型输出与先验量（`p_line`, `v_surface`）做融合校准，控制整体风险均值在 `[risk_mean_floor, risk_mean_cap]`（当前 `[0.18, 0.55]`）范围内。

---

## 7. Stage7 上下文策略路由规则（核心逻辑）

函数：`route_strategy_by_context(...)`

全局极端条件：
- `expected_nk_fail_lines >= robust_nk_threshold`
- 或 `max_critical_outage_prob >= robust_critical_threshold`
- 或 `high_line_ratio >= robust_high_line_ratio_threshold`

逐小时策略：
1. 若 `line_risk_t >= robust_line_risk_threshold`
   或（全局极端 且 `line_risk_t >= stochastic_line_risk_threshold`）
   -> `Robust_UC`
2. 否则若 `unc_t >= stochastic_uncertainty_threshold`
   或 `line_risk_t >= stochastic_line_risk_threshold`
   -> `Stochastic_UC`
3. 否则 -> `SCUC`

当前主配置阈值：
- `stochastic_uncertainty_threshold=0.22`
- `stochastic_line_risk_threshold=0.45`
- `robust_line_risk_threshold=0.72`
- `robust_nk_threshold=3.0`
- `robust_critical_threshold=0.22`
- `robust_high_line_ratio_threshold=0.3`

---

## 8. 配置体系与差异

## 8.1 关键配置文件
- `configs/gridagent_framework.formal2024.quicktest.json`
- `configs/gridagent_framework.formal2024.json`
- `configs/gridagent_framework.ieee118_n60.metapath_opt124.json`（当前主配置）
- `configs/multiscenario_fusion.formal2024.json`

## 8.2 三套主配置差异（摘要）

| 配置 | 拓扑 | failure hours | warning train_ratio | horizon_start | metapath_topk | entropy_reg |
|---|---|---:|---:|---:|---:|---:|
| formal2024.quicktest | 15/15 | 24 | 0.70 | 0 | 默认 | 0 |
| formal2024 | 15/15 | 72 | 0.70 | 0 | 4 | 0 |
| ieee118_n60.metapath_opt124 | 60/93 | 72 | 0.45 | 24 | 6 | 0.0005 |

---

## 9. 最新主运行快照（重点）

运行目录：
- `results/gridagent_framework/ieee118_n60_stagewise_20260324_195044`

## 9.1 各阶段核心指标

| Stage | 关键指标 | 当前值 |
|---|---|---|
| Stage1 | 典型场景数 | 10 |
| Stage1 | wind/pv 90% 覆盖 | 0.955 / 0.996 |
| Stage2 | 线路数 × 时间步 | 93 × 72 |
| Stage2 | `overall_p_line_mean` | 0.032736 |
| Stage3 | `risk_lift_ratio` | 226.9996 |
| Stage3 | `avg_outage_rate` | 0.032803 |
| Stage4 | 最优 policy | priority_with_reserve |
| Stage5 | TOPSIS 第一名 | priority_with_reserve |
| Stage6 | metapath_v1 `val_mae` | 0.014406 |
| Stage6 | baseline `val_mae` | 0.064813 |
| Stage7 | contextual 选模 | SCUC 16h / Stochastic 8h |
| Stage7 | `EENS` / `overload_count` | 0.0 / 0 |

## 9.2 Stage6 调优轨迹（同 run 下多个备份目录）

| 目录 | entropy λ | val_mae(meta) | horizon_mae(meta) | best_val_mse(meta) | 备注 |
|---|---:|---:|---:|---:|---|
| `stage6_warning_before_opt124_20260324_233556` | 0 | 0.061883 | 0.102610 | 0.016194 | 早期版本，明显较差 |
| `stage6_warning_entropy_test` | 0.0030 | 0.022802 | 0.034433 | 0.001078 | 熵正则过强，退化 |
| `stage6_warning_entropy_test_0001` | 0.0001 | 0.013085 | 0.020755 | 0.000633 | 指标较好 |
| `stage6_warning_before_lambda0005_20260325_002847` | 0 | 0.013682 | 0.020877 | 0.000603 | 指标最好之一 |
| `stage6_warning` | 0.0005 | 0.014406 | 0.021554 | 0.000661 | 当前激活版本 |

说明：
- 当前启用版本不一定是绝对最优数值版本，更多是稳定性/解释性与页面一致性的折中快照。

---

## 10. 可视化系统（dashboard）说明

入口：
- `dashboard/gridagent_dashboard.py`

数据加载策略：
1. 优先加载 `results/gridagent_framework/*` 的 stage 化结果
2. 对缺失文件使用 warning_report 字段回填
3. 再缺失时从 `results/early_warning/*` 的历史文件 fallback

主要渲染函数：
- `render_overview`, `render_pipeline`, `render_scenario_failure`
- `render_warning`, `render_node_weather`, `render_metapath`
- `render_dispatch`, `render_resilience`, `render_export`

MetaPath 页面关键数据源：
- `stage6_warning/metapath_attention_summary.csv`
- `stage6_warning/model_comparison.csv`
- `stage6_warning/warning_report.json` 的 `training.metapath_attention_mean`

---

## 11. 运行与复现命令

## 11.1 全链路 baseline（推荐）
```powershell
python scripts/gridagent_framework.py `
  --config configs/gridagent_framework.ieee118_n60.metapath_opt124.json `
  --mode baseline `
  --run-tag ieee118_n60_stagewise_YYYYMMDD_HHMMSS
```

## 11.2 全链路 adaptive（边云筛选）
```powershell
python scripts/gridagent_framework.py `
  --config configs/gridagent_framework.formal2024.json `
  --mode adaptive `
  --run-tag formal2024_adaptive_YYYYMMDD_HHMMSS
```

## 11.3 仅运行预警模块（Stage6）
```powershell
python scripts/gnn_warning_module.py `
  --grid data_final/ieee118_n60/grid_topology.json `
  --aligned data_final/formal_guangdong_2024/aligned_merged.csv `
  --failure-csv results/gridagent_framework/.../stage2_failure/schloemer/line_failure_timeseries_schloemer.csv `
  --contingency-tensor results/gridagent_framework/.../stage3_contingency/schloemer/contingency_tensor_c3po_ref.npy `
  --load-priority-csv results/gridagent_framework/.../stage4_scheduling/.../load_bus_priority_profile.csv `
  --output-dir results/gridagent_framework/.../stage6_warning `
  --metapath-v1-enabled --run-baseline-comparison
```

## 11.4 启动可视化
```powershell
python -m streamlit run dashboard/gridagent_dashboard.py
```

---

## 12. 面向 AI 协作者的阅读顺序与问答策略

若 AI 需要快速回答“项目现在做到了哪里”，优先读取：
1. `results/gridagent_framework/latest_run.json`
2. 最新 run 下 `stage6_warning/warning_report.json`
3. 最新 run 下 `stage6_warning/model_comparison.csv`
4. 最新 run 下 `stage7_dispatch_optimization/dispatch_optimization_report.json`
5. 当前主配置 `configs/gridagent_framework.ieee118_n60.metapath_opt124.json`

若 AI 需要解释 MetaPath：
1. `scripts/gnn_warning_module.py`（`build_fixed_metapath_tensors` + `MetaPathSemanticBlock` + `LineRiskMetaPathGNN`）
2. `stage6_warning/metapath_attention_summary.csv`
3. `dashboard/gridagent_dashboard.py` 的 `render_metapath`

若 AI 需要解释调度切换：
1. `scripts/dispatch_optimization_module.py` 的 `route_strategy_by_context`
2. `stage7_dispatch_optimization/dispatch_strategy_selection.csv`
3. `dispatch_optimization_report.json` 的 `strategy_rules` 与 `warning_context_snapshot`

---

## 13. 已知限制与注意事项

1. `ieee118_n60_stagewise_20260324_195044` 是 stage 目录齐全的主运行，但根目录下可能没有 `framework_report.json`（非致命）。
2. 节点天气在 Stage6 中是“全局时序 + 空间影响场”投影生成，不是每节点实测气象。
3. Stage6 风险等级使用“窗口最大小时风险”而非累计概率，强调操作预警敏感性。
4. Stage7 选择逻辑是规则路由，不是端到端 RL 策略网络。
5. 仍有地理精细化待办（参考 `results/pending_work.md`）：真实 GIS 对齐后应复验脆弱线路排序稳定性。

---

## 14. 术语与字段速查

- `rr`：Robustness（服务率类稳健指标）
- `ra`：可恢复性相关指标（由 Stage4 计算）
- `EENS`：Expected Energy Not Served，期望未供电量
- `high_line_ratio`：高风险线路占比
- `metapath_topk`：每条元路径每个目标线路保留的语义邻居数量
- `risk_weight_alpha/beta`：风险加权损失参数（提升高风险样本训练权重）
- `metapath_attention_entropy_reg_lambda`：注意力熵正则系数，抑制注意力塌缩

---

## 15. 一句话总结（给模型快速注入）

该项目已形成从极端天气风险建模到调度决策的 Stage1~Stage7 闭环；当前主线在 `ieee118_n60`（60 节点/93 线路）上运行，Stage6 的 MetaPath V1（固定元路径 + 语义注意力 + 残差门控）相对 baseline GNN 在验证与地平线指标上显著提升，Stage7 使用风险/不确定性上下文规则在 SCUC 与 Stochastic_UC 之间按小时切换并实现 `EENS=0`、`overload=0` 的调度结果。
