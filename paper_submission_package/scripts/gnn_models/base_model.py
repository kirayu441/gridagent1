"""
Base GNN Model Class
=====================
Abstract base class for all GNN models in the comparison experiment.
"""

from abc import ABC, abstractmethod
import torch
import torch.nn as nn
from typing import Optional


class BaseGNNModel(nn.Module, ABC):
    """Abstract base class for GNN models."""
    
    def __init__(
        self,
        node_dim: int,
        edge_dyn_dim: int,
        edge_static_dim: int,
        hidden_dim: int = 64,
    ) -> None:
        super().__init__()
        self.node_dim = node_dim
        self.edge_dyn_dim = edge_dyn_dim
        self.edge_static_dim = edge_static_dim
        self.hidden_dim = hidden_dim
    
    @abstractmethod
    def forward(
        self,
        node_x: torch.Tensor,
        edge_dyn_x: torch.Tensor,
        edge_static_x: torch.Tensor,
        src: torch.Tensor,
        dst: torch.Tensor,
    ) -> torch.Tensor:
        """
        Forward pass.
        
        Args:
            node_x: [N, node_dim] node features
            edge_dyn_x: [E, edge_dyn_dim] dynamic edge features
            edge_static_x: [E, edge_static_dim] static edge features
            src: [E] source node indices
            dst: [E] destination node indices
        
        Returns:
            [E] edge risk predictions (probabilities)
        """
        pass
    
    def get_edge_features(
        self,
        h: torch.Tensor,
        edge_dyn_x: torch.Tensor,
        edge_static_x: torch.Tensor,
        src: torch.Tensor,
        dst: torch.Tensor,
    ) -> torch.Tensor:
        """Concatenate node embeddings with edge features."""
        return torch.cat([h[src], h[dst], edge_dyn_x, edge_static_x], dim=1)
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model name for logging."""
        pass
    
    @property
    def num_parameters(self) -> int:
        """Count total trainable parameters."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)
