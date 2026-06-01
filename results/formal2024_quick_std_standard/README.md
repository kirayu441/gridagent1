# formal2024_quick_std_standard 结果说明

本目录为 `formal2024` 小型测试（run tag: `formal2024_quick_std`）的标准化输出，结构如下：

- `summary/`
- `warning/`
- `dispatch/`
- `resilience/`
- `scenario/`

源运行目录：

- `C:\Users\yuhan\Desktop\gridagent1\results\gridagent_framework\formal2024_quick_std`

---

## 1) summary

| 文件 | 含义 | 主要来源 |
|---|---|---|
| `summary/experiment_summary.json` | 本次实验摘要（模式、时间、链路、标准输出路径） | `framework_report.json` 整理输出 |
| `summary/indicator_table.csv` | 韧性指标总表（含 TOPSIS） | `stage5_assessment/indicator_table.csv` |

## 2) warning

| 文件 | 含义 | 主要来源 |
|---|---|---|
| `warning/line_risk_prediction.csv` | 高风险线路预测（风险概率、等级、预计故障时刻） | `stage6_warning` |
| `warning/nk_failure_risk.csv` | N-k 故障规模概率分布 | `stage6_warning` |
| `warning/critical_load_risk.csv` | 关键负荷失供风险 | `stage6_warning` |

## 3) dispatch

| 文件 | 含义 | 主要来源 |
|---|---|---|
| `dispatch/generation_schedule.csv` | 机组分时出力计划（按机组展开） | `stage7_dispatch_optimization/contextual_dispatch_unit_schedule.csv` 透视生成 |
| `dispatch/reserve_schedule.csv` | 分时备用容量（当前含 `reserve_up`，`reserve_down` 为 0） | `stage7_dispatch_optimization/contextual_dispatch_unit_schedule.csv` 汇总 |
| `dispatch/load_shedding.csv` | 分时负荷切除策略（节点、负荷类型、切除量） | `stage7_dispatch_optimization/contextual_dispatch_load_shedding.csv` 字段映射 |
| `dispatch/line_flow.csv` | 分时线路潮流结果（潮流、限额、负载率、过载标记、策略） | `stage7_dispatch_optimization/line_flow.csv` |

## 4) resilience

| 文件 | 含义 | 主要来源 |
|---|---|---|
| `resilience/resilience_metrics.csv` | 多指标韧性评估（Priority/Robustness/Rapidity/Sustainability） | `stage5_assessment/indicator_table.csv` 子集 |
| `resilience/topsis_ranking.csv` | 综合评分与排序（TOPSIS） | `stage5_assessment/ewm_topsis_result.csv` 字段映射 |

## 5) scenario

| 文件 | 含义 | 主要来源 |
|---|---|---|
| `scenario/wind_solar_scenarios.csv` | 风光典型场景（按时间展开多场景列） | `stage1_wind_pv/formal2024/typical_scenarios_long.csv` 重排 |
| `scenario/component_failure_prob.csv` | 组件（线路）失效概率时序 | `stage2_failure/schloemer/line_failure_timeseries_schloemer.csv` 字段映射 |
| `scenario/contingency_scenarios.csv` | 空间-时间故障场景（含 `failed_lines` 集合） | `stage3_contingency/schloemer/contingency_scenarios_c3po_ref.csv` |

---

## 生成方式

本目录由脚本自动导出：

- `C:\Users\yuhan\Desktop\gridagent1\scripts\export_standard_results.py`

执行命令：

```powershell
python scripts/export_standard_results.py --run-root results/gridagent_framework/formal2024_quick_std --output-root results/formal2024_quick_std_standard
```
