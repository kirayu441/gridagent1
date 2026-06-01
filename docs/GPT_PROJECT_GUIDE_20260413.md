# GridAgent1 项目说明书（GPT 专用，2026-04-13）

## 0. 文档用途

这份文档用于让 GPT 在最短时间内“读懂并可执行”本项目，重点是：

1. 这个项目在做什么（业务目标 + 研究目标）
2. 每个阶段输入输出是什么（避免理解错数据）
3. 代码入口在哪（避免 GPT 在仓库里迷路）
4. 当前结论和注意事项（避免过度归因）

项目根目录：`C:\Users\yuhan\Desktop\gridagent1`

---

## 1. 一句话概览

`GridAgent1` 是一个面向极端天气下电网韧性的端到端实验框架，包含 Stage1~Stage7 七个模块：  
从风光不确定性建模出发，经过线路故障概率、时空故障场景、负荷优先级调度、韧性评估、GNN 风险预警，到最终的调度策略自动切换。

---

## 2. 你应该先看的文件（阅读顺序）

1. `configs/gridagent_framework.formal2024.json`  
2. `scripts/gridagent_framework.py`  
3. `scripts/gnn_warning_module.py`  
4. `scripts/dispatch_optimization_module.py`  
5. `docs/STAGE6_WARNING_UPLIFT_REPORT_20260408.md`  

如果只需要“快速知道项目全貌”，先看：  
`docs/PROJECT_FULL_SUMMARY_FOR_AI.md`

---

## 3. 最新主运行与结果位置

- 最新运行标记：`results/gridagent_framework/latest_run.json`
- 当前指向：`formal2024_full_metapath_tuned_20260407`
- 主结果目录：
  `results/gridagent_framework/formal2024_full_metapath_tuned_20260407`

阶段目录：

- `stage1_wind_pv`
- `stage2_failure`
- `stage3_contingency`
- `stage4_scheduling`
- `stage5_assessment`
- `stage6_warning`
- `stage7_dispatch_optimization`

---

## 4. 核心配置（formal2024）

配置文件：`configs/gridagent_framework.formal2024.json`

关键点：

1. 数据路径：
   - `paths.grid`: `data_final/formal_guangdong_2024/grid_topology.json`
   - `paths.trim_input`: `data_final/formal_guangdong_2024/TRIM_input.csv`
   - `paths.aligned`: `data_final/formal_guangdong_2024/aligned_merged.csv`
2. 基线链路：
   - `failure_model = schloemer`
   - `contingency_method = c3po_ref`
   - `n_scenarios = 256`
3. Stage6 预警已启用 MetaPath 与比较：
   - `metapath_v1_enabled = true`
   - `run_baseline_comparison = true`
4. Stage6 当前关键训练参数：
   - `metapath_topk = 3`
   - `risk_weight_alpha = 1.0`
   - `risk_weight_beta = 2.0`
   - `metapath_gate_reg_lambda = 0.0002`
   - `metapath_warmup_epochs = 12`
5. Stage7 调度优化已启用 contextual 选模：
   - `dispatch_optimization.enabled = true`
   - `strategy_mode = contextual`

---

## 5. 七阶段流程（输入 -> 输出）

## Stage1 风光不确定性（`wind_pv_uncertainty_modeling.py`）

输入：
- `DPGMM_input.csv`
- `TRIM_input.csv`

输出（典型）：
- `typical_scenarios.npy`
- `scenario_probabilities.csv`
- `typical_scenarios_long.csv`
- `uncertainty_report.json`

作用：生成风电/光伏不确定场景，供后续故障与调度模块使用。

## Stage2 线路故障概率（`component_failure_probability.py`）

输入：
- 电网拓扑 + 台风参数

输出（典型）：
- `line_failure_timeseries_schloemer.csv`
- `failure_probability_report.json`

作用：得到每条线路在每个时刻的故障概率 `p_line`。

## Stage3 时空故障场景（`spatiotemporal_contingency_generator.py`）

输入：
- Stage2 的 `p_line` 时序

输出（典型）：
- `contingency_tensor_<method>.npy`（核心标签来源）
- `contingency_scenarios_<method>.csv`
- `method_comparison.csv`

作用：把概率转换为可采样的故障场景张量。

重要术语：  
“标签张量”通常指这里生成的 `contingency_tensor_*.npy`，形状是 `[S, T, E]`（场景、时间、线路）。

## Stage4 负荷优先级与预调度（`load_prioritization_scheduling.py`）

输入：
- Stage1 场景
- Stage2 概率
- Stage3 场景张量

输出（典型）：
- `policy_comparison.csv`
- `pre_disaster_dispatch_schedule.csv`
- `load_bus_priority_profile.csv`

作用：在不同策略下比较负荷保障能力。

## Stage5 韧性综合评估（`multi_criteria_resilience_assessment.py`）

输入：
- Stage4 的策略结果

输出（典型）：
- `ewm_topsis_result.csv`
- `multi_criteria_report.json`

作用：用 EWM+TOPSIS 对策略进行多指标综合排序。

## Stage6 GNN 风险预警（`gnn_warning_module.py`）

输入：
- `grid_topology.json`
- Stage2 线路故障时序
- Stage3 `contingency_tensor_*.npy`
- Stage4 优先级文件

输出（典型）：
- `line_risk_prediction.csv`
- `calibrated_hourly_line_probability.csv`
- `model_comparison.csv`（metapath vs baseline）
- `warning_report.json`

作用：预测未来时段线路风险，输出给 Stage7。

## Stage7 调度优化（`dispatch_optimization_module.py`）

输入：
- Stage6 小时级线路风险
- Stage1/4/5 输出的上下文

输出（典型）：
- `dispatch_strategy_selection.csv`
- `generation_schedule.csv`
- `line_flow.csv`
- `dispatch_optimization_report.json`

作用：在 SCUC / Stochastic / Robust 之间按风险上下文切换。

---

## 6. 关键方法说明（GPT 容易问到）

## 6.1 MetaPath V1 是什么

Stage6 的增强版 GNN，核心是：

1. 固定电网语义元路径
2. 语义注意力聚合
3. 残差门控（gate）融合基线输出

输出形式可理解为：  
`final = base + gate * delta`（并带 warmup 缩放）

## 6.2 warmup / gate / 风险加权是什么意思

1. warmup：前几轮先小幅启用元路径修正，避免训练早期不稳定。  
2. gate：每条线学习一个 0~1 开关，决定元路径修正加多少。  
3. 风险加权：高风险样本的训练误差权重更高，模型更关注危险点。

---

## 7. 当前已确认的重要实验结论（截至 2026-04-13）

来自：`results/gridagent_framework/formal2024_full_metapath_tuned_20260407/stage6_warning/model_comparison.csv`

1. 同次运行内，`metapath_v1` 显著优于 `baseline_gnn`。  
2. 典型指标（val_mae）约从 `0.1281` 降至 `0.0286`。  
3. 高风险相关误差下降更明显。  

但请注意：  
旧版 MetaPath 常用 `wang_qmc` 标签张量，本轮主运行用 `c3po_ref`，标签分布显著不同。  
因此“提升原因”应解释为“模型改进 + 训练策略 + 标签分布”共同作用，而非单因素。

---

## 8. 常见误解与防踩坑

1. 不要把“本次运行内模型对比”和“跨历史版本对比”混为一谈。  
2. 不要忽略 Stage3 标签生成方法（`c3po_ref` vs `wang_qmc`）对 Stage6 的强影响。  
3. Stage6 指标好，不代表 Stage7 一定同步大幅提升（调度结果受更多约束）。  
4. `results/` 下目录很多，引用结果时请带完整 run_tag。

---

## 9. 常用命令（复现主线）

全链路运行（formal2024）：

```powershell
python scripts\gridagent_framework.py --config configs\gridagent_framework.formal2024.json --mode baseline --run-tag formal2024_full_metapath_tuned_20260407
```

只看 Stage6 报告核心文件：

```powershell
Get-Content results\gridagent_framework\formal2024_full_metapath_tuned_20260407\stage6_warning\model_comparison.csv
```

---

## 10. 给 GPT 的任务提示模板（可直接复用）

当你要 GPT 帮忙时，建议在提问里明确这 5 件事：

1. 你要看的 run_tag  
2. 你关心的 stage（例如只看 Stage6）  
3. 你要“代码改动”还是“结果分析”  
4. 是否允许重跑实验  
5. 结果输出形式（表格/文档/结论）

示例：

```text
请基于 run_tag=formal2024_full_metapath_tuned_20260407，只分析 Stage6。
先读 model_comparison.csv 和 warning_report.json，
输出“3条结论 + 2条风险 + 1个下一步实验建议”，不要改代码。
```

---

## 11. 本文档与已有文档关系

1. 本文档是“GPT 快速上手说明”。  
2. 更完整背景见：`docs/PROJECT_FULL_SUMMARY_FOR_AI.md`。  
3. Stage6 提升细节见：`docs/STAGE6_WARNING_UPLIFT_REPORT_20260408.md`。  
4. 如果出现冲突，以代码和当前 run 结果文件为准。

---

## 12. 模块级详细说明（按脚本）

本节按“脚本级”给出具体用途，方便 GPT 定位到可执行模块。

### 12.1 编排与总流程模块

1. `scripts/gridagent_framework.py`  
定位：Stage1~Stage7 总编排器（主入口）。  
输入：配置 JSON（默认 formal2024 配置）。  
输出：`results/gridagent_framework/<run_tag>/stage1~stage7` 全套产物。  
典型命令：  
`python scripts\gridagent_framework.py --config configs\gridagent_framework.formal2024.json --mode baseline --run-tag <tag>`

2. `scripts/run_end_to_end_resilience.py`  
定位：简化版“一键运行”（Failure->Contingency->Scheduling->Assessment）。  
输入：grid + stage 参数。  
输出：四阶段结果目录 + `results/end_to_end_resilience_summary.json`。  
用途：快速打通非 GNN 链路。

3. `scripts/export_standard_results.py`  
定位：把框架输出整理成标准化结果包，供 dashboard/paper 复用。  
输入：某次 run 根目录。  
输出：`*_standard` 风格结果目录。

### 12.2 Stage1 模块（风光不确定性）

1. `scripts/wind_pv_uncertainty_modeling.py`  
定位：滚动 DPGMM + 场景生成 + 典型场景压缩。  
关键参数：`window_radius`、`max_components`、`n_sampled_scenarios`、`n_typical_scenarios`。  
关键输出：`typical_scenarios.npy`、`scenario_probabilities.csv`、`typical_scenarios_long.csv`、`uncertainty_report.json`。

2. `scripts/stage1_method_comparison.py`  
定位：Stage1 方法对比实验（不同不确定性建模方法）。  
输出：方法对比表与报告。  
用途：论文/方法学比较。

### 12.3 Stage2 模块（线路故障概率）

1. `scripts/component_failure_probability.py`  
定位：基于台风风场（Batts/Schloemer）与应力-强度模型计算线路故障概率。  
关键参数：`model`、`hours`、`center_lat/lon`、`intensity_scale`、`design_scale`。  
关键输出：`line_failure_timeseries_<model>.csv`、`failure_probability_report.json`。

### 12.4 Stage3 模块（时空故障场景）

1. `scripts/spatiotemporal_contingency_generator.py`  
定位：按多种方法生成故障张量和场景表。  
支持方法：`wang_qmc`、`wang_mc`、`c3po_ref`、`trim_ref`。  
关键输出：`contingency_tensor_<method>.npy`、`contingency_scenarios_<method>.csv`、`method_comparison.csv`。  
注意：Stage6 标签高度依赖这里的 method 选择。

2. `scripts/stage123_method_comparison.py`  
定位：Stage1~3 联合方法组合对比。  
用途：跨阶段方法耦合效果分析。

3. `scripts/analyze_stage123_results.py`  
定位：Stage1~3 对比结果后处理分析。  
输出：统计汇总与诊断表。

### 12.5 Stage4 模块（负荷优先级与预调度）

1. `scripts/load_prioritization_scheduling.py`  
定位：基于故障场景与负荷优先级做灾前调度。  
关键参数：`reserve_ratio`、`load_shed_cost`、`policy_set`、`priority_stress_factor`。  
关键输出：`policy_comparison.csv`、`pre_disaster_dispatch_schedule.csv`、`load_bus_priority_profile.csv`、`worst_scenario_shedding_detail.csv`。

### 12.6 Stage5 模块（韧性评估）

1. `scripts/multi_criteria_resilience_assessment.py`  
定位：Priority/Robustness/Rapidity/Sustainability 的 EWM+TOPSIS 综合评估。  
输入：Stage4 策略比较与最坏场景明细。  
输出：`ewm_topsis_result.csv`、`indicator_table.csv`、`multi_criteria_report.json`。

### 12.7 Stage6 模块（GNN 风险预警）

1. `scripts/gnn_warning_module.py`  
定位：线路风险预警主模块（baseline GNN + MetaPath V1）。  
关键参数：`metapath_v1_enabled`、`metapath_topk`、`risk_weight_alpha/beta`、`metapath_warmup_epochs`、`metapath_gate_reg_lambda`。  
关键输出：  
- `line_risk_prediction.csv`  
- `calibrated_hourly_line_probability.csv`  
- `model_comparison.csv`  
- `warning_report.json`

2. `scripts/gnn_ablation_experiment.py`  
定位：GNN 模型族消融（GCN/GAT/GraphSAGE/MLP/STGCN/MetaPath 等）。  
用途：模型结构对比。

3. `scripts/run_warning_scale_experiments.py`  
定位：Stage6 参数规模化扫描。  
用途：自动网格实验，输出批量对比结果。

4. `scripts/gnn_models/base_model.py`  
定位：Stage6 模型公共基类与共享模块。

5. `scripts/gnn_models/baseline_gnn.py`  
定位：Stage6 基线模型。

6. `scripts/gnn_models/metapath_v1.py`  
定位：MetaPath V1（固定元路径 + 语义注意力 + gate 残差）。

7. `scripts/gnn_models/gcn.py`  
定位：GCN 变体模型。

8. `scripts/gnn_models/gat.py`  
定位：GAT 变体模型。

9. `scripts/gnn_models/graphsage.py`  
定位：GraphSAGE 变体模型。

10. `scripts/gnn_models/stgcn.py`  
定位：时空图卷积变体。

11. `scripts/gnn_models/mlp.py`  
定位：非图结构 MLP 对照模型。

12. `scripts/gnn_models/__init__.py`  
定位：模型注册导出入口。

### 12.8 Stage7 模块（调度优化）

1. `scripts/dispatch_optimization_module.py`  
定位：SCUC / Stochastic UC / Robust UC 与 contextual 策略切换。  
关键参数：  
- 风险触发阈值：`stochastic_*`、`robust_*`  
- 优化约束：`reserve_ratio`、`voll`、`line_derate_coeff`、`mip_gap`、`time_limit_sec`  
关键输出：`dispatch_strategy_selection.csv`、`generation_schedule.csv`、`line_flow.csv`、`dispatch_optimization_report.json`。

### 12.9 多场景融合与灵敏度实验模块

1. `scripts/multiscenario_fusion_experiment.py`  
定位：多场景融合实验设计与指标矩阵构建。  
输出：融合实验配置与中间产物。

2. `scripts/multiscenario_fusion_run.py`  
定位：执行多场景融合批量运行。  
输出：融合实验结果包。

3. `scripts/module_sensitivity_analysis.py`  
定位：模块/指标灵敏度分析。  
输出：敏感性排序与解释报告。

4. `scripts/run_paper_comparison_experiment.py`  
定位：生成论文对比表（基线方法 vs 本方法）。  
输出：对比数据表与 markdown 报告。

### 12.10 数据准备与拓扑构建模块

1. `scripts/download_data.py`  
定位：下载外部原始数据。  
输出：原始数据落盘。

2. `scripts/prepare_formal_sources.py`  
定位：formal 数据源预处理。  
输出：结构化中间数据。

3. `scripts/build_dataset.py`  
定位：构建对齐后的建模数据集。  
输出：`aligned_merged.csv`、模型输入表等。

4. `scripts/build_ieee_subgrid.py`  
定位：从 IEEE 网络提取子网。  
输出：子网拓扑 json。

5. `scripts/generate_scaled_topology.py`  
定位：生成不同规模拓扑（如 g60_n75）。  
输出：缩放拓扑文件。

6. `scripts/generate_mock_data.py`  
定位：生成 mock 数据用于调试。  
输出：可复现实验样本数据。

7. `scripts/dataset_config.example.json` / `scripts/dataset_config.formal_guangdong_2024.json`  
定位：数据构建配置模板与正式配置。

### 12.11 可视化模块

1. `dashboard/gridagent_dashboard.py`  
定位：Streamlit 可视化入口。  
页面：Overview / Pipeline View / Scenario & Failure / Warning / Node Weather / MetaPath / Dispatch / Resilience / Export。

2. `dashboard/README.md`  
定位：启动方式与数据源优先级说明。

3. `dashboard/requirements-visualization.txt`  
定位：可视化依赖清单。

---

## 13. 模块依赖图（文本版）

1. `wind_pv_uncertainty_modeling` -> 提供不确定场景给 Stage4、Stage7  
2. `component_failure_probability` -> 提供 `p_line` 给 Stage3、Stage6、Stage7  
3. `spatiotemporal_contingency_generator` -> 提供 `contingency_tensor` 给 Stage4、Stage6  
4. `load_prioritization_scheduling` -> 提供优先级/策略结果给 Stage5、Stage6、Stage7  
5. `gnn_warning_module` -> 提供小时级线路风险给 Stage7  
6. `dispatch_optimization_module` -> 使用 Stage1/2/4/6 上下文输出最终调度

---

## 14. GPT 在每个模块应优先检查的文件

1. Stage1：`uncertainty_report.json`、`typical_scenarios_long.csv`  
2. Stage2：`failure_probability_report.json`、`line_failure_timeseries_*.csv`  
3. Stage3：`method_comparison.csv`、`contingency_tensor_*.npy`  
4. Stage4：`policy_comparison.csv`、`load_prioritization_report.json`  
5. Stage5：`ewm_topsis_result.csv`、`multi_criteria_report.json`  
6. Stage6：`model_comparison.csv`、`warning_report.json`、`metapath_attention_summary.csv`  
7. Stage7：`dispatch_strategy_selection.csv`、`generation_schedule.csv`、`dispatch_optimization_report.json`

---

## 15. 推荐回答模板（让 GPT 输出更稳定）

当用户问“某模块效果如何”时，建议 GPT 按固定结构回答：

1. 模块目标（做什么）
2. 本次输入来源（用了哪些上游文件）
3. 关键参数（当前 run 实际值）
4. 结果指标（先报核心指标，再报次级）
5. 风险与边界（哪些结论不能过度外推）
6. 下一步实验建议（1~2 条）
