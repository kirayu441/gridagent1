"""
GNN Models Package for Grid Risk Prediction
==========================================

This package contains modular GNN model implementations for comparison experiments.
Each model is in a separate file for easy maintenance and extension.

Models:
- gcn: Graph Convolutional Network (Kipf & Welling, 2017)
- gat: Graph Attention Network (Velickovic et al., 2018)
- graphsage: Graph Sample and Aggregate (Hamilton et al., 2017)
- stgcn: Spatio-Temporal Graph Convolutional Networks (Yu et al., 2018)
- baseline_gnn: Two-layer message passing baseline
- metapath_v1: Fixed metapath + semantic attention + residual gating (Ours)

References:
- Kipf & Welling (2017): Semi-supervised classification with GCN. ICLR.
- Velickovic et al. (2018): Graph attention networks. ICLR.
- Hamilton et al. (2017): Inductive representation learning. NeurIPS.
- Yu et al. (2018): Spatio-temporal GCN for traffic forecasting. IJCAI.
"""

from .base_model import BaseGNNModel
from .gcn import GCNModel
from .gat import GATModel
from .graphsage import GraphSAGEModel
from .stgcn import STGCNModel
from .baseline_gnn import BaselineGNNModel
from .metapath_v1 import MetaPathV1LocalGateModel, MetaPathV1Model
from .metapath_local import (
    MetaPathLocalResidualModel,
    MetaPathLocalRiskAttentionModel,
    MetaPathLocalRiskAttentionResidualModel,
)
from .mlp import MLPModel

# Model registry for easy access
MODEL_REGISTRY = {
    'gcn': GCNModel,
    'gat': GATModel,
    'graphsage': GraphSAGEModel,
    'stgcn': STGCNModel,
    'baseline_gnn': BaselineGNNModel,
    'metapath_v1': MetaPathV1Model,
    'metapath_v1_local_gate': MetaPathV1LocalGateModel,
    'metapath_local': MetaPathLocalResidualModel,
    'metapath_local_riskattn': MetaPathLocalRiskAttentionModel,
    'metapath_local_riskattn_resid': MetaPathLocalRiskAttentionResidualModel,
    'mlp': MLPModel,
}

__all__ = [
    'BaseGNNModel',
    'GCNModel',
    'GATModel',
    'GraphSAGEModel',
    'STGCNModel',
    'BaselineGNNModel',
    'MetaPathV1Model',
    'MetaPathV1LocalGateModel',
    'MetaPathLocalResidualModel',
    'MetaPathLocalRiskAttentionModel',
    'MetaPathLocalRiskAttentionResidualModel',
    'MLPModel',
    'MODEL_REGISTRY',
]
