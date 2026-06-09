"""
GNN Ablation Experiment: Stage6 Model Comparison
===============================================
This script compares MetaPath V1 against classical GNN models for power grid 
line risk prediction.

Comparison Models:
- MetaPath V1 (Ours): Fixed metapath + semantic attention + residual gating
- Baseline GNN: Two-layer message passing (no metapath)
- GCN: Graph Convolutional Network (Kipf & Welling, 2017)
- GAT: Graph Attention Network (Velickovic et al., 2018)
- GraphSAGE: Graph Sample and Aggregate (Hamilton et al., 2017)
- STGCN: Spatio-Temporal Graph Convolutional Networks (Yu et al., 2018)

References:
- Kipf & Welling (2017): Semi-supervised classification with GCN. ICLR.
- Velickovic et al. (2018): Graph attention networks. ICLR.
- Hamilton et al. (2017): Inductive representation learning. NeurIPS.
- Yu et al. (2018): Spatio-temporal GCN. IJCAI.

Usage:
    # Run single model
    python scripts/gnn_ablation_experiment.py --model-type gcn --output-dir results/ablation/stage6_gcn
    
    # Run all models and generate comparison
    python scripts/gnn_ablation_experiment.py --run-all --output-root results/ablation/stage6_comparison
    
    # Run with custom hyperparameters
    python scripts/gnn_ablation_experiment.py --model-type metapath_v1 --hidden-dim 80 --epochs 700
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from scipy.stats import spearmanr

# Import from existing gnn_warning_module
sys.path.insert(0, str(Path(__file__).parent))
from gnn_warning_module import (
    WarningDataset,
    build_dataset,
    load_failure_features,
    load_grid_topology,
    project_root,
)

# Import GNN models from the gnn_models package
from gnn_models import (
    GCNModel,
    GATModel,
    GraphSAGEModel,
    STGCNModel,
    BaselineGNNModel,
    MetaPathV1Model,
    MetaPathLocalResidualModel,
    MetaPathLocalRiskAttentionModel,
    MetaPathLocalRiskAttentionResidualModel,
    MLPModel,
    MODEL_REGISTRY,
)


# ============================================================================
# Data Types
# ============================================================================

@dataclass
class ExperimentConfig:
    """Configuration for a single experiment run."""
    model_type: str
    output_dir: Path
    
    # Data paths
    grid_path: Path = field(default_factory=lambda: project_root() / "data_final/formal_guangdong_2024/grid_topology.json")
    aligned_csv: Path = field(default_factory=lambda: project_root() / "data_final/formal_guangdong_2024/aligned_merged.csv")
    failure_csv: Path | None = None
    
    # Model hyperparameters
    hidden_dim: int = 80
    num_layers: int = 2
    learning_rate: float = 0.006
    weight_decay: float = 1e-4
    dropout: float = 0.1
    metapath_topk: int = 4
    
    # Training
    epochs: int = 700
    patience: int = 60
    seed: int = 42
    train_ratio: float = 0.6
    
    # Risk weighting (for metapath_v1)
    risk_weight_alpha: float = 0.5
    risk_weight_beta: float = 1.0
    risk_weight_threshold: float = 0.10
    risk_weight_on_metapath_only: bool = False
    metapath_gate_reg_lambda: float = 0.01
    metapath_attention_entropy_reg_lambda: float = 0.005
    metapath_warmup_epochs: int = 100
    rank_loss_beta: float = 0.0
    rank_loss_margin: float = 0.02
    rank_loss_min_diff: float = 0.02
    
    # High-risk evaluation
    high_risk_threshold: float = 0.10
    top_risk_quantile: float = 0.90
    
    # Ablation-specific
    delta_scale: float = 1.0
    
    # GAT-specific
    num_heads: int = 4
    
    # GraphSAGE-specific
    aggregation: str = 'mean'
    
    # STGCN-specific
    temporal_kernel: int = 3
    
    # Evaluation thresholds
    val_mae_threshold: float = 0.4
    horizon_mae_threshold: float = 0.15


@dataclass
class ExperimentResult:
    """Results from a single experiment run."""
    model_type: str
    config: dict
    
    # Training metrics
    train_time_seconds: float
    best_epoch: int
    final_train_loss: float
    final_val_loss: float
    
    # Primary metrics
    val_mae: float
    horizon_mae: float
    best_val_mse: float
    
    # High-risk metrics
    high_risk_mae: float
    high_risk_count: int
    high_risk_ratio: float
    
    # Top-k metrics
    top_risk_mae: float
    top_risk_count: int
    top_risk_ratio: float
    top_risk_threshold: float
    
    # Ranking metrics
    spearman_corr: float
    precision_at_5: float = float("nan")
    recall_at_5: float = float("nan")
    hit_at_5: float = float("nan")
    ndcg_at_5: float = float("nan")
    precision_at_10: float = float("nan")
    recall_at_10: float = float("nan")
    hit_at_10: float = float("nan")
    ndcg_at_10: float = float("nan")
    precision_at_20: float = float("nan")
    recall_at_20: float = float("nan")
    hit_at_20: float = float("nan")
    ndcg_at_20: float = float("nan")
    
    # Model info
    num_parameters: int = 0
    
    # Per-epoch history
    history: list[dict] = field(default_factory=list)
    
    # Winner determination
    winner_by_metric: dict[str, str] = field(default_factory=dict)


# ============================================================================
# Utility Functions
# ============================================================================

def compute_risk_weight_tensor(
    truth: torch.Tensor,
    alpha: float,
    beta: float,
    threshold: float,
) -> torch.Tensor:
    """Compute sample weights for risk-aware training."""
    thr = float(np.clip(threshold, 0.0, 1.0))
    base = torch.ones_like(truth)
    if float(alpha) > 0.0:
        base = base + float(alpha) * truth
    if float(beta) > 0.0:
        base = base + float(beta) * (truth >= thr).to(truth.dtype)
    return base


def weighted_mse_loss(pred: torch.Tensor, truth: torch.Tensor, weight: torch.Tensor) -> torch.Tensor:
    """Weighted MSE loss with normalization."""
    err2 = (pred - truth) ** 2
    return (err2 * weight).mean() / weight.mean().clamp_min(1e-6)


def pairwise_ranking_loss(
    pred: torch.Tensor,
    truth: torch.Tensor,
    margin: float,
    min_diff: float,
) -> torch.Tensor:
    """Hinge ranking loss over line pairs within one timestamp."""
    diff_truth = truth.unsqueeze(1) - truth.unsqueeze(0)
    mask = diff_truth > float(min_diff)
    if not bool(mask.any()):
        return pred.new_tensor(0.0)
    diff_pred = pred.unsqueeze(1) - pred.unsqueeze(0)
    loss = F.relu(float(margin) - diff_pred[mask])
    return loss.mean()


def evaluate_prob_metrics(
    pred: np.ndarray,
    truth: np.ndarray,
    high_risk_threshold: float = 0.10,
    top_risk_quantile: float = 0.90,
) -> dict[str, float]:
    """Evaluate probability prediction metrics."""
    pred_flat = np.asarray(pred, dtype=float).reshape(-1)
    truth_flat = np.asarray(truth, dtype=float).reshape(-1)

    if pred_flat.size == 0 or truth_flat.size == 0:
        return {
            "mae": float("nan"),
            "rmse": float("nan"),
            "brier": float("nan"),
            "high_risk_mae": float("nan"),
            "high_risk_count": 0.0,
            "high_risk_ratio": 0.0,
            "top_risk_mae": float("nan"),
            "top_risk_count": 0.0,
            "top_risk_ratio": 0.0,
            "high_risk_threshold": high_risk_threshold,
            "top_risk_quantile": top_risk_quantile,
            "top_risk_threshold": float("nan"),
        }

    err = pred_flat - truth_flat
    mse = float(np.mean(err ** 2))

    # High-risk metrics
    thr = float(np.clip(high_risk_threshold, 0.0, 1.0))
    mask_high = truth_flat >= thr
    high_count = int(mask_high.sum())
    if high_count > 0:
        err_high = err[mask_high]
        high_mae = float(np.mean(np.abs(err_high)))
    else:
        high_mae = float("nan")

    # Top-k metrics
    q = float(np.clip(top_risk_quantile, 0.0, 1.0))
    top_thr = float(np.quantile(truth_flat, q))
    mask_top = truth_flat >= top_thr
    top_count = int(mask_top.sum())
    if top_count > 0:
        err_top = err[mask_top]
        top_mae = float(np.mean(np.abs(err_top)))
    else:
        top_mae = float("nan")

    total = max(int(truth_flat.size), 1)
    return {
        "mae": float(np.mean(np.abs(err))),
        "rmse": float(np.sqrt(mse)),
        "brier": mse,
        "high_risk_mae": high_mae,
        "high_risk_count": float(high_count),
        "high_risk_ratio": float(high_count / total),
        "top_risk_mae": top_mae,
        "top_risk_count": float(top_count),
        "top_risk_ratio": float(top_count / total),
        "high_risk_threshold": thr,
        "top_risk_quantile": q,
        "top_risk_threshold": top_thr,
    }


def compute_spearman_correlation(pred: np.ndarray, truth: np.ndarray) -> float:
    """Compute Spearman rank correlation."""
    pred_flat = pred.reshape(-1)
    truth_flat = truth.reshape(-1)
    if len(pred_flat) < 2:
        return float("nan")
    corr, _ = spearmanr(pred_flat, truth_flat)
    return float(corr) if not np.isnan(corr) else 0.0


def _dcg(relevances: list[int]) -> float:
    return float(sum(rel / np.log2(i + 2) for i, rel in enumerate(relevances)))


def compute_topk_ranking_metrics(
    pred: np.ndarray,
    truth: np.ndarray,
    ks: tuple[int, ...] = (5, 10, 20),
) -> dict[str, float]:
    """Compute line-level Top-k metrics from validation predictions.

    The score for each line is the maximum predicted/true risk over the
    validation window. This matches the paper's line-ranking use case.
    """
    if pred.size == 0 or truth.size == 0:
        return {}

    pred_line_score = np.max(np.asarray(pred, dtype=float), axis=0)
    truth_line_score = np.max(np.asarray(truth, dtype=float), axis=0)
    pred_order = list(np.argsort(-pred_line_score))
    truth_order = list(np.argsort(-truth_line_score))

    metrics: dict[str, float] = {}
    for k in ks:
        kk = int(min(max(k, 1), len(pred_order), len(truth_order)))
        pred_top = set(pred_order[:kk])
        truth_top = set(truth_order[:kk])
        hits = len(pred_top & truth_top)
        metrics[f"precision_at_{k}"] = float(hits / max(len(pred_top), 1))
        metrics[f"recall_at_{k}"] = float(hits / max(len(truth_top), 1))
        metrics[f"hit_at_{k}"] = float(1.0 if hits > 0 else 0.0)
        relevances = [1 if idx in truth_top else 0 for idx in pred_order[:kk]]
        denom = _dcg([1] * kk)
        metrics[f"ndcg_at_{k}"] = float(_dcg(relevances) / denom) if denom > 0 else float("nan")

    return metrics


# ============================================================================
# Training Functions
# ============================================================================

def train_model(
    data: WarningDataset,
    config: ExperimentConfig,
) -> tuple[nn.Module, list[dict], int, float, float]:
    """Train a GNN model and return the best model."""
    
    torch.manual_seed(config.seed)
    np.random.seed(config.seed)
    
    device = torch.device("cpu")
    n_time = data.node_x.shape[0]
    
    # Data split
    split = int(np.floor(n_time * config.train_ratio))
    split = max(1, min(split, n_time - 1)) if n_time > 1 else 1
    idx_train = np.arange(0, split)
    idx_val = np.arange(split, n_time)
    
    # Prepare tensors
    node_x = torch.tensor(data.node_x, dtype=torch.float32, device=device)
    edge_dyn = torch.tensor(data.edge_dyn_x, dtype=torch.float32, device=device)
    edge_static = torch.tensor(data.edge_static_x, dtype=torch.float32, device=device)
    labels = torch.tensor(data.labels, dtype=torch.float32, device=device)
    
    node_to_idx = {b: i for i, b in enumerate(data.node_ids)}
    src_idx = torch.tensor([node_to_idx[int(b)] for b in data.from_bus], dtype=torch.long, device=device)
    dst_idx = torch.tensor([node_to_idx[int(b)] for b in data.to_bus], dtype=torch.long, device=device)
    
    # Build model
    model = build_model(config, data)
    model = model.to(device)
    
    # Prepare metapath data
    metapath_enabled = (
        config.model_type in {
            "metapath_v1",
            "metapath_local",
            "metapath_local_riskattn",
            "metapath_local_riskattn_resid",
        }
        and data.metapath_index is not None
        and data.metapath_mask is not None
        and data.metapath_names is not None
        and len(data.metapath_names) > 0
    )
    
    metapath_index_t: torch.Tensor | None = None
    metapath_mask_t: torch.Tensor | None = None
    
    if metapath_enabled:
        metapath_index_t = torch.tensor(data.metapath_index, dtype=torch.long, device=device)
        metapath_mask_t = torch.tensor(data.metapath_mask, dtype=torch.float32, device=device)
    
    # Optimizer
    eff_lr = float(config.learning_rate * 0.7) if metapath_enabled else float(config.learning_rate)
    eff_weight_decay = float(config.weight_decay * 0.5) if metapath_enabled else float(config.weight_decay)
    optimizer = torch.optim.AdamW(model.parameters(), lr=eff_lr, weight_decay=eff_weight_decay)
    
    # Risk weighting
    risk_weight_active = (
        (float(config.risk_weight_alpha) > 0.0 or float(config.risk_weight_beta) > 0.0)
        and (metapath_enabled or (not bool(config.risk_weight_on_metapath_only)))
    )
    
    # Regularization
    gate_reg_active = bool(metapath_enabled and float(config.metapath_gate_reg_lambda) > 0.0)
    attn_entropy_reg_active = bool(
        metapath_enabled and float(config.metapath_attention_entropy_reg_lambda) > 0.0
    )
    rank_loss_active = bool(float(config.rank_loss_beta) > 0.0)
    warmup_epochs = max(int(config.metapath_warmup_epochs), 0)
    
    # Training loop
    best_val = float("inf")
    best_state: dict[str, torch.Tensor] | None = None
    patience_count = 0
    history: list[dict] = []
    
    start_time = time.time()
    
    for ep in range(1, config.epochs + 1):
        model.train()
        train_loss = torch.tensor(0.0, device=device)
        train_gate_reg = torch.tensor(0.0, device=device)
        train_attn_entropy = torch.tensor(0.0, device=device)
        train_rank_loss = torch.tensor(0.0, device=device)
        
        # Warmup scale for metapath
        warmup_scale = 1.0
        if metapath_enabled and warmup_epochs > 0:
            warmup_scale = float(min(1.0, ep / warmup_epochs))
        
        for t in idx_train:
            # Forward pass
            if metapath_enabled:
                assert metapath_index_t is not None
                assert metapath_mask_t is not None
                
                pred_t, alpha_t, gate_t = model(
                    node_x[t],
                    edge_dyn[t],
                    edge_static,
                    src_idx,
                    dst_idx,
                    metapath_index=metapath_index_t,
                    metapath_mask=metapath_mask_t,
                    delta_scale=warmup_scale,
                    return_attention=True,
                )
            else:
                pred_t = model(node_x[t], edge_dyn[t], edge_static, src_idx, dst_idx)
                gate_t = None
                alpha_t = None
            
            # Compute loss
            if risk_weight_active:
                weight_t = compute_risk_weight_tensor(
                    truth=labels[t],
                    alpha=config.risk_weight_alpha,
                    beta=config.risk_weight_beta,
                    threshold=config.risk_weight_threshold,
                )
                pred_loss_t = weighted_mse_loss(pred_t, labels[t], weight_t)
            else:
                pred_loss_t = F.mse_loss(pred_t, labels[t])

            if rank_loss_active:
                rank_loss_t = pairwise_ranking_loss(
                    pred=pred_t,
                    truth=labels[t],
                    margin=float(config.rank_loss_margin),
                    min_diff=float(config.rank_loss_min_diff),
                )
                train_rank_loss = train_rank_loss + rank_loss_t
                pred_loss_t = pred_loss_t + float(config.rank_loss_beta) * rank_loss_t
            
            train_loss = train_loss + pred_loss_t
            
            # Regularization
            if gate_reg_active and gate_t is not None:
                train_gate_reg = train_gate_reg + torch.mean(gate_t ** 2)
            if attn_entropy_reg_active and alpha_t is not None:
                ent = -(alpha_t * torch.log(alpha_t.clamp_min(1e-8))).sum(dim=1)
                ent_norm = ent / float(np.log(max((data.metapath_names and len(data.metapath_names)) or 2, 2)))
                train_attn_entropy = train_attn_entropy + ent_norm.mean()
        
        # Average losses
        train_loss = train_loss / max(len(idx_train), 1)
        if rank_loss_active:
            train_rank_loss = train_rank_loss / max(len(idx_train), 1)
        if gate_reg_active:
            train_gate_reg = train_gate_reg / max(len(idx_train), 1)
            train_loss = train_loss + float(config.metapath_gate_reg_lambda) * train_gate_reg
        if attn_entropy_reg_active:
            train_attn_entropy = train_attn_entropy / max(len(idx_train), 1)
            train_loss = train_loss - float(config.metapath_attention_entropy_reg_lambda) * train_attn_entropy
        
        # Backward pass
        optimizer.zero_grad()
        train_loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=2.0)
        optimizer.step()
        
        # Validation
        model.eval()
        with torch.no_grad():
            if len(idx_val) > 0:
                val_loss = torch.tensor(0.0, device=device)
                for t in idx_val:
                    if metapath_enabled:
                        pred_t = model(
                            node_x[t], edge_dyn[t], edge_static, src_idx, dst_idx,
                            metapath_index=metapath_index_t,
                            metapath_mask=metapath_mask_t,
                            delta_scale=1.0,
                        )
                    else:
                        pred_t = model(node_x[t], edge_dyn[t], edge_static, src_idx, dst_idx)
                    val_loss = val_loss + F.mse_loss(pred_t, labels[t])
                val_loss = val_loss / len(idx_val)
            else:
                val_loss = train_loss.detach().clone()
        
        # Record history
        history.append({
            "epoch": float(ep),
            "train_mse": float(train_loss.item()),
            "val_mse": float(val_loss.item()),
            "warmup_scale": float(warmup_scale),
            "train_gate_reg": float(train_gate_reg.item()),
            "train_attn_entropy": float(train_attn_entropy.item()),
            "train_rank_loss": float(train_rank_loss.item()),
        })
        
        # Early stopping check
        if float(val_loss.item()) + 1e-8 < best_val:
            best_val = float(val_loss.item())
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
            patience_count = 0
        else:
            patience_count += 1
        
        if patience_count >= config.patience:
            break
    
    train_time = time.time() - start_time
    
    # Load best model
    if best_state is not None:
        model.load_state_dict(best_state)
    
    # Compute final losses
    model.eval()
    with torch.no_grad():
        final_train_loss = 0.0
        for t in idx_train:
            if metapath_enabled:
                pred_t = model(
                    node_x[t], edge_dyn[t], edge_static, src_idx, dst_idx,
                    metapath_index=metapath_index_t,
                    metapath_mask=metapath_mask_t,
                    delta_scale=1.0,
                )
            else:
                pred_t = model(node_x[t], edge_dyn[t], edge_static, src_idx, dst_idx)
            final_train_loss += float(F.mse_loss(pred_t, labels[t]).item())
        final_train_loss /= max(len(idx_train), 1)
        
        final_val_loss = 0.0
        for t in idx_val:
            if metapath_enabled:
                pred_t = model(
                    node_x[t], edge_dyn[t], edge_static, src_idx, dst_idx,
                    metapath_index=metapath_index_t,
                    metapath_mask=metapath_mask_t,
                    delta_scale=1.0,
                )
            else:
                pred_t = model(node_x[t], edge_dyn[t], edge_static, src_idx, dst_idx)
            final_val_loss += float(F.mse_loss(pred_t, labels[t]).item())
        final_val_loss /= max(len(idx_val), 1)
    
    best_epoch = len(history) - patience_count if patience_count > 0 else len(history)
    
    return model, history, best_epoch, final_train_loss, final_val_loss


def build_model(config: ExperimentConfig, data: WarningDataset) -> nn.Module:
    """Build model based on configuration."""
    
    node_dim = data.node_x.shape[2]
    edge_dyn_dim = data.edge_dyn_x.shape[2]
    edge_static_dim = data.edge_static_x.shape[1]
    
    if config.model_type == "gcn":
        return GCNModel(
            node_dim=node_dim,
            edge_dyn_dim=edge_dyn_dim,
            edge_static_dim=edge_static_dim,
            hidden_dim=config.hidden_dim,
            num_layers=config.num_layers,
            dropout=config.dropout,
        )
    
    elif config.model_type == "gat":
        return GATModel(
            node_dim=node_dim,
            edge_dyn_dim=edge_dyn_dim,
            edge_static_dim=edge_static_dim,
            hidden_dim=config.hidden_dim,
            num_heads=config.num_heads,
            num_layers=config.num_layers,
            dropout=config.dropout,
        )
    
    elif config.model_type == "graphsage":
        return GraphSAGEModel(
            node_dim=node_dim,
            edge_dyn_dim=edge_dyn_dim,
            edge_static_dim=edge_static_dim,
            hidden_dim=config.hidden_dim,
            num_layers=config.num_layers,
            aggregation=config.aggregation,
            dropout=config.dropout,
        )
    
    elif config.model_type == "stgcn":
        return STGCNModel(
            node_dim=node_dim,
            edge_dyn_dim=edge_dyn_dim,
            edge_static_dim=edge_static_dim,
            hidden_dim=config.hidden_dim,
            num_st_blocks=config.num_layers,
            temporal_kernel=config.temporal_kernel,
            dropout=config.dropout,
        )
    
    elif config.model_type == "baseline_gnn":
        return BaselineGNNModel(
            node_dim=node_dim,
            edge_dyn_dim=edge_dyn_dim,
            edge_static_dim=edge_static_dim,
            hidden_dim=config.hidden_dim,
            num_layers=config.num_layers,
            dropout=config.dropout,
        )
    
    elif config.model_type == "metapath_v1":
        return MetaPathV1Model(
            node_dim=node_dim,
            edge_dyn_dim=edge_dyn_dim,
            edge_static_dim=edge_static_dim,
            hidden_dim=config.hidden_dim,
            num_metapaths=len(data.metapath_names) if data.metapath_names else 4,
            num_layers=config.num_layers,
            dropout=config.dropout,
        )

    elif config.model_type == "metapath_local":
        return MetaPathLocalResidualModel(
            node_dim=node_dim,
            edge_dyn_dim=edge_dyn_dim,
            edge_static_dim=edge_static_dim,
            hidden_dim=config.hidden_dim,
            num_metapaths=len(data.metapath_names) if data.metapath_names else 4,
            num_layers=config.num_layers,
            dropout=config.dropout,
        )

    elif config.model_type == "metapath_local_riskattn":
        return MetaPathLocalRiskAttentionModel(
            node_dim=node_dim,
            edge_dyn_dim=edge_dyn_dim,
            edge_static_dim=edge_static_dim,
            hidden_dim=config.hidden_dim,
            num_metapaths=len(data.metapath_names) if data.metapath_names else 4,
            num_layers=config.num_layers,
            dropout=config.dropout,
        )

    elif config.model_type == "metapath_local_riskattn_resid":
        return MetaPathLocalRiskAttentionResidualModel(
            node_dim=node_dim,
            edge_dyn_dim=edge_dyn_dim,
            edge_static_dim=edge_static_dim,
            hidden_dim=config.hidden_dim,
            num_metapaths=len(data.metapath_names) if data.metapath_names else 4,
            num_layers=config.num_layers,
            dropout=config.dropout,
        )
    
    elif config.model_type == "mlp":
        return MLPModel(
            node_dim=node_dim,
            edge_dyn_dim=edge_dyn_dim,
            edge_static_dim=edge_static_dim,
            hidden_dim=config.hidden_dim,
            num_layers=3,
            dropout=config.dropout,
        )
    
    else:
        raise ValueError(f"Unknown model type: {config.model_type}")


# ============================================================================
# Evaluation Functions
# ============================================================================

def evaluate_model(
    model: nn.Module,
    data: WarningDataset,
    config: ExperimentConfig,
) -> tuple[np.ndarray, np.ndarray]:
    """Evaluate model on validation/test set."""
    
    device = torch.device("cpu")
    n_time = data.node_x.shape[0]
    
    split = int(np.floor(n_time * config.train_ratio))
    split = max(1, min(split, n_time - 1)) if n_time > 1 else 1
    idx_val = np.arange(split, n_time)
    
    node_x = torch.tensor(data.node_x, dtype=torch.float32, device=device)
    edge_dyn = torch.tensor(data.edge_dyn_x, dtype=torch.float32, device=device)
    edge_static = torch.tensor(data.edge_static_x, dtype=torch.float32, device=device)
    
    node_to_idx = {b: i for i, b in enumerate(data.node_ids)}
    src_idx = torch.tensor([node_to_idx[int(b)] for b in data.from_bus], dtype=torch.long, device=device)
    dst_idx = torch.tensor([node_to_idx[int(b)] for b in data.to_bus], dtype=torch.long, device=device)
    
    metapath_enabled = (
        config.model_type in {
            "metapath_v1",
            "metapath_local",
            "metapath_local_riskattn",
            "metapath_local_riskattn_resid",
        }
        and data.metapath_index is not None
        and data.metapath_mask is not None
    )
    
    metapath_index_t: torch.Tensor | None = None
    metapath_mask_t: torch.Tensor | None = None
    
    if metapath_enabled:
        metapath_index_t = torch.tensor(data.metapath_index, dtype=torch.long, device=device)
        metapath_mask_t = torch.tensor(data.metapath_mask, dtype=torch.float32, device=device)
    
    model.eval()
    predictions = []
    ground_truth = []
    
    with torch.no_grad():
        for t in idx_val:
            if metapath_enabled:
                pred_t = model(
                    node_x[t], edge_dyn[t], edge_static, src_idx, dst_idx,
                    metapath_index=metapath_index_t,
                    metapath_mask=metapath_mask_t,
                    delta_scale=1.0,
                )
            else:
                pred_t = model(node_x[t], edge_dyn[t], edge_static, src_idx, dst_idx)
            
            predictions.append(pred_t.cpu().numpy())
            ground_truth.append(data.labels[t])
    
    pred_array = np.stack(predictions, axis=0)  # [T_val, E]
    truth_array = np.stack(ground_truth, axis=0)  # [T_val, E]
    
    return pred_array, truth_array


def compute_result_metrics(
    pred: np.ndarray,
    truth: np.ndarray,
    model: nn.Module,
    config: ExperimentConfig,
    history: list[dict],
    train_time: float,
    best_epoch: int,
    final_train_loss: float,
    final_val_loss: float,
) -> ExperimentResult:
    """Compute all evaluation metrics."""
    
    # Compute probability metrics
    prob_metrics = evaluate_prob_metrics(
        pred,
        truth,
        high_risk_threshold=config.high_risk_threshold,
        top_risk_quantile=config.top_risk_quantile,
    )
    
    # Compute horizon MAE (last 20% of validation)
    n_val = pred.shape[0]
    horizon_start = int(n_val * 0.8)
    if horizon_start < n_val:
        horizon_pred = pred[horizon_start:]
        horizon_truth = truth[horizon_start:]
        horizon_mae = float(np.mean(np.abs(horizon_pred - horizon_truth)))
    else:
        horizon_mae = prob_metrics["mae"]
    
    # Compute Spearman correlation
    spearman_corr = compute_spearman_correlation(pred, truth)
    topk_metrics = compute_topk_ranking_metrics(pred, truth)
    
    # Find best validation MSE from history
    best_val_mse = min(h["val_mse"] for h in history) if history else float("inf")
    
    return ExperimentResult(
        model_type=config.model_type,
        config=asdict(config),
        train_time_seconds=train_time,
        best_epoch=best_epoch,
        final_train_loss=final_train_loss,
        final_val_loss=final_val_loss,
        val_mae=prob_metrics["mae"],
        horizon_mae=horizon_mae,
        best_val_mse=best_val_mse,
        high_risk_mae=prob_metrics["high_risk_mae"],
        high_risk_count=int(prob_metrics["high_risk_count"]),
        high_risk_ratio=prob_metrics["high_risk_ratio"],
        top_risk_mae=prob_metrics["top_risk_mae"],
        top_risk_count=int(prob_metrics["top_risk_count"]),
        top_risk_ratio=prob_metrics["top_risk_ratio"],
        top_risk_threshold=prob_metrics["top_risk_threshold"],
        spearman_corr=spearman_corr,
        precision_at_5=topk_metrics.get("precision_at_5", float("nan")),
        recall_at_5=topk_metrics.get("recall_at_5", float("nan")),
        hit_at_5=topk_metrics.get("hit_at_5", float("nan")),
        ndcg_at_5=topk_metrics.get("ndcg_at_5", float("nan")),
        precision_at_10=topk_metrics.get("precision_at_10", float("nan")),
        recall_at_10=topk_metrics.get("recall_at_10", float("nan")),
        hit_at_10=topk_metrics.get("hit_at_10", float("nan")),
        ndcg_at_10=topk_metrics.get("ndcg_at_10", float("nan")),
        precision_at_20=topk_metrics.get("precision_at_20", float("nan")),
        recall_at_20=topk_metrics.get("recall_at_20", float("nan")),
        hit_at_20=topk_metrics.get("hit_at_20", float("nan")),
        ndcg_at_20=topk_metrics.get("ndcg_at_20", float("nan")),
        num_parameters=sum(p.numel() for p in model.parameters() if p.requires_grad),
        history=history,
        winner_by_metric={},
    )


# ============================================================================
# Output Functions
# ============================================================================

def save_result(result: ExperimentResult, output_dir: Path) -> None:
    """Save experiment result to output directory."""
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save main result JSON
    result_dict = asdict(result)
    with open(output_dir / "result.json", "w", encoding="utf-8") as f:
        json.dump(result_dict, f, indent=2, ensure_ascii=False, default=str)
    
    # Save metrics CSV
    metrics_df = pd.DataFrame([{
        "model_type": result.model_type,
        "train_time_seconds": result.train_time_seconds,
        "best_epoch": result.best_epoch,
        "final_train_loss": result.final_train_loss,
        "final_val_loss": result.final_val_loss,
        "val_mae": result.val_mae,
        "horizon_mae": result.horizon_mae,
        "best_val_mse": result.best_val_mse,
        "high_risk_mae": result.high_risk_mae,
        "high_risk_count": result.high_risk_count,
        "high_risk_ratio": result.high_risk_ratio,
        "top_risk_mae": result.top_risk_mae,
        "top_risk_count": result.top_risk_count,
        "top_risk_ratio": result.top_risk_ratio,
        "spearman_corr": result.spearman_corr,
        "precision_at_5": result.precision_at_5,
        "recall_at_5": result.recall_at_5,
        "hit_at_5": result.hit_at_5,
        "ndcg_at_5": result.ndcg_at_5,
        "precision_at_10": result.precision_at_10,
        "recall_at_10": result.recall_at_10,
        "hit_at_10": result.hit_at_10,
        "ndcg_at_10": result.ndcg_at_10,
        "precision_at_20": result.precision_at_20,
        "recall_at_20": result.recall_at_20,
        "hit_at_20": result.hit_at_20,
        "ndcg_at_20": result.ndcg_at_20,
        "num_parameters": result.num_parameters,
    }])
    metrics_df.to_csv(output_dir / "metrics.csv", index=False)
    
    # Save training history CSV
    if result.history:
        history_df = pd.DataFrame(result.history)
        history_df.to_csv(output_dir / "training_history.csv", index=False)
    
    # Save winner determination
    if result.winner_by_metric:
        with open(output_dir / "winner.json", "w", encoding="utf-8") as f:
            json.dump(result.winner_by_metric, f, indent=2)


def save_prediction_artifacts(
    pred: np.ndarray,
    truth: np.ndarray,
    data: WarningDataset,
    config: ExperimentConfig,
) -> None:
    """Save validation prediction details and line-level ranking table."""
    output_dir = config.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    n_time = data.node_x.shape[0]
    split = int(np.floor(n_time * config.train_ratio))
    split = max(1, min(split, n_time - 1)) if n_time > 1 else 1
    val_timestamps = data.timestamps[split:n_time]

    wide_pred = pd.DataFrame(pred, columns=data.line_ids)
    wide_pred.insert(0, "timestamp", val_timestamps.astype(str).to_numpy())
    wide_pred.to_csv(output_dir / "validation_predictions_wide.csv", index=False)

    wide_truth = pd.DataFrame(truth, columns=data.line_ids)
    wide_truth.insert(0, "timestamp", val_timestamps.astype(str).to_numpy())
    wide_truth.to_csv(output_dir / "validation_truth_wide.csv", index=False)

    pred_score = np.max(pred, axis=0)
    truth_score = np.max(truth, axis=0)
    rank_df = pd.DataFrame(
        {
            "line_id": data.line_ids,
            "predicted_max_risk": pred_score,
            "true_max_risk": truth_score,
        }
    )
    rank_df["predicted_rank"] = rank_df["predicted_max_risk"].rank(method="first", ascending=False).astype(int)
    rank_df["true_rank"] = rank_df["true_max_risk"].rank(method="first", ascending=False).astype(int)
    rank_df = rank_df.sort_values("predicted_rank")
    rank_df.to_csv(output_dir / "line_ranking_validation.csv", index=False)


def save_comparison_results(results: list[ExperimentResult], output_dir: Path) -> None:
    """Save comparison results for all models."""
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save all results JSON
    all_results = [asdict(r) for r in results]
    with open(output_dir / "all_results.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False, default=str)
    
    # Save comparison CSV
    comparison_data = []
    for r in results:
        row = {
            "model": r.model_type,
            "val_mae": r.val_mae,
            "horizon_mae": r.horizon_mae,
            "best_val_mse": r.best_val_mse,
            "high_risk_mae": r.high_risk_mae,
            "top_risk_mae": r.top_risk_mae,
            "spearman_corr": r.spearman_corr,
            "precision_at_5": r.precision_at_5,
            "recall_at_5": r.recall_at_5,
            "ndcg_at_5": r.ndcg_at_5,
            "precision_at_10": r.precision_at_10,
            "recall_at_10": r.recall_at_10,
            "hit_at_10": r.hit_at_10,
            "ndcg_at_10": r.ndcg_at_10,
            "precision_at_20": r.precision_at_20,
            "recall_at_20": r.recall_at_20,
            "ndcg_at_20": r.ndcg_at_20,
            "train_time_seconds": r.train_time_seconds,
            "num_parameters": r.num_parameters,
        }
        comparison_data.append(row)
    
    comparison_df = pd.DataFrame(comparison_data)
    comparison_df = comparison_df.sort_values("val_mae")
    comparison_df.to_csv(output_dir / "model_comparison.csv", index=False)
    
    # Determine winners
    if len(results) > 1:
        winner_by_metric = {
            "val_mae": min(results, key=lambda r: r.val_mae).model_type,
            "horizon_mae": min(results, key=lambda r: r.horizon_mae).model_type,
            "best_val_mse": min(results, key=lambda r: r.best_val_mse).model_type,
            "high_risk_mae": min(results, key=lambda r: r.high_risk_mae if not np.isnan(r.high_risk_mae) else float("inf")).model_type,
            "spearman_corr": max(results, key=lambda r: r.spearman_corr if not np.isnan(r.spearman_corr) else 0.0).model_type,
        }
        
        with open(output_dir / "winner_by_metric.json", "w", encoding="utf-8") as f:
            json.dump(winner_by_metric, f, indent=2)
        
        # Save summary table
        summary = {
            "experiment_date": datetime.now().isoformat(),
            "num_models_compared": len(results),
            "models": [r.model_type for r in results],
            "winner_by_metric": winner_by_metric,
            "comparison_table": comparison_data,
        }
        with open(output_dir / "summary.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print("MODEL COMPARISON RESULTS")
    print(f"{'='*60}")
    print(comparison_df.to_string(index=False))
    print(f"\nResults saved to: {output_dir}")


# ============================================================================
# Main Experiment Functions
# ============================================================================

def find_latest_failure_csv(output_root: Path) -> Path | None:
    """Find the latest failure probability CSV from previous runs."""
    
    # Look in results directory
    results_dir = project_root() / "results"
    if not results_dir.exists():
        return None
    
    # Search for stage2 failure CSVs
    for stage2_dir in sorted(results_dir.glob("*/stage2_failure/*/line_failure*.csv"), reverse=True):
        if stage2_dir.exists():
            return stage2_dir
    
    return None


def run_single_experiment(config: ExperimentConfig) -> ExperimentResult:
    """Run a single experiment."""
    
    print(f"\n{'='*60}")
    print(f"Running experiment: {config.model_type}")
    print(f"{'='*60}")
    print(f"Output directory: {config.output_dir}")
    print(f"Hidden dim: {config.hidden_dim}, Epochs: {config.epochs}")
    print(f"Learning rate: {config.learning_rate}")
    
    # Find failure CSV if not provided
    if config.failure_csv is None:
        config.failure_csv = find_latest_failure_csv(project_root() / "results")
        if config.failure_csv is None:
            raise FileNotFoundError(
                "Failure CSV not found. Please specify --failure-csv or run Stage2 first."
            )
    
    print(f"Loading failure data from: {config.failure_csv}")
    
    # Load grid topology
    grid_payload = load_grid_topology(config.grid_path)
    
    # Load failure data
    ts, line_ids, p_arr, v_arr, edge_map = load_failure_features(config.failure_csv)
    
    # Load labels (use failure probability as proxy for labels)
    labels = p_arr
    
    # Build dataset
    data = build_dataset(
        grid_payload=grid_payload,
        timestamps=ts,
        line_ids=line_ids,
        edge_map=edge_map,
        p_line=p_arr,
        v_surface=v_arr,
        labels=labels,
        aligned_csv=config.aligned_csv,
        priority_csv=None,
        metapath_topk=config.metapath_topk,
    )
    
    print(f"Dataset built: {len(ts)} time steps, {len(line_ids)} edges")
    print(f"Metapath enabled: {data.metapath_names is not None and len(data.metapath_names) > 0}")
    if data.metapath_names:
        print(f"Metapath names: {data.metapath_names}")
    
    # Train model
    print("\nTraining...")
    model, history, best_epoch, final_train_loss, final_val_loss = train_model(data, config)
    
    # Evaluate model
    print("Evaluating...")
    pred, truth = evaluate_model(model, data, config)
    
    # Compute metrics
    result = compute_result_metrics(
        pred=pred,
        truth=truth,
        model=model,
        config=config,
        history=history,
        train_time=0.0,  # Will be set by caller
        best_epoch=best_epoch,
        final_train_loss=final_train_loss,
        final_val_loss=final_val_loss,
    )
    
    # Save result
    save_result(result, config.output_dir)
    save_prediction_artifacts(pred, truth, data, config)
    
    print(f"\nResults:")
    print(f"  Val MAE: {result.val_mae:.6f}")
    print(f"  Horizon MAE: {result.horizon_mae:.6f}")
    print(f"  Best Val MSE: {result.best_val_mse:.6f}")
    print(f"  High Risk MAE: {result.high_risk_mae:.6f}")
    print(f"  Spearman Corr: {result.spearman_corr:.4f}")
    print(f"  Parameters: {result.num_parameters}")
    
    return result


def run_all_experiments(output_root: Path) -> list[ExperimentResult]:
    """Run experiments for all model types."""
    
    model_types = [
        "gcn",
        "gat",
        "graphsage",
        "stgcn",
        "baseline_gnn",
        "metapath_v1",
        "metapath_local",
        "metapath_local_riskattn",
        "metapath_local_riskattn_resid",
    ]
    results = []
    
    # Find failure CSV
    failure_csv = find_latest_failure_csv(project_root() / "results")
    if failure_csv is None:
        raise FileNotFoundError(
            "Failure CSV not found. Please run Stage2 first."
        )
    
    for model_type in model_types:
        config = ExperimentConfig(
            model_type=model_type,
            output_dir=output_root / model_type,
            failure_csv=failure_csv,
            hidden_dim=80,
            epochs=700,
            learning_rate=0.006,
            metapath_topk=4,
            patience=60,
        )
        
        start_time = time.time()
        result = run_single_experiment(config)
        result.train_time_seconds = time.time() - start_time
        results.append(result)
        
        # Add to comparison
        save_comparison_results(results, output_root)
    
    return results


# ============================================================================
# CLI Entry Point
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="GNN Ablation Experiment for Stage6 Line Risk Prediction",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    
    # Model selection
    parser.add_argument(
        "--model-type",
        type=str,
        choices=[
            "gcn",
            "gat",
            "graphsage",
            "stgcn",
            "baseline_gnn",
            "metapath_v1",
            "metapath_local",
            "metapath_local_riskattn",
            "metapath_local_riskattn_resid",
            "mlp",
            "all",
        ],
        default="all",
        help="Model type to train",
    )
    
    # Output
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for single model experiment",
    )
    parser.add_argument(
        "--output-root",
        type=str,
        default="results/ablation/stage6_comparison",
        help="Root directory for all experiment outputs",
    )
    parser.add_argument(
        "--run-all",
        action="store_true",
        help="Run all model types and generate comparison",
    )
    
    # Data paths
    parser.add_argument(
        "--grid-path",
        type=str,
        default="data_final/formal_guangdong_2024/grid_topology.json",
        help="Path to grid topology JSON",
    )
    parser.add_argument(
        "--aligned-csv",
        type=str,
        default="data_final/formal_guangdong_2024/aligned_merged.csv",
        help="Path to aligned CSV",
    )
    parser.add_argument(
        "--failure-csv",
        type=str,
        default=None,
        help="Path to failure probability CSV (from Stage2)",
    )
    
    # Model hyperparameters
    parser.add_argument("--hidden-dim", type=int, default=80, help="Hidden dimension")
    parser.add_argument("--num-layers", type=int, default=2, help="Number of GNN layers")
    parser.add_argument("--learning-rate", type=float, default=0.006, help="Learning rate")
    parser.add_argument("--weight-decay", type=float, default=1e-4, help="Weight decay")
    parser.add_argument("--dropout", type=float, default=0.1, help="Dropout rate")
    parser.add_argument("--metapath-topk", type=int, default=4, help="Top-k neighbors for metapath")
    
    # GAT-specific
    parser.add_argument("--num-heads", type=int, default=4, help="Number of attention heads (GAT)")
    
    # GraphSAGE-specific
    parser.add_argument(
        "--aggregation",
        type=str,
        default="mean",
        choices=["mean", "pool", "lstm"],
        help="GraphSAGE aggregation function",
    )
    
    # Training
    parser.add_argument("--epochs", type=int, default=700, help="Number of training epochs")
    parser.add_argument("--patience", type=int, default=60, help="Early stopping patience")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--train-ratio", type=float, default=0.6, help="Training data ratio")
    parser.add_argument("--rank-loss-beta", type=float, default=0.0, help="Weight for pairwise ranking loss")
    parser.add_argument("--rank-loss-margin", type=float, default=0.02, help="Margin for pairwise ranking loss")
    parser.add_argument("--rank-loss-min-diff", type=float, default=0.02, help="Minimum label gap for ranking pairs")
    
    args = parser.parse_args()
    
    # Determine output directory
    if args.run_all or args.model_type == "all":
        output_root = Path(args.output_root)
        results = run_all_experiments(output_root)
        
    else:
        if args.output_dir is None:
            args.output_dir = f"results/ablation/stage6_{args.model_type}"
        
        config = ExperimentConfig(
            model_type=args.model_type,
            output_dir=Path(args.output_dir),
            grid_path=Path(args.grid_path),
            aligned_csv=Path(args.aligned_csv),
            failure_csv=Path(args.failure_csv) if args.failure_csv else None,
            hidden_dim=args.hidden_dim,
            num_layers=args.num_layers,
            learning_rate=args.learning_rate,
            weight_decay=args.weight_decay,
            dropout=args.dropout,
            metapath_topk=args.metapath_topk,
            epochs=args.epochs,
            patience=args.patience,
            seed=args.seed,
            train_ratio=args.train_ratio,
            rank_loss_beta=args.rank_loss_beta,
            rank_loss_margin=args.rank_loss_margin,
            rank_loss_min_diff=args.rank_loss_min_diff,
            num_heads=args.num_heads,
            aggregation=args.aggregation,
        )
        
        start_time = time.time()
        result = run_single_experiment(config)
        result.train_time_seconds = time.time() - start_time
        
        # Save with train time
        save_result(result, config.output_dir)
    
    print("\nExperiment completed successfully!")


if __name__ == "__main__":
    main()
