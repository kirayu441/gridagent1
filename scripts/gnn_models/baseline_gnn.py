"""
Baseline GNN: Two-layer Message Passing Baseline
================================================
Baseline model with two-layer message passing without metapath enhancement.
This serves as the ablation baseline for the MetaPath V1 model.

Architecture:
- Node feature encoder: MLP
- Two message passing layers
- Edge risk prediction head
"""

import torch
import torch.nn as nn
import torch.nn.functional as F

from .base_model import BaseGNNModel


class GraphMessageLayer(nn.Module):
    """Message passing layer for baseline GNN."""
    
    def __init__(self, hidden_dim: int) -> None:
        super().__init__()
        self.self_fc = nn.Linear(hidden_dim, hidden_dim)
        self.nei_fc = nn.Linear(hidden_dim, hidden_dim)
        self.norm = nn.LayerNorm(hidden_dim)
    
    def forward(self, h: torch.Tensor, src: torch.Tensor, dst: torch.Tensor) -> torch.Tensor:
        """
        Args:
            h: [N, H] node embeddings
            src: [E] source node indices
            dst: [E] destination node indices
        
        Returns:
            [N, H] updated node embeddings
        """
        n = h.shape[0]
        
        # Aggregate neighbor features
        agg = torch.zeros_like(h)
        agg.index_add_(0, dst, h[src])
        agg.index_add_(0, src, h[dst])
        
        # Normalize by degree
        deg = torch.zeros(n, device=h.device)
        ones = torch.ones(src.shape[0], device=h.device)
        deg.index_add_(0, dst, ones)
        deg.index_add_(0, src, ones)
        deg = deg.clamp_min(1.0).unsqueeze(1)
        
        # Message passing with residual
        h_next = self.self_fc(h) + self.nei_fc(agg / deg)
        h_next = F.gelu(h_next)
        return self.norm(h_next)


class BaselineGNNModel(BaseGNNModel):
    """Baseline GNN: Two-layer message passing without metapath."""
    
    def __init__(
        self,
        node_dim: int,
        edge_dyn_dim: int,
        edge_static_dim: int,
        hidden_dim: int = 64,
        num_layers: int = 2,
        dropout: float = 0.1,
    ) -> None:
        super().__init__(node_dim, edge_dyn_dim, edge_static_dim, hidden_dim)
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
        
        # Edge risk prediction head
        self.edge_head = nn.Sequential(
            nn.Linear(hidden_dim * 2 + edge_dyn_dim + edge_static_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(p=dropout),
            nn.Linear(hidden_dim, 1),
        )
    
    def forward(
        self,
        node_x: torch.Tensor,
        edge_dyn_x: torch.Tensor,
        edge_static_x: torch.Tensor,
        src: torch.Tensor,
        dst: torch.Tensor,
    ) -> torch.Tensor:
        """
        Args:
            node_x: [N, node_dim]
            edge_dyn_x: [E, edge_dyn_dim]
            edge_static_x: [E, edge_static_dim]
            src: [E]
            dst: [E]
        
        Returns:
            [E] edge risk predictions
        """
        # Encode node features
        h = self.node_encoder(node_x)
        
        # Two-layer message passing
        h = self.mp1(h, src, dst)
        h = self.mp2(h, src, dst)
        
        # Predict edge risks
        edge_feat = self.get_edge_features(h, edge_dyn_x, edge_static_x, src, dst)
        out = self.edge_head(edge_feat)
        return torch.sigmoid(out.squeeze(1))
    
    @property
    def model_name(self) -> str:
        return "Baseline-GNN"
    
    def __repr__(self) -> str:
        return f"BaselineGNNModel(hidden_dim={self.hidden_dim}, num_layers={self.num_layers})"
