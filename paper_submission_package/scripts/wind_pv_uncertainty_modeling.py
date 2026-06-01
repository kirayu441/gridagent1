from __future__ import annotations

import argparse
import json
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.mixture import BayesianGaussianMixture


@dataclass(frozen=True)
class DatasetSpec:
    name: str
    dpgmm_input: Path
    trim_input: Path


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def default_dataset_specs() -> dict[str, DatasetSpec]:
    root = project_root()
    return {
        "demo2020": DatasetSpec(
            name="demo2020",
            dpgmm_input=root / "data_final" / "DPGMM_input.csv",
            trim_input=root / "data_final" / "TRIM_input.csv",
        ),
        "formal2024": DatasetSpec(
            name="formal2024",
            dpgmm_input=root / "data_final" / "formal_guangdong_2024" / "DPGMM_input.csv",
            trim_input=root / "data_final" / "formal_guangdong_2024" / "TRIM_input.csv",
        ),
    }


def sanitize_name(raw: str) -> str:
    return "".join(ch if ch.isalnum() or ch in ("_", "-", ".") else "_" for ch in raw).strip("_")


def infer_wind_pv_columns(table: pd.DataFrame) -> tuple[list[str], list[str]]:
    wind_cols = [c for c in table.columns if "wind" in c.lower()]
    pv_cols = [c for c in table.columns if any(tag in c.lower() for tag in ("pv", "solar"))]
    if not wind_cols or not pv_cols:
        raise ValueError(f"无法自动识别风光列。当前列: {list(table.columns)}")
    return wind_cols, pv_cols


def load_wind_pv_series(spec: DatasetSpec, max_steps: int | None) -> tuple[pd.DatetimeIndex, np.ndarray, dict[str, Any]]:
    if not spec.dpgmm_input.exists():
        raise FileNotFoundError(f"缺少文件: {spec.dpgmm_input}")
    if not spec.trim_input.exists():
        raise FileNotFoundError(f"缺少文件: {spec.trim_input}")

    dpgmm_frame = pd.read_csv(spec.dpgmm_input)
    trim_frame = pd.read_csv(spec.trim_input)
    if "timestamp" not in trim_frame.columns:
        raise ValueError(f"文件缺少 timestamp 列: {spec.trim_input}")
    timestamp = pd.to_datetime(trim_frame["timestamp"], errors="coerce")
    if timestamp.isna().any():
        raise ValueError(f"timestamp 含无法解析值: {spec.trim_input}")
    if len(dpgmm_frame) != len(timestamp):
        raise ValueError(
            f"时间与特征长度不一致: dpgmm_rows={len(dpgmm_frame)}, timestamp_rows={len(timestamp)}"
        )

    wind_cols, pv_cols = infer_wind_pv_columns(dpgmm_frame)
    wind = dpgmm_frame[wind_cols].sum(axis=1).to_numpy(dtype=float)
    pv = dpgmm_frame[pv_cols].sum(axis=1).to_numpy(dtype=float)
    pair = np.column_stack([np.clip(wind, 0.0, None), np.clip(pv, 0.0, None)])
    idx = pd.DatetimeIndex(timestamp)

    if max_steps is not None and max_steps > 0:
        idx = idx[:max_steps]
        pair = pair[:max_steps]

    metadata: dict[str, Any] = {
        "wind_columns": wind_cols,
        "pv_columns": pv_cols,
        "original_rows": int(len(dpgmm_frame)),
        "used_rows": int(len(pair)),
        "start": str(idx.min()) if len(idx) else None,
        "end": str(idx.max()) if len(idx) else None,
    }
    return idx, pair, metadata


class RollingDPGMM:
    def __init__(
        self,
        window_radius: int = 6,
        max_components: int = 8,
        max_iter: int = 400,
        random_state: int = 42,
    ) -> None:
        self.window_radius = int(window_radius)
        self.max_components = int(max_components)
        self.max_iter = int(max_iter)
        self.random_state = int(random_state)

    def fit_models(self, pair: np.ndarray) -> list[BayesianGaussianMixture]:
        if pair.ndim != 2 or pair.shape[1] != 2:
            raise ValueError(f"输入维度错误，期望 [T,2]，实际 {pair.shape}")
        total_steps = pair.shape[0]
        models: list[BayesianGaussianMixture] = []

        warnings.filterwarnings("ignore", category=UserWarning)
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        warnings.filterwarnings("ignore", category=FutureWarning)

        for t in range(total_steps):
            lo = max(0, t - self.window_radius)
            hi = min(total_steps, t + self.window_radius + 1)
            window = pair[lo:hi]
            if window.shape[0] < 3:
                rng = np.random.default_rng(self.random_state + t)
                jitter = rng.normal(0.0, 1e-4, size=(3 - window.shape[0], 2))
                window = np.vstack([window, window[:1] + jitter])

            n_comp = min(self.max_components, window.shape[0])
            model = BayesianGaussianMixture(
                n_components=n_comp,
                covariance_type="full",
                weight_concentration_prior_type="dirichlet_process",
                max_iter=self.max_iter,
                random_state=self.random_state + t,
            )
            model.fit(window)
            models.append(model)

            if (t + 1) % 500 == 0 or (t + 1) == total_steps:
                print(f"  fitted {t + 1}/{total_steps}")
        return models

    def sample_trajectories(self, models: list[BayesianGaussianMixture], n_scenarios: int) -> np.ndarray:
        total_steps = len(models)
        scenarios = np.zeros((n_scenarios, total_steps, 2), dtype=float)
        for t, model in enumerate(models):
            sampled, _ = model.sample(n_scenarios)
            scenarios[:, t, :] = np.clip(sampled, 0.0, None)
        return scenarios


def reduce_scenarios_kmeans(
    scenarios: np.ndarray, n_typical: int = 10, random_state: int = 42
) -> tuple[np.ndarray, np.ndarray]:
    n_samples, total_steps, dims = scenarios.shape
    n_clusters = min(max(1, int(n_typical)), n_samples)
    flat = scenarios.reshape(n_samples, total_steps * dims)
    model = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=20)
    labels = model.fit_predict(flat)
    centers = model.cluster_centers_.reshape(n_clusters, total_steps, dims)
    probs = np.array([(labels == i).mean() for i in range(n_clusters)], dtype=float)
    probs = probs / probs.sum()
    return centers, probs


def weighted_stats(values: np.ndarray, weights: np.ndarray) -> tuple[float, float]:
    mean = float(np.sum(values * weights))
    var = float(np.sum(weights * (values - mean) ** 2))
    return mean, float(np.sqrt(max(var, 0.0)))


def evaluate_uncertainty_model(history: np.ndarray, sampled: np.ndarray, typical: np.ndarray, probs: np.ndarray) -> dict[str, Any]:
    history_wind = history[:, 0]
    history_pv = history[:, 1]
    sampled_flat = sampled.reshape(-1, 2)
    sampled_wind = sampled_flat[:, 0]
    sampled_pv = sampled_flat[:, 1]

    hist_corr = float(np.corrcoef(history_wind, history_pv)[0, 1])
    sample_corr = float(np.corrcoef(sampled_wind, sampled_pv)[0, 1])

    q05 = np.quantile(sampled[:, :, 0], 0.05, axis=0)
    q95 = np.quantile(sampled[:, :, 0], 0.95, axis=0)
    wind_90_cov = float(np.mean((history_wind >= q05) & (history_wind <= q95)))

    q05_pv = np.quantile(sampled[:, :, 1], 0.05, axis=0)
    q95_pv = np.quantile(sampled[:, :, 1], 0.95, axis=0)
    pv_90_cov = float(np.mean((history_pv >= q05_pv) & (history_pv <= q95_pv)))

    scenario_count, horizon, _ = typical.shape
    weights = np.repeat(probs / horizon, horizon)
    typical_flat = typical.reshape(scenario_count * horizon, 2)
    typ_wind_mean, typ_wind_std = weighted_stats(typical_flat[:, 0], weights)
    typ_pv_mean, typ_pv_std = weighted_stats(typical_flat[:, 1], weights)

    return {
        "history": {
            "wind_mean": float(history_wind.mean()),
            "wind_std": float(history_wind.std(ddof=0)),
            "pv_mean": float(history_pv.mean()),
            "pv_std": float(history_pv.std(ddof=0)),
            "wind_pv_corr": hist_corr,
        },
        "sampled": {
            "wind_mean": float(sampled_wind.mean()),
            "wind_std": float(sampled_wind.std(ddof=0)),
            "pv_mean": float(sampled_pv.mean()),
            "pv_std": float(sampled_pv.std(ddof=0)),
            "wind_pv_corr": sample_corr,
            "wind_90pct_coverage": wind_90_cov,
            "pv_90pct_coverage": pv_90_cov,
        },
        "typical_weighted": {
            "scenario_count": int(scenario_count),
            "wind_mean": typ_wind_mean,
            "wind_std": typ_wind_std,
            "pv_mean": typ_pv_mean,
            "pv_std": typ_pv_std,
        },
    }


def save_outputs(
    output_dir: Path,
    timestamps: pd.DatetimeIndex,
    history: np.ndarray,
    sampled: np.ndarray,
    typical: np.ndarray,
    probs: np.ndarray,
    report: dict[str, Any],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    np.save(output_dir / "sampled_scenarios.npy", sampled)
    np.save(output_dir / "typical_scenarios.npy", typical)

    pd.DataFrame(
        {
            "scenario_id": np.arange(len(probs), dtype=int),
            "probability": probs,
        }
    ).to_csv(output_dir / "scenario_probabilities.csv", index=False, encoding="utf-8")

    history_df = pd.DataFrame(
        {
            "timestamp": timestamps.tz_localize(None) if timestamps.tz is not None else timestamps,
            "wind": history[:, 0],
            "pv": history[:, 1],
        }
    )
    history_df.to_csv(output_dir / "history_series.csv", index=False, encoding="utf-8")

    records: list[dict[str, Any]] = []
    ts_plain = timestamps.tz_localize(None) if timestamps.tz is not None else timestamps
    for sid in range(typical.shape[0]):
        for t in range(typical.shape[1]):
            records.append(
                {
                    "scenario_id": sid,
                    "timestamp": str(ts_plain[t]),
                    "wind": float(typical[sid, t, 0]),
                    "pv": float(typical[sid, t, 1]),
                    "scenario_probability": float(probs[sid]),
                }
            )
    pd.DataFrame.from_records(records).to_csv(
        output_dir / "typical_scenarios_long.csv", index=False, encoding="utf-8"
    )

    with (output_dir / "uncertainty_report.json").open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)


def run_one_dataset(
    spec: DatasetSpec,
    output_root: Path,
    window_radius: int,
    max_components: int,
    max_iter: int,
    n_sampled_scenarios: int,
    n_typical_scenarios: int,
    seed: int,
    max_steps: int | None,
) -> Path:
    print(f"\n=== Running dataset: {spec.name} ===")
    timestamps, history, metadata = load_wind_pv_series(spec=spec, max_steps=max_steps)
    if len(history) == 0:
        raise ValueError(f"数据为空: {spec.name}")

    model = RollingDPGMM(
        window_radius=window_radius,
        max_components=max_components,
        max_iter=max_iter,
        random_state=seed,
    )
    models = model.fit_models(history)
    sampled = model.sample_trajectories(models=models, n_scenarios=n_sampled_scenarios)
    typical, probs = reduce_scenarios_kmeans(
        scenarios=sampled, n_typical=n_typical_scenarios, random_state=seed + 1000
    )
    metrics = evaluate_uncertainty_model(history=history, sampled=sampled, typical=typical, probs=probs)

    report = {
        "dataset": spec.name,
        "input": {
            "dpgmm_input": str(spec.dpgmm_input),
            "trim_input": str(spec.trim_input),
        },
        "series_metadata": metadata,
        "model_params": {
            "window_radius": int(window_radius),
            "max_components": int(max_components),
            "max_iter": int(max_iter),
            "seed": int(seed),
            "n_sampled_scenarios": int(n_sampled_scenarios),
            "n_typical_scenarios": int(n_typical_scenarios),
        },
        "metrics": metrics,
    }

    output_dir = output_root / sanitize_name(spec.name)
    save_outputs(
        output_dir=output_dir,
        timestamps=timestamps,
        history=history,
        sampled=sampled,
        typical=typical,
        probs=probs,
        report=report,
    )
    print(f"  output -> {output_dir}")
    return output_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="独立执行风光联合不确定性建模（滚动 DPGMM + 场景生成 + 典型场景压缩）。"
    )
    parser.add_argument(
        "--dataset",
        choices=("demo2020", "formal2024", "both"),
        default="both",
        help="选择数据集，默认 both。",
    )
    parser.add_argument(
        "--output-dir",
        default="results/wind_pv_uncertainty",
        help="输出目录，默认 results/wind_pv_uncertainty",
    )
    parser.add_argument("--window-radius", type=int, default=6, help="滚动窗口半径，默认 6。")
    parser.add_argument("--max-components", type=int, default=8, help="DPGMM 最大分量数，默认 8。")
    parser.add_argument("--max-iter", type=int, default=400, help="单时刻 DPGMM 最大迭代数，默认 400。")
    parser.add_argument("--n-sampled-scenarios", type=int, default=200, help="采样场景数量，默认 200。")
    parser.add_argument("--n-typical-scenarios", type=int, default=10, help="典型场景数量，默认 10。")
    parser.add_argument("--seed", type=int, default=42, help="随机种子，默认 42。")
    parser.add_argument(
        "--dpgmm-input",
        default="",
        help="可选：显式指定 DPGMM 输入 CSV。设置后仅运行 --dataset 指定的单个数据集。",
    )
    parser.add_argument(
        "--trim-input",
        default="",
        help="可选：显式指定 TRIM/timestamp 输入 CSV。设置后仅运行 --dataset 指定的单个数据集。",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=None,
        help="调试参数：仅使用前 N 个时间步（默认全量）。",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    specs = default_dataset_specs()
    selected = ["demo2020", "formal2024"] if args.dataset == "both" else [args.dataset]
    dpgmm_input = str(args.dpgmm_input).strip()
    trim_input = str(args.trim_input).strip()
    if dpgmm_input or trim_input:
        if args.dataset == "both":
            raise ValueError("--dpgmm-input/--trim-input 需要配合单个 --dataset 使用，不能使用 both。")
        if not dpgmm_input or not trim_input:
            raise ValueError("--dpgmm-input 和 --trim-input 必须同时提供。")
        specs[args.dataset] = DatasetSpec(
            name=args.dataset,
            dpgmm_input=(project_root() / dpgmm_input).resolve(),
            trim_input=(project_root() / trim_input).resolve(),
        )
    output_root = project_root() / args.output_dir

    outputs: list[Path] = []
    for name in selected:
        outputs.append(
            run_one_dataset(
                spec=specs[name],
                output_root=output_root,
                window_radius=args.window_radius,
                max_components=args.max_components,
                max_iter=args.max_iter,
                n_sampled_scenarios=args.n_sampled_scenarios,
                n_typical_scenarios=args.n_typical_scenarios,
                seed=args.seed,
                max_steps=args.max_steps,
            )
        )

    print("\nDone. Generated outputs:")
    for out in outputs:
        print(f" - {out}")


if __name__ == "__main__":
    main()
