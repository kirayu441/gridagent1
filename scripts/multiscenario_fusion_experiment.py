from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import qmc


@dataclass(frozen=True)
class WindPVVariant:
    name: str
    wind_scale: float
    pv_scale: float


@dataclass(frozen=True)
class LoadScenario:
    name: str
    demand_scale: float
    priority_stress_factor: float


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def resolve_path(root: Path, raw: str) -> Path:
    return (root / raw).resolve()


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def sanitize_name(raw: str) -> str:
    return "".join(ch if ch.isalnum() or ch in ("_", "-", ".") else "_" for ch in raw).strip("_")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Multi-scenario fusion experiment preparation (typhoon intensity + wind/pv + load scenarios)."
    )
    parser.add_argument(
        "--config",
        default="configs/multiscenario_fusion.formal2024.json",
        help="Config json path.",
    )
    parser.add_argument(
        "--phase",
        choices=("design",),
        default="design",
        help="Current executable phase. v1 supports design phase.",
    )
    parser.add_argument("--run-tag", default="", help="Optional run tag. If empty, use timestamp.")
    parser.add_argument("--seed", type=int, default=None, help="Optional seed override.")
    parser.add_argument(
        "--no-reuse-existing",
        action="store_true",
        help="Disable reuse and rebuild prepared files.",
    )
    return parser.parse_args()


def ensure_uncertainty_base(base_dir: Path) -> None:
    required = [
        base_dir / "typical_scenarios.npy",
        base_dir / "scenario_probabilities.csv",
        base_dir / "history_series.csv",
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise FileNotFoundError(
            "missing base wind-pv uncertainty artifacts. "
            "run scripts/wind_pv_uncertainty_modeling.py --dataset formal2024 first.\n"
            f"missing files: {missing}"
        )


def prepare_wind_pv_variants(
    base_uncertainty_dir: Path,
    variants: list[WindPVVariant],
    out_root: Path,
    reuse_existing: bool,
) -> pd.DataFrame:
    ensure_uncertainty_base(base_uncertainty_dir)
    out_root.mkdir(parents=True, exist_ok=True)

    typical_base = np.load(base_uncertainty_dir / "typical_scenarios.npy")
    sampled_base = base_uncertainty_dir / "sampled_scenarios.npy"
    sampled = np.load(sampled_base) if sampled_base.exists() else None
    probs_df = pd.read_csv(base_uncertainty_dir / "scenario_probabilities.csv")
    hist_df = pd.read_csv(base_uncertainty_dir / "history_series.csv")
    if "wind" not in hist_df.columns or "pv" not in hist_df.columns:
        raise ValueError(f"history_series missing wind/pv columns: {base_uncertainty_dir / 'history_series.csv'}")

    rows: list[dict[str, Any]] = []
    for v in variants:
        name = sanitize_name(v.name)
        variant_dir = out_root / name
        variant_dir.mkdir(parents=True, exist_ok=True)
        expected = [variant_dir / "typical_scenarios.npy", variant_dir / "scenario_probabilities.csv", variant_dir / "history_series.csv"]
        if reuse_existing and all(p.exists() for p in expected):
            rows.append(
                {
                    "variant": name,
                    "wind_scale": float(v.wind_scale),
                    "pv_scale": float(v.pv_scale),
                    "uncertainty_dir": str(variant_dir),
                }
            )
            continue

        typical = typical_base.copy()
        typical[:, :, 0] = np.clip(typical[:, :, 0] * float(v.wind_scale), 0.0, None)
        typical[:, :, 1] = np.clip(typical[:, :, 1] * float(v.pv_scale), 0.0, None)
        np.save(variant_dir / "typical_scenarios.npy", typical)

        if sampled is not None:
            sampled_scaled = sampled.copy()
            sampled_scaled[:, :, 0] = np.clip(sampled_scaled[:, :, 0] * float(v.wind_scale), 0.0, None)
            sampled_scaled[:, :, 1] = np.clip(sampled_scaled[:, :, 1] * float(v.pv_scale), 0.0, None)
            np.save(variant_dir / "sampled_scenarios.npy", sampled_scaled)

        hist_scaled = hist_df.copy()
        hist_scaled["wind"] = np.clip(hist_scaled["wind"].to_numpy(dtype=float) * float(v.wind_scale), 0.0, None)
        hist_scaled["pv"] = np.clip(hist_scaled["pv"].to_numpy(dtype=float) * float(v.pv_scale), 0.0, None)
        hist_scaled.to_csv(variant_dir / "history_series.csv", index=False, encoding="utf-8")
        probs_df.to_csv(variant_dir / "scenario_probabilities.csv", index=False, encoding="utf-8")

        meta = {
            "base_uncertainty_dir": str(base_uncertainty_dir),
            "variant": name,
            "wind_scale": float(v.wind_scale),
            "pv_scale": float(v.pv_scale),
            "generated_at": datetime.now().isoformat(timespec="seconds"),
        }
        (variant_dir / "variant_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

        rows.append(
            {
                "variant": name,
                "wind_scale": float(v.wind_scale),
                "pv_scale": float(v.pv_scale),
                "uncertainty_dir": str(variant_dir),
            }
        )
    return pd.DataFrame(rows)


def prepare_load_scenarios(
    trim_input: Path,
    load_scenarios: list[LoadScenario],
    out_root: Path,
    reuse_existing: bool,
) -> pd.DataFrame:
    if not trim_input.exists():
        raise FileNotFoundError(f"trim input not found: {trim_input}")
    out_root.mkdir(parents=True, exist_ok=True)

    base_df = pd.read_csv(trim_input)
    load_cols = [c for c in base_df.columns if c.startswith("load_")]
    if not load_cols:
        raise ValueError(f"no load_ columns found in {trim_input}")

    rows: list[dict[str, Any]] = []
    for s in load_scenarios:
        name = sanitize_name(s.name)
        scenario_dir = out_root / name
        scenario_dir.mkdir(parents=True, exist_ok=True)
        trim_out = scenario_dir / "TRIM_input.csv"
        if not (reuse_existing and trim_out.exists()):
            scaled = base_df.copy()
            scaled[load_cols] = np.clip(
                scaled[load_cols].to_numpy(dtype=float) * float(s.demand_scale),
                0.0,
                None,
            )
            scaled.to_csv(trim_out, index=False, encoding="utf-8")
            meta = {
                "base_trim_input": str(trim_input),
                "load_scenario": name,
                "demand_scale": float(s.demand_scale),
                "priority_stress_factor": float(s.priority_stress_factor),
                "generated_at": datetime.now().isoformat(timespec="seconds"),
            }
            (scenario_dir / "scenario_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

        rows.append(
            {
                "load_scenario": name,
                "demand_scale": float(s.demand_scale),
                "priority_stress_factor": float(s.priority_stress_factor),
                "trim_input": str(trim_out),
            }
        )
    return pd.DataFrame(rows)


def sobol_select_indices(
    n_intensity: int,
    n_windpv: int,
    n_load: int,
    n_samples: int,
    seed: int,
) -> list[tuple[int, int, int]]:
    total = n_intensity * n_windpv * n_load
    target = min(max(n_samples, 1), total)
    if target >= total:
        return [(i, j, k) for i in range(n_intensity) for j in range(n_windpv) for k in range(n_load)]

    m_power = int(np.ceil(np.log2(max(target, 2))))
    sampler = qmc.Sobol(d=3, scramble=True, seed=seed)
    draws = sampler.random_base2(m=m_power)
    selected: list[tuple[int, int, int]] = []
    seen: set[tuple[int, int, int]] = set()
    for u in draws:
        i = min(int(np.floor(u[0] * n_intensity)), n_intensity - 1)
        j = min(int(np.floor(u[1] * n_windpv)), n_windpv - 1)
        k = min(int(np.floor(u[2] * n_load)), n_load - 1)
        key = (i, j, k)
        if key in seen:
            continue
        seen.add(key)
        selected.append(key)
        if len(selected) >= target:
            break

    if len(selected) < target:
        rng = np.random.default_rng(seed + 100)
        all_keys = [(i, j, k) for i in range(n_intensity) for j in range(n_windpv) for k in range(n_load)]
        rng.shuffle(all_keys)
        for key in all_keys:
            if key in seen:
                continue
            seen.add(key)
            selected.append(key)
            if len(selected) >= target:
                break
    return selected


def build_environment_matrix(
    intensity_levels: list[float],
    wind_df: pd.DataFrame,
    load_df: pd.DataFrame,
    sampling_mode: str,
    n_samples: int | None,
    seed: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    wind_records = wind_df.to_dict(orient="records")
    load_records = load_df.to_dict(orient="records")
    full_rows: list[dict[str, Any]] = []
    for i, intensity in enumerate(intensity_levels):
        for j, w in enumerate(wind_records):
            for k, l in enumerate(load_records):
                full_rows.append(
                    {
                        "intensity_idx": i,
                        "wind_idx": j,
                        "load_idx": k,
                        "intensity_scale": float(intensity),
                        "wind_variant": str(w["variant"]),
                        "wind_scale": float(w["wind_scale"]),
                        "pv_scale": float(w["pv_scale"]),
                        "uncertainty_dir": str(w["uncertainty_dir"]),
                        "load_scenario": str(l["load_scenario"]),
                        "demand_scale": float(l["demand_scale"]),
                        "priority_stress_factor": float(l["priority_stress_factor"]),
                        "trim_input": str(l["trim_input"]),
                    }
                )
    full_df = pd.DataFrame(full_rows)
    full_df.insert(0, "env_id", [f"ENV_{i + 1:04d}" for i in range(len(full_df))])

    if sampling_mode == "full":
        return full_df, full_df.copy()
    if sampling_mode != "qmc":
        raise ValueError(f"unsupported sampling_mode: {sampling_mode}")
    if n_samples is None or n_samples <= 0:
        raise ValueError("qmc sampling requires positive n_samples")

    idx_keys = sobol_select_indices(
        n_intensity=len(intensity_levels),
        n_windpv=len(wind_records),
        n_load=len(load_records),
        n_samples=n_samples,
        seed=seed,
    )
    key_set = {(i, j, k) for i, j, k in idx_keys}
    sampled_df = full_df[
        full_df.apply(lambda r: (int(r["intensity_idx"]), int(r["wind_idx"]), int(r["load_idx"])) in key_set, axis=1)
    ].copy()
    sampled_df = sampled_df.reset_index(drop=True)
    sampled_df["sample_id"] = [f"S{i + 1:04d}" for i in range(len(sampled_df))]
    return full_df, sampled_df


def build_strategy_pool(
    strategy_cfg: dict[str, Any],
    root: Path,
) -> pd.DataFrame:
    source_csv = resolve_path(root, str(strategy_cfg["source_csv"]))
    top_k = int(strategy_cfg.get("top_k", 6))
    if not source_csv.exists():
        raise FileNotFoundError(f"strategy source csv missing: {source_csv}")

    df = pd.read_csv(source_csv)
    need = {"failure_model", "contingency_method", "reserve_ratio"}
    miss = need - set(df.columns)
    if miss:
        raise ValueError(f"strategy source missing columns: {sorted(miss)}")

    if "TOPSIS_Score" in df.columns:
        df = df.sort_values("TOPSIS_Score", ascending=False)
    elif "TOPSIS_Rank" in df.columns:
        df = df.sort_values("TOPSIS_Rank", ascending=True)

    key_cols = ["failure_model", "contingency_method", "reserve_ratio"]
    unique = df.drop_duplicates(subset=key_cols).reset_index(drop=True)
    pool = unique.head(max(top_k, 1)).copy()
    pool.insert(0, "strategy_id", [f"STR_{i + 1:03d}" for i in range(len(pool))])
    if "run_tag" not in pool.columns:
        pool["run_tag"] = pool.apply(
            lambda r: f"{r['failure_model']}__{r['contingency_method']}__rr{str(r['reserve_ratio']).replace('.', 'p')}",
            axis=1,
        )
    return pool[
        ["strategy_id", "run_tag", "failure_model", "contingency_method", "reserve_ratio"]
    ].copy()


def main() -> None:
    args = parse_args()
    root = project_root()
    config_path = resolve_path(root, args.config)
    if not config_path.exists():
        raise FileNotFoundError(f"config not found: {config_path}")
    config = read_json(config_path)

    reuse_existing = not args.no_reuse_existing
    seed = int(args.seed) if args.seed is not None else int(config.get("seed", 42))
    run_tag = args.run_tag.strip() or datetime.now().strftime("%Y%m%d_%H%M%S")
    output_root = resolve_path(root, str(config.get("output_root", "results/multiscenario_fusion")))
    run_root = output_root / run_tag
    run_root.mkdir(parents=True, exist_ok=True)

    base_inputs = config["base_inputs"]
    base_uncertainty_dir = resolve_path(root, str(base_inputs["wind_pv_uncertainty_dir"]))
    trim_input = resolve_path(root, str(base_inputs["trim_input"]))

    wind_variants = [
        WindPVVariant(
            name=str(v["name"]),
            wind_scale=float(v["wind_scale"]),
            pv_scale=float(v["pv_scale"]),
        )
        for v in config["wind_pv_variants"]
    ]
    load_scenarios = [
        LoadScenario(
            name=str(s["name"]),
            demand_scale=float(s["demand_scale"]),
            priority_stress_factor=float(s.get("priority_stress_factor", 1.0)),
        )
        for s in config["load_scenarios"]
    ]

    prep_root = run_root / "prepared"
    wind_root = prep_root / "wind_pv_variants"
    load_root = prep_root / "load_scenarios"

    wind_df = prepare_wind_pv_variants(
        base_uncertainty_dir=base_uncertainty_dir,
        variants=wind_variants,
        out_root=wind_root,
        reuse_existing=reuse_existing,
    )
    load_df = prepare_load_scenarios(
        trim_input=trim_input,
        load_scenarios=load_scenarios,
        out_root=load_root,
        reuse_existing=reuse_existing,
    )

    sampling_cfg = config.get("env_sampling", {"mode": "full"})
    sampling_mode = str(sampling_cfg.get("mode", "full")).lower()
    n_samples = sampling_cfg.get("n_samples")
    intensity_levels = [float(x) for x in config["typhoon_intensity_levels"]]
    full_env_df, sampled_env_df = build_environment_matrix(
        intensity_levels=intensity_levels,
        wind_df=wind_df,
        load_df=load_df,
        sampling_mode=sampling_mode,
        n_samples=int(n_samples) if n_samples is not None else None,
        seed=seed,
    )

    strategy_pool_df = build_strategy_pool(
        strategy_cfg=config["strategy_pool"],
        root=root,
    )

    full_env_csv = run_root / "env_matrix_full.csv"
    sampled_env_csv = run_root / "env_matrix_sampled.csv"
    wind_csv = run_root / "wind_pv_variants.csv"
    load_csv = run_root / "load_scenarios.csv"
    strategy_csv = run_root / "strategy_pool.csv"

    full_env_df.to_csv(full_env_csv, index=False, encoding="utf-8")
    sampled_env_df.to_csv(sampled_env_csv, index=False, encoding="utf-8")
    wind_df.to_csv(wind_csv, index=False, encoding="utf-8")
    load_df.to_csv(load_csv, index=False, encoding="utf-8")
    strategy_pool_df.to_csv(strategy_csv, index=False, encoding="utf-8")

    manifest = {
        "run_tag": run_tag,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "config_path": str(config_path),
        "run_root": str(run_root),
        "seed": seed,
        "phase": args.phase,
        "inputs": {
            "base_uncertainty_dir": str(base_uncertainty_dir),
            "trim_input": str(trim_input),
            "intensity_levels": intensity_levels,
        },
        "counts": {
            "wind_pv_variants": int(len(wind_df)),
            "load_scenarios": int(len(load_df)),
            "environment_full": int(len(full_env_df)),
            "environment_sampled": int(len(sampled_env_df)),
            "strategy_pool": int(len(strategy_pool_df)),
        },
        "artifacts": {
            "wind_pv_variants_csv": str(wind_csv),
            "load_scenarios_csv": str(load_csv),
            "env_matrix_full_csv": str(full_env_csv),
            "env_matrix_sampled_csv": str(sampled_env_csv),
            "strategy_pool_csv": str(strategy_csv),
        },
        "next_step": {
            "description": "Run edge-stage simulation and warning/scheduling evaluation on sampled environment matrix.",
            "recommended_command": (
                "python scripts/multiscenario_fusion_run.py "
                "--design-manifest "
                f"{str(run_root / 'experiment_manifest.json')}"
            ),
        },
    }
    manifest_path = run_root / "experiment_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print("Done.")
    print(f"run root          -> {run_root}")
    print(f"full env matrix   -> {full_env_csv}")
    print(f"sampled env matrix-> {sampled_env_csv}")
    print(f"strategy pool     -> {strategy_csv}")
    print(f"manifest          -> {manifest_path}")


if __name__ == "__main__":
    main()
