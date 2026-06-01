"""
MLP: Multi-Layer Perceptron Baseline
====================================
Reference: Standard feedforward neural network

This is a no-graph baseline that only uses edge features (no graph structure).
Used as a baseline to measure the contribution of graph information.

Key Features:
- No graph structure utilized
- Only edge dynamic and static features
- Simple fully-connected layers
"""

import torch
import torch.nn as nn
import torch.nn.functional as F

from .base_model import BaseGNNModel


class MLPModel(BaseGNNModel):
    """MLP: Multi-Layer Perceptron (no-graph baseline)."""
    
    def __init__(
        self,
        node_dim: int,
        edge_dyn_dim: int,
        edge_static_dim: int,
        hidden_dim: int = 64,
        num_layers: int = 3,
        dropout: float = 0.1,
    ) -> None:
        super().__init__(node_dim, edge_dyn_dim, edge_static_dim, hidden_dim)
        self.num_layers = num_layers
        self.dropout = dropout
        
        # Total input dimension = edge dynamic + edge static
        total_dim = edge_dyn_dim + edge_static_dim
        
        # Build MLP layers
        layers = []
        in_dim = total_dim
        for i in range(num_layers - 1):
            layers.append(nn.Linear(in_dim, hidden_dim))
            layers.append(nn.GELU())
            layers.append(nn.Dropout(p=dropout))
            in_dim = hidden_dim
        
        # Final layer outputs 1 for risk prediction
        layers.append(nn.Linear(in_dim, 1))
        self.mlp = nn.Sequential(*layers)
        
        self._param_count = sum(p.numel() for p in self.parameters())
    
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
            node_x: [N, node_dim] (ignored in MLP)
            edge_dyn_x: [E, edge_dyn_dim]
            edge_static_x: [E, edge_static_dim]
            src: [E] (ignored in MLP)
            dst: [E] (ignored in MLP)
        
        Returns:
            [E] edge risk predictions
        """
        # Concatenate edge features only (no node features)
        edge_feat = torch.cat([edge_dyn_x, edge_static_x], dim=1)  # [E, edge_dyn_dim + edge_static_dim]
        
        # Pass through MLP
        out = self.mlp(edge_feat)
        
        return torch.sigmoid(out.squeeze(1))
    
    @property
    def model_name(self) -> str:
        return "MLP"
    
    @property
    def num_parameters(self) -> int:
        return self._param_count
    
    def __repr__(self) -> str:
        return f"MLPModel(hidden_dim={self.hidden_dim}, num_layers={self.num_layers})"
