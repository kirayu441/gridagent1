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


@dataclass(frozen=True)
class ScalingSpec:
    scale: np.ndarray
    upper: np.ndarray
    pv_day_mask: np.ndarray


def sanitize_name(raw: str) -> str:
    return "".join(ch if ch.isalnum() or ch in ("_", "-", ".") else "_" for ch in raw).strip("_")


def resolve_path(path_str: str, root: Path) -> Path:
    path = Path(path_str)
    return path if path.is_absolute() else (root / path).resolve()


def infer_wind_pv_columns(table: pd.DataFrame) -> tuple[list[str], list[str]]:
    wind_cols = [c for c in table.columns if "wind" in c.lower()]
    pv_cols = [c for c in table.columns if any(tag in c.lower() for tag in ("pv", "solar"))]
    if not wind_cols or not pv_cols:
        raise ValueError(f"cannot infer wind/pv columns from {list(table.columns)}")
    return wind_cols, pv_cols


def load_wind_pv_series(spec: DatasetSpec, max_steps: int | None) -> tuple[pd.DatetimeIndex, np.ndarray, dict[str, Any]]:
    if not spec.dpgmm_input.exists():
        raise FileNotFoundError(f"missing file: {spec.dpgmm_input}")
    if not spec.trim_input.exists():
        raise FileNotFoundError(f"missing file: {spec.trim_input}")

    dpgmm_frame = pd.read_csv(spec.dpgmm_input)
    trim_frame = pd.read_csv(spec.trim_input)
    if "timestamp" not in trim_frame.columns:
        raise ValueError(f"timestamp column missing in {spec.trim_input}")
    timestamp = pd.to_datetime(trim_frame["timestamp"], errors="coerce")
    if timestamp.isna().any():
        raise ValueError(f"timestamp contains invalid values: {spec.trim_input}")
    if len(dpgmm_frame) != len(timestamp):
        raise ValueError(
            f"row mismatch: dpgmm_rows={len(dpgmm_frame)}, timestamp_rows={len(timestamp)}"
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


def build_transition_tensor(pair: np.ndarray) -> np.ndarray:
    if len(pair) < 2:
        raise ValueError("at least 2 time steps are required")
    prev = pair[:-1]
    curr = pair[1:]
    return np.hstack([prev, curr])


def build_target_transition_tensor(pair: np.ndarray, target_idx: int) -> np.ndarray:
    if len(pair) < 2:
        raise ValueError("at least 2 time steps are required")
    prev = pair[:-1]
    curr_target = pair[1:, target_idx : target_idx + 1]
    return np.hstack([prev, curr_target])


def build_scaling_spec(
    history: np.ndarray,
    timestamps: pd.DatetimeIndex,
    pv_eps: float = 1e-4,
    quantile: float = 0.95,
) -> ScalingSpec:
    upper = np.maximum(history.max(axis=0), 1e-6)
    scale = upper.copy()
    mask_frame = pd.DataFrame(
        {
            "month": timestamps.month,
            "hour": timestamps.hour,
            "pv": history[:, 1],
        }
    )
    pv_q = mask_frame.groupby(["month", "hour"])["pv"].quantile(quantile)
    pv_day_mask = np.array(
        [float(pv_q.loc[(ts.month, ts.hour)]) > pv_eps for ts in timestamps],
        dtype=bool,
    )
    return ScalingSpec(scale=scale, upper=upper, pv_day_mask=pv_day_mask)


def normalize_history(history: np.ndarray, scaling: ScalingSpec) -> np.ndarray:
    return history / scaling.scale


def restore_history(normalized: np.ndarray, scaling: ScalingSpec) -> np.ndarray:
    return normalized * scaling.scale


def apply_output_constraints(values: np.ndarray, upper: np.ndarray, pv_allowed: bool) -> np.ndarray:
    clipped = np.clip(values, 0.0, upper)
    if not pv_allowed:
        clipped[1] = 0.0
    return clipped


def calibrate_wind_global(
    sampled: np.ndarray,
    history: np.ndarray,
    upper: np.ndarray,
    shrink: float,
    min_std: float = 1e-6,
) -> np.ndarray:
    calibrated = sampled.copy()
    hist_mean = float(history[:, 0].mean())
    hist_std = float(history[:, 0].std(ddof=0))
    samp_mean = float(calibrated[:, :, 0].mean())
    samp_std = float(calibrated[:, :, 0].std(ddof=0))
    if samp_std < min_std:
        calibrated[:, :, 0] = hist_mean
    else:
        adjusted = hist_mean + shrink * (hist_std / (samp_std + min_std)) * (calibrated[:, :, 0] - samp_mean)
        calibrated[:, :, 0] = adjusted
    calibrated[:, :, 0] = np.clip(calibrated[:, :, 0], 0.0, upper[0])
    return calibrated


def calibrate_wind_by_month_hour(
    sampled: np.ndarray,
    history: np.ndarray,
    timestamps: pd.DatetimeIndex,
    upper: np.ndarray,
    shrink: float,
    min_std: float = 1e-6,
) -> np.ndarray:
    calibrated = sampled.copy()
    for month in range(1, 13):
        for hour in range(24):
            idx = np.where((timestamps.month == month) & (timestamps.hour == hour))[0]
            if len(idx) == 0:
                continue
            hist_vals = history[idx, 0]
            samp_vals = calibrated[:, idx, 0].reshape(-1)
            hist_mean = float(hist_vals.mean())
            hist_std = float(hist_vals.std(ddof=0))
            samp_mean = float(samp_vals.mean())
            samp_std = float(samp_vals.std(ddof=0))
            if samp_std < min_std:
                calibrated[:, idx, 0] = hist_mean
            else:
                adjusted = hist_mean + shrink * (hist_std / (samp_std + min_std)) * (calibrated[:, idx, 0] - samp_mean)
                calibrated[:, idx, 0] = adjusted
    calibrated[:, :, 0] = np.clip(calibrated[:, :, 0], 0.0, upper[0])
    return calibrated


def make_psd(cov: np.ndarray, eps: float) -> np.ndarray:
    sym_cov = 0.5 * (cov + cov.T)
    vals, vecs = np.linalg.eigh(sym_cov)
    vals = np.maximum(vals, eps)
    return vecs @ np.diag(vals) @ vecs.T


def cyclic_hour_diff(hours: np.ndarray, target_hour: int) -> np.ndarray:
    diff = np.abs(hours - target_hour)
    return np.minimum(diff, 24 - diff)


def cyclic_day_diff(days: np.ndarray, target_day: int) -> np.ndarray:
    diff = np.abs(days - target_day)
    return np.minimum(diff, 366 - diff)


class ConditionalRollingDPGMM:
    def __init__(
        self,
        window_radius: int = 24,
        season_day_band: int = 30,
        pv_season_day_band: int | None = None,
        hour_band: int = 0,
        min_structured_window: int = 30,
        max_components: int = 8,
        max_iter: int = 150,
        shared_block_hours: int = 1,
        random_state: int = 42,
        covariance_reg: float = 1e-6,
    ) -> None:
        self.window_radius = int(window_radius)
        self.season_day_band = int(season_day_band)
        self.pv_season_day_band = int(pv_season_day_band) if pv_season_day_band is not None else int(season_day_band)
        self.hour_band = int(hour_band)
        self.min_structured_window = int(min_structured_window)
        self.max_components = int(max_components)
        self.max_iter = int(max_iter)
        self.shared_block_hours = max(1, int(shared_block_hours))
        self.random_state = int(random_state)
        self.covariance_reg = float(covariance_reg)

    def _select_structured_window(
        self,
        timestamps: pd.DatetimeIndex,
        pv_day_mask: np.ndarray,
        t_center: int,
        enforce_pv_state: bool = True,
        use_pv_band: bool = False,
    ) -> np.ndarray:
        transition_ts = timestamps[1:]
        target = transition_ts[t_center]
        transition_hours = transition_ts.hour.to_numpy()
        transition_days = transition_ts.dayofyear.to_numpy()
        hour_ok = cyclic_hour_diff(transition_hours, int(target.hour)) <= self.hour_band
        season_band = self.pv_season_day_band if use_pv_band else self.season_day_band
        day_ok = cyclic_day_diff(transition_days, int(target.dayofyear)) <= season_band
        if enforce_pv_state:
            target_pv_day = bool(pv_day_mask[t_center + 1])
            pv_ok = pv_day_mask[1:] == target_pv_day
        else:
            pv_ok = np.ones(len(transition_ts), dtype=bool)
        return np.where(hour_ok & day_ok & pv_ok)[0]

    def fit_models(
        self,
        transitions: np.ndarray,
        timestamps: pd.DatetimeIndex,
        pv_day_mask: np.ndarray,
        enforce_pv_state: bool = True,
        use_pv_band: bool = False,
    ) -> list[BayesianGaussianMixture]:
        if transitions.ndim != 2 or transitions.shape[1] < 3:
            raise ValueError(f"expected transitions [T-1,d>=3], got {transitions.shape}")
        total_steps = transitions.shape[0]
        models: list[BayesianGaussianMixture] = [None] * total_steps  # type: ignore[list-item]
        block_starts = range(0, total_steps, self.shared_block_hours)

        warnings.filterwarnings("ignore", category=UserWarning)
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        warnings.filterwarnings("ignore", category=FutureWarning)

        for block_start in block_starts:
            block_end = min(total_steps, block_start + self.shared_block_hours)
            t_center = block_start + (block_end - block_start - 1) // 2
            structured_idx = self._select_structured_window(
                timestamps,
                pv_day_mask,
                t_center,
                enforce_pv_state=enforce_pv_state,
                use_pv_band=use_pv_band,
            )
            if structured_idx.size >= self.min_structured_window:
                window = transitions[structured_idx]
            else:
                lo = max(0, t_center - self.window_radius)
                hi = min(total_steps, t_center + self.window_radius + 1)
                window = transitions[lo:hi]
            if window.shape[0] < 8:
                reps = int(np.ceil(8 / max(window.shape[0], 1)))
                window = np.vstack([window for _ in range(reps)])[:8]
                rng = np.random.default_rng(self.random_state + block_start)
                window = window + rng.normal(0.0, 1e-5, size=window.shape)

            n_comp = min(self.max_components, max(2, window.shape[0] // 20))
            model = BayesianGaussianMixture(
                n_components=n_comp,
                covariance_type="full",
                weight_concentration_prior_type="dirichlet_process",
                max_iter=self.max_iter,
                reg_covar=self.covariance_reg,
                random_state=self.random_state + block_start,
            )
            model.fit(window)
            for t in range(block_start, block_end):
                models[t] = model

            if block_end % 500 == 0 or block_end == total_steps:
                print(f"  fitted {block_end}/{total_steps} steps using shared {self.shared_block_hours}h blocks")
        return models

    def _component_conditional(
        self,
        mean: np.ndarray,
        cov: np.ndarray,
        x_prev: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray, float]:
        prev_dim = len(x_prev)
        mu_prev = mean[:prev_dim]
        mu_curr = mean[prev_dim:]
        cov_pp = cov[:prev_dim, :prev_dim]
        cov_pc = cov[:prev_dim, prev_dim:]
        cov_cp = cov[prev_dim:, :prev_dim]
        cov_cc = cov[prev_dim:, prev_dim:]

        cov_pp = cov_pp + np.eye(prev_dim) * self.covariance_reg
        cov_cc = cov_cc + np.eye(cov_cc.shape[0]) * self.covariance_reg
        inv_pp = np.linalg.pinv(cov_pp)

        delta = x_prev - mu_prev
        cond_mean = mu_curr + cov_cp @ inv_pp @ delta
        cond_cov = cov_cc - cov_cp @ inv_pp @ cov_pc
        cond_cov = make_psd(cond_cov, self.covariance_reg)

        sign, logdet = np.linalg.slogdet(cov_pp)
        if sign <= 0:
            logdet = np.log(max(np.linalg.det(cov_pp + np.eye(prev_dim) * 1e-6), 1e-12))
        mahal = float(delta.T @ inv_pp @ delta)
        logpdf = -0.5 * (prev_dim * np.log(2 * np.pi) + logdet + mahal)
        return cond_mean, cond_cov, logpdf

    def _sample_one_target(
        self,
        model: BayesianGaussianMixture,
        x_prev: np.ndarray,
        rng: np.random.Generator,
    ) -> float:
        weights = np.asarray(model.weights_, dtype=float)
        means = np.asarray(model.means_, dtype=float)
        covs = np.asarray(model.covariances_, dtype=float)
        comp_means = []
        comp_covs = []
        logw = []
        for k in range(len(weights)):
            cond_mean, cond_cov, logpdf = self._component_conditional(means[k], covs[k], x_prev)
            comp_means.append(cond_mean)
            comp_covs.append(cond_cov)
            logw.append(np.log(max(weights[k], 1e-12)) + logpdf)

        logw_arr = np.asarray(logw, dtype=float)
        logw_arr = logw_arr - np.max(logw_arr)
        post_w = np.exp(logw_arr)
        post_w = post_w / np.sum(post_w)
        k_sel = int(rng.choice(len(post_w), p=post_w))
        sample = rng.multivariate_normal(comp_means[k_sel], comp_covs[k_sel])
        return float(np.clip(sample.reshape(-1)[0], 0.0, 1.0))

    def sample_trajectories(
        self,
        wind_models: list[BayesianGaussianMixture],
        pv_models: list[BayesianGaussianMixture],
        history: np.ndarray,
        n_scenarios: int,
    ) -> np.ndarray:
        total_steps = len(wind_models) + 1
        rng = np.random.default_rng(self.random_state + 777)
        scenarios = np.zeros((n_scenarios, total_steps, 2), dtype=float)

        init_pool = history[: min(len(history), self.window_radius + 1)]
        start_choices = rng.integers(0, len(init_pool), size=n_scenarios)
        scenarios[:, 0, :] = init_pool[start_choices]

        for t, (wind_model, pv_model) in enumerate(zip(wind_models, pv_models), start=1):
            for s in range(n_scenarios):
                x_prev = scenarios[s, t - 1, :]
                scenarios[s, t, 0] = self._sample_one_target(wind_model, x_prev, rng)
                scenarios[s, t, 1] = self._sample_one_target(pv_model, x_prev, rng)
        return scenarios


def reduce_scenarios_kmeans_medoid(
    scenarios: np.ndarray,
    n_typical: int = 10,
    random_state: int = 42,
) -> tuple[np.ndarray, np.ndarray]:
    n_samples, total_steps, dims = scenarios.shape
    n_clusters = min(max(1, int(n_typical)), n_samples)
    flat = scenarios.reshape(n_samples, total_steps * dims)
    mean = flat.mean(axis=0, keepdims=True)
    std = flat.std(axis=0, keepdims=True) + 1e-8
    flat_norm = (flat - mean) / std
    model = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=20)
    labels = model.fit_predict(flat_norm)
    centers = model.cluster_centers_
    medoid_indices: list[int] = []
    probs = np.array([(labels == i).mean() for i in range(n_clusters)], dtype=float)
    probs = probs / probs.sum()
    for i in range(n_clusters):
        members = np.where(labels == i)[0]
        member_flat = flat_norm[members]
        dist = np.linalg.norm(member_flat - centers[i], axis=1)
        medoid_indices.append(int(members[int(np.argmin(dist))]))
    typical = scenarios[np.asarray(medoid_indices, dtype=int)]
    return typical, probs


def weighted_stats(values: np.ndarray, weights: np.ndarray) -> tuple[float, float]:
    mean = float(np.sum(values * weights))
    var = float(np.sum(weights * (values - mean) ** 2))
    return mean, float(np.sqrt(max(var, 0.0)))


def evaluate_scenarios(history: np.ndarray, sampled: np.ndarray, typical: np.ndarray, probs: np.ndarray) -> dict[str, Any]:
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

    hist_wind_ramp = np.diff(history_wind)
    hist_pv_ramp = np.diff(history_pv)
    sampled_wind_ramp = np.diff(sampled[:, :, 0], axis=1).reshape(-1)
    sampled_pv_ramp = np.diff(sampled[:, :, 1], axis=1).reshape(-1)

    return {
        "history": {
            "wind_mean": float(history_wind.mean()),
            "wind_std": float(history_wind.std(ddof=0)),
            "pv_mean": float(history_pv.mean()),
            "pv_std": float(history_pv.std(ddof=0)),
            "wind_pv_corr": hist_corr,
            "wind_ramp_std": float(hist_wind_ramp.std(ddof=0)),
            "pv_ramp_std": float(hist_pv_ramp.std(ddof=0)),
        },
        "sampled": {
            "wind_mean": float(sampled_wind.mean()),
            "wind_std": float(sampled_wind.std(ddof=0)),
            "pv_mean": float(sampled_pv.mean()),
            "pv_std": float(sampled_pv.std(ddof=0)),
            "wind_pv_corr": sample_corr,
            "wind_90pct_coverage": wind_90_cov,
            "pv_90pct_coverage": pv_90_cov,
            "wind_ramp_std": float(sampled_wind_ramp.std(ddof=0)),
            "pv_ramp_std": float(sampled_pv_ramp.std(ddof=0)),
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

    history_df = pd.DataFrame({"timestamp": timestamps.astype(str), "wind": history[:, 0], "pv": history[:, 1]})
    history_df.to_csv(output_dir / "history_series.csv", index=False, encoding="utf-8")

    np.save(output_dir / "sampled_scenarios.npy", sampled)
    np.save(output_dir / "typical_scenarios.npy", typical)

    prob_df = pd.DataFrame({"scenario_id": np.arange(len(probs)), "probability": probs})
    prob_df.to_csv(output_dir / "scenario_probabilities.csv", index=False, encoding="utf-8")

    records: list[dict[str, Any]] = []
    for sid in range(typical.shape[0]):
        for t, ts in enumerate(timestamps):
            records.append(
                {
                    "scenario_id": int(sid),
                    "timestamp": str(ts),
                    "wind": float(typical[sid, t, 0]),
                    "pv": float(typical[sid, t, 1]),
                    "scenario_probability": float(probs[sid]),
                }
            )
    pd.DataFrame.from_records(records).to_csv(output_dir / "typical_scenarios_long.csv", index=False, encoding="utf-8")

    with (output_dir / "uncertainty_report.json").open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)


def run_one_dataset(
    spec: DatasetSpec,
    output_root: Path,
    window_radius: int,
    max_components: int,
    max_iter: int,
    shared_block_hours: int,
    n_sampled_scenarios: int,
    n_typical_scenarios: int,
    seed: int,
    max_steps: int | None,
    covariance_reg: float,
    wind_calibration_shrink: float,
    wind_calibration_mode: str,
    season_day_band: int,
    pv_season_day_band: int,
) -> Path:
    print(f"\n=== Running dataset: {spec.name} ===")
    timestamps, history, metadata = load_wind_pv_series(spec=spec, max_steps=max_steps)
    scaling = build_scaling_spec(history, timestamps)
    history_norm = normalize_history(history, scaling)
    wind_transitions = build_target_transition_tensor(history_norm, target_idx=0)
    pv_transitions = build_target_transition_tensor(history_norm, target_idx=1)

    model = ConditionalRollingDPGMM(
        window_radius=window_radius,
        season_day_band=season_day_band,
        pv_season_day_band=pv_season_day_band,
        hour_band=0,
        min_structured_window=30,
        max_components=max_components,
        max_iter=max_iter,
        shared_block_hours=shared_block_hours,
        random_state=seed,
        covariance_reg=covariance_reg,
    )
    wind_models = model.fit_models(
        wind_transitions,
        timestamps=timestamps,
        pv_day_mask=scaling.pv_day_mask,
        enforce_pv_state=False,
        use_pv_band=False,
    )
    pv_models = model.fit_models(
        pv_transitions,
        timestamps=timestamps,
        pv_day_mask=scaling.pv_day_mask,
        enforce_pv_state=True,
        use_pv_band=True,
    )
    sampled_norm = model.sample_trajectories(
        wind_models=wind_models,
        pv_models=pv_models,
        history=history_norm,
        n_scenarios=n_sampled_scenarios,
    )
    sampled = restore_history(sampled_norm, scaling)
    for t in range(sampled.shape[1]):
        pv_allowed = bool(scaling.pv_day_mask[t])
        for s in range(sampled.shape[0]):
            sampled[s, t, :] = apply_output_constraints(sampled[s, t, :], scaling.upper, pv_allowed)
    if wind_calibration_shrink > 0:
        if wind_calibration_mode == "month_hour":
            sampled = calibrate_wind_by_month_hour(
                sampled,
                history,
                timestamps,
                scaling.upper,
                shrink=wind_calibration_shrink,
            )
        else:
            sampled = calibrate_wind_global(sampled, history, scaling.upper, shrink=wind_calibration_shrink)
    typical, probs = reduce_scenarios_kmeans_medoid(sampled, n_typical=n_typical_scenarios, random_state=seed + 1000)
    metrics = evaluate_scenarios(history=history, sampled=sampled, typical=typical, probs=probs)

    report = {
        "dataset": spec.name,
        "method": "Semi-decoupled structured Conditional Rolling DPGMM + KMeans(nearest-to-centroid representative)",
        "input": {
            "dpgmm_input": str(spec.dpgmm_input),
            "trim_input": str(spec.trim_input),
        },
        "series_metadata": metadata,
        "model_params": {
            "window_radius": int(window_radius),
            "max_components": int(max_components),
            "max_iter": int(max_iter),
            "shared_block_hours": int(shared_block_hours),
            "seed": int(seed),
            "n_sampled_scenarios": int(n_sampled_scenarios),
            "n_typical_scenarios": int(n_typical_scenarios),
            "covariance_reg": float(covariance_reg),
            "transition_dimension": 4,
            "normalization": "per-variable max scaling from historical series",
            "initialization": "sample first hour from first local window",
            "pv_night_rule": "set PV to 0 using month-hour daylight mask derived from historical PV quantiles",
            "representative_scenario_rule": "nearest-to-centroid sampled trajectory",
            "window_selection": "same-hour seasonal window without PV-state restriction for joint wind/PV fitting; contiguous fallback when structured sample size is insufficient",
            "season_day_band": int(season_day_band),
            "pv_season_day_band": int(pv_season_day_band),
            "hour_band": 0,
            "min_structured_window": 30,
            "wind_calibration": wind_calibration_mode if wind_calibration_shrink > 0 else "disabled",
            "wind_calibration_shrink": float(wind_calibration_shrink),
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
        description="Conditional Rolling DPGMM + KMeans wind-PV scenario generation."
    )
    parser.add_argument("--dataset", default="formal2024", help="Dataset label shown in outputs.")
    parser.add_argument("--dpgmm-input", required=True, help="Path to DPGMM wind/PV CSV.")
    parser.add_argument("--trim-input", required=True, help="Path to TRIM/timestamp CSV.")
    parser.add_argument("--output-dir", default="outputs", help="Output directory root.")
    parser.add_argument("--window-radius", type=int, default=24, help="Transition window half-width.")
    parser.add_argument("--max-components", type=int, default=8, help="Maximum number of DPGMM components.")
    parser.add_argument("--max-iter", type=int, default=150, help="Maximum DPGMM iterations.")
    parser.add_argument("--shared-block-hours", type=int, default=1, help="Reuse one fitted DPGMM for each consecutive block of hours.")
    parser.add_argument("--n-sampled-scenarios", type=int, default=200, help="Sampled scenario count.")
    parser.add_argument("--n-typical-scenarios", type=int, default=10, help="Representative scenario count.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument("--covariance-reg", type=float, default=1e-6, help="Covariance regularization.")
    parser.add_argument("--wind-calibration-shrink", type=float, default=0.0, help="Optional global wind moment calibration shrink factor.")
    parser.add_argument("--wind-calibration-mode", choices=["global", "month_hour"], default="global", help="Wind calibration mode.")
    parser.add_argument("--season-day-band", type=int, default=30, help="Day-of-year band for same-hour seasonal structured window.")
    parser.add_argument("--pv-season-day-band", type=int, default=30, help="Day-of-year band for PV structured window.")
    parser.add_argument("--max-steps", type=int, default=None, help="Optional debug truncation.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path.cwd()
    spec = DatasetSpec(
        name=str(args.dataset),
        dpgmm_input=resolve_path(str(args.dpgmm_input), root),
        trim_input=resolve_path(str(args.trim_input), root),
    )
    output_root = resolve_path(str(args.output_dir), root)
    outputs = [
        run_one_dataset(
            spec=spec,
            output_root=output_root,
            window_radius=int(args.window_radius),
            max_components=int(args.max_components),
            max_iter=int(args.max_iter),
            shared_block_hours=int(args.shared_block_hours),
            n_sampled_scenarios=int(args.n_sampled_scenarios),
            n_typical_scenarios=int(args.n_typical_scenarios),
            seed=int(args.seed),
            max_steps=args.max_steps,
            covariance_reg=float(args.covariance_reg),
            wind_calibration_shrink=float(args.wind_calibration_shrink),
            wind_calibration_mode=str(args.wind_calibration_mode),
            season_day_band=int(args.season_day_band),
            pv_season_day_band=int(args.pv_season_day_band),
        )
    ]

    print("\nDone. Generated outputs:")
    for out in outputs:
        print(f" - {out}")


if __name__ == "__main__":
    main()
