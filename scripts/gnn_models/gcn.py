"""
GCN: Graph Convolutional Network
=================================
Reference: Kipf & Welling (2017)
Semi-supervised classification with graph convolutional networks. ICLR.

Core Formula:
    H^{(l+1)} = σ(D̃^{-1/2} Ã D̃^{-1/2} H^{(l)} W^{(l)})

Key Features:
- Spectral graph convolution (simplified)
- Normalized adjacency matrix aggregation
- Transductive learning
"""

import torch
import torch.nn as nn
import torch.nn.functional as F

from .base_model import BaseGNNModel


class GCNModel(BaseGNNModel):
    """GCN: Graph Convolutional Network (Kipf & Welling, 2017)."""
    
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
        )
        
        # GCN layers
        self.convs = nn.ModuleList([
            nn.Linear(hidden_dim, hidden_dim)
            for _ in range(num_layers)
        ])
        self.norms = nn.ModuleList([
            nn.LayerNorm(hidden_dim)
            for _ in range(num_layers)
        ])
        
        # Edge risk prediction head
        self.edge_head = nn.Sequential(
            nn.Linear(hidden_dim * 2 + edge_dyn_dim + edge_static_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(p=dropout),
            nn.Linear(hidden_dim, 1),
        )
    
    def _build_adjacency(self, num_nodes: int, src: torch.Tensor, dst: torch.Tensor) -> torch.Tensor:
        """Build normalized adjacency matrix."""
        adj = torch.zeros(num_nodes, num_nodes, device=src.device)
        adj[src, dst] = 1.0
        adj[dst, src] = 1.0
        # Add self-loops
        adj = adj + torch.eye(num_nodes, device=src.device)
        # Degree matrix
        deg = adj.sum(dim=1, keepdim=True).clamp_min(1.0)
        # Normalized adjacency: D^{-1/2} A D^{-1/2}
        norm_deg = deg.pow(-0.5)
        norm_deg[torch.isinf(norm_deg)] = 0.0
        adj = norm_deg * adj * norm_deg.T
        return adj
    
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
        num_nodes = node_x.shape[0]
        
        # Encode node features
        h = self.node_encoder(node_x)
        
        # Build adjacency and apply GCN layers
        adj = self._build_adjacency(num_nodes, src, dst)
        
        for i in range(self.num_layers):
            h_new = adj @ self.convs[i](h)
            h_new = self.norms[i](h_new)
            h_new = F.gelu(h_new)
            h_new = F.dropout(h_new, p=self.dropout, training=self.training)
            h = h_new
        
        # Predict edge risks
        edge_feat = self.get_edge_features(h, edge_dyn_x, edge_static_x, src, dst)
        out = self.edge_head(edge_feat)
        return torch.sigmoid(out.squeeze(1))
    
    @property
    def model_name(self) -> str:
        return "GCN"
    
    def __repr__(self) -> str:
        return f"GCNModel(hidden_dim={self.hidden_dim}, num_layers={self.num_layers})"
