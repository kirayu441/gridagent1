# Stage6 预警能力提升汇报（2026-04-08）

## 1. 汇报范围

本汇报仅针对本次 Stage6（预警模块）性能提升结果进行整理，覆盖：

- 本次运行内的模型对比（`metapath_v1` vs `baseline_gnn`）
- 与历史全链路基线运行的 Stage6 指标对比
- 训练稳定性与结果可信性说明

不包含后续“真实物理电流流向元路径”等新增方向化元路径改进方案。

---

## 2. 实验对象与对比口径

### 2.1 本次主运行（用于汇报）

- 运行目录：`results/gridagent_framework/formal2024_full_metapath_tuned_20260407/stage6_warning`
- 评估时域：`2024-09-01 00:00:00` 到 `2024-09-01 23:00:00`（24 小时）
- 训练/验证切分：训练 50 个时段，验证 22 个时段
- 实际有效训练轮数：131（请求 700，早停生效）

### 2.2 历史基线运行（横向参照）

- 对比目录：`results/gridagent_framework/formal2024_full_baseline_20260310_233109/stage6_warning`

---

## 3. 关键结果（一）本次运行内模型对比

对比文件：`model_comparison.csv`

| 指标 | baseline_gnn | metapath_v1 | 相对改善 |
|---|---:|---:|---:|
| val_mae | 0.12810 | 0.02860 | 77.67% |
| val_rmse | 0.15431 | 0.03632 | 76.46% |
| horizon_mae | 0.44479 | 0.01566 | 96.48% |
| horizon_rmse | 0.58027 | 0.02983 | 94.86% |
| val_high_risk_mae | 0.36883 | 0.04921 | 86.66% |
| horizon_high_risk_mae | 0.81463 | 0.02327 | 97.14% |
| horizon_top_risk_mae | 0.88172 | 0.01293 | 98.53% |
| best_val_mse | 0.02381 | 0.001319 | 94.46% |

结论：在本次同口径同数据对比下，Stage6 预警模型在整体误差与高风险区误差上均有显著下降。

---

## 4. 关键结果（二）与历史全链路基线对比

对比口径：`warning_report.json` 中 validation 指标（历史基线 vs 本次结果）

| 指标 | 历史基线（2026-03-10） | 本次结果（2026-04-07） | 相对改善 |
|---|---:|---:|---:|
| val_mae | 0.12218 | 0.02860 | 76.59% |
| val_rmse | 0.15027 | 0.03632 | 75.83% |
| val_brier | 0.02258 | 0.001319 | 94.16% |
| best_val_mse | 0.02258 | 0.001319 | 94.16% |
| epochs_effective | 64 | 131 | 训练更充分 |

结论：相对 2026-03-10 的全链路基线，Stage6 的核心验证误差与概率质量指标（Brier/MSE）均实现量级改善。

---

## 5. 训练稳定性与可解释性补充

来源：`warning_report.json` 与 `metapath_attention_summary.csv`

- 优化器（实际记录）：`lr=0.00315`，`weight_decay=0.00015`
- 风险加权训练开启：`risk_weight_alpha=1.0`，`risk_weight_beta=2.0`，阈值 `0.1`
- 元路径 warmup：12 轮
- gate 均值：`0.9999988`（元路径分支在最终阶段被充分使用）
- 语义注意力均值：
  - `share_bus`：0.999909
  - `source_bridge`：0.0000519
  - `primary_load_bridge`：0.0000321
  - `two_hop_topology`：0.0000066

解释：当前数据分布下，模型主要依赖 `share_bus` 语义通道完成增益，其余通道贡献较小但保持可学习状态。

---

## 6. 本次 MetaPath 改进总结（仅本轮）

本节只列“相对以前 MetaPath（`results/early_warning/formal2024_metapath_v1_tuned`）”的变化：

1. 训练目标从“普通 MSE”升级为“风险加权目标”。  
以前：无 `objective` 配置。  
本次：`alpha=1.0`、`beta=2.0`、`threshold=0.1`，高风险样本权重更高。

2. 新增 warmup 机制（以前没有）。  
以前：`metapath_warmup_epochs=0`（等效无 warmup）。  
本次：`metapath_warmup_epochs=12`，前期逐步放大元路径残差，训练更稳。

3. 新增 gate 正则（以前没有）。  
以前：`metapath_gate_reg_lambda=0.0`。  
本次：`metapath_gate_reg_lambda=0.0002`，减少门控分支训练震荡。

4. 元路径邻居裁剪更激进。  
以前：`metapath_topk=4`。  
本次：`metapath_topk=3`，减少噪声邻居干扰。

5. 优化器强度重配。  
以前：`lr=0.0042`、`weight_decay=0.00005`。  
本次：`lr=0.00315`、`weight_decay=0.00015`（更保守学习率 + 更强正则）。

6. 元路径分支由“弱参与”变为“强参与”。  
以前：`metapath_gate_mean=0.0623`（门控大多关闭）。  
本次：`metapath_gate_mean=0.999999`（门控几乎全开）。

7. 注意力从“均匀分配”变为“主通道聚焦”。  
以前四条路径权重约均分（`0.24~0.26`）。  
本次几乎集中在 `share_bus=0.999909`，语义利用更聚焦。

8. 与旧版 MetaPath 的结果差异（仅作事实对照）。  
`val_mae: 0.33937 -> 0.02860`，`best_val_mse: 0.21458 -> 0.001319`。  
说明本轮 MetaPath 方案整体效果明显优于旧版 MetaPath。

说明：旧版 MetaPath 使用的是 `wang_qmc` 标签张量，而本次使用 `c3po_ref` 标签张量，标签分布不同。上述结果提升是“模型改进 + 训练策略改进 + 标签分布变化”共同作用，不应简单归因为单一改动。  

---

## 7. 最终结论（可直接对外复述）

1. 本次 Stage6 预警能力提升已被同口径对比明确验证，核心误差指标降幅约 76%~96%。  
2. 高风险相关误差（尤其 horizon 高风险段）下降更明显，说明模型对关键风险区识别能力明显增强。  
3. 与历史全链路基线相比，本次结果在验证集概率预测质量（Brier/MSE）上达到约 94% 的改善。  
4. 本汇报结论仅覆盖“本次 Stage6 提升结果”，不涉及后续方向化元路径等新增方案。  
