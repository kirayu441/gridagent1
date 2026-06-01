from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate Stage1 Rolling DPGMM + KMeans outputs using existing artifacts."
    )
    parser.add_argument(
        "--stage1-dir",
        default="final_results/runs_ieee118_full_guangdong2024/ieee118_full_guangdong2024_formal/stage1_wind_pv/formal2024",
        help="Stage1 output directory.",
    )
    parser.add_argument(
        "--comparison-report",
        default="results/ablation/stage1_comparison/stage1_comparison_report.json",
        help="Existing Stage1 method comparison report.",
    )
    parser.add_argument(
        "--stage4-report",
        default="results/gridagent_framework/formal2024_full_baseline_20260310_233109/stage4_scheduling/schloemer__c3po_ref__rr0p3/load_prioritization_report.json",
        help="Existing Stage4 report tied to the DPGMM uncertainty outputs.",
    )
    parser.add_argument(
        "--stage5-report",
        default="results/multi_criteria_resilience/formal2024/multi_criteria_report.json",
        help="Existing Stage5 report.",
    )
    parser.add_argument(
        "--stage7-report",
        default="results/gridagent_framework/formal2024_full_baseline_20260310_233109/stage7_dispatch_optimization/dispatch_optimization_report.json",
        help="Existing Stage7 dispatch report.",
    )
    parser.add_argument(
        "--output-dir",
        default="gridagent_final/stage1_performance/results",
        help="Where to write evaluation artifacts.",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_report_path(raw: Any, root: Path, fallback: Path) -> Path:
    if not raw:
        return fallback
    p = Path(str(raw))
    if p.exists():
        return p
    text = str(raw).replace("\\", "/")
    marker = "/results/"
    if marker in text:
        suffix = text.split(marker, 1)[1]
        candidate = root / "results" / Path(suffix)
        if candidate.exists():
            return candidate
    return fallback


def weighted_stats(values: np.ndarray, weights: np.ndarray) -> tuple[float, float]:
    mean = float(np.sum(values * weights))
    var = float(np.sum(weights * (values - mean) ** 2))
    return mean, float(np.sqrt(max(var, 0.0)))


def weighted_corr(x: np.ndarray, y: np.ndarray, w: np.ndarray) -> float:
    mx = np.sum(w * x)
    my = np.sum(w * y)
    cov = np.sum(w * (x - mx) * (y - my))
    vx = np.sum(w * (x - mx) ** 2)
    vy = np.sum(w * (y - my) ** 2)
    if vx <= 1e-12 or vy <= 1e-12:
        return 0.0
    return float(cov / np.sqrt(vx * vy))


def weighted_quantile(values: np.ndarray, quantiles: list[float], weights: np.ndarray | None = None) -> np.ndarray:
    v = np.asarray(values, dtype=float)
    q = np.asarray(quantiles, dtype=float)
    if weights is None:
        return np.quantile(v, q)
    w = np.asarray(weights, dtype=float)
    order = np.argsort(v)
    v = v[order]
    w = w[order]
    cw = np.cumsum(w)
    cw = cw / cw[-1]
    return np.interp(q, cw, v)


def ks_distance(x: np.ndarray, y: np.ndarray, wy: np.ndarray | None = None) -> float:
    x = np.sort(np.asarray(x, dtype=float))
    y = np.asarray(y, dtype=float)
    if wy is None:
        y = np.sort(y)
        grid = np.unique(np.concatenate([x, y]))
        fx = np.searchsorted(x, grid, side="right") / len(x)
        fy = np.searchsorted(y, grid, side="right") / len(y)
        return float(np.max(np.abs(fx - fy)))
    order = np.argsort(y)
    y = y[order]
    wy = np.asarray(wy, dtype=float)[order]
    wy = wy / wy.sum()
    grid = np.unique(np.concatenate([x, y]))
    fx = np.searchsorted(x, grid, side="right") / len(x)
    idx = np.searchsorted(y, grid, side="right") - 1
    idx = np.clip(idx, -1, len(y) - 1)
    cwy = np.cumsum(wy)
    fy = np.where(idx >= 0, cwy[idx], 0.0)
    return float(np.max(np.abs(fx - fy)))


def wasserstein_1d(x: np.ndarray, y: np.ndarray, wy: np.ndarray | None = None) -> float:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if wy is None:
        wy = np.full_like(y, 1.0 / len(y), dtype=float)
    else:
        wy = np.asarray(wy, dtype=float)
        wy = wy / wy.sum()
    wx = np.full_like(x, 1.0 / len(x), dtype=float)
    x_order = np.argsort(x)
    y_order = np.argsort(y)
    x = x[x_order]
    y = y[y_order]
    wx = wx[x_order]
    wy = wy[y_order]
    grid = np.sort(np.unique(np.concatenate([x, y])))
    if len(grid) <= 1:
        return 0.0
    cdf_x = np.searchsorted(x, grid, side="right") / len(x)
    idx = np.searchsorted(y, grid, side="right") - 1
    idx = np.clip(idx, -1, len(y) - 1)
    cwy = np.cumsum(wy)
    cdf_y = np.where(idx >= 0, cwy[idx], 0.0)
    dx = np.diff(grid)
    avg_gap = np.abs(cdf_x[:-1] - cdf_y[:-1])
    return float(np.sum(avg_gap * dx))


def acf(series: np.ndarray, max_lag: int) -> np.ndarray:
    s = np.asarray(series, dtype=float)
    s = s - s.mean()
    var = np.dot(s, s)
    out = np.ones(max_lag + 1, dtype=float)
    if var <= 1e-12:
        return out
    for lag in range(1, max_lag + 1):
        out[lag] = np.dot(s[:-lag], s[lag:]) / var
    return out


def longest_spell(mask: np.ndarray) -> int:
    best = 0
    cur = 0
    for item in mask:
        if item:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return int(best)


def js_divergence_2d(a: np.ndarray, b: np.ndarray, bins: int = 30) -> float:
    lo0 = min(float(a[:, 0].min()), float(b[:, 0].min()))
    hi0 = max(float(a[:, 0].max()), float(b[:, 0].max()))
    lo1 = min(float(a[:, 1].min()), float(b[:, 1].min()))
    hi1 = max(float(a[:, 1].max()), float(b[:, 1].max()))
    h1, _, _ = np.histogram2d(a[:, 0], a[:, 1], bins=bins, range=[[lo0, hi0], [lo1, hi1]], density=True)
    h2, _, _ = np.histogram2d(b[:, 0], b[:, 1], bins=bins, range=[[lo0, hi0], [lo1, hi1]], density=True)
    p = h1.flatten() + 1e-12
    q = h2.flatten() + 1e-12
    p = p / p.sum()
    q = q / q.sum()
    m = 0.5 * (p + q)
    kl_pm = np.sum(p * np.log(p / m))
    kl_qm = np.sum(q * np.log(q / m))
    return float(0.5 * (kl_pm + kl_qm))


def scenario_weights(probs: np.ndarray, horizon: int) -> np.ndarray:
    return np.repeat(probs / horizon, horizon)


def flatten_scenarios(arr: np.ndarray) -> np.ndarray:
    return arr.reshape(arr.shape[0] * arr.shape[1], arr.shape[2])


def build_distribution_rows(
    history: np.ndarray,
    sampled: np.ndarray,
    typical: np.ndarray,
    probs: np.ndarray,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    hist_flat = history
    sampled_flat = sampled.reshape(-1, 2)
    typical_flat = flatten_scenarios(typical)
    typ_w = scenario_weights(probs, typical.shape[1])

    rows: list[dict[str, Any]] = []
    dist_metrics: dict[str, Any] = {}
    for idx, name in enumerate(["wind", "pv"]):
        q = [0.05, 0.25, 0.50, 0.75, 0.95]
        hist_q = weighted_quantile(hist_flat[:, idx], q)
        samp_q = weighted_quantile(sampled_flat[:, idx], q)
        typ_q = weighted_quantile(typical_flat[:, idx], q, typ_w)
        for source, values, quantiles in [
            ("history", hist_flat[:, idx], hist_q),
            ("sampled", sampled_flat[:, idx], samp_q),
            ("typical_weighted", typical_flat[:, idx], typ_q),
        ]:
            if source == "typical_weighted":
                mean, std = weighted_stats(values, typ_w)
            else:
                mean = float(np.mean(values))
                std = float(np.std(values, ddof=0))
            rows.append(
                {
                    "variable": name,
                    "source": source,
                    "mean": mean,
                    "std": std,
                    "min": float(np.min(values)),
                    "max": float(np.max(values)),
                    "q05": float(quantiles[0]),
                    "q25": float(quantiles[1]),
                    "q50": float(quantiles[2]),
                    "q75": float(quantiles[3]),
                    "q95": float(quantiles[4]),
                }
            )
        dist_metrics[name] = {
            "sampled_vs_history": {
                "ks": ks_distance(hist_flat[:, idx], sampled_flat[:, idx]),
                "wasserstein": wasserstein_1d(hist_flat[:, idx], sampled_flat[:, idx]),
            },
            "typical_weighted_vs_history": {
                "ks": ks_distance(hist_flat[:, idx], typical_flat[:, idx], typ_w),
                "wasserstein": wasserstein_1d(hist_flat[:, idx], typical_flat[:, idx], typ_w),
            },
        }
    return pd.DataFrame(rows), dist_metrics


def build_joint_metrics(history: np.ndarray, sampled: np.ndarray, typical: np.ndarray, probs: np.ndarray) -> dict[str, Any]:
    sampled_flat = sampled.reshape(-1, 2)
    typical_flat = flatten_scenarios(typical)
    typ_w = scenario_weights(probs, typical.shape[1])
    hist_corr = float(np.corrcoef(history[:, 0], history[:, 1])[0, 1])
    sampled_corr = float(np.corrcoef(sampled_flat[:, 0], sampled_flat[:, 1])[0, 1])
    typical_corr = weighted_corr(typical_flat[:, 0], typical_flat[:, 1], typ_w)
    return {
        "history_corr": hist_corr,
        "sampled_corr": sampled_corr,
        "typical_weighted_corr": typical_corr,
        "sampled_corr_error": abs(sampled_corr - hist_corr),
        "typical_corr_error": abs(typical_corr - hist_corr),
        "sampled_joint_js_divergence": js_divergence_2d(history, sampled_flat),
        "typical_joint_js_divergence": js_divergence_2d(history, typical_flat),
    }


def build_time_metrics(history: np.ndarray, sampled: np.ndarray, typical: np.ndarray, probs: np.ndarray) -> dict[str, Any]:
    max_lag = 24
    out: dict[str, Any] = {}
    for idx, name in enumerate(["wind", "pv"]):
        hist_acf = acf(history[:, idx], max_lag)
        sampled_acf = np.mean([acf(sampled[s, :, idx], max_lag) for s in range(sampled.shape[0])], axis=0)
        typical_acf = np.average(
            np.stack([acf(typical[s, :, idx], max_lag) for s in range(typical.shape[0])], axis=0),
            axis=0,
            weights=probs,
        )
        hist_ramp = np.diff(history[:, idx])
        sampled_ramp = np.diff(sampled[:, :, idx], axis=1).reshape(-1)
        typical_ramp = np.diff(typical[:, :, idx], axis=1).reshape(-1)
        typ_rw = np.repeat(probs / (typical.shape[1] - 1), typical.shape[1] - 1)
        out[name] = {
            "history_lag1_acf": float(hist_acf[1]),
            "sampled_lag1_acf": float(sampled_acf[1]),
            "typical_lag1_acf": float(typical_acf[1]),
            "sampled_acf_mae_lag1_24": float(np.mean(np.abs(sampled_acf[1:] - hist_acf[1:]))),
            "typical_acf_mae_lag1_24": float(np.mean(np.abs(typical_acf[1:] - hist_acf[1:]))),
            "history_ramp_std": float(np.std(hist_ramp, ddof=0)),
            "sampled_ramp_std": float(np.std(sampled_ramp, ddof=0)),
            "typical_ramp_std": float(np.sqrt(np.sum(typ_rw * (typical_ramp - np.sum(typ_rw * typical_ramp)) ** 2))),
            "sampled_ramp_wasserstein": wasserstein_1d(hist_ramp, sampled_ramp),
            "typical_ramp_wasserstein": wasserstein_1d(hist_ramp, typical_ramp, typ_rw),
        }
    return out


def build_extreme_metrics(history: np.ndarray, sampled: np.ndarray, typical: np.ndarray, probs: np.ndarray) -> dict[str, Any]:
    out: dict[str, Any] = {}
    typ_flat = flatten_scenarios(typical)
    typ_w = scenario_weights(probs, typical.shape[1])
    for idx, name in enumerate(["wind", "pv"]):
        hist_q = np.quantile(history[:, idx], [0.05, 0.95])
        samp_q = np.quantile(sampled[:, :, idx].reshape(-1), [0.05, 0.95])
        typ_q = weighted_quantile(typ_flat[:, idx], [0.05, 0.95], typ_w)
        out[name] = {
            "history_q05": float(hist_q[0]),
            "history_q95": float(hist_q[1]),
            "sampled_q05_error": float(abs(samp_q[0] - hist_q[0])),
            "sampled_q95_error": float(abs(samp_q[1] - hist_q[1])),
            "typical_q05_error": float(abs(typ_q[0] - hist_q[0])),
            "typical_q95_error": float(abs(typ_q[1] - hist_q[1])),
        }

    total_hist = history[:, 0] + history[:, 1]
    total_sampled = sampled[:, :, 0] + sampled[:, :, 1]
    total_typ = typical[:, :, 0] + typical[:, :, 1]
    low_thr = float(np.quantile(total_hist, 0.10))
    high_ramp_thr = float(np.quantile(np.abs(np.diff(total_hist)), 0.95))

    hist_low_rate = float(np.mean(total_hist <= low_thr))
    sampled_low_rate = float(np.mean(total_sampled <= low_thr))
    typical_low_rate = float(np.sum(probs * np.mean(total_typ <= low_thr, axis=1)))

    hist_longest = longest_spell(total_hist <= low_thr)
    sampled_longest_mean = float(np.mean([longest_spell(total_sampled[i] <= low_thr) for i in range(total_sampled.shape[0])]))
    typical_longest_mean = float(np.sum(probs * np.array([longest_spell(total_typ[i] <= low_thr) for i in range(total_typ.shape[0])])))

    hist_high_ramp_rate = float(np.mean(np.abs(np.diff(total_hist)) >= high_ramp_thr))
    sampled_high_ramp_rate = float(np.mean(np.abs(np.diff(total_sampled, axis=1)) >= high_ramp_thr))
    typical_high_ramp_rate = float(
        np.sum(probs * np.mean(np.abs(np.diff(total_typ, axis=1)) >= high_ramp_thr, axis=1))
    )

    out["system_extremes"] = {
        "low_total_renewable_threshold_p10": low_thr,
        "history_low_rate": hist_low_rate,
        "sampled_low_rate": sampled_low_rate,
        "typical_low_rate": typical_low_rate,
        "history_longest_low_spell_hours": hist_longest,
        "sampled_mean_longest_low_spell_hours": sampled_longest_mean,
        "typical_mean_longest_low_spell_hours": typical_longest_mean,
        "high_abs_ramp_threshold_p95": high_ramp_thr,
        "history_high_ramp_rate": hist_high_ramp_rate,
        "sampled_high_ramp_rate": sampled_high_ramp_rate,
        "typical_high_ramp_rate": typical_high_ramp_rate,
    }
    return out


def build_downstream_snapshot(
    stage4_report: dict[str, Any],
    stage5_report: dict[str, Any],
    stage7_report: dict[str, Any],
    root: Path,
) -> dict[str, Any]:
    policy_csv = resolve_report_path(
        stage4_report.get("outputs", {}).get("policy_comparison_csv"),
        root=root,
        fallback=root / "results/load_prioritization_scheduling/formal2024/policy_comparison.csv",
    )
    policy_df = pd.read_csv(policy_csv)
    best_policy = policy_df.sort_values("critical_served_ratio", ascending=False).iloc[0].to_dict()

    topsis_csv = resolve_report_path(
        stage5_report.get("output_files", {}).get("ewm_topsis_result_csv"),
        root=root,
        fallback=root / "results/multi_criteria_resilience/formal2024/ewm_topsis_result.csv",
    )
    topsis_df = pd.read_csv(topsis_csv)
    top_rank = topsis_df.sort_values("rank" if "rank" in topsis_df.columns else topsis_df.columns[-1]).iloc[0].to_dict()

    dispatch_metrics = stage7_report.get("contextual_final_metrics", {})
    return {
        "stage4": {
            "uncertainty_dir": stage4_report.get("inputs", {}).get("uncertainty_dir"),
            "best_policy_by_critical_served_ratio": best_policy,
            "schedule_summary": stage4_report.get("modeling", {}).get("schedule_summary", {}),
        },
        "stage5": {
            "indicator_weights": stage5_report.get("ewm_weights", {}),
            "top_ranked_policy": top_rank,
        },
        "stage7": {
            "uncertainty_dir": stage7_report.get("inputs", {}).get("uncertainty_dir"),
            "selected_strategy_hours": stage7_report.get("selected_strategy_hours", []),
            "contextual_final_metrics": dispatch_metrics,
        },
    }


def extract_method_context(comparison_report: dict[str, Any]) -> pd.DataFrame:
    rows = []
    methods = comparison_report.get("methods", {})
    for name, payload in methods.items():
        metrics = payload.get("metrics", {})
        sampled = metrics.get("sampled", {})
        rows.append(
            {
                "method": name,
                "elapsed_sec": payload.get("elapsed_sec"),
                "wind_90pct_coverage": sampled.get("wind_90pct_coverage"),
                "pv_90pct_coverage": sampled.get("pv_90pct_coverage"),
                "wind_pv_corr": sampled.get("wind_pv_corr"),
                "correlation_error": metrics.get("correlation_error"),
            }
        )
    return pd.DataFrame(rows)


def make_plots(history: np.ndarray, sampled: np.ndarray, typical: np.ndarray, probs: np.ndarray, output_dir: Path) -> None:
    typ_flat = flatten_scenarios(typical)
    typ_w = scenario_weights(probs, typical.shape[1])

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    for idx, name in enumerate(["wind", "pv"]):
        axes[idx].hist(history[:, idx], bins=50, density=True, alpha=0.5, label="history")
        axes[idx].hist(sampled[:, :, idx].reshape(-1), bins=50, density=True, alpha=0.35, label="sampled")
        axes[idx].hist(typ_flat[:, idx], bins=50, density=True, alpha=0.35, weights=typ_w, label="typical")
        axes[idx].set_title(f"{name} marginal distribution")
        axes[idx].legend()
    fig.tight_layout()
    fig.savefig(output_dir / "distribution_fit.png", dpi=160)
    plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    axes[0].scatter(history[::24, 0], history[::24, 1], s=6, alpha=0.5)
    axes[0].set_title("History wind-pv scatter")
    sampled_flat = sampled.reshape(-1, 2)
    axes[1].scatter(sampled_flat[::500, 0], sampled_flat[::500, 1], s=4, alpha=0.35)
    axes[1].set_title("Sampled scenario scatter")
    axes[2].scatter(typ_flat[::100, 0], typ_flat[::100, 1], s=4, alpha=0.35)
    axes[2].set_title("Typical scenario scatter")
    for ax in axes:
        ax.set_xlabel("wind")
        ax.set_ylabel("pv")
    fig.tight_layout()
    fig.savefig(output_dir / "wind_pv_joint_relation.png", dpi=160)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    for idx, name in enumerate(["wind", "pv"]):
        hist_acf = acf(history[:, idx], 24)
        sampled_acf = np.mean([acf(sampled[s, :, idx], 24) for s in range(sampled.shape[0])], axis=0)
        typical_acf = np.average(
            np.stack([acf(typical[s, :, idx], 24) for s in range(typical.shape[0])], axis=0),
            axis=0,
            weights=probs,
        )
        axes[idx].plot(range(25), hist_acf, label="history")
        axes[idx].plot(range(25), sampled_acf, label="sampled")
        axes[idx].plot(range(25), typical_acf, label="typical")
        axes[idx].set_title(f"{name} ACF (lag 0-24)")
        axes[idx].legend()
    fig.tight_layout()
    fig.savefig(output_dir / "time_continuity_acf.png", dpi=160)
    plt.close(fig)


def dataframe_to_markdown(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    lines = []
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("|" + "|".join(["---"] * len(cols)) + "|")
    for _, row in df.iterrows():
        vals = []
        for col in cols:
            val = row[col]
            if isinstance(val, float):
                vals.append(f"{val:.6f}")
            else:
                vals.append(str(val))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def write_markdown(
    output_dir: Path,
    stage1_report: dict[str, Any],
    distribution_metrics: dict[str, Any],
    joint_metrics: dict[str, Any],
    time_metrics: dict[str, Any],
    extreme_metrics: dict[str, Any],
    downstream_snapshot: dict[str, Any],
    method_context: pd.DataFrame,
) -> None:
    lines: list[str] = []
    lines.append("# Stage1 Performance Report")
    lines.append("")
    lines.append("## Scope")
    lines.append("")
    lines.append("This report evaluates the current Stage1 method: Rolling DPGMM + KMeans scenario reduction.")
    lines.append("It reuses existing Stage1 outputs and existing downstream reports to avoid rerunning expensive stages.")
    lines.append("")
    lines.append("## 1. Distribution Fit")
    lines.append("")
    for name in ["wind", "pv"]:
        m = distribution_metrics[name]["typical_weighted_vs_history"]
        lines.append(
            f"- `{name}` typical-weighted vs history: KS={m['ks']:.6f}, Wasserstein={m['wasserstein']:.6f}."
        )
    lines.append("")
    lines.append("## 2. Wind-PV Joint Relation")
    lines.append("")
    lines.append(
        f"- History correlation: {joint_metrics['history_corr']:.6f}; "
        f"typical weighted correlation: {joint_metrics['typical_weighted_corr']:.6f}; "
        f"error: {joint_metrics['typical_corr_error']:.6f}."
    )
    lines.append(
        f"- Joint distribution JS divergence: sampled={joint_metrics['sampled_joint_js_divergence']:.6f}, "
        f"typical={joint_metrics['typical_joint_js_divergence']:.6f}."
    )
    lines.append("")
    lines.append("## 3. Time Continuity")
    lines.append("")
    for name in ["wind", "pv"]:
        m = time_metrics[name]
        lines.append(
            f"- `{name}` lag-1 ACF: history={m['history_lag1_acf']:.6f}, "
            f"typical={m['typical_lag1_acf']:.6f}; "
            f"ACF MAE(1-24)={m['typical_acf_mae_lag1_24']:.6f}; "
            f"ramp Wasserstein={m['typical_ramp_wasserstein']:.6f}."
        )
    lines.append("")
    lines.append("## 4. Extreme Coverage")
    lines.append("")
    sysx = extreme_metrics["system_extremes"]
    lines.append(
        f"- Low total renewable threshold (P10)={sysx['low_total_renewable_threshold_p10']:.6f}; "
        f"history low-rate={sysx['history_low_rate']:.6f}; "
        f"typical low-rate={sysx['typical_low_rate']:.6f}."
    )
    lines.append(
        f"- Longest low-renewable spell: history={sysx['history_longest_low_spell_hours']}h; "
        f"typical mean={sysx['typical_mean_longest_low_spell_hours']:.2f}h."
    )
    lines.append(
        f"- High absolute ramp threshold (P95)={sysx['high_abs_ramp_threshold_p95']:.6f}; "
        f"history high-ramp rate={sysx['history_high_ramp_rate']:.6f}; "
        f"typical high-ramp rate={sysx['typical_high_ramp_rate']:.6f}."
    )
    lines.append("")
    lines.append("## 5. Downstream Snapshot")
    lines.append("")
    st4 = downstream_snapshot["stage4"]["best_policy_by_critical_served_ratio"]
    lines.append(
        f"- Stage4 best policy by critical served ratio: `{st4.get('policy')}`, "
        f"critical_served_ratio={float(st4.get('critical_served_ratio', 0.0)):.6f}, "
        f"expected_total_shed={float(st4.get('expected_total_shed', 0.0)):.6f}."
    )
    st7 = downstream_snapshot["stage7"]["contextual_final_metrics"]
    lines.append(
        f"- Stage7 contextual dispatch: total_cost={float(st7.get('total_cost', 0.0)):.6f}, "
        f"EENS={float(st7.get('EENS', 0.0)):.6f}, "
        f"reliability_score={float(st7.get('reliability_score', 0.0)):.6f}."
    )
    lines.append("")
    lines.append("## 6. Existing Method Context")
    lines.append("")
    lines.append("The existing Stage1 method-comparison artifacts show the following method context:")
    lines.append("")
    lines.append(dataframe_to_markdown(method_context))
    lines.append("")
    lines.append("## Caveat")
    lines.append("")
    lines.append(
        "Downstream metrics are reused from existing formal2024 Stage4/5/7 runs driven by the same DPGMM-style uncertainty outputs. "
        "They show task usefulness, but they are not yet a full end-to-end re-run against alternative Stage1 methods."
    )
    (output_dir / "stage1_performance_report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    root = project_root()
    stage1_dir = (root / args.stage1_dir).resolve()
    comparison_report_path = (root / args.comparison_report).resolve()
    stage4_report_path = (root / args.stage4_report).resolve()
    stage5_report_path = (root / args.stage5_report).resolve()
    stage7_report_path = (root / args.stage7_report).resolve()
    output_dir = (root / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    history_df = pd.read_csv(stage1_dir / "history_series.csv")
    history = history_df[["wind", "pv"]].to_numpy(dtype=float)
    sampled = np.load(stage1_dir / "sampled_scenarios.npy")
    typical = np.load(stage1_dir / "typical_scenarios.npy")
    probs = pd.read_csv(stage1_dir / "scenario_probabilities.csv")["probability"].to_numpy(dtype=float)
    stage1_report = load_json(stage1_dir / "uncertainty_report.json")

    distribution_table, distribution_metrics = build_distribution_rows(history, sampled, typical, probs)
    distribution_table.to_csv(output_dir / "distribution_fit_table.csv", index=False, encoding="utf-8")
    (output_dir / "distribution_fit_metrics.json").write_text(
        json.dumps(distribution_metrics, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    joint_metrics = build_joint_metrics(history, sampled, typical, probs)
    (output_dir / "joint_relation_metrics.json").write_text(
        json.dumps(joint_metrics, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    time_metrics = build_time_metrics(history, sampled, typical, probs)
    (output_dir / "time_continuity_metrics.json").write_text(
        json.dumps(time_metrics, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    extreme_metrics = build_extreme_metrics(history, sampled, typical, probs)
    (output_dir / "extreme_coverage_metrics.json").write_text(
        json.dumps(extreme_metrics, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    comparison_report = load_json(comparison_report_path)
    method_context = extract_method_context(comparison_report)
    method_context.to_csv(output_dir / "existing_method_context.csv", index=False, encoding="utf-8")

    stage4_report = load_json(stage4_report_path)
    stage5_report = load_json(stage5_report_path)
    stage7_report = load_json(stage7_report_path)
    downstream_snapshot = build_downstream_snapshot(stage4_report, stage5_report, stage7_report, root)
    (output_dir / "downstream_effectiveness_snapshot.json").write_text(
        json.dumps(downstream_snapshot, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    make_plots(history, sampled, typical, probs, output_dir)
    write_markdown(
        output_dir=output_dir,
        stage1_report=stage1_report,
        distribution_metrics=distribution_metrics,
        joint_metrics=joint_metrics,
        time_metrics=time_metrics,
        extreme_metrics=extreme_metrics,
        downstream_snapshot=downstream_snapshot,
        method_context=method_context,
    )

    summary = {
        "stage1_dir": str(stage1_dir),
        "output_dir": str(output_dir),
        "history_rows": int(history.shape[0]),
        "sampled_shape": list(sampled.shape),
        "typical_shape": list(typical.shape),
        "scenario_count": int(len(probs)),
    }
    (output_dir / "run_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
