"""
STGCN: Spatio-Temporal Graph Convolutional Networks
====================================================
Reference: Yu et al. (2018)
Spatio-temporal graph convolutional networks: A deep learning framework 
for traffic forecasting. IJCAI.

Core Architecture:
- Spatial Graph Convolution: GCN-like operation
- Temporal Convolution: 1D Conv on time series
- Spatio-Temporal Block: Alternating GCN and 1D Conv layers

Key Features:
- Simultaneous modeling of spatial and temporal dependencies
- 1D convolution for efficient temporal modeling
- GCN for graph structure modeling
"""

import torch
import torch.nn as nn
import torch.nn.functional as F

from .base_model import BaseGNNModel


class TemporalConvLayer(nn.Module):
    """1D Temporal Convolution Layer."""
    
    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int = 3,
    ) -> None:
        super().__init__()
        padding = (kernel_size - 1) // 2
        self.conv = nn.Conv1d(
            in_channels,
            out_channels,
            kernel_size=kernel_size,
            padding=padding,
        )
        self.norm = nn.BatchNorm1d(out_channels)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: [B, C, T] where B=batch, C=channels, T=time steps
        
        Returns:
            [B, C', T]
        """
        x = self.conv(x)
        x = self.norm(x)
        return F.gelu(x)


class SpatialGraphConv(nn.Module):
    """Spatial Graph Convolution Layer."""
    
    def __init__(self, hidden_dim: int) -> None:
        super().__init__()
        self.fc = nn.Linear(hidden_dim, hidden_dim)
        self.norm = nn.LayerNorm(hidden_dim)
    
    def forward(self, h: torch.Tensor, adj: torch.Tensor) -> torch.Tensor:
        """
        Args:
            h: [B*N, H] node features (or [B, N, H])
            adj: [N, N] adjacency matrix
        
        Returns:
            [B*N, H] updated features
        """
        if h.dim() == 2:
            h_out = torch.matmul(adj, h)
        else:
            h_out = torch.bmm(adj.unsqueeze(0).expand(h.shape[0], -1, -1), h)
        h_out = self.fc(h_out)
        h_out = self.norm(h_out)
        return F.gelu(h_out)


class SpatioTemporalBlock(nn.Module):
    """Spatio-Temporal Convolutional Block."""
    
    def __init__(
        self,
        hidden_dim: int,
        kernel_size: int = 3,
    ) -> None:
        super().__init__()
        self.temporal_conv1 = TemporalConvLayer(hidden_dim, hidden_dim, kernel_size)
        self.spatial_conv = SpatialGraphConv(hidden_dim)
        self.temporal_conv2 = TemporalConvLayer(hidden_dim, hidden_dim, kernel_size)
        self.dropout = nn.Dropout(0.1)
    
    def forward(self, x: torch.Tensor, adj: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: [B, N, H, T] node features over time
            adj: [N, N] adjacency matrix
        
        Returns:
            [B, N, H, T] updated features
        """
        B, N, H, T = x.shape
        
        # Temporal convolution 1
        x_t = x.permute(0, 3, 1, 2)  # [B, T, N, H]
        x_t = x_t.reshape(B * N, H, T)  # [B*N, H, T]
        x_t = self.temporal_conv1(x_t)  # [B*N, H, T]
        x_t = x_t.reshape(B, T, N, H)  # [B, T, N, H]
        x_t = x_t.permute(0, 2, 3, 1)  # [B, N, H, T]
        
        # Spatial convolution
        x_s = x_t.permute(0, 3, 1, 2)  # [B, T, N, H]
        x_s = x_s.reshape(B * T, N, H)  # [B*T, N, H]
        x_s = self.spatial_conv(x_s, adj)  # [B*T, N, H]
        x_s = x_s.reshape(B, T, N, H)  # [B, T, N, H]
        x_s = x_s.permute(0, 2, 3, 1)  # [B, N, H, T]
        
        # Temporal convolution 2
        x_out = x_s.permute(0, 3, 1, 2)  # [B, T, N, H]
        x_out = x_out.reshape(B * N, H, T)  # [B*N, H, T]
        x_out = self.temporal_conv2(x_out)  # [B*N, H, T]
        x_out = x_out.reshape(B, T, N, H)  # [B, T, N, H]
        x_out = x_out.permute(0, 2, 3, 1)  # [B, N, H, T]
        
        return self.dropout(x_out)


class STGCNModel(BaseGNNModel):
    """STGCN: Spatio-Temporal Graph Convolutional Network (Yu et al., 2018)."""
    
    def __init__(
        self,
        node_dim: int,
        edge_dyn_dim: int,
        edge_static_dim: int,
        hidden_dim: int = 64,
        num_st_blocks: int = 2,
        temporal_kernel: int = 3,
        dropout: float = 0.1,
        num_timesteps: int = 3,
    ) -> None:
        super().__init__(node_dim, edge_dyn_dim, edge_static_dim, hidden_dim)
        self.num_st_blocks = num_st_blocks
        self.num_timesteps = num_timesteps
        self.dropout = dropout
        
        # Node feature encoder
        self.node_encoder = nn.Sequential(
            nn.Linear(node_dim, hidden_dim),
            nn.GELU(),
        )
        
        # Spatio-temporal blocks
        self.st_blocks = nn.ModuleList([
            SpatioTemporalBlock(hidden_dim, temporal_kernel)
            for _ in range(num_st_blocks)
        ])
        
        # Final temporal conv
        self.final_temporal = TemporalConvLayer(hidden_dim, hidden_dim)
        
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
        adj = adj + torch.eye(num_nodes, device=src.device)
        deg = adj.sum(dim=1, keepdim=True).clamp_min(1.0)
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
            node_x: [N, node_dim] - single time step input
            edge_dyn_x: [E, edge_dyn_dim]
            edge_static_x: [E, edge_static_dim]
            src: [E]
            dst: [E]
        
        Returns:
            [E] edge risk predictions
        """
        num_nodes = node_x.shape[0]
        
        # Encode node features
        h = self.node_encoder(node_x)  # [N, H]
        
        # Build adjacency
        adj = self._build_adjacency(num_nodes, src, dst)
        
        # Add time dimension: [N, H] -> [1, N, H, 1] -> [1, N, H, T]
        h = h.unsqueeze(0).unsqueeze(-1)  # [1, N, H, 1]
        h = h.expand(-1, -1, -1, self.num_timesteps)  # [1, N, H, T]
        
        # Apply spatio-temporal blocks
        for block in self.st_blocks:
            h = block(h, adj)
        
        # Apply final temporal conv
        B, N, H, T = h.shape
        x_t = h.permute(0, 3, 1, 2)  # [B, T, N, H]
        x_t = x_t.reshape(B * N, H, T)  # [B*N, H, T]
        x_t = self.final_temporal(x_t)  # [B*N, H, T]
        x_t = x_t.reshape(B, T, N, H)  # [B, T, N, H]
        x_t = x_t.permute(0, 2, 3, 1)  # [B, N, H, T]
        
        # Take last time step and squeeze
        h = x_t.squeeze(0)[:, :, -1]  # [N, H]
        
        # Predict edge risks
        edge_feat = self.get_edge_features(h, edge_dyn_x, edge_static_x, src, dst)
        out = self.edge_head(edge_feat)
        return torch.sigmoid(out.squeeze(1))
    
    @property
    def model_name(self) -> str:
        return "STGCN"
    
    def __repr__(self) -> str:
        return f"STGCNModel(hidden_dim={self.hidden_dim}, num_st_blocks={self.num_st_blocks})"
