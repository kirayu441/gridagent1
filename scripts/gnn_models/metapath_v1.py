"""
MetaPath V1: Fixed Metapath + Semantic Attention + Residual Gating
===================================================================
The proposed model with electrical topology-aware structural semantic enhancement.

Core Innovation:
1. Fixed Metapath: L-B-L, L-B-L-B-L, L-B-source-B-L, L-B-primary_load-B-L
2. Semantic Attention: Learn importance weights over metapath semantics
3. Residual Gating: Controlled integration of metapath branch with baseline

Reference:
- GridAgent Project (Wang et al., 2024 framework)

Key Features:
- Domain-aware metapath design based on electrical topology
- Semantic attention for metapath importance weighting
- Residual gating for stable training (initialized with negative bias)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

from .base_model import BaseGNNModel


class GraphMessageLayer(nn.Module):
    """Message passing layer (shared with baseline)."""
    
    def __init__(self, hidden_dim: int) -> None:
        super().__init__()
        self.self_fc = nn.Linear(hidden_dim, hidden_dim)
        self.nei_fc = nn.Linear(hidden_dim, hidden_dim)
        self.norm = nn.LayerNorm(hidden_dim)
    
    def forward(self, h: torch.Tensor, src: torch.Tensor, dst: torch.Tensor) -> torch.Tensor:
        n = h.shape[0]
        agg = torch.zeros_like(h)
        agg.index_add_(0, dst, h[src])
        agg.index_add_(0, src, h[dst])
        
        deg = torch.zeros(n, device=h.device)
        ones = torch.ones(src.shape[0], device=h.device)
        deg.index_add_(0, dst, ones)
        deg.index_add_(0, src, ones)
        deg = deg.clamp_min(1.0).unsqueeze(1)
        
        h_next = self.self_fc(h) + self.nei_fc(agg / deg)
        h_next = F.gelu(h_next)
        return self.norm(h_next)


class MetaPathSemanticBlock(nn.Module):
    """Semantic attention over fixed metapath patterns."""
    
    def __init__(self, hidden_dim: int, num_metapaths: int) -> None:
        super().__init__()
        self.num_metapaths = int(num_metapaths)
        self.score_proj = nn.Linear(hidden_dim, hidden_dim)
        # Learnable context vectors for each metapath
        self.context_vectors = nn.Parameter(torch.randn(self.num_metapaths, hidden_dim) * 0.02)
    
    def forward(
        self,
        edge_repr: torch.Tensor,
        metapath_index: torch.Tensor,
        metapath_mask: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """
        Args:
            edge_repr: [E, H] edge representations
            metapath_index: [P, E, K] indices of metapath neighbors
            metapath_mask: [P, E, K] mask for valid neighbors
        
        Returns:
            context: [E, H] metapath-enhanced context
            alpha: [E, P] attention weights over metapaths
        """
        # metapath_index: [P,E,K], metapath_mask: [P,E,K]
        safe_index = metapath_index.clamp_min(0)
        
        # Gather neighbor representations: [P,E,K,H]
        neighbor_repr = edge_repr[safe_index]
        mask = metapath_mask.unsqueeze(-1)  # [P,E,K,1]
        
        # Average over neighbors for each metapath: [P,E,H]
        denom = mask.sum(dim=2).clamp_min(1.0)  # [P,E,1]
        path_repr = (neighbor_repr * mask).sum(dim=2) / denom
        
        # Permute for batch processing: [E,P,H]
        path_repr_ep = path_repr.permute(1, 0, 2)
        
        # Compute attention scores: [E,P]
        score_feat = torch.tanh(self.score_proj(path_repr_ep))  # [E,P,H]
        score = torch.einsum('eph,ph->ep', score_feat, self.context_vectors)  # [E,P]
        alpha = torch.softmax(score, dim=1)  # [E,P]
        
        # Weighted sum of metapath contexts: [E,H]
        context = (alpha.unsqueeze(-1) * path_repr_ep).sum(dim=1)
        
        return context, alpha


class MetaPathV1Model(BaseGNNModel):
    """
    MetaPath V1: Fixed Metapath + Semantic Attention + Residual Gating
    
    Architecture:
    1. Node encoder → Message passing layers
    2. Baseline edge prediction head
    3. Metapath semantic block
    4. Delta head + Gate head
    5. Final: sigmoid(base + gate * delta)
    """
    
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
        self.num_metapaths = num_metapaths
        self.num_layers = num_layers
        self.dropout = dropout
        
        # Node feature encoder
        self.node_encoder = nn.Sequential(
            nn.Linear(node_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.GELU(),
        )
        
        # Message passing layers
        self.mp1 = GraphMessageLayer(hidden_dim)
        self.mp2 = GraphMessageLayer(hidden_dim)
        
        # Edge base encoder
        self.edge_base_encoder = nn.Sequential(
            nn.Linear(hidden_dim * 2 + edge_dyn_dim + edge_static_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.GELU(),
        )
        
        # Metapath semantic block
        self.metapath_block = MetaPathSemanticBlock(
            hidden_dim=hidden_dim,
            num_metapaths=num_metapaths,
        )
        
        # Baseline prediction head
        self.base_head = nn.Sequential(
            nn.Linear(hidden_dim * 2 + edge_dyn_dim + edge_static_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(p=dropout),
            nn.Linear(hidden_dim, 1),
        )
        
        # Delta prediction head (metapath correction)
        self.delta_head = nn.Sequential(
            nn.Linear(hidden_dim * 2 + edge_dyn_dim + edge_static_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(p=dropout * 0.5),  # Lower dropout for delta
            nn.Linear(hidden_dim, 1),
        )
        
        # Gate head (controls delta contribution)
        self.gate_head = nn.Sequential(
            nn.Linear(hidden_dim * 2 + edge_dyn_dim + edge_static_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, 1),
        )
        
        # Initialize gate bias to negative for conservative start
        gate_last = self.gate_head[-1]
        if isinstance(gate_last, nn.Linear):
            nn.init.constant_(gate_last.bias, -2.0)
    
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
    ) -> torch.Tensor | tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Args:
            node_x: [N, node_dim]
            edge_dyn_x: [E, edge_dyn_dim]
            edge_static_x: [E, edge_static_dim]
            src: [E]
            dst: [E]
            metapath_index: [P, E, K] optional
            metapath_mask: [P, E, K] optional
            delta_scale: scale for delta contribution
            return_attention: whether to return attention weights
        
        Returns:
            predictions: [E] edge risk predictions
            (optional) alpha: [E, P] attention weights
            (optional) gate: [E] gate values
        """
        # Encode and pass messages
        h = self.node_encoder(node_x)
        h = self.mp1(h, src, dst)
        h = self.mp2(h, src, dst)
        
        # Edge raw features
        edge_raw = torch.cat([h[src], h[dst], edge_dyn_x, edge_static_x], dim=1)
        
        # Baseline prediction
        base_logit = self.base_head(edge_raw).squeeze(1)
        
        # If metapath not provided, fall back to baseline
        if metapath_index is None or metapath_mask is None:
            if return_attention:
                return torch.sigmoid(base_logit), None, None
            return torch.sigmoid(base_logit)
        
        # Edge representations for metapath
        edge_repr = self.edge_base_encoder(edge_raw)
        
        # Metapath semantic aggregation
        metapath_context, alpha = self.metapath_block(
            edge_repr=edge_repr,
            metapath_index=metapath_index,
            metapath_mask=metapath_mask,
        )
        
        # Delta prediction (metapath correction)
        delta_feat = torch.cat([edge_repr, metapath_context, edge_dyn_x, edge_static_x], dim=1)
        delta_logit = self.delta_head(delta_feat).squeeze(1)
        
        # Gate prediction
        gate = torch.sigmoid(self.gate_head(edge_raw).squeeze(1))
        
        # Final prediction with residual gating
        scale = float(np.clip(delta_scale, 0.0, 1.0))
        out = torch.sigmoid(base_logit + (scale * gate) * delta_logit)
        
        if return_attention:
            return out, alpha, gate
        return out
    
    @property
    def model_name(self) -> str:
        return "MetaPath-V1"
    
    def __repr__(self) -> str:
        return f"MetaPathV1Model(hidden_dim={self.hidden_dim}, num_metapaths={self.num_metapaths})"
