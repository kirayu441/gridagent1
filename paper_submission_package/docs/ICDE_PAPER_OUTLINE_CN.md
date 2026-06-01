# ICDE 风格论文大纲（中文草案）

## 题目方向（暂定）

当前先不给出唯一最终题目，但标题风格建议向以下方向靠拢：

- `A Data-Centric Framework for Probabilistic Spatiotemporal Risk Analytics on Critical Infrastructure`
- `Scenario Compression and Risk Graph Materialization for Decision-Serving Infrastructure Analytics`
- `From Uncertain Scenarios to Risk-Aware Decisions: A Data Pipeline for Spatiotemporal Infrastructure Analytics`

现阶段建议遵循的命名原则是：

> 少写 `typhoon / Guangdong / IEEE118`，多写 `data-centric`、`probabilistic`、`spatiotemporal`、`risk analytics`、`decision-serving`。

---

## 摘要

摘要部分后续再细写，但结构建议固定为以下 5 句逻辑：

1. 背景：极端天气基础设施分析面临多源异构、时空相关和不确定数据。
2. 问题：现有方法缺少统一的数据产品链路来服务风险分析与决策。
3. 方法：提出一个 4 模块的数据中心框架。
4. 核心技术：场景压缩、风险图物化、图分析和面向决策的数据接口。
5. 结果：在广东 2024 年时序数据与 IEEE118 全节点拓扑上验证框架有效。

---

# 1. Introduction

## 1.1 背景

- 极端天气下关键基础设施运行越来越依赖多源时空数据。
- 新能源不确定性、元件脆弱性、故障传播、风险预警与调度决策彼此耦合。
- 这些数据通常异构、分散，且缺少统一表达与组织方式。

## 1.2 问题

- 原始时序数据难以直接服务下游优化。
- 风险概率、场景张量与图结构信息难以统一组织。
- 现有研究往往只覆盖单点任务，缺少端到端的数据产品链路。

## 1.3 本文目标

- 构建统一的不确定时空风险数据框架。
- 将多源输入转化为可复用、可压缩、可消费的数据产品。
- 支持图风险分析与下游决策。

## 1.4 主要贡献

建议写成 3 到 4 点：

1. 提出统一的概率时空风险数据框架。
2. 提出面向下游任务的场景压缩与风险图物化机制。
3. 设计风险感知图分析层，并输出结构化决策摘要。
4. 在真实年度时序与 IEEE118 拓扑上验证端到端有效性。

---

# 2. Problem Formulation

本节应尽量采用 ICDE 风格表述，而不是单纯领域背景介绍。

## 2.1 数据输入定义

- 多源时序数据：
  - 风电
  - 光伏
  - 负荷
  - 气象
- 静态拓扑数据：
  - 节点
  - 线路
  - 发电机
  - 负荷节点
- 场景标签与风险标签

## 2.2 场景数据对象定义

定义以下对象：

- historical series
- sampled trajectories
- representative scenarios
- scenario probabilities

## 2.3 风险图数据对象定义

定义以下对象：

- line failure probability time series
- contingency tensor
- node/edge feature tables
- warning summaries

## 2.4 下游任务接口定义

说明：

- 图分析模块消费哪些输入。
- 决策模块消费哪些输入。
- 最终输出哪些标准化结果产品。

---

# 3. Framework Overview

本节建议配整体框架图。

## 3.1 四模块框架总览

四个模块分别为：

1. Uncertainty Scenario Construction
2. Probabilistic Spatiotemporal Risk Graph Materialization
3. Risk-Aware Graph Analytics
4. Decision-Serving Resilience Analytics

## 3.2 数据流

说明各模块输入输出关系：

- `aligned_merged / DPGMM_input / TRIM_input`
- `typical_scenarios / probabilities`
- `line_failure_timeseries`
- `contingency_tensor`
- `line_risk_prediction / critical_load_risk`
- `dispatch / resilience / summary`

## 3.3 设计目标

建议强调三个关键词：

- compression
- materialization
- reusability

---

# 4. Uncertainty Scenario Construction

对应原始 Stage1。

## 4.1 数据预处理与输入组织

- `aligned_merged.csv`
- `DPGMM_input.csv`
- `TRIM_input.csv`
- 时间对齐与特征抽取

## 4.2 概率场景建模

- Rolling DPGMM
- annual trajectory sampling
- 200 sampled annual trajectories

## 4.3 场景压缩

- KMeans scenario reduction
- 10 representative yearly scenarios
- empirical scenario probabilities

## 4.4 数据产品输出

- `history_series.csv`
- `typical_scenarios.npy`
- `scenario_probabilities.csv`
- `uncertainty_report.json`

## 4.5 扩展版本（可选）

- Conditional / enhanced Stage1 作为增强研究线
- 不作为当前主链路，但可在讨论中作为增强方向说明

---

# 5. Probabilistic Spatiotemporal Risk Graph Materialization

对应原始 Stage2 与 Stage3。

## 5.1 元件失效概率构建

- 从天气与强度输入映射到线路故障概率
- `schloemer` 最终候选
- 输出 `line_failure_timeseries`

## 5.2 时空故障场景物化

- `c3po_ref`
- 从 line failure probabilities 到 contingency scenarios
- 生成 `contingency_tensor`

## 5.3 风险张量与统计摘要

- `line_probability_summary`
- `state_summary`
- 场景级统计量

## 5.4 数据产品输出

- `line_failure_timeseries_schloemer.csv`
- `contingency_tensor_c3po_ref.npy`
- `contingency_scenarios_c3po_ref.csv`

---

# 6. Risk-Aware Graph Analytics

对应原始 Stage6。

## 6.1 图结构输入构建

- 从 topology、contingency、weather 与 load priority profile 构建图输入
- 节点特征、边特征与时序上下文

## 6.2 风险感知图学习模型

- baseline GNN
- MetaPath-enhanced GNN
- A2 adaptive global attention
- training enhancements:
  - warmup
  - gate_reg
  - risk_weight
  - lower lr

## 6.3 风险摘要输出

- `line_risk_prediction.csv`
- `critical_load_risk.csv`
- `nk_failure_risk.csv`
- `warning_report.json`

## 6.4 数据接口价值

说明这些结果并非单纯模型输出，而是：

- 为 Stage7 提供结构化风险输入
- 形成 decision-serving warning summaries

---

# 7. Decision-Serving Resilience Analytics

对应原始 Stage4、Stage5、Stage7 与 Stage8。

## 7.1 负荷优先级与调度输入构造

- 从 contingency data 和 scenario data 生成调度可消费输入

## 7.2 韧性分析数据产品

- `policy_comparison.csv`
- `worst_scenario_shedding_detail.csv`
- `indicator_table.csv`
- `ewm_topsis_result.csv`

## 7.3 上下文调度决策

- Contextual dispatch
- SCUC / Stochastic_UC / Robust_UC 的选择逻辑
- Stage6 风险摘要如何进入决策层

## 7.4 标准化结果导出

- `scenario/`
- `warning/`
- `dispatch/`
- `resilience/`
- `summary/`

## 7.5 本模块作用

应明确说明：

- 该部分不仅是应用验证；
- 也是验证前面数据产品是否真正可消费、可复用的重要证据。

---

# 8. Experimental Evaluation

本节先列结构，后续再按结果填充。

## 8.1 实验对象

- Guangdong 2024
- IEEE118 full topology
- 72h failure modeling horizon
- 24h dispatch window

## 8.2 对比设置

建议分三类：

1. 场景构建对比
2. 图分析对比
3. 决策收益对比

## 8.3 场景数据产品质量

- distribution fit
- joint dependency
- time continuity
- extreme coverage

## 8.4 风险图分析效果

- Stage6 baseline vs A2
- label setting effects
- structure effects

## 8.5 下游任务收益

- Stage4 / Stage5 policy quality
- Stage7 dispatch metrics
- Stage8 standardized outputs

## 8.6 系统与数据层分析

后续若进一步增强 ICDE 风格，可加入：

- compression ratio
- runtime
- scalability
- reuse of intermediate products

---

# 9. Related Work

建议分 4 组组织。

## 9.1 Probabilistic scenario construction

对应 Stage1。

## 9.2 Spatiotemporal risk modeling on infrastructure networks

对应 Stage2 与 Stage3。

## 9.3 Graph analytics and GNNs for infrastructure risk

对应 Stage6。

## 9.4 Data-centric decision support and resilience analytics

对应 Stage4、Stage5 与 Stage7。

---

# 10. Discussion

本节很重要，可使稿件显得更成熟。

## 10.1 当前框架优势

- 统一数据链路
- 场景压缩与图物化
- 风险分析与决策接口统一

## 10.2 当前限制

- enhanced Stage1 尚未稳定进入主链路
- 多窗口验证仍然不足
- 数据规模与效率实验仍需补足

## 10.3 未来扩展

- 更大规模图
- 更多极端天气过程
- 更强的不确定图数据管理能力

---

# 11. Conclusion

结论建议强调：

- 本文不是只做单点风险预测；
- 而是构建了一个从不确定场景、风险图物化、图分析到决策服务的统一框架；
- 并在真实年度时序与 IEEE118 场景中验证了其可行性与有效性。

---

# 附录（可选）

## A. 文件与数据对象映射

将 `paper_submission_package` 中的文件结构映射到论文数据对象。

## B. 各阶段输入输出表

整理每个模块的输入、输出和中间数据产品，便于投稿后 rebuttal 或补充说明。

## C. 补充实验

后续补充的数据规模实验、效率实验和敏感性实验可以放入附录。

---

## 当前主线提醒

后续撰写过程中，建议始终围绕以下主线展开：

> 本文不是在讲 8 个分散阶段，而是在讲一个从不确定时空数据到风险图数据产品，再到决策服务分析的统一数据框架。

