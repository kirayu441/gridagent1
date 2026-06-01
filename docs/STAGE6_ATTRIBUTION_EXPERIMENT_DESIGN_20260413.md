# Stage6 归因拆分实验设计（2026-04-13）

## 目标

回答 Stage6 提升来源：

1. 模型结构（`metapath_v1`）是否独立有效  
2. 标签方法（`c3po_ref` / `wang_qmc`）影响有多大  
3. 训练策略（`warmup` / `gate_reg` / `risk_weight`）各自贡献多少

---

## 控制变量原则

1. 固定 `grid/aligned/failure_csv/load_priority_csv`。  
2. 每次仅改变一个归因因子。  
3. 多随机种子重复（建议 10，最低 5）。  
4. 统一指标：`val_mae`, `val_rmse`, `best_val_mse`, `val_high_risk_mae`。  

---

## 实验块

1. Block A（标签 × 模型，训练策略全关）  
标签：`c3po_ref`, `wang_qmc`  
模型：`baseline_gnn`, `metapath_v1`  
用途：检验结构是否在同标签下仍有效。

2. Block B（标签 × warmup × gate_reg × risk_weight）  
模型固定 `metapath_v1`。  
用途：拆分训练策略主效应与组合效应。

3. Block C（旧版 MetaPath 预设 vs 新版 MetaPath 预设）  
每个标签都做 old/new 对照。  
用途：回答“这次比以前 MetaPath 为什么提升更大”。

---

## 自动化脚本

脚本：`scripts/run_stage6_attribution_experiment.py`

输出目录（自动时间戳）：
`results/early_warning/<tag>_<timestamp>/`

关键产物：

1. `experiment_manifest.json`：实验配置  
2. `experiment_matrix.csv`：完整实验矩阵  
3. `all_runs.csv`：逐运行结果汇总  
4. `blockA_summary.csv` / `blockB_*` / `blockC_summary.csv`：分块统计  
5. `attribution_report.md`：自动汇总报告

---

## 推荐执行命令

先做 smoke：

```powershell
python scripts\run_stage6_attribution_experiment.py --dry-run true --max-runs 3 --tag stage6_attr_smoke
```

再做正式（5 seeds）：

```powershell
python scripts\run_stage6_attribution_experiment.py --seeds 42,43,44,45,46 --tag stage6_attr_full
```

如果要 10 seeds：

```powershell
python scripts\run_stage6_attribution_experiment.py --seeds 42,43,44,45,46,47,48,49,50,51 --tag stage6_attr_full10
```

