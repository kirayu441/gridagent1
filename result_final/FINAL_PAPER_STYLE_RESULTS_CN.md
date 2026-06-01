# GridAgent 最终实验结果正文版（中文）

## 摘要

本文基于广东省 2024 年风光负荷数据与 IEEE 118 节点全网拓扑，完成了 GridAgent 从 Stage1 到 Stage8 的全链路实验整理与复现实验。最终稳定可运行的主链路为：Stage1 风光不确定性建模、Stage2 台风线路失效概率建模、Stage3 时空故障场景生成、Stage4 负荷优先级调度、Stage5 多指标韧性评估、Stage6 线路级 GNN 风险预警、Stage7 上下文自适应调度，以及 Stage8 标准化结果导出。实验结果表明，所选链路能够在 118 节点全网场景下稳定完成风险识别与调度联动，其中 Stage6 的 A2 型 MetaPath 预警模型相较基线 GNN 明显提升了验证误差表现，Stage7 的上下文调度结果实现了零负荷损失、关键负荷供电率为 1、无线路过载的稳定运行结果。

需要说明的是，增强版 Stage1 已经作为研究增强结果完成构建与验证，但在当前 Stage7 随机机组组合模型下会导致 `Stochastic_UC` 不可行。因此，最终稳定交付链路保留了 Stage6 的增强预警结果，同时在 Stage7 中继续使用原始 Stage1 正式场景输出作为不确定性输入。

## 1. 实验对象与最终链路

### 1.1 数据与系统对象

本次最终实验采用如下对象：

- 电网拓扑：IEEE 118 节点全网
- 气象与新能源数据：广东省 2024 年风电、光伏与负荷时序
- 台风失效建模时段：72 小时
- 调度与预警重点分析窗口：24 小时

### 1.2 最终选定链路

最终用于标准化导出与结果交付的链路如下：

| 阶段 | 最终采用结果 | 说明 |
|---|---|---|
| Stage1 | `gridagent_final/stage1/outputs` | 作为最终 Stage7/Stage8 的不确定性输入 |
| Stage2 | `formal_ieee118_full_candidate_ds0p03_it3p5` | Schloemer 失效概率正式候选 |
| Stage3 | `c3po_ref` | 最终故障场景标签来源 |
| Stage4 | `formal_ieee118_full_candidate_rr0p30` | 负荷优先级调度正式候选 |
| Stage5 | `formal_ieee118_full_candidate_rr0p30` | 韧性综合排序结果 |
| Stage6 | `formal_ieee118_full_a2_c3po_ref` | A2 自适应全局注意力预警模型 |
| Stage7 | `formal_ieee118_full_contextual_stage1baseline_a2_c3po_ref_h24` | 最终上下文调度结果 |
| Stage8 | `formal_ieee118_full_standard` | 最终标准化结果包 |

## 2. 实验设置

### 2.1 Stage2-Stage4 主链参数

| 模块 | 关键设置 |
|---|---|
| Stage2 | `failure_model = schloemer`，`design_scale = 0.03`，`intensity_scale = 3.5` |
| Stage3 | `contingency_method = c3po_ref`，`n_scenarios = 256` |
| Stage4 | `reserve_ratio = 0.3` |

### 2.2 Stage6 最终预警方案

Stage6 最终采用的主实验方案为：

- 结构方案：`A2_metapath_adaptive_global`
- 监督标签：`c3po_ref`
- 训练增强：`warmup + gate_reg + risk_weight + lower lr`

对应关键训练设置可概括为：

- `metapath_attention_mode = adaptive_global`
- `metapath_topk = 3`
- `risk_weight_alpha = 1.0`
- `risk_weight_beta = 2.0`
- `metapath_gate_reg_lambda = 0.0002`
- `metapath_warmup_epochs = 12`

### 2.3 Stage7 最终调度方案

Stage7 最终采用：

- 调度模式：`contextual`
- 不确定性输入：原始 Stage1 正式输出
- 预警输入：Stage6 A2 正式结果
- 调度窗口：`2024-09-02 00:00:00` 至 `2024-09-02 23:00:00`

## 3. 各阶段核心结果

### 3.1 Stage2 线路失效概率结果

Stage2 最终候选结果显示，在 IEEE 118 节点全网中，Schloemer 模型能够产生非零且有区分度的线路故障概率。其主要统计量如下：

| 指标 | 数值 |
|---|---:|
| line_count | 186 |
| time_steps | 72 |
| overall_p_line_mean | 0.03571393304946701 |
| overall_p_line_max | 0.9996201728741191 |

从结果上看，该参数组已经能够形成较明显的高风险线路分化，为下游 Stage3 故障场景生成提供了可用输入。

### 3.2 Stage3 时空故障场景结果

Stage3 在 `c3po_ref` 方法下生成了 256 个时空故障场景。系统规模与关键统计结果如下：

| 指标 | 数值 |
|---|---:|
| 总节点数 | 118 |
| 负荷节点数 | 99 |
| 线路数 | 186 |
| 场景数 | 256 |
| avg_outage_rate | 0.03571891101030466 |
| multi_line_event_rate_ge2 | 0.3303493923611111 |
| avg_disconnected_loads | 0.7868381076388888 |
| max_disconnected_loads | 13 |

该结果说明 Stage3 不仅保留了线路级失效概率结构，还能够形成具有多线路联动特征的故障场景，为后续调度和预警提供了更接近真实运行压力的场景背景。

### 3.3 Stage4 负荷优先级调度结果

Stage4 比较了多种调度策略，其中 `priority_with_reserve` 为综合最优方案。其核心结果如下：

| 策略 | rr | ra | expected_total_shed | expected_weighted_shed_cost | critical_served_ratio |
|---|---:|---:|---:|---:|---:|
| priority_with_reserve | 0.9776769489519685 | 0.9814682982403482 | 2.0147071179049223 | 34.99868462847388 | 0.9985318854974644 |
| uniform_with_reserve | 0.9776769489519685 | 0.9711683155467223 | 2.0147071179049223 | 100.7353558952461 | 0.9776769489519687 |
| priority_no_reserve | 0.8920011802650506 | 0.9311362727110746 | 9.747143899692036 | 131.43517890326828 | 0.9920429214736786 |

可以看到，在总削减量相同的情况下，优先级加备用策略显著降低了加权损失成本，并提升了关键负荷供电水平。这说明负荷优先级与备用协调机制在本系统中是有效的。

### 3.4 Stage5 韧性综合评估结果

Stage5 基于 `Priority / Robustness / Rapidity / Sustainability` 四指标，通过 EWM+TOPSIS 对 Stage4 策略进行综合排序。结果如下：

| policy | Priority | Robustness | Rapidity | Sustainability | TOPSIS_Score | TOPSIS_Rank |
|---|---:|---:|---:|---:|---:|---:|
| priority_with_reserve | 0.9985318854974644 | 0.9776769489519684 | 0.9591894571091382 | 0.9330829219411452 | 1.0 | 1 |
| uniform_with_reserve | 0.9776769489519688 | 0.9776769489519684 | 0.9591894571091382 | 0.9330829219411452 | 0.5381582918153403 | 2 |
| priority_no_reserve | 0.9920429214736786 | 0.8920011802650506 | 0.9591894571091382 | 0.7254144737310283 | 0.3635252477767912 | 3 |

该结果进一步验证了 `priority_with_reserve` 的综合优势，也说明 Stage4 所选策略在韧性评价层面具有一致性。

### 3.5 Stage6 GNN 线路风险预警结果

Stage6 最终采用 `A2_metapath_adaptive_global + c3po_ref` 方案。与基线 GNN 的同口径对比如下：

| 模型 | val_mae | val_rmse | horizon_mae | horizon_rmse | best_val_mse |
|---|---:|---:|---:|---:|---:|
| metapath_v1 (A2) | 0.0061492545204510215 | 0.006875613308289462 | 0.10040826113666342 | 0.22364454749126622 | 0.000047274053940782323 |
| baseline_gnn | 0.011412894439074199 | 0.011419297799770039 | 0.10327514181185621 | 0.22826371221456937 | 0.00013040036719758064 |

从结果上看，A2 方案在验证集误差与最优验证均方误差上均优于 baseline，说明 MetaPath 语义增强与训练增强机制是有效的。与此同时，本次元路径平均语义权重并未塌缩到单一路径，而是保持了相对有区分的多通道分配，其中 `share_bus` 权重最高。

### 3.6 Stage7 上下文调度结果

Stage7 最终稳定跑通的结果使用：

- Stage6 A2 正式预警输出
- Stage1 原始正式不确定性场景
- 24 小时调度窗口 `2024-09-02`

其最终结果如下：

| 指标 | 数值 |
|---|---:|
| total_cost | 102224.5454568511 |
| generation_cost | 2524.1792484811076 |
| reserve_cost | 102.5737094025494 |
| startup_shutdown_cost | 99597.79249896746 |
| load_shedding_penalty | 0.0 |
| EENS | 0.0 |
| critical_load_supply_rate | 1.0 |
| reliability_score | 1.0 |
| overload_count | 0 |
| solve_success | true |

策略切换统计为：

| selected_strategy | hours_selected |
|---|---:|
| Robust_UC | 19 |
| SCUC | 5 |

这说明在当前预警上下文下，系统多数时段被判定为较高风险运行状态，因此更倾向采用稳健调度；同时，最终仍实现了零负荷损失、关键负荷完全供电和零线路过载。

### 3.7 Stage8 标准化导出结果

Stage8 将最终链路整理成统一的交付结构，包括：

- `scenario/`
- `warning/`
- `dispatch/`
- `resilience/`
- `summary/`

这一步并不新增建模结果，而是将已确认的 Stage1-7 正式候选结果整理成适合论文、展示和交付的结构化结果包。

## 4. 结果讨论

### 4.1 本次最终链路的主要优点

1. 全链路已经在 IEEE 118 全网场景下稳定跑通，并形成完整可复现实验闭环。  
2. Stage6 的增强预警模型已经能够稳定嵌入最终链路，相较基线 GNN 取得了更优误差表现。  
3. Stage7 上下文调度在最终窗口内实现了零负荷损失和零过载，说明预警与调度联动框架具备可操作性。  
4. Stage8 进一步将结果整理为标准化交付结构，提升了结果复用性与论文写作便利性。

### 4.2 当前链路的关键限制

1. 增强版 Stage1 虽然在不确定性建模层面具有研究价值，但与当前 Stage7 随机 UC 约束耦合时会引发 `Stochastic_UC` 不可行。  
2. Stage6 当前窗口下验证集高风险样本较少，因此部分高风险误差指标不够稳定。  
3. Stage7 目前只完成了一个正式 24 小时窗口的稳定交付，若要形成更强论文说服力，仍建议扩展到多窗口或多台风过程对比。

## 5. 结论

综合来看，本次实验已经形成一条可稳定交付的最终链路：

> Stage1 原始正式不确定性场景 + Stage2 Schloemer 失效模型 + Stage3 c3po_ref 故障场景 + Stage4/Stage5 优先级韧性链路 + Stage6 A2 MetaPath 预警 + Stage7 上下文调度 + Stage8 标准化导出。

该链路的主要特点是：

- 在 118 节点全网层面可稳定运行；
- 在预警模块中体现了结构增强带来的收益；
- 在调度模块中实现了高风险时段下的稳健策略切换；
- 在结果层面已经具备较完整的论文与交付支撑基础。

如果将本文作为论文最终实验主线，当前最稳妥的表述方式应当是：

1. 将增强版 Stage1 作为研究增强结果保留；
2. 将 Stage6 A2 作为正式预警增强结果突出展示；
3. 将 Stage7 的最终稳定链路明确说明为基于原始 Stage1 场景输入的可行调度结果；
4. 将 Stage8 标准化结果包作为最终实验交付物。

