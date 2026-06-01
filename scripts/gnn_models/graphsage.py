"""
GraphSAGE: Graph Sample and Aggregate
=======================================
Reference: Hamilton et al. (2017)
Inductive representation learning on large graphs. NeurIPS.

Core Formula:
    h_N(v) = AGG({h_u, ∀u ∈ N(v)})
    h_v^{(k)} = σ(W · CONCAT(h_v^{(k-1)}, h_N(v)^{(k)}))

Key Features:
- Inductive learning (generalizable to unseen nodes)
- Multiple aggregation functions (mean, LSTM, pooling)
- Neighbor sampling for scalability
"""

import torch
import torch.nn as nn
import torch.nn.functional as F

from .base_model import BaseGNNModel


class GraphSAGEModel(BaseGNNModel):
    """GraphSAGE: Graph Sample and Aggregate (Hamilton et al., 2017)."""
    
    def __init__(
        self,
        node_dim: int,
        edge_dyn_dim: int,
        edge_static_dim: int,
        hidden_dim: int = 64,
        num_layers: int = 2,
        aggregation: str = 'mean',
        dropout: float = 0.1,
    ) -> None:
        super().__init__(node_dim, edge_dyn_dim, edge_static_dim, hidden_dim)
        self.num_layers = num_layers
        self.aggregation = aggregation
        self.dropout = dropout
        
        # Node feature encoder
        self.node_encoder = nn.Sequential(
            nn.Linear(node_dim, hidden_dim),
            nn.GELU(),
        )
        
        # GraphSAGE layers: self transformation + neighbor aggregation
        self.self_layers = nn.ModuleList([
            nn.Linear(hidden_dim, hidden_dim)
            for _ in range(num_layers)
        ])
        self.neigh_layers = nn.ModuleList([
            nn.Linear(hidden_dim, hidden_dim)
            for _ in range(num_layers)
        ])
        self.norms = nn.ModuleList([
            nn.LayerNorm(hidden_dim)
            for _ in range(num_layers)
        ])
        self.proj_layers = nn.ModuleList([
            nn.Linear(hidden_dim * 2, hidden_dim)
            for _ in range(num_layers)
        ])
        
        # Edge risk prediction head
        self.edge_head = nn.Sequential(
            nn.Linear(hidden_dim * 2 + edge_dyn_dim + edge_static_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(p=dropout),
            nn.Linear(hidden_dim, 1),
        )
    
    def _aggregate_neighbors(
        self,
        h: torch.Tensor,
        src: torch.Tensor,
        dst: torch.Tensor,
        hidden_dim: int,
    ) -> torch.Tensor:
        """
        Aggregate neighbor features using mean aggregation.
        
        Args:
            h: [N, H] node features
            src: [E] source node indices
            dst: [E] destination node indices
            hidden_dim: feature dimension
        
        Returns:
            [N, H] aggregated neighbor features
        """
        N = h.shape[0]
        
        # For each edge (u,v), we aggregate from u to v
        # Build adjacency: for each destination node, sum features from source nodes
        h_src = h[src]  # [E, H]
        
        # Sum aggregation
        neighbor_agg = torch.zeros(N, hidden_dim, device=h.device)
        neighbor_agg.index_add_(0, dst, h_src)  # [N, H]
        
        # Normalize by degree
        deg = torch.zeros(N, device=h.device)
        deg.index_add_(0, dst, torch.ones_like(dst, dtype=torch.float))
        deg = deg.clamp_min(1.0)
        
        neighbor_agg = neighbor_agg / deg.unsqueeze(1)
        
        return neighbor_agg
    
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
        h = self.node_encoder(node_x)  # [N, H]
        
        # Apply GraphSAGE layers
        for i in range(self.num_layers):
            # Self transformation
            h_self = self.self_layers[i](h)  # [N, H]
            
            # Neighbor aggregation
            h_neigh = self._aggregate_neighbors(h, src, dst, self.hidden_dim)  # [N, H]
            h_neigh = self.neigh_layers[i](h_neigh)  # [N, H]
            
            # Concatenate and project back
            h = torch.cat([h_self, h_neigh], dim=1)  # [N, 2H]
            h_proj = self.proj_layers[i](h)  # [N, H]
            h = self.norms[i](h_proj)
            h = F.gelu(h)
            h = F.dropout(h, p=self.dropout, training=self.training)
        
        # Predict edge risks
        edge_feat = self.get_edge_features(h, edge_dyn_x, edge_static_x, src, dst)
        out = self.edge_head(edge_feat)
        return torch.sigmoid(out.squeeze(1))
    
    @property
    def model_name(self) -> str:
        return f"GraphSAGE-{self.aggregation}"
    
    def __repr__(self) -> str:
        return f"GraphSAGEModel(hidden_dim={self.hidden_dim}, num_layers={self.num_layers}, aggr={self.aggregation})"
