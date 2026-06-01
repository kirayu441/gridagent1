# GridAgent `formal2024` 全量实验结果报告（Baseline）

## 1. 实验信息

- 运行模式：`baseline`
- 配置文件：`C:\Users\yuhan\Desktop\gridagent1\configs\gridagent_framework.formal2024.json`
- 运行目录：`C:\Users\yuhan\Desktop\gridagent1\results\gridagent_framework\formal2024_full_baseline_20260310_233109`
- 标准化结果目录：`C:\Users\yuhan\Desktop\gridagent1\results\formal2024_full_baseline_20260310_233109_standard`
- 运行时间：2026-03-10 23:31:33 到 23:38:03（约 6 分 30 秒）
- 场景链路：`Schloemer + C3PO_ref + reserve_ratio=0.3 + n_scenarios=256`

---

## 2. 数据与实验规模

| 项目 | 数值 |
|---|---:|
| 节点数 | 15 |
| 线路数 | 15 |
| 发电单元数 | 10（热 1、风 1、光 8） |
| 风光典型场景数 | 10（风）+ 10（光） |
| 风光时间点 | 8784 |
| 故障概率时间点 | 72 小时 |
| 故障场景数 | 256 |
| 故障场景总记录 | 18432（256×72） |

---

## 3. 各模块结果

## 3.1 场景与失效（Scenario）

| 指标 | 数值 |
|---|---:|
| 风场景范围 | 0.000074 ～ 0.983340 |
| 光场景范围 | 0.000011 ～ 0.930021 |
| 线路失效概率均值 | 0.178328 |
| 线路失效概率最大值 | 1.000000 |
| 故障场景平均失效线路数 | 2.675998 |
| `outage_line_count >= 2` 比例 | 0.334256 |
| `outage_line_count >= 4` 比例 | 0.220432 |
| 平均失供负荷节点数 | 0.947103 |

Top-5 脆弱线路（按 `p_line_mean`）：

| line_id | p_line_mean | p_line_max |
|---|---:|---:|
| L4 | 0.237089 | 1.000000 |
| L10 | 0.230573 | 1.000000 |
| L0 | 0.225883 | 1.000000 |
| L11 | 0.222674 | 1.000000 |
| L12 | 0.198046 | 0.999998 |

---

## 3.2 预警模块（Warning）

| 指标 | 数值 |
|---|---:|
| 线路风险等级分布 | HIGH=5, MEDIUM=5, LOW=5 |
| 期望 N-k 失效线路数 | 1.040663 |
| 最可能 N-k 场景 | S1（0 线失效），概率 0.419667 |
| GNN 有效训练轮数 | 64 |
| GNN 最优验证 MSE | 0.022582 |

Top-5 高风险线路：

| line_id | risk_prob | risk_level | predicted_fail_hour |
|---|---:|---|---:|
| L8 | 0.409398 | HIGH | 6 |
| L12 | 0.408007 | HIGH | 6 |
| L4 | 0.405232 | HIGH | 7 |
| L6 | 0.403796 | HIGH | 6 |
| L3 | 0.402361 | HIGH | 6 |

关键负荷失供风险 Top-3：

| node | load_type | outage_prob |
|---|---|---:|
| load_bus_1 | primary | 0.127667 |
| load_bus_12 | secondary | 0.122000 |
| load_bus_13 | secondary | 0.091000 |

---

## 3.3 调度模块（Dispatch，按场景切换）

策略切换结果：

| selected_strategy | hours_selected |
|---|---:|
| Robust_UC | 17 |
| SCUC | 7 |

调度关键指标：

| 指标 | 数值 |
|---|---:|
| 调度时长 | 24 小时 |
| 总发电量（调度出力累计） | 7.152762 |
| 总备用上调 | 4.421327 |
| 平均备用上调 | 0.184222 |
| 总切负荷 | 18.849255 |
| 非零切负荷记录数 | 227 |
| 线路过载次数 | 0 |
| 最大线路负载率 | 0.046293 |
| 平均线路负载率 | 0.008108 |

Contextual_Adaptive 综合结果（来自 dispatch report）：

| 指标 | 数值 |
|---|---:|
| total_cost | 25878.0621 |
| generation_cost | 929.8590 |
| reserve_cost | 163.8261 |
| startup_shutdown_cost | 12.0000 |
| load_shedding_penalty | 24772.3770 |
| EENS | 18.8493 |
| priority_index | 0.6307 |
| reliability_score | 0.3605 |
| rapidity | 0.0498 |

---

## 3.4 韧性评估（Resilience）

多指标结果：

| policy | Priority | Robustness | Rapidity | Sustainability |
|---|---:|---:|---:|---:|
| priority_with_reserve | 0.669147 | 0.351863 | 0.049787 | 0.340968 |
| uniform_with_reserve | 0.351863 | 0.351863 | 0.049787 | 0.340671 |
| priority_no_reserve | 0.413526 | 0.227040 | 0.049787 | 0.229043 |

TOPSIS 排名：

| policy | score | rank |
|---|---:|---:|
| priority_with_reserve | 1.000000 | 1 |
| uniform_with_reserve | 0.386773 | 2 |
| priority_no_reserve | 0.159556 | 3 |

---

## 4. 结果解读

1. 全链路在 `formal2024` 全量配置下可稳定跑通，得到完整 `stage1~stage7` 输出。  
2. 预警结果呈现分层（5/5/5），说明风险刻画有分辨率，不是“一刀切高风险”。  
3. 调度策略在 24 小时内出现明显切换（Robust_UC 17h, SCUC 7h），符合“不同场景用不同策略”的设计目标。  
4. 线路潮流无过载（`overload_count=0`），但切负荷成本仍高，说明当前主要瓶颈在供给紧张和风险约束，而不是线路越限。  
5. 韧性评估显示 `priority_with_reserve` 仍为最优策略，和此前小型测试结论一致，具有稳定性。

---

## 5. 对应文件入口

- 框架总报告：`C:\Users\yuhan\Desktop\gridagent1\results\gridagent_framework\formal2024_full_baseline_20260310_233109\framework_report.json`
- 标准化摘要：`C:\Users\yuhan\Desktop\gridagent1\results\formal2024_full_baseline_20260310_233109_standard\summary\experiment_summary.json`
- 标准化目录：
  - `C:\Users\yuhan\Desktop\gridagent1\results\formal2024_full_baseline_20260310_233109_standard\warning`
  - `C:\Users\yuhan\Desktop\gridagent1\results\formal2024_full_baseline_20260310_233109_standard\dispatch`
  - `C:\Users\yuhan\Desktop\gridagent1\results\formal2024_full_baseline_20260310_233109_standard\resilience`
  - `C:\Users\yuhan\Desktop\gridagent1\results\formal2024_full_baseline_20260310_233109_standard\scenario`

