# 分阶段对比试验清单（中文）

说明：

- `✓`：已经完成，且当前工作区可找到对应结果
- `△`：部分完成，已有中间结果或已有初步依据，但还未整理成正式对比结论
- `—`：尚未完成，建议后续补充
- 建议优先级：
  - `高`：优先补，最影响论文说服力
  - `中`：有价值，但不是当前最关键短板
  - `低`：属于增强型补充，可后置

---

## Stage1 对比试验表

| 对比内容 | 对比目的 | 当前状态 | 建议优先级 | 对应结果文件路径 |
|---|---|---:|---|---|
| 分布拟合（均值、方差、覆盖率） | 验证场景统计是否接近历史数据 | ✓ | — | `gridagent_final/stage1_performance/results/stage1_performance_report.md` |
| wind-PV 联合关系 | 验证联合不确定性是否保留 | ✓ | — | `gridagent_final/stage1_performance/results/stage1_performance_report.md` |
| 时间连续性（ramp/连续性） | 验证时序特征是否保留 | ✓ | — | `gridagent_final/stage1_performance/results/stage1_performance_report.md` |
| 极端覆盖能力 | 验证低风低光/高波动场景覆盖 | ✓ | — | `gridagent_final/stage1_performance/results/stage1_performance_report.md` |
| 下游调度/韧性快照 | 验证 Stage1 对后续模块是否有帮助 | ✓ | — | `gridagent_final/stage1_performance/results/stage1_performance_report.md` |
| Rolling DPGMM vs Historical Sampling | 证明不是简单历史重排 | — | 高 | 暂无 |
| Rolling DPGMM vs ARIMA / VAR | 证明优于传统线性时序模型 | — | 高 | 暂无 |
| Rolling DPGMM vs Copula | 证明联合分布建模优势 | — | 高 | 暂无 |

---

## Enhanced Stage1 对比试验表

| 对比内容 | 对比目的 | 当前状态 | 建议优先级 | 对应结果文件路径 |
|---|---|---:|---|---|
| 原始 Stage1 vs Conditional Rolling DPGMM | 验证条件建模是否提升 | ✓ | — | `gridagent_final/enhanced_stage1/ENHANCED_STAGE1_REPORT_CN.md` |
| structured / split / semidecoupled 版本对比 | 选择增强版结构 | ✓ | — | `gridagent_final/enhanced_stage1/outputs/*/uncertainty_report.json` |
| 不同 PV 修正策略对比 | 解决 PV 偏低问题 | ✓ | — | `gridagent_final/enhanced_stage1/outputs/formal2024_medium1440_structured*/uncertainty_report.json` |
| 不同 wind 修正策略对比 | 解决 wind 偏高问题 | ✓ | — | `gridagent_final/enhanced_stage1/outputs/formal2024_medium1440_structured_relaxedwind/uncertainty_report.json`；`formal2024_medium1440_structured_windcal08/uncertainty_report.json` |
| enhanced Stage1 对 Stage7 可行性影响 | 验证增强版能否进入最终链路 | ✓ | — | `result_final/FINAL_EXPERIMENT_REPORT.md`；`result_final/FINAL_PAPER_STYLE_RESULTS_CN.md` |
| enhanced Stage1 vs 原始 Stage1 的正式下游全链路对比 | 证明增强版全链路收益 | — | 高 | 暂无 |

---

## Stage2 对比试验表

| 对比内容 | 对比目的 | 当前状态 | 建议优先级 | 对应结果文件路径 |
|---|---|---:|---|---|
| 不同参数组（design/intensity）对比 | 找到可用的非零故障概率参数 | ✓ | — | `gridagent_final/stage2/outputs/sweep_ds0p05_it2p0/failure_probability_report.json`；`sweep_ds0p03_it2p8/failure_probability_report.json`；`sweep_ds0p03_it3p5/failure_probability_report.json` |
| `schloemer` 候选参数稳定性验证 | 选定正式候选参数 | ✓ | — | `gridagent_final/stage2/outputs/formal_ieee118_full_candidate_ds0p03_it3p5/failure_probability_report.json` |
| `batts` vs `schloemer` 同口径对比 | 证明最终为何选 `schloemer` | △ | 高 | 当前 `stage2` 清理包中未整理成正式对比表 |
| 不同拓扑规模对比 | 说明 118 节点全网必要性 | — | 中 | 暂无 |

---

## Stage3 对比试验表

| 对比内容 | 对比目的 | 当前状态 | 建议优先级 | 对应结果文件路径 |
|---|---|---:|---|---|
| Stage2 零风险输入 vs 非零风险输入 | 验证 Stage3 是否真正受 Stage2 驱动 | ✓ | — | 当前对话过程已验证；正式清理包保留非零正式结果 |
| `c3po_ref` 方法结果验证 | 确认可作为正式候选 | ✓ | — | `gridagent_final/stage3/outputs/contingency_report.json` |
| `c3po_ref` vs `wang_qmc` | 比较标签/场景方法差异 | △ | 高 | `gridagent_final/stage3/outputs/method_comparison.csv` 仅含部分对比信息 |
| `c3po_ref` vs `wang_mc` / `trim_ref` | 完整方法对比 | — | 高 | 暂无 |
| 不同 `n_scenarios` 对比 | 验证 256 场景数合理性 | — | 中 | 暂无 |
| 不同修复参数对比 | 验证 repair_hours 等参数影响 | — | 中 | 暂无 |

---

## Stage4 对比试验表

| 对比内容 | 对比目的 | 当前状态 | 建议优先级 | 对应结果文件路径 |
|---|---|---:|---|---|
| `priority_with_reserve` vs `uniform_with_reserve` | 证明优先级机制有效 | ✓ | — | `gridagent_final/stage4/outputs/formal_ieee118_full_candidate_rr0p30/policy_comparison.csv` |
| `priority_with_reserve` vs `priority_no_reserve` | 证明备用机制有效 | ✓ | — | `gridagent_final/stage4/outputs/formal_ieee118_full_candidate_rr0p30/policy_comparison.csv` |
| 三种策略综合比较 | 形成正式策略选择依据 | ✓ | — | `gridagent_final/stage4/outputs/formal_ieee118_full_candidate_rr0p30/policy_comparison.csv` |
| 不同 `reserve_ratio` 对比 | 证明 `0.3` 的合理性 | — | 高 | 暂无 |
| 不同优先级划分规则对比 | 验证 priority profile 稳健性 | — | 中 | 暂无 |

---

## Stage5 对比试验表

| 对比内容 | 对比目的 | 当前状态 | 建议优先级 | 对应结果文件路径 |
|---|---|---:|---|---|
| 不同策略四指标比较 | 支撑综合排序结果 | ✓ | — | `gridagent_final/stage5/outputs/formal_ieee118_full_candidate_rr0p30/indicator_table.csv` |
| EWM+TOPSIS 最终排序 | 得到正式策略排名 | ✓ | — | `gridagent_final/stage5/outputs/formal_ieee118_full_candidate_rr0p30/ewm_topsis_result.csv` |
| EWM+TOPSIS vs 固定权重排序 | 验证排序方法鲁棒性 | — | 中 | 暂无 |
| 指标敏感性分析 | 看排序是否过度依赖单一指标 | — | 中 | 暂无 |

---

## Stage6 对比试验表

| 对比内容 | 对比目的 | 当前状态 | 建议优先级 | 对应结果文件路径 |
|---|---|---:|---|---|
| `baseline_gnn` vs `metapath_v1` | 证明 MetaPath 增强有效 | ✓ | — | `gridagent_final/stage6/outputs/formal_ieee118_full_a2_c3po_ref/model_comparison.csv` |
| A0 / A1 / A2 / A3 结构对比 | 比较不同 MetaPath 结构 | △ | 高 | 已有实验脚本基础，但清理包未形成正式总表 |
| `c3po_ref` vs `wang_qmc` 标签对比 | 评估监督标签影响 | △ | 高 | 已有实验脚本基础，但清理包未形成正式总表 |
| `warmup / gate_reg / risk_weight` 归因实验 | 分析训练增强项作用 | △ | 高 | 已有归因实验基础，但未整理成正式表 |
| fixed / adaptive_global / adaptive_context 对比 | 说明最终为何选 A2 | △ | 高 | 当前已确定 A2，但尚缺正式结构对比表 |
| attention entropy reg 对比 | 检查是否需要额外正则 | — | 低 | 暂无 |

---

## Stage7 对比试验表

| 对比内容 | 对比目的 | 当前状态 | 建议优先级 | 对应结果文件路径 |
|---|---|---:|---|---|
| `SCUC` vs `Stochastic_UC` vs `Robust_UC` | 比较三类调度模型差异 | ✓ | — | `gridagent_final/stage7/outputs/formal_ieee118_full_contextual_stage1baseline_a2_c3po_ref_h24/dispatch_model_comparison.csv` |
| `Contextual_Adaptive` vs 单一固定策略 | 证明上下文切换有意义 | △ | 高 | `dispatch_model_comparison.csv` 含结果，但未单独写成正式比较结论 |
| Stage1 原始输出 vs enhanced Stage1 输出 | 评估不确定性输入对 UC 可行性的影响 | ✓ | — | `result_final/FINAL_EXPERIMENT_REPORT.md`；`FINAL_PAPER_STYLE_RESULTS_CN.md` |
| 不同时间窗口对比 | 验证结果不是单窗口偶然 | — | 高 | 暂无 |
| 不同预警输入（Stage6 baseline vs A2）对比 | 证明预警模块对调度选择的贡献 | — | 高 | 暂无 |

---

## Stage8 对比试验表

| 对比内容 | 对比目的 | 当前状态 | 建议优先级 | 对应结果文件路径 |
|---|---|---:|---|---|
| 标准化导出一致性检查 | 确认导出层未篡改结果 | ✓ | — | `gridagent_final/stage8/outputs/formal_ieee118_full_standard` 与源结果对照 |
| 最终链路结果整理 | 形成交付包 | ✓ | — | `result_final/standardized_results` |
| baseline chain vs final chain 标准化结果对比 | 形成论文总对比图表 | — | 中 | 暂无 |
| 多版本导出包对比 | 验证最终交付版本选择 | — | 低 | 暂无 |

---

## 建议优先补充的实验

如果从论文收益和当前短板来看，最建议优先补的对比实验是以下 8 项：

1. Stage1：`Historical Sampling / ARIMA / Copula` 对比
2. Enhanced Stage1：增强版 vs 原始版的正式下游全链路对比
3. Stage2：`Batts vs Schloemer` 正式同口径对比
4. Stage3：`c3po_ref vs wang_qmc` 正式对比
5. Stage4：不同 `reserve_ratio` 对比
6. Stage6：`A0 / A1 / A2 / A3` 结构对比总表
7. Stage6：`warmup / gate_reg / risk_weight` 归因总表
8. Stage7：`Contextual_Adaptive vs 单一固定策略` 与 `不同预警输入` 对比

