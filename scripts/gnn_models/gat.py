"""
GAT: Graph Attention Network
==============================
Reference: Velickovic et al. (2018)
Graph attention networks. ICLR.

Core Formula:
    α_{ij} = softmax_j(LeakyReLU(a^T [Wh_i || Wh_j]))
    h_i' = σ(Σ_{j∈N_i} α_{ij} W h_j)

Key Features:
- Implicit attention mechanism
- Multi-head attention
- Induction-friendly
"""

import torch
import torch.nn as nn
import torch.nn.functional as F

from .base_model import BaseGNNModel


class GraphAttentionLayer(nn.Module):
    """Single Graph Attention Layer with multi-head attention."""
    
    def __init__(
        self,
        in_dim: int,
        out_dim: int,
        num_heads: int = 4,
        dropout: float = 0.1,
        leakiness: float = 0.2,
    ) -> None:
        super().__init__()
        self.num_heads = num_heads
        self.head_dim = out_dim // num_heads
        assert out_dim % num_heads == 0, "out_dim must be divisible by num_heads"
        
        self.W = nn.Linear(in_dim, out_dim)
        self.att = nn.Parameter(torch.randn(self.head_dim * 2) * 0.02)
        self.leaky_relu = nn.LeakyReLU(leakiness)
        self.dropout = nn.Dropout(dropout)
        
        self.reset_parameters()
    
    def reset_parameters(self) -> None:
        nn.init.xavier_uniform_(self.W.weight)
        nn.init.zeros_(self.W.bias)
        nn.init.zeros_(self.att)
    
    def forward(self, h: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        """
        Args:
            h: [N, in_dim] node features
            edge_index: [2, E] source and target indices
        
        Returns:
            [N, out_dim] updated node features
        """
        N = h.shape[0]
        H = self.num_heads
        D = self.head_dim
        E = edge_index.shape[1]
        
        # Linear projection
        Wh = self.W(h)  # [N, H*D]
        Wh = Wh.view(N, H, D)  # [N, H, D]
        
        src_idx, dst_idx = edge_index[0], edge_index[1]
        
        # Get source and destination features for each edge
        Wh_src = Wh[src_idx]  # [E, H, D]
        Wh_dst = Wh[dst_idx]  # [E, H, D]
        
        # Compute attention scores for each head
        # Concatenate source and dest: [E, H, 2D]
        a_input = torch.cat([Wh_src, Wh_dst], dim=-1)
        
        # Reshape for efficient computation
        a_input_flat = a_input.view(E * H, 2 * D)
        att_flat = torch.matmul(a_input_flat, self.att)  # [E*H]
        att = att_flat.view(E, H)  # [E, H]
        
        att = self.leaky_relu(att)  # [E, H]
        
        # Compute attention weights by grouping edges to same destination
        att_exp = torch.exp(att)  # [E, H]
        
        # Sum exp scores per destination node
        att_sum = torch.zeros(N, H, device=h.device)
        att_sum.index_add_(0, dst_idx, att_exp)  # [N, H]
        att_sum = att_sum.clamp_min(1e-8)
        
        # Compute final attention weights
        att_weights = att_exp / att_sum[dst_idx]  # [E, H]
        att_weights = self.dropout(att_weights)  # [E, H]
        
        # Aggregate neighbor features: weighted sum per head
        aggregated = Wh_src * att_weights.unsqueeze(-1)  # [E, H, D]
        
        # Sum to each destination node for each head
        h_prime = torch.zeros(N, H, D, device=h.device)
        h_prime.index_add_(0, dst_idx, aggregated)  # [N, H, D]
        
        # Reshape output: concat heads
        h_prime = h_prime.view(N, -1)  # [N, H*D] = [N, out_dim]
        
        return F.elu(h_prime)


class GATModel(BaseGNNModel):
    """GAT: Graph Attention Network (Velickovic et al., 2018)."""
    
    def __init__(
        self,
        node_dim: int,
        edge_dyn_dim: int,
        edge_static_dim: int,
        hidden_dim: int = 64,
        num_heads: int = 4,
        num_layers: int = 2,
        dropout: float = 0.1,
    ) -> None:
        super().__init__(node_dim, edge_dyn_dim, edge_static_dim, hidden_dim)
        self.num_heads = num_heads
        self.num_layers = num_layers
        self.dropout = dropout
        
        # Node feature encoder
        self.node_encoder = nn.Sequential(
            nn.Linear(node_dim, hidden_dim),
            nn.GELU(),
        )
        
        # GAT layers
        self.gat_layers = nn.ModuleList([
            GraphAttentionLayer(
                in_dim=hidden_dim,
                out_dim=hidden_dim,
                num_heads=num_heads,
                dropout=dropout,
            )
            for _ in range(num_layers)
        ])
        
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
        
        # Stack edge index for GAT layers
        edge_index = torch.stack([src, dst], dim=0)
        
        # Apply GAT layers
        for layer in self.gat_layers:
            h = layer(h, edge_index)
        
        # Predict edge risks
        edge_feat = self.get_edge_features(h, edge_dyn_x, edge_static_x, src, dst)
        out = self.edge_head(edge_feat)
        return torch.sigmoid(out.squeeze(1))
    
    @property
    def model_name(self) -> str:
        return "GAT"
    
    def __repr__(self) -> str:
        return f"GATModel(hidden_dim={self.hidden_dim}, num_heads={self.num_heads}, num_layers={self.num_layers})"
