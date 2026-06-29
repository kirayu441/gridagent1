# 论文实验输出整理状态

本文件按“是否已有真实输出文件支撑论文表格/图”整理。新增表格由 `scripts/collect_paper_experiment_outputs.py` 从当前仓库已有实验结果汇总生成。

## 输出目录

- 主输出目录：`result_final/paper_experiment_outputs`
- 论文包同步目录：`paper_submission_package/results/paper_experiments`

## 已整理输出文件

| 文件 | 对应实验 | 当前可用性 | 说明 |
|---|---|---|---|
| `dataset_statistics.csv` | E1 数据集统计 | 可用 | 使用 IEEE118-full 主实验链路统计，避免误用 15-line formal_guangdong_2024 小拓扑 |
| `main_prediction_comparison.csv` | E8 主模型 vs 基线模型 | 部分可用 | 已有 MAE/RMSE/high-risk MAE/训练时间；Recall@10 和 Hit@10 仍需保存预测或重跑 |
| `topk_risk_identification.csv` | E9 Top-k 高风险线路识别 | 主模型可用 | 基于最终线路风险排序与标准化故障概率 max ranking 计算 |
| `ablation_study.csv` | E10 消融实验 | 部分可用 | A0/A1/A2/A3 五随机种子 MAE/RMSE/high-risk MAE 已汇总；Recall@10 未记录 |
| `graph_structure_analysis.csv` | E11 图结构有效性 | 代理可用 | 用 MLP/no explicit graph 与 GCN/GAT/GraphSAGE/STGCN/MetaPath 代理比较；random/fully connected 仍需专门实验 |
| `downstream_dispatch_utility.csv` | E12 下游调度效用 | 部分可用 | 已整理 Stage7 调度模型对比；no warning/prior only/MLP warning 仍需专门预警输入对比 |
| `multi_window_evaluation.csv` | E13 多时间窗口 | 部分可用 | 当前只有 2024-09-01 00:00 和 17:00 两个快照 |
| `risk_label_distribution.csv` | E14 风险标签分布 | 可用 | 基于 Stage6 输入的 `p_line` 风险概率分箱 |
| `runtime_scalability.csv` | E15 运行效率与可扩展性 | 可用 | 汇总已有 Stage6 模型训练时间和 Stage7 调度运行时间 |
| `experiment_completion_status.csv` | 总状态表 | 可用 | 标记每个新增实验表的完成程度 |

## 仍建议重跑或补充的实验

1. `Historical Average`、`prior only`、`LSTM` 等尚未在最终主比较表中找到同口径输出。
2. `main_prediction_comparison.csv` 的 `recall_at_10`、`hit_at_10` 需要模型预测明细或重跑 Stage6 时记录排名指标。
3. `ablation_study.csv` 的 `recall_at_10` 也需要 A0/A1/A2/A3 各 run 的预测明细。
4. `graph_structure_analysis.csv` 目前是代理实验；若论文明确写 no graph/random graph/fully connected graph，需要新增三种图构造实验。
5. `downstream_dispatch_utility.csv` 目前是调度模型对比；若论文明确写 no warning/prior only/MLP warning，需要重跑 Stage7 的不同预警输入链路。
6. `multi_window_evaluation.csv` 目前只有两个窗口，正式论文建议至少扩展到 4-6 个代表性窗口。
