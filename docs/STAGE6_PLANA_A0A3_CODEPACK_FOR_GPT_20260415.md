# Stage6 PlanA A0-A3 Code Pack (For GPT)

## 1) 目的

这份文档把 Stage6 里 A0/A1/A2/A3 的定义和关键代码集中在一起，方便直接发给 GPT 做二次分析。

## 2) A0/A1/A2/A3 定义

- A0 `A0_baseline`
  - `metapath_v1_enabled=False`
  - 无 MetaPath 分支，走 `LineRiskGNN`。
- A1 `A1_metapath_fixed`
  - `metapath_v1_enabled=True`
  - `metapath_attention_mode='fixed'`。
- A2 `A2_metapath_adaptive_global`
  - `metapath_v1_enabled=True`
  - `metapath_attention_mode='adaptive_global'`。
- A3 `A3_metapath_adaptive_context`
  - `metapath_v1_enabled=True`
  - `metapath_attention_mode='adaptive_context'`。

## 3) 实验分组代码（A0~A3）

来源：`scripts/run_stage6_planA_experiment.py`

```python
def build_cases(args: argparse.Namespace, c3po: Path, wang: Path) -> list[PlanACase]:
    label_to_tensor = {
        "c3po_ref": str(c3po),
        "wang_qmc": str(wang),
    }
    model_groups = [
        ("A0_baseline", False, "fixed"),
        ("A1_metapath_fixed", True, "fixed"),
        ("A2_metapath_adaptive_global", True, "adaptive_global"),
        ("A3_metapath_adaptive_context", True, "adaptive_context"),
    ]
    seeds = parse_int_list(args.seeds)
    out: list[PlanACase] = []
    for seed in seeds:
        for label_method, tensor in label_to_tensor.items():
            for group_name, use_metapath, attention_mode in model_groups:
                case_id = f"A_label-{label_method}_group-{group_name}_seed-{seed}"
                out.append(
                    PlanACase(
                        block="A",
                        case_id=case_id,
                        seed=int(seed),
                        label_method=label_method,
                        model_group=group_name,
                        contingency_tensor=tensor,
                        metapath_v1_enabled=bool(use_metapath),
                        metapath_attention_mode=str(attention_mode),
                        metapath_topk=int(args.metapath_topk),
                        hidden_dim=int(args.hidden_dim),
                        epochs=int(args.epochs),
                        lr=float(args.lr),
                        weight_decay=float(args.weight_decay),
                        train_ratio=float(args.train_ratio),
                        risk_weight_alpha=0.0,
                        risk_weight_beta=0.0,
                        risk_weight_threshold=float(args.risk_weight_threshold),
                        metapath_gate_reg_lambda=0.0,
                        metapath_attention_entropy_reg_lambda=0.0,
                        metapath_warmup_epochs=0,
                    )
                )
    return out
```

## 4) A0 基线模型代码（LineRiskGNN）

来源：`scripts/gnn_warning_module.py`

```python
class LineRiskGNN(nn.Module):
    def __init__(self, node_dim: int, edge_dyn_dim: int, edge_static_dim: int, hidden_dim: int = 64) -> None:
        super().__init__()
        self.node_encoder = nn.Sequential(
            nn.Linear(node_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.GELU(),
        )
        self.mp1 = GraphMessageLayer(hidden_dim)
        self.mp2 = GraphMessageLayer(hidden_dim)
        self.edge_head = nn.Sequential(
            nn.Linear(hidden_dim * 2 + edge_dyn_dim + edge_static_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(p=0.10),
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
        h = self.node_encoder(node_x)
        h = self.mp1(h, src, dst)
        h = self.mp2(h, src, dst)
        edge_feat = torch.cat([h[src], h[dst], edge_dyn_x, edge_static_x], dim=1)
        out = self.edge_head(edge_feat).squeeze(1)
        return torch.sigmoid(out)
```

## 5) A1/A2/A3 注意力模式核心代码

来源：`scripts/gnn_warning_module.py`

```python
class MetaPathSemanticBlock(nn.Module):
    def __init__(
        self,
        hidden_dim: int,
        num_metapaths: int,
        attention_mode: str = "fixed",
        edge_dyn_dim: int = 0,
    ) -> None:
        super().__init__()
        self.num_metapaths = int(num_metapaths)
        self.attention_mode = str(attention_mode)
        self.score_proj = nn.Linear(hidden_dim, hidden_dim)
        self.context_vectors = nn.Parameter(torch.randn(self.num_metapaths, hidden_dim) * 0.02)
        self.global_path_bias = nn.Parameter(torch.zeros(self.num_metapaths))
        self.condition_proj: nn.Linear | None = None
        if self.attention_mode == "adaptive_context" and int(edge_dyn_dim) > 0:
            self.condition_proj = nn.Linear(int(edge_dyn_dim), hidden_dim, bias=False)

    def forward(
        self,
        edge_repr: torch.Tensor,
        metapath_index: torch.Tensor,
        metapath_mask: torch.Tensor,
        edge_context: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        safe_index = metapath_index.clamp_min(0)
        neighbor_repr = edge_repr[safe_index]  # [P,E,K,H]
        mask = metapath_mask.unsqueeze(-1)  # [P,E,K,1]

        denom = mask.sum(dim=2).clamp_min(1.0)  # [P,E,1]
        path_repr = (neighbor_repr * mask).sum(dim=2) / denom  # [P,E,H]

        path_repr_ep = path_repr.permute(1, 0, 2)  # [E,P,H]
        score_feat = torch.tanh(self.score_proj(path_repr_ep))  # [E,P,H]
        score = torch.einsum("eph,ph->ep", score_feat, self.context_vectors)  # [E,P]
        if self.attention_mode == "adaptive_global":
            global_ctx = torch.tanh(path_repr_ep.mean(dim=0))  # [P,H]
            adaptive_bias = (global_ctx * self.context_vectors).sum(dim=1)  # [P]
            score = score + adaptive_bias.unsqueeze(0) + self.global_path_bias.unsqueeze(0)
        elif self.attention_mode == "adaptive_context" and self.condition_proj is not None and edge_context is not None:
            cond = torch.tanh(self.condition_proj(edge_context))  # [E,H]
            score = score + torch.einsum("eph,eh->ep", score_feat, cond)
        alpha = torch.softmax(score, dim=1)

        context = (alpha.unsqueeze(-1) * path_repr_ep).sum(dim=1)  # [E,H]
        return context, alpha
```

## 6) MetaPath主模型如何接收注意力模式

来源：`scripts/gnn_warning_module.py`

```python
class LineRiskMetaPathGNN(nn.Module):
    def __init__(
        self,
        node_dim: int,
        edge_dyn_dim: int,
        edge_static_dim: int,
        hidden_dim: int,
        num_metapaths: int,
        metapath_attention_mode: str = "fixed",
    ) -> None:
        super().__init__()
        ...
        self.metapath_block = MetaPathSemanticBlock(
            hidden_dim=hidden_dim,
            num_metapaths=num_metapaths,
            attention_mode=metapath_attention_mode,
            edge_dyn_dim=edge_dyn_dim,
        )
        ...

    def forward(...):
        ...
        metapath_context, alpha = self.metapath_block(
            edge_repr=edge_repr,
            metapath_index=metapath_index,
            metapath_mask=metapath_mask,
            edge_context=edge_dyn_x,
        )
        ...
```

## 7) 训练时 A0/A1~A3 走不同模型分支

来源：`scripts/gnn_warning_module.py`

```python
metapath_enabled = bool(
    use_metapath_v1
    and data.metapath_index is not None
    and data.metapath_mask is not None
    and data.metapath_names is not None
    and len(data.metapath_names) > 0
)

if metapath_enabled:
    model: nn.Module = LineRiskMetaPathGNN(
        node_dim=node_x.shape[2],
        edge_dyn_dim=edge_dyn.shape[2],
        edge_static_dim=edge_static.shape[1],
        hidden_dim=hidden_dim,
        num_metapaths=len(data.metapath_names or []),
        metapath_attention_mode=str(metapath_attention_mode),
    ).to(device)
else:
    model = LineRiskGNN(
        node_dim=node_x.shape[2],
        edge_dyn_dim=edge_dyn.shape[2],
        edge_static_dim=edge_static.shape[1],
        hidden_dim=hidden_dim,
    ).to(device)
```

## 8) CLI 参数（注意力模式开关）

来源：`scripts/gnn_warning_module.py`

```python
parser.add_argument(
    "--metapath-attention-mode",
    type=str,
    choices=["fixed", "adaptive_global", "adaptive_context"],
    default="fixed",
    help="Semantic-attention mode for MetaPath branch.",
)
```

## 9) PlanA 运行器如何把模式传给 Stage6

来源：`scripts/run_stage6_planA_experiment.py`

```python
cmd = [
    python_exe,
    str(root / "scripts" / "gnn_warning_module.py"),
    ...
    "--metapath-attention-mode",
    str(c.metapath_attention_mode),
    ...
]
cmd.append("--metapath-v1-enabled" if c.metapath_v1_enabled else "--no-metapath-v1-enabled")
```

## 10) 给 GPT 的一句话上下文

当前 Stage6 PlanA 实验在同一标签与同一训练配置下，对比了：
- A0: 无 MetaPath（Baseline GNN）
- A1: MetaPath + fixed attention
- A2: MetaPath + adaptive global attention
- A3: MetaPath + adaptive context attention

其中 A2 比 A1 多了全局自适应偏置，A3 比 A1 多了基于边动态特征的条件化打分。
