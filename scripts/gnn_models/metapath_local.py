"""
MetaPath Local Residual Model
=============================

MetaPath V1 with an explicit local edge-feature branch.
The local branch preserves line-level dynamic/static signals that can be
important for high-risk Top-k ranking, while the graph branch keeps the
existing metapath semantic context.
"""

import numpy as np
import torch
import torch.nn as nn

from .base_model import BaseGNNModel
from .metapath_v1 import GraphMessageLayer, MetaPathSemanticBlock


class RiskAwareLineAttentionBlock(nn.Module):
    """Line-level attention conditioned on local risk-related edge features."""

    def __init__(self, hidden_dim: int, local_dim: int, dropout: float = 0.1) -> None:
        super().__init__()
        self.local_proj = nn.Sequential(
            nn.Linear(local_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, hidden_dim),
        )
        self.q_proj = nn.Linear(hidden_dim, hidden_dim)
        self.k_proj = nn.Linear(hidden_dim, hidden_dim)
        self.v_proj = nn.Linear(hidden_dim, hidden_dim)
        self.out_proj = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(p=dropout),
            nn.Linear(hidden_dim, hidden_dim),
        )
        self.norm = nn.LayerNorm(hidden_dim)

    def forward(
        self,
        edge_repr: torch.Tensor,
        edge_local: torch.Tensor,
        src: torch.Tensor,
        dst: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        e_count = edge_repr.shape[0]
        risk_context = edge_repr + self.local_proj(edge_local)
        q = self.q_proj(risk_context)
        k = self.k_proj(risk_context)
        v = self.v_proj(edge_repr)

        scale = float(max(q.shape[1], 1)) ** -0.5
        score = torch.matmul(q, k.transpose(0, 1)) * scale

        share_bus = (
            (src[:, None] == src[None, :])
            | (src[:, None] == dst[None, :])
            | (dst[:, None] == src[None, :])
            | (dst[:, None] == dst[None, :])
        )
        self_mask = torch.eye(e_count, dtype=torch.bool, device=edge_repr.device)
        attn_mask = share_bus | self_mask
        score = score.masked_fill(~attn_mask, -1e9)

        alpha = torch.softmax(score, dim=1)
        context = torch.matmul(alpha, v)
        return self.norm(edge_repr + self.out_proj(context)), alpha


class MetaPathLocalResidualModel(BaseGNNModel):
    """MetaPath graph branch + MLP-style local branch with learned fusion."""

    def __init__(
        self,
        node_dim: int,
        edge_dyn_dim: int,
        edge_static_dim: int,
        hidden_dim: int = 64,
        num_metapaths: int = 4,
        num_layers: int = 2,
        dropout: float = 0.1,
    ) -> None:
        super().__init__(node_dim, edge_dyn_dim, edge_static_dim, hidden_dim)
        self.num_metapaths = int(num_metapaths)
        self.num_layers = int(num_layers)
        self.dropout = float(dropout)

        self.node_encoder = nn.Sequential(
            nn.Linear(node_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.GELU(),
        )
        self.mp1 = GraphMessageLayer(hidden_dim)
        self.mp2 = GraphMessageLayer(hidden_dim)

        edge_raw_dim = hidden_dim * 2 + edge_dyn_dim + edge_static_dim
        local_dim = edge_dyn_dim + edge_static_dim

        self.edge_base_encoder = nn.Sequential(
            nn.Linear(edge_raw_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.GELU(),
        )
        self.metapath_block = MetaPathSemanticBlock(
            hidden_dim=hidden_dim,
            num_metapaths=num_metapaths,
        )

        self.graph_head = nn.Sequential(
            nn.Linear(hidden_dim * 2 + edge_dyn_dim + edge_static_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(p=dropout),
            nn.Linear(hidden_dim, 1),
        )
        self.local_head = nn.Sequential(
            nn.Linear(local_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(p=dropout),
            nn.Linear(hidden_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(p=dropout * 0.5),
            nn.Linear(hidden_dim, 1),
        )
        self.fusion_gate = nn.Sequential(
            nn.Linear(edge_raw_dim + local_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, 1),
        )

        gate_last = self.fusion_gate[-1]
        if isinstance(gate_last, nn.Linear):
            nn.init.constant_(gate_last.bias, 0.0)

    def forward(
        self,
        node_x: torch.Tensor,
        edge_dyn_x: torch.Tensor,
        edge_static_x: torch.Tensor,
        src: torch.Tensor,
        dst: torch.Tensor,
        metapath_index: torch.Tensor | None = None,
        metapath_mask: torch.Tensor | None = None,
        delta_scale: float = 1.0,
        return_attention: bool = False,
    ) -> torch.Tensor | tuple[torch.Tensor, torch.Tensor | None, torch.Tensor]:
        h = self.node_encoder(node_x)
        h = self.mp1(h, src, dst)
        h = self.mp2(h, src, dst)

        edge_local = torch.cat([edge_dyn_x, edge_static_x], dim=1)
        edge_raw = torch.cat([h[src], h[dst], edge_dyn_x, edge_static_x], dim=1)
        local_logit = self.local_head(edge_local).squeeze(1)

        if metapath_index is not None and metapath_mask is not None:
            edge_repr = self.edge_base_encoder(edge_raw)
            metapath_context, alpha = self.metapath_block(
                edge_repr=edge_repr,
                metapath_index=metapath_index,
                metapath_mask=metapath_mask,
            )
            graph_feat = torch.cat([edge_repr, metapath_context, edge_dyn_x, edge_static_x], dim=1)
            graph_logit = self.graph_head(graph_feat).squeeze(1)
        else:
            alpha = None
            graph_logit = self.graph_head(
                torch.cat([self.edge_base_encoder(edge_raw), self.edge_base_encoder(edge_raw), edge_dyn_x, edge_static_x], dim=1)
            ).squeeze(1)

        gate = torch.sigmoid(self.fusion_gate(torch.cat([edge_raw, edge_local], dim=1)).squeeze(1))
        scale = float(np.clip(delta_scale, 0.0, 1.0))
        out = torch.sigmoid((1.0 - scale * gate) * local_logit + (scale * gate) * graph_logit)

        if return_attention:
            return out, alpha, gate
        return out

    @property
    def model_name(self) -> str:
        return "MetaPath-LocalResidual"


class MetaPathLocalRiskAttentionModel(BaseGNNModel):
    """MetaPath + local branch + risk-aware line-level attention."""

    def __init__(
        self,
        node_dim: int,
        edge_dyn_dim: int,
        edge_static_dim: int,
        hidden_dim: int = 64,
        num_metapaths: int = 4,
        num_layers: int = 2,
        dropout: float = 0.1,
    ) -> None:
        super().__init__(node_dim, edge_dyn_dim, edge_static_dim, hidden_dim)
        self.num_metapaths = int(num_metapaths)
        self.num_layers = int(num_layers)
        self.dropout = float(dropout)

        self.node_encoder = nn.Sequential(
            nn.Linear(node_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.GELU(),
        )
        self.mp1 = GraphMessageLayer(hidden_dim)
        self.mp2 = GraphMessageLayer(hidden_dim)

        edge_raw_dim = hidden_dim * 2 + edge_dyn_dim + edge_static_dim
        local_dim = edge_dyn_dim + edge_static_dim

        self.edge_base_encoder = nn.Sequential(
            nn.Linear(edge_raw_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.GELU(),
        )
        self.metapath_block = MetaPathSemanticBlock(
            hidden_dim=hidden_dim,
            num_metapaths=num_metapaths,
        )
        self.line_attention = RiskAwareLineAttentionBlock(
            hidden_dim=hidden_dim,
            local_dim=local_dim,
            dropout=dropout,
        )

        self.graph_head = nn.Sequential(
            nn.Linear(hidden_dim * 3 + edge_dyn_dim + edge_static_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(p=dropout),
            nn.Linear(hidden_dim, 1),
        )
        self.local_head = nn.Sequential(
            nn.Linear(local_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(p=dropout),
            nn.Linear(hidden_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(p=dropout * 0.5),
            nn.Linear(hidden_dim, 1),
        )
        self.fusion_gate = nn.Sequential(
            nn.Linear(edge_raw_dim + local_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, 1),
        )

        gate_last = self.fusion_gate[-1]
        if isinstance(gate_last, nn.Linear):
            nn.init.constant_(gate_last.bias, 0.0)

    def forward(
        self,
        node_x: torch.Tensor,
        edge_dyn_x: torch.Tensor,
        edge_static_x: torch.Tensor,
        src: torch.Tensor,
        dst: torch.Tensor,
        metapath_index: torch.Tensor | None = None,
        metapath_mask: torch.Tensor | None = None,
        delta_scale: float = 1.0,
        return_attention: bool = False,
    ) -> torch.Tensor | tuple[torch.Tensor, torch.Tensor | None, torch.Tensor]:
        h = self.node_encoder(node_x)
        h = self.mp1(h, src, dst)
        h = self.mp2(h, src, dst)

        edge_local = torch.cat([edge_dyn_x, edge_static_x], dim=1)
        edge_raw = torch.cat([h[src], h[dst], edge_dyn_x, edge_static_x], dim=1)
        edge_repr = self.edge_base_encoder(edge_raw)
        local_logit = self.local_head(edge_local).squeeze(1)
        line_context, _line_alpha = self.line_attention(edge_repr, edge_local, src, dst)

        if metapath_index is not None and metapath_mask is not None:
            metapath_context, alpha = self.metapath_block(
                edge_repr=edge_repr,
                metapath_index=metapath_index,
                metapath_mask=metapath_mask,
            )
        else:
            alpha = None
            metapath_context = edge_repr

        graph_feat = torch.cat([edge_repr, metapath_context, line_context, edge_dyn_x, edge_static_x], dim=1)
        graph_logit = self.graph_head(graph_feat).squeeze(1)

        gate = torch.sigmoid(self.fusion_gate(torch.cat([edge_raw, edge_local], dim=1)).squeeze(1))
        scale = float(np.clip(delta_scale, 0.0, 1.0))
        out = torch.sigmoid((1.0 - scale * gate) * local_logit + (scale * gate) * graph_logit)

        if return_attention:
            return out, alpha, gate
        return out

    @property
    def model_name(self) -> str:
        return "MetaPath-LocalRiskAttention"


class MetaPathLocalRiskAttentionResidualModel(BaseGNNModel):
    """Conservative risk-aware line attention as a gated residual correction."""

    def __init__(
        self,
        node_dim: int,
        edge_dyn_dim: int,
        edge_static_dim: int,
        hidden_dim: int = 64,
        num_metapaths: int = 4,
        num_layers: int = 2,
        dropout: float = 0.1,
    ) -> None:
        super().__init__(node_dim, edge_dyn_dim, edge_static_dim, hidden_dim)
        self.num_metapaths = int(num_metapaths)
        self.num_layers = int(num_layers)
        self.dropout = float(dropout)

        self.node_encoder = nn.Sequential(
            nn.Linear(node_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.GELU(),
        )
        self.mp1 = GraphMessageLayer(hidden_dim)
        self.mp2 = GraphMessageLayer(hidden_dim)

        edge_raw_dim = hidden_dim * 2 + edge_dyn_dim + edge_static_dim
        local_dim = edge_dyn_dim + edge_static_dim

        self.edge_base_encoder = nn.Sequential(
            nn.Linear(edge_raw_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.GELU(),
        )
        self.metapath_block = MetaPathSemanticBlock(
            hidden_dim=hidden_dim,
            num_metapaths=num_metapaths,
        )
        self.line_attention = RiskAwareLineAttentionBlock(
            hidden_dim=hidden_dim,
            local_dim=local_dim,
            dropout=dropout,
        )
        self.attention_gate = nn.Sequential(
            nn.Linear(edge_raw_dim + local_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, 1),
        )

        self.graph_head = nn.Sequential(
            nn.Linear(hidden_dim * 2 + edge_dyn_dim + edge_static_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(p=dropout),
            nn.Linear(hidden_dim, 1),
        )
        self.local_head = nn.Sequential(
            nn.Linear(local_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(p=dropout),
            nn.Linear(hidden_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(p=dropout * 0.5),
            nn.Linear(hidden_dim, 1),
        )
        self.fusion_gate = nn.Sequential(
            nn.Linear(edge_raw_dim + local_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, 1),
        )

        attn_gate_last = self.attention_gate[-1]
        if isinstance(attn_gate_last, nn.Linear):
            nn.init.constant_(attn_gate_last.bias, -3.0)
        fusion_gate_last = self.fusion_gate[-1]
        if isinstance(fusion_gate_last, nn.Linear):
            nn.init.constant_(fusion_gate_last.bias, 0.0)

    def forward(
        self,
        node_x: torch.Tensor,
        edge_dyn_x: torch.Tensor,
        edge_static_x: torch.Tensor,
        src: torch.Tensor,
        dst: torch.Tensor,
        metapath_index: torch.Tensor | None = None,
        metapath_mask: torch.Tensor | None = None,
        delta_scale: float = 1.0,
        return_attention: bool = False,
    ) -> torch.Tensor | tuple[torch.Tensor, torch.Tensor | None, torch.Tensor]:
        h = self.node_encoder(node_x)
        h = self.mp1(h, src, dst)
        h = self.mp2(h, src, dst)

        edge_local = torch.cat([edge_dyn_x, edge_static_x], dim=1)
        edge_raw = torch.cat([h[src], h[dst], edge_dyn_x, edge_static_x], dim=1)
        edge_repr = self.edge_base_encoder(edge_raw)
        local_logit = self.local_head(edge_local).squeeze(1)

        line_context, _line_alpha = self.line_attention(edge_repr, edge_local, src, dst)
        attn_gate = torch.sigmoid(self.attention_gate(torch.cat([edge_raw, edge_local], dim=1)))
        edge_repr_attn = edge_repr + attn_gate * (line_context - edge_repr)

        if metapath_index is not None and metapath_mask is not None:
            metapath_context, alpha = self.metapath_block(
                edge_repr=edge_repr_attn,
                metapath_index=metapath_index,
                metapath_mask=metapath_mask,
            )
        else:
            alpha = None
            metapath_context = edge_repr_attn

        graph_feat = torch.cat([edge_repr_attn, metapath_context, edge_dyn_x, edge_static_x], dim=1)
        graph_logit = self.graph_head(graph_feat).squeeze(1)

        gate = torch.sigmoid(self.fusion_gate(torch.cat([edge_raw, edge_local], dim=1)).squeeze(1))
        scale = float(np.clip(delta_scale, 0.0, 1.0))
        out = torch.sigmoid((1.0 - scale * gate) * local_logit + (scale * gate) * graph_logit)

        if return_attention:
            return out, alpha, gate
        return out

    @property
    def model_name(self) -> str:
        return "MetaPath-LocalRiskAttentionResidual"
