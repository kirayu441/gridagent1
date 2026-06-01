# Stage6 A3 调参记录

生成时间：2026-04-27

## 调参目标

针对 A3 `MetaPath + Adaptive Context Attention` 效果不如预期的问题，先不改模型结构，只调整训练策略：

- lower lr
- risk_weight
- metapath_warmup
- gate_reg
- attention entropy regularization

## 5-seed 调参结果

输出目录：

`final_results/stage6_a3_tuned_strategy_v1`

参数：

| 参数 | 值 |
|---|---:|
| `lr` | 0.0025 |
| `weight_decay` | 0.0001 |
| `risk_weight_alpha` | 1.0 |
| `risk_weight_beta` | 2.0 |
| `risk_weight_threshold` | 0.1 |
| `metapath_gate_reg_lambda` | 0.0005 |
| `metapath_attention_entropy_reg_lambda` | 0.0005 |
| `metapath_warmup_epochs` | 25 |

结果：

| seed | val_mae | best_val_mse | val_high_risk_mae | gate_mean | epochs |
|---:|---:|---:|---:|---:|---:|
| 42 | 0.098341 | 0.013976 | 0.236277 | 0.948288 | 84 |
| 43 | 0.035938 | 0.003085 | 0.115738 | 0.999800 | 231 |
| 44 | 0.042335 | 0.003649 | 0.114746 | 0.999982 | 137 |
| 45 | 0.026725 | 0.001313 | 0.114218 | 0.999628 | 137 |
| 46 | 0.030096 | 0.002516 | 0.131457 | 0.999779 | 299 |

均值：

| model | n | val_mae_mean | val_mae_std | best_val_mse_mean | val_high_risk_mae_mean |
|---|---:|---:|---:|---:|---:|
| A3 tuned strategy v1 | 5 | 0.046687 | 0.029480 | 0.004908 | 0.142487 |

原始 PlanA 对比：

| model | n | val_mae_mean | val_mae_std | best_val_mse_mean | high_risk_mae_mean |
|---|---:|---:|---:|---:|---:|
| A1 MetaPath Fixed | 5 | 0.022069 | 0.006740 | 0.001058 | 0.074713 |
| A2 Adaptive Global | 5 | 0.023948 | 0.005249 | 0.001087 | 0.070424 |
| A3 Adaptive Context | 5 | 0.024102 | 0.004247 | 0.001234 | 0.089740 |

结论：该组调参明显退化，不建议作为最终配置。

## Seed 42 探针

输出目录：

`final_results/stage6_a3_tuning_probe_seed42`

| case | val_mae | best_val_mse | high_risk_mae | gate_mean | 说明 |
|---|---:|---:|---:|---:|---|
| v2_mild | 0.032914 | 0.002972 | 0.155758 | 0.993848 | 温和 risk + reg + warmup |
| v3_reg_only | 0.026664 | 0.002534 | 0.155711 | 0.994129 | 只开 reg + warmup |
| v4_risk_only_mild | 0.037970 | 0.003015 | 0.123233 | 0.999827 | 只开温和 risk + warmup |
| v5_lr_only_warm | 0.029236 | 0.002767 | 0.156817 | 0.999969 | lower lr + warmup |

Seed 42 原始结果：

| model | val_mae | best_val_mse | high_risk_mae |
|---|---:|---:|---:|
| A1 | 0.021099 | 0.000624 | 0.062177 |
| A2 | 0.020941 | 0.000597 | 0.059412 |
| A3 | 0.022478 | 0.001175 | 0.108644 |

结论：在当前实现下，单纯加入 warmup、gate 正则、entropy 正则、risk weight 和 lower lr 不能改善 A3，说明问题主要不在训练旋钮，而在 A3 上下文注意力的建模方式。

## 原因判断

1. A3 的上下文条件化只使用 `edge_dyn_x`，未使用 `edge_static_x`、`edge_repr`、两端节点状态或物理应力特征。
2. `score += einsum(score_feat, cond)` 是较强的加性扰动，容易改变 MetaPath 注意力分布。
3. gate 在多数运行中仍接近 1，正则未能有效防止 MetaPath 残差分支过度接管。
4. 数据规模较小，A3 额外参数更容易过拟合或 seed 敏感。
5. risk-weighted loss 与当前早停指标 `val_mse` 不完全一致，可能使训练优化方向与模型选择指标错位。

## 后续建议

1. 暂时不把当前 A3 作为最终主方法，优先使用 A1 或 A2 作为 Stage6 主结果。
2. 若继续优化 A3，应优先改结构：将 `edge_context` 从 `edge_dyn_x` 扩展为 `concat(edge_repr, edge_dyn_x, edge_static_x)`。
3. 为 A3 增加 context scale 参数，例如 `score = score + gamma * context_score`，并将 `gamma` 初始化为较小值。
4. 将早停指标改为与目标一致的组合指标，例如 `val_mse + lambda * val_high_risk_mae` 或 weighted validation loss。
5. 在结构改完后再重新小范围搜索 warmup/gate/entropy/risk_weight。
