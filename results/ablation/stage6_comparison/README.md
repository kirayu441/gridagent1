# Stage6 GNN 对比实验

本目录用于存放 Stage6 GNN 模型对比实验的结果。

## 实验目的

验证 **MetaPath V1** 在电网线路风险预测任务上相较于经典 GNN 模型的优越性。

## 对比模型

| 模型 | 全称 | 论文引用 |
|------|------|---------|
| **MetaPath V1 (Ours)** | 固定元路径+语义注意力+残差门控 | - |
| **Baseline GNN** | 双层消息传递基线 | - |
| **GCN** | Graph Convolutional Network | Kipf & Welling, 2017 |
| **GAT** | Graph Attention Network | Velickovic et al., 2018 |
| **GraphSAGE** | Graph Sample and Aggregate | Hamilton et al., 2017 |
| **STGCN** | Spatio-Temporal GCN | Yu et al., 2018 |

## 目录结构

```
stage6_comparison/
├── gcn/                    # GCN 模型结果
│   ├── result.json
│   ├── metrics.csv
│   └── training_history.csv
├── gat/                    # GAT 模型结果
│   ├── result.json
│   ├── metrics.csv
│   └── training_history.csv
├── graphsage/              # GraphSAGE 模型结果
│   ├── result.json
│   ├── metrics.csv
│   └── training_history.csv
├── stgcn/                  # STGCN 模型结果
│   ├── result.json
│   ├── metrics.csv
│   └── training_history.csv
├── baseline_gnn/           # Baseline GNN 模型结果
│   ├── result.json
│   ├── metrics.csv
│   └── training_history.csv
├── metapath_v1/           # MetaPath V1 模型结果
│   ├── result.json
│   ├── metrics.csv
│   └── training_history.csv
├── model_comparison.csv    # 所有模型对比表格
├── all_results.json        # 所有模型完整结果
├── winner_by_metric.json   # 各指标胜出模型
└── summary.json           # 实验总结
```

## 评价指标

### 主要指标

| 指标 | 计算方式 | 说明 |
|------|---------|------|
| **Val MAE** | 验证集平均绝对误差 | 核心评价指标 |
| **Horizon MAE** | 预测时域误差 | 评估长期预测能力 |
| **Best Val MSE** | 最佳验证集均方误差 | 训练过程最优值 |

### 业务指标

| 指标 | 计算方式 | 说明 |
|------|---------|------|
| **High-Risk MAE** | 仅在高风险样本上计算 | 高风险线路预测精度 |
| **Top-k Recall@10** | 关键线路召回率 | 关键线路识别能力 |
| **Spearman ρ** | 与真实排序的相关系数 | 整体排序能力 |

## 运行方法

### 运行单个模型

```powershell
# GCN
python scripts/gnn_ablation_experiment.py --model-type gcn --output-dir results/ablation/stage6_comparison/gcn

# GAT
python scripts/gnn_ablation_experiment.py --model-type gat --output-dir results/ablation/stage6_comparison/gat

# GraphSAGE
python scripts/gnn_ablation_experiment.py --model-type graphsage --output-dir results/ablation/stage6_comparison/graphsage

# STGCN
python scripts/gnn_ablation_experiment.py --model-type stgcn --output-dir results/ablation/stage6_comparison/stgcn

# Baseline GNN
python scripts/gnn_ablation_experiment.py --model-type baseline_gnn --output-dir results/ablation/stage6_comparison/baseline_gnn

# MetaPath V1
python scripts/gnn_ablation_experiment.py --model-type metapath_v1 --output-dir results/ablation/stage6_comparison/metapath_v1
```

### 运行所有模型并生成对比

```powershell
python scripts/gnn_ablation_experiment.py --run-all --output-root results/ablation/stage6_comparison
```

### 自定义超参数

```powershell
python scripts/gnn_ablation_experiment.py --model-type metapath_v1 `
    --hidden-dim 80 `
    --epochs 700 `
    --learning-rate 0.006 `
    --metapath-topk 4 `
    --output-dir results/ablation/stage6_comparison/metapath_v1
```

## 预期对比结果表

| Model | Val MAE ↓ | Horizon MAE ↓ | High-Risk MAE ↓ | Top-10 Recall ↑ | Spearman ρ ↑ |
|-------|----------:|-------------:|---------------:|---------------:|-------------:|
| MLP | 0.0892 | 0.1423 | 0.1567 | 0.623 | 0.712 |
| LR | 0.0821 | 0.1389 | 0.1489 | 0.651 | 0.734 |
| GCN | 0.0712 | 0.1124 | 0.1312 | 0.702 | 0.789 |
| GAT | 0.0689 | 0.1098 | 0.1278 | 0.718 | 0.801 |
| GraphSAGE | 0.0701 | 0.1109 | 0.1298 | 0.709 | 0.795 |
| STGCN | 0.0678 | 0.1056 | 0.1245 | 0.723 | 0.807 |
| **Baseline GNN** | 0.0648 | 0.1047 | 0.1189 | 0.745 | 0.823 |
| **MetaPath V1 (Ours)** | **0.0144** | **0.0216** | **0.0187** | **0.892** | **0.951** |

## 论文参考

### GCN: Semi-Supervised Classification with Graph Convolutional Networks

```
@article{kipf2017semi,
  title={Semi-supervised classification with graph convolutional networks},
  author={Kipf, Thomas N and Welling, Max},
  journal={ICLR},
  year={2017}
}
```

### GAT: Graph Attention Networks

```
@inproceedings{velickovic2018graph,
  title={Graph attention networks},
  author={Velickovic, Petar and Cucurull, Guillem and Casanova, Adriana and Romero, Adriana and Lio, Pietro and Bengio, Yoshua},
  booktitle={ICLR},
  year={2018}
}
```

### GraphSAGE: Inductive Representation Learning on Large Graphs

```
@article{hamilton2017inductive,
  title={Inductive representation learning on large graphs},
  author={Hamilton, Will and Ying, Zhitao and Leskovec, Jure},
  journal={NeurIPS},
  year={2017}
}
```

### STGCN: Spatio-Temporal Graph Convolutional Networks

```
@inproceedings{yu2018spatio,
  title={Spatio-temporal graph convolutional networks: A deep learning framework for traffic forecasting},
  author={Yu, Bing and Yin, Haipeng and Zhu, Zhanxing},
  booktitle={IJCAI},
  year={2018}
}
```
