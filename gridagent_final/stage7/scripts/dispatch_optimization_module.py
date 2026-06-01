from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_matrix


@dataclass(frozen=True)
class UCUnit:
    unit_id: str
    bus: int
    pmin: float
    pmax: float
    ramp: float
    gen_cost: float
    reserve_cost: float
    startup_cost: float
    shutdown_cost: float
    initial_on: int = 0
    initial_p: float = 0.0


@dataclass(frozen=True)
class UCLine:
    line_id: str
    from_bus: int
    to_bus: int
    susceptance: float
    fmax_nominal: float
    fmax_effective: float


@dataclass
class UCInputs:
    timestamps: pd.DatetimeIndex
    buses: list[int]
    load_buses: list[int]
    load_levels: dict[int, int]
    priority_weights: dict[int, float]
    voll_weights: dict[int, float]
    units: list[UCUnit]
    lines: list[UCLine]
    base_load_node: np.ndarray  # [T,N]
    base_ren_node: np.ndarray  # [T,N]
    stoch_load_node: np.ndarray  # [S,T,N]
    stoch_ren_node: np.ndarray  # [S,T,N]
    stoch_probs: np.ndarray  # [S]
    robust_load_node: np.ndarray  # [K,T,N]
    robust_ren_node: np.ndarray  # [K,T,N]
    line_risk_map: dict[str, float]


@dataclass
class ModelSolution:
    status: str
    objective: float
    solve_success: bool
    fallback_relaxation: bool
    u: np.ndarray  # [G,T]
    p: np.ndarray  # [G,T]
    r: np.ndarray  # [G,T]
    su: np.ndarray  # [G,T]
    sd: np.ndarray  # [G,T]
    ls: np.ndarray  # [T,Nload]
    generation_cost: float
    reserve_cost: float
    startup_shutdown_cost: float
    load_shed_penalty: float
    extra: dict[str, Any]


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def parse_optional_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        x = float(value)
    except (TypeError, ValueError):
        return None
    if np.isnan(x):
        return None
    return float(x)


def ewm_topsis(matrix: np.ndarray, benefit_flags: list[bool]) -> tuple[np.ndarray, np.ndarray]:
    x = np.array(matrix, dtype=float)
    benefit = np.array(benefit_flags, dtype=bool)

    x_forward = np.zeros_like(x)
    for j in range(x.shape[1]):
        col = x[:, j]
        cmin = float(col.min())
        cmax = float(col.max())
        span = cmax - cmin
        if span < 1e-12:
            x_forward[:, j] = 1.0
        elif benefit[j]:
            x_forward[:, j] = (col - cmin) / span
        else:
            x_forward[:, j] = (cmax - col) / span

    p = x_forward / np.clip(x_forward.sum(axis=0, keepdims=True), 1e-12, None)
    k = 1.0 / np.log(max(x.shape[0], 2))
    safe_p = np.clip(p, 1e-12, 1.0)
    entropy = -k * np.sum(p * np.log(safe_p), axis=0)
    divergence = 1.0 - entropy
    if divergence.sum() <= 1e-12:
        w = np.full(x.shape[1], 1.0 / x.shape[1], dtype=float)
    else:
        w = divergence / divergence.sum()

    r = x_forward / np.clip(np.sqrt((x_forward**2).sum(axis=0, keepdims=True)), 1e-12, None)
    v = r * w
    ideal_best = v.max(axis=0)
    ideal_worst = v.min(axis=0)
    d_plus = np.sqrt(((v - ideal_best) ** 2).sum(axis=1))
    d_minus = np.sqrt(((v - ideal_worst) ** 2).sum(axis=1))
    score = d_minus / np.clip(d_plus + d_minus, 1e-12, None)
    return score, w


def calc_rapidity(hourly_shed_ratio: np.ndarray) -> float:
    ratio = np.clip(np.asarray(hourly_shed_ratio, dtype=float), 0.0, 1.0)
    peak = float(ratio.max(initial=0.0))
    if peak <= 1e-9 or len(ratio) <= 1:
        return 1.0
    peak_idx = int(np.argmax(ratio))
    target = 0.2 * peak
    rec_idx = None
    for i in range(peak_idx, len(ratio)):
        if ratio[i] <= target:
            rec_idx = i
            break
    rec_hours = float(len(ratio) if rec_idx is None else rec_idx - peak_idx)
    tau = max(len(ratio) / 3.0, 1.0)
    return float(np.exp(-rec_hours / tau))


class ConstraintBuilder:
    def __init__(self, n_vars: int) -> None:
        self.n_vars = int(n_vars)
        self.rows: list[int] = []
        self.cols: list[int] = []
        self.data: list[float] = []
        self.lb: list[float] = []
        self.ub: list[float] = []
        self._row = 0

    def add(self, idx: list[int], coef: list[float], lower: float = -np.inf, upper: float = np.inf) -> None:
        if len(idx) != len(coef):
            raise ValueError("idx and coef length mismatch")
        self.rows.extend([self._row] * len(idx))
        self.cols.extend(idx)
        self.data.extend(coef)
        self.lb.append(float(lower))
        self.ub.append(float(upper))
        self._row += 1

    def build(self) -> LinearConstraint:
        a = coo_matrix((self.data, (self.rows, self.cols)), shape=(self._row, self.n_vars)).tocsr()
        return LinearConstraint(a, np.array(self.lb, dtype=float), np.array(self.ub, dtype=float))


def load_grid(grid_path: Path) -> dict[str, Any]:
    if not grid_path.exists():
        raise FileNotFoundError(f"missing grid file: {grid_path}")
    payload = json.loads(grid_path.read_text(encoding="utf-8"))
    if not payload.get("nodes") or not payload.get("lines"):
        raise ValueError(f"invalid grid topology: {grid_path}")
    return payload


def parse_capacity_list(raw: str) -> list[float]:
    out: list[float] = []
    for part in raw.split(","):
        s = part.strip()
        if not s:
            continue
        out.append(float(s))
    return out

def derive_load_priority_map(load_buses: list[int], profile_csv: Path | None) -> tuple[dict[int, int], dict[int, float], dict[int, float]]:
    if profile_csv is not None and profile_csv.exists():
        df = pd.read_csv(profile_csv)
        if {"load_bus", "priority_level", "priority_weight"}.issubset(df.columns):
            level_map: dict[int, int] = {}
            pw_map: dict[int, float] = {}
            for _, row in df.iterrows():
                bus = int(row["load_bus"])
                level = int(row["priority_level"])
                weight = float(row["priority_weight"])
                level_map[bus] = level
                pw_map[bus] = weight
            for b in load_buses:
                if b not in level_map:
                    level_map[b] = 3
                if b not in pw_map:
                    pw_map[b] = 0.2
            voll_map = {b: float(2.0 if level_map[b] == 1 else (1.2 if level_map[b] == 2 else 0.8)) for b in load_buses}
            return level_map, pw_map, voll_map

    sorted_b = sorted(load_buses)
    n = len(sorted_b)
    k1 = max(1, int(np.ceil(0.30 * n)))
    k2 = max(1, int(np.ceil(0.30 * n)))
    set1 = set(sorted_b[:k1])
    set2 = set(sorted_b[k1 : k1 + k2])

    level_map: dict[int, int] = {}
    pw_map: dict[int, float] = {}
    voll_map: dict[int, float] = {}
    for b in sorted_b:
        if b in set1:
            level_map[b] = 1
            pw_map[b] = 1.0
            voll_map[b] = 2.0
        elif b in set2:
            level_map[b] = 2
            pw_map[b] = 0.5
            voll_map[b] = 1.2
        else:
            level_map[b] = 3
            pw_map[b] = 0.2
            voll_map[b] = 0.8
    return level_map, pw_map, voll_map


def load_failure_timestamps(failure_csv: Path) -> pd.DatetimeIndex:
    if not failure_csv.exists():
        raise FileNotFoundError(f"missing failure csv: {failure_csv}")
    df = pd.read_csv(failure_csv)
    if "timestamp" not in df.columns:
        raise ValueError(f"failure csv missing timestamp: {failure_csv}")
    ts = pd.to_datetime(df["timestamp"], errors="coerce")
    if ts.isna().any():
        raise ValueError(f"invalid timestamp in failure csv: {failure_csv}")
    return pd.DatetimeIndex(sorted(ts.unique()))


def load_trim_series(trim_input: Path, target_ts: pd.DatetimeIndex) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if not trim_input.exists():
        raise FileNotFoundError(f"missing trim input: {trim_input}")
    df = pd.read_csv(trim_input)
    if "timestamp" not in df.columns:
        raise ValueError(f"trim input missing timestamp: {trim_input}")
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"]).set_index("timestamp").sort_index()

    load_cols = [c for c in df.columns if c.startswith("load_")]
    if not load_cols:
        raise ValueError("trim input missing load_ columns")

    wind_col = next((c for c in df.columns if "wind" in c.lower() and "electricity" in c.lower()), None)
    pv_col = next((c for c in df.columns if "pv" in c.lower() and "electricity" in c.lower()), None)
    if wind_col is None or pv_col is None:
        raise ValueError("trim input missing wind/pv electricity columns")

    aligned = df.reindex(target_ts).interpolate(method="time").ffill().bfill()
    load_total = aligned[load_cols].sum(axis=1).to_numpy(dtype=float)
    wind_total = np.clip(aligned[wind_col].to_numpy(dtype=float), 0.0, None)
    pv_total = np.clip(aligned[pv_col].to_numpy(dtype=float), 0.0, None)
    return load_total, wind_total, pv_total


def distribute_load_to_buses(load_total: np.ndarray, load_buses: list[int], levels: dict[int, int]) -> tuple[np.ndarray, dict[int, float]]:
    if not load_buses:
        raise ValueError("no load buses")
    weights = np.array([2.2 if levels[b] == 1 else (1.4 if levels[b] == 2 else 1.0) for b in load_buses], dtype=float)
    shares = weights / weights.sum()
    load_bus = load_total[:, None] * shares[None, :]
    share_map = {b: float(s) for b, s in zip(load_buses, shares)}
    return load_bus, share_map


def distribute_renewable_to_buses(
    wind_total: np.ndarray,
    pv_total: np.ndarray,
    buses: list[int],
    generators: list[dict[str, Any]],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    bus_to_idx = {b: i for i, b in enumerate(buses)}
    n = len(buses)

    wind_share = np.zeros(n, dtype=float)
    pv_share = np.zeros(n, dtype=float)

    for g in generators:
        bus = int(g.get("bus", -1))
        if bus not in bus_to_idx:
            continue
        cap = max(parse_optional_float(g.get("capacity")) or 0.0, 0.0)
        gtype = str(g.get("type", "")).lower()
        if gtype == "wind":
            wind_share[bus_to_idx[bus]] += cap
        elif gtype == "pv":
            pv_share[bus_to_idx[bus]] += cap

    if wind_share.sum() <= 1e-12:
        wind_share += 1.0
    if pv_share.sum() <= 1e-12:
        pv_share += 1.0

    wind_share /= wind_share.sum()
    pv_share /= pv_share.sum()

    ren_node = wind_total[:, None] * wind_share[None, :] + pv_total[:, None] * pv_share[None, :]
    return ren_node, wind_share, pv_share


def load_line_risk(line_risk_csv: Path | None) -> dict[str, float]:
    if line_risk_csv is None or not line_risk_csv.exists():
        return {}
    df = pd.read_csv(line_risk_csv)
    if not {"line_id", "risk_prob"}.issubset(df.columns):
        return {}
    return {str(r["line_id"]): float(r["risk_prob"]) for _, r in df.iterrows()}


def build_lines(
    grid: dict[str, Any],
    line_risk_map: dict[str, float],
    line_derate_coeff: float,
    robust_line_factor: float,
    robust: bool,
) -> list[UCLine]:
    out: list[UCLine] = []
    for row in grid.get("lines", []):
        lid = str(row.get("id", ""))
        fb = int(row.get("from", row.get("from_bus")))
        tb = int(row.get("to", row.get("to_bus")))
        length = max(parse_optional_float(row.get("length_km")) or 1.0, 0.05)
        cap = max(parse_optional_float(row.get("capacity")) or 1.0, 0.2)
        x = max(0.06 + 0.02 * length, 0.04)
        b = 1.0 / x
        risk = float(np.clip(line_risk_map.get(lid, 0.0), 0.0, 1.0))
        f_eff = cap * max(0.35, 1.0 - line_derate_coeff * risk)
        if robust:
            f_eff *= float(np.clip(robust_line_factor, 0.5, 1.0))
        out.append(
            UCLine(
                line_id=lid,
                from_bus=fb,
                to_bus=tb,
                susceptance=float(b),
                fmax_nominal=float(cap),
                fmax_effective=float(max(f_eff, 0.1)),
            )
        )
    if not out:
        raise ValueError("no valid lines in grid")
    return out


def build_units(
    grid: dict[str, Any],
    load_buses: list[int],
    slack_dispatchable_capacity: float,
    emergency_caps: list[float],
) -> list[UCUnit]:
    gens = grid.get("generators", [])
    units: list[UCUnit] = []

    for g in gens:
        gtype = str(g.get("type", "")).lower()
        if gtype not in {"thermal", "slack", "ext_grid"}:
            continue
        bus = int(g.get("bus", 0))
        cap = max(parse_optional_float(g.get("capacity")) or 0.0, 0.0)
        if gtype in {"slack", "ext_grid"}:
            cap = max(cap, slack_dispatchable_capacity)
        if cap <= 0:
            cap = slack_dispatchable_capacity

        units.append(
            UCUnit(
                unit_id=str(g.get("id", f"THERM_{bus}")),
                bus=bus,
                pmin=0.10 * cap,
                pmax=cap,
                ramp=max(0.40 * cap, 0.08),
                gen_cost=95.0,
                reserve_cost=24.0,
                startup_cost=22.0 * cap,
                shutdown_cost=10.0 * cap,
                initial_on=1,
                initial_p=0.20 * cap,
            )
        )

    sorted_load = sorted(load_buses) or [0]
    for i, cap in enumerate(emergency_caps):
        c = max(float(cap), 0.0)
        if c <= 0:
            continue
        bus = sorted_load[i % len(sorted_load)]
        units.append(
            UCUnit(
                unit_id=f"EMG_{i+1}",
                bus=bus,
                pmin=0.0,
                pmax=c,
                ramp=max(0.90 * c, 0.05),
                gen_cost=130.0,
                reserve_cost=35.0,
                startup_cost=8.0 * c,
                shutdown_cost=4.0 * c,
                initial_on=1,
                initial_p=0.0,
            )
        )

    if len(units) < 3:
        base_bus = int(grid.get("nodes", [{}])[0].get("id", 0))
        for uid, cap, gc in [("SYN_BASE", 0.55, 85.0), ("SYN_MID", 0.40, 105.0), ("SYN_PEAK", 0.30, 145.0)]:
            units.append(
                UCUnit(
                    unit_id=uid,
                    bus=base_bus,
                    pmin=0.0,
                    pmax=cap,
                    ramp=max(0.45 * cap, 0.08),
                    gen_cost=gc,
                    reserve_cost=30.0,
                    startup_cost=12.0 * cap,
                    shutdown_cost=6.0 * cap,
                    initial_on=1,
                    initial_p=0.0,
                )
            )

    return units


def ensure_capacity_margin(units: list[UCUnit], required_peak: float, bus: int) -> list[UCUnit]:
    total = float(sum(u.pmax for u in units))
    if total >= required_peak:
        return units
    extra = required_peak - total + 0.15
    out = list(units)
    out.append(
        UCUnit(
            unit_id="BOOSTER",
            bus=bus,
            pmin=0.0,
            pmax=extra,
            ramp=max(0.60 * extra, 0.1),
            gen_cost=160.0,
            reserve_cost=42.0,
            startup_cost=14.0 * extra,
            shutdown_cost=7.0 * extra,
            initial_on=1,
            initial_p=0.0,
        )
    )
    return out

def load_uncertainty_scenarios(
    uncertainty_dir: Path,
    target_ts: pd.DatetimeIndex,
    n_scenarios: int,
    seed: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    typical_path = uncertainty_dir / "typical_scenarios.npy"
    prob_path = uncertainty_dir / "scenario_probabilities.csv"
    history_path = uncertainty_dir / "history_series.csv"

    if not typical_path.exists() or not prob_path.exists() or not history_path.exists():
        raise FileNotFoundError(f"missing uncertainty outputs in {uncertainty_dir}")

    typical = np.load(typical_path)  # [K,T,2]
    prob = pd.read_csv(prob_path)["probability"].to_numpy(dtype=float)
    prob = prob / np.clip(prob.sum(), 1e-12, None)

    history = pd.read_csv(history_path)
    history["timestamp"] = pd.to_datetime(history["timestamp"], errors="coerce")
    history = history.dropna(subset=["timestamp"]).set_index("timestamp").sort_index()
    ref_ts = pd.DatetimeIndex(history.index)

    pos = ref_ts.get_indexer(target_ts, method="nearest")
    if np.any(pos < 0):
        raise ValueError("cannot align uncertainty scenarios to target timestamps")
    typical_win = typical[:, pos, :]

    rng = np.random.default_rng(seed)
    k_ids = rng.choice(np.arange(typical_win.shape[0]), size=n_scenarios, replace=True, p=prob)
    sampled = typical_win[k_ids, :, :]  # [S,T,2]
    probs = np.full(n_scenarios, 1.0 / n_scenarios, dtype=float)
    return sampled[:, :, 0], sampled[:, :, 1], probs


def build_stochastic_and_robust_sets(
    base_load_node: np.ndarray,
    wind_share: np.ndarray,
    pv_share: np.ndarray,
    stoch_wind_total: np.ndarray,
    stoch_pv_total: np.ndarray,
    robust_wind_low: float,
    robust_wind_high: float,
    robust_load_low: float,
    robust_load_high: float,
    robust_set_size: int,
    seed: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    t_count, _ = base_load_node.shape

    stoch_ren_node = (
        stoch_wind_total[:, :, None] * wind_share[None, None, :]
        + stoch_pv_total[:, :, None] * pv_share[None, None, :]
    )

    rng = np.random.default_rng(seed)
    load_factor = rng.normal(loc=1.0, scale=0.08, size=(stoch_ren_node.shape[0], t_count))
    load_factor = np.clip(load_factor, 0.85, 1.20)
    stoch_load_node = base_load_node[None, :, :] * load_factor[:, :, None]

    wind_grid = np.linspace(robust_wind_low, robust_wind_high, num=3)
    load_grid = np.linspace(robust_load_low, robust_load_high, num=3)
    candidates: list[tuple[float, float, float, float]] = []
    for wf in wind_grid:
        for pf in wind_grid:
            for lf in load_grid:
                severity = lf - 0.5 * (wf + pf)
                candidates.append((severity, wf, pf, lf))
    candidates = sorted(candidates, key=lambda x: x[0], reverse=True)
    pick = candidates[: max(1, robust_set_size)]

    robust_load_list: list[np.ndarray] = []
    robust_ren_list: list[np.ndarray] = []
    base_wind = stoch_wind_total.mean(axis=0)
    base_pv = stoch_pv_total.mean(axis=0)

    for _, wf, pf, lf in pick:
        ren = (wf * base_wind)[:, None] * wind_share[None, :] + (pf * base_pv)[:, None] * pv_share[None, :]
        load = lf * base_load_node
        robust_ren_list.append(np.clip(ren, 0.0, None))
        robust_load_list.append(np.clip(load, 0.0, None))

    robust_load_node = np.stack(robust_load_list, axis=0)
    robust_ren_node = np.stack(robust_ren_list, axis=0)
    return stoch_load_node, stoch_ren_node, robust_load_node, robust_ren_node


def build_inputs(args: argparse.Namespace) -> UCInputs:
    root = project_root()
    grid_path = (root / args.grid).resolve()
    trim_path = (root / args.trim_input).resolve()
    failure_csv = (root / args.failure_csv).resolve()
    uncertainty_dir = (root / args.uncertainty_dir).resolve()
    line_risk_csv = (root / args.line_risk_csv).resolve() if args.line_risk_csv else None
    priority_csv = (root / args.load_priority_csv).resolve() if args.load_priority_csv else None

    grid = load_grid(grid_path)
    raw_ts = load_failure_timestamps(failure_csv)
    start_idx = int(np.clip(args.horizon_start_index, 0, max(len(raw_ts) - 1, 0)))
    end_idx = min(start_idx + max(args.horizon_hours, 1), len(raw_ts))
    ts = raw_ts[start_idx:end_idx]
    if len(ts) == 0:
        raise ValueError("empty horizon after slicing")

    buses = sorted(int(n["id"]) for n in grid.get("nodes", []) if "id" in n)
    load_buses = sorted(int(n["id"]) for n in grid.get("nodes", []) if str(n.get("type", "")).lower() == "load")
    if not load_buses:
        raise ValueError("grid has no load buses")

    load_levels, priority_weights, voll_weights = derive_load_priority_map(load_buses=load_buses, profile_csv=priority_csv)
    load_total, wind_total, pv_total = load_trim_series(trim_input=trim_path, target_ts=ts)
    load_by_bus, _ = distribute_load_to_buses(load_total=load_total, load_buses=load_buses, levels=load_levels)

    bus_to_idx = {b: i for i, b in enumerate(buses)}
    base_load_node = np.zeros((len(ts), len(buses)), dtype=float)
    for j, b in enumerate(load_buses):
        base_load_node[:, bus_to_idx[b]] = load_by_bus[:, j]

    base_ren_node, wind_share, pv_share = distribute_renewable_to_buses(
        wind_total=wind_total,
        pv_total=pv_total,
        buses=buses,
        generators=grid.get("generators", []),
    )

    stoch_wind_total, stoch_pv_total, stoch_probs = load_uncertainty_scenarios(
        uncertainty_dir=uncertainty_dir,
        target_ts=ts,
        n_scenarios=max(args.stochastic_scenarios, 1),
        seed=args.seed + 10,
    )

    stoch_load_node, stoch_ren_node, robust_load_node, robust_ren_node = build_stochastic_and_robust_sets(
        base_load_node=base_load_node,
        wind_share=wind_share,
        pv_share=pv_share,
        stoch_wind_total=stoch_wind_total,
        stoch_pv_total=stoch_pv_total,
        robust_wind_low=args.robust_wind_low,
        robust_wind_high=args.robust_wind_high,
        robust_load_low=args.robust_load_low,
        robust_load_high=args.robust_load_high,
        robust_set_size=max(args.robust_set_size, 1),
        seed=args.seed + 20,
    )

    line_risk_map = load_line_risk(line_risk_csv)
    lines = build_lines(
        grid=grid,
        line_risk_map=line_risk_map,
        line_derate_coeff=args.line_derate_coeff,
        robust_line_factor=args.robust_line_factor,
        robust=False,
    )

    units = build_units(
        grid=grid,
        load_buses=load_buses,
        slack_dispatchable_capacity=args.slack_dispatchable_capacity,
        emergency_caps=parse_capacity_list(args.emergency_dg_capacities),
    )

    peak_required = float(base_load_node.sum(axis=1).max() * (1.0 + max(args.reserve_ratio, 0.0)))
    units = ensure_capacity_margin(units=units, required_peak=peak_required, bus=buses[0])

    return UCInputs(
        timestamps=ts,
        buses=buses,
        load_buses=load_buses,
        load_levels=load_levels,
        priority_weights=priority_weights,
        voll_weights=voll_weights,
        units=units,
        lines=lines,
        base_load_node=base_load_node,
        base_ren_node=base_ren_node,
        stoch_load_node=stoch_load_node,
        stoch_ren_node=stoch_ren_node,
        stoch_probs=stoch_probs,
        robust_load_node=robust_load_node,
        robust_ren_node=robust_ren_node,
        line_risk_map=line_risk_map,
    )


def _solve_milp(
    c: np.ndarray,
    lb_var: np.ndarray,
    ub_var: np.ndarray,
    integrality: np.ndarray,
    builder: ConstraintBuilder,
    time_limit: float,
    mip_gap: float,
) -> tuple[Any, bool]:
    constraint = builder.build()
    bounds = Bounds(lb_var, ub_var)

    options = {
        "time_limit": float(max(time_limit, 1.0)),
        "mip_rel_gap": float(max(mip_gap, 1e-6)),
        "presolve": True,
        "disp": False,
    }
    res = milp(c=c, constraints=[constraint], integrality=integrality, bounds=bounds, options=options)
    if res.success:
        return res, False

    res_lp = milp(
        c=c,
        constraints=[constraint],
        integrality=np.zeros_like(integrality),
        bounds=bounds,
        options={"time_limit": float(max(time_limit, 1.0)), "presolve": True, "disp": False},
    )
    if res_lp.success:
        return res_lp, True

    raise RuntimeError(f"MILP failed; mip='{res.message}', lp='{res_lp.message}'")


def _core_sets(data: UCInputs) -> tuple[dict[int, list[int]], dict[int, list[int]], dict[int, list[int]], dict[int, int], dict[int, int]]:
    bus_to_idx = {b: i for i, b in enumerate(data.buses)}

    gen_at_bus: dict[int, list[int]] = {i: [] for i in range(len(data.buses))}
    for g, unit in enumerate(data.units):
        gen_at_bus[bus_to_idx[unit.bus]].append(g)

    out_lines: dict[int, list[int]] = {i: [] for i in range(len(data.buses))}
    in_lines: dict[int, list[int]] = {i: [] for i in range(len(data.buses))}
    for l, line in enumerate(data.lines):
        i = bus_to_idx[line.from_bus]
        j = bus_to_idx[line.to_bus]
        out_lines[i].append(l)
        in_lines[j].append(l)

    load_pos = {b: i for i, b in enumerate(data.load_buses)}
    return gen_at_bus, out_lines, in_lines, load_pos, bus_to_idx

def solve_scuc(data: UCInputs, args: argparse.Namespace) -> ModelSolution:
    g_count = len(data.units)
    t_count = len(data.timestamps)
    n_bus = len(data.buses)
    l_count = len(data.lines)
    n_load = len(data.load_buses)

    offset = 0
    u_idx = np.arange(offset, offset + g_count * t_count).reshape(g_count, t_count)
    offset += g_count * t_count
    p_idx = np.arange(offset, offset + g_count * t_count).reshape(g_count, t_count)
    offset += g_count * t_count
    r_idx = np.arange(offset, offset + g_count * t_count).reshape(g_count, t_count)
    offset += g_count * t_count
    su_idx = np.arange(offset, offset + g_count * t_count).reshape(g_count, t_count)
    offset += g_count * t_count
    sd_idx = np.arange(offset, offset + g_count * t_count).reshape(g_count, t_count)
    offset += g_count * t_count
    th_idx = np.arange(offset, offset + n_bus * t_count).reshape(n_bus, t_count)
    offset += n_bus * t_count
    f_idx = np.arange(offset, offset + l_count * t_count).reshape(l_count, t_count)
    offset += l_count * t_count
    ls_idx = np.arange(offset, offset + n_load * t_count).reshape(n_load, t_count)
    offset += n_load * t_count
    n_var = offset

    c = np.zeros(n_var, dtype=float)
    lb = np.full(n_var, 0.0, dtype=float)
    ub = np.full(n_var, np.inf, dtype=float)
    integrality = np.zeros(n_var, dtype=int)

    for g, unit in enumerate(data.units):
        for t in range(t_count):
            integrality[u_idx[g, t]] = 1
            ub[u_idx[g, t]] = 1.0
            c[p_idx[g, t]] = unit.gen_cost
            c[r_idx[g, t]] = unit.reserve_cost
            c[su_idx[g, t]] = unit.startup_cost
            c[sd_idx[g, t]] = unit.shutdown_cost
            ub[p_idx[g, t]] = unit.pmax
            ub[r_idx[g, t]] = unit.pmax

    for n in range(n_bus):
        for t in range(t_count):
            lb[th_idx[n, t]] = -np.pi
            ub[th_idx[n, t]] = np.pi

    for l, line in enumerate(data.lines):
        for t in range(t_count):
            lb[f_idx[l, t]] = -line.fmax_effective
            ub[f_idx[l, t]] = line.fmax_effective

    bus_to_col = {b: i for i, b in enumerate(data.buses)}
    for j, bus in enumerate(data.load_buses):
        for t in range(t_count):
            c[ls_idx[j, t]] = args.voll * data.voll_weights[bus]
            ub[ls_idx[j, t]] = data.base_load_node[t, bus_to_col[bus]]

    builder = ConstraintBuilder(n_var)
    gen_at_bus, out_lines, in_lines, load_pos, bus_to_idx = _core_sets(data)

    for g, unit in enumerate(data.units):
        for t in range(t_count):
            builder.add([p_idx[g, t], u_idx[g, t]], [1.0, -unit.pmax], upper=0.0)
            builder.add([p_idx[g, t], u_idx[g, t]], [-1.0, unit.pmin], upper=0.0)
            builder.add([p_idx[g, t], r_idx[g, t], u_idx[g, t]], [1.0, 1.0, -unit.pmax], upper=0.0)

            if t == 0:
                uprev = float(unit.initial_on)
                pprev = float(unit.initial_p)
                builder.add([u_idx[g, t], su_idx[g, t]], [1.0, -1.0], upper=uprev)
                builder.add([u_idx[g, t], sd_idx[g, t]], [-1.0, -1.0], upper=-uprev)
                builder.add([p_idx[g, t]], [1.0], upper=pprev + unit.ramp)
                builder.add([p_idx[g, t]], [-1.0], upper=unit.ramp - pprev)
            else:
                builder.add([u_idx[g, t], u_idx[g, t - 1], su_idx[g, t]], [1.0, -1.0, -1.0], upper=0.0)
                builder.add([u_idx[g, t], u_idx[g, t - 1], sd_idx[g, t]], [-1.0, 1.0, -1.0], upper=0.0)
                builder.add([p_idx[g, t], p_idx[g, t - 1]], [1.0, -1.0], upper=unit.ramp)
                builder.add([p_idx[g, t], p_idx[g, t - 1]], [-1.0, 1.0], upper=unit.ramp)

    total_load_t = data.base_load_node.sum(axis=1)
    for t in range(t_count):
        builder.add([int(r_idx[g, t]) for g in range(g_count)], [-1.0] * g_count, upper=-args.reserve_ratio * float(total_load_t[t]))

    ref_bus = 0
    for t in range(t_count):
        builder.add([int(th_idx[ref_bus, t])], [1.0], lower=0.0, upper=0.0)

        for l, line in enumerate(data.lines):
            i = bus_to_idx[line.from_bus]
            j = bus_to_idx[line.to_bus]
            builder.add(
                [int(f_idx[l, t]), int(th_idx[i, t]), int(th_idx[j, t])],
                [1.0, -line.susceptance, line.susceptance],
                lower=0.0,
                upper=0.0,
            )

        for n, bus in enumerate(data.buses):
            idx: list[int] = []
            coef: list[float] = []
            for g in gen_at_bus[n]:
                idx.append(int(p_idx[g, t]))
                coef.append(1.0)
            lp = load_pos.get(bus)
            if lp is not None:
                idx.append(int(ls_idx[lp, t]))
                coef.append(1.0)
            for l in out_lines[n]:
                idx.append(int(f_idx[l, t]))
                coef.append(-1.0)
            for l in in_lines[n]:
                idx.append(int(f_idx[l, t]))
                coef.append(1.0)
            rhs = float(data.base_load_node[t, n] - data.base_ren_node[t, n])
            builder.add(idx, coef, lower=rhs, upper=rhs)

    res, fallback = _solve_milp(
        c=c,
        lb_var=lb,
        ub_var=ub,
        integrality=integrality,
        builder=builder,
        time_limit=args.time_limit_sec,
        mip_gap=args.mip_gap,
    )

    x = np.asarray(res.x, dtype=float)
    u = x[u_idx].reshape(g_count, t_count)
    p = x[p_idx].reshape(g_count, t_count)
    r = x[r_idx].reshape(g_count, t_count)
    su = x[su_idx].reshape(g_count, t_count)
    sd = x[sd_idx].reshape(g_count, t_count)
    ls = x[ls_idx].reshape(n_load, t_count).T
    f = x[f_idx].reshape(l_count, t_count).T

    generation_cost = float(sum(data.units[g].gen_cost * p[g, t] for g in range(g_count) for t in range(t_count)))
    reserve_cost = float(sum(data.units[g].reserve_cost * r[g, t] for g in range(g_count) for t in range(t_count)))
    startup_shutdown = float(sum(data.units[g].startup_cost * su[g, t] + data.units[g].shutdown_cost * sd[g, t] for g in range(g_count) for t in range(t_count)))
    ls_penalty = float(sum(args.voll * data.voll_weights[b] * ls[:, j].sum() for j, b in enumerate(data.load_buses)))

    return ModelSolution(
        status=str(res.status),
        objective=float(res.fun),
        solve_success=bool(res.success),
        fallback_relaxation=fallback,
        u=u,
        p=p,
        r=r,
        su=su,
        sd=sd,
        ls=ls,
        generation_cost=generation_cost,
        reserve_cost=reserve_cost,
        startup_shutdown_cost=startup_shutdown,
        load_shed_penalty=ls_penalty,
        extra={
            "line_flow": f,
            "line_limits": np.tile(np.array([line.fmax_effective for line in data.lines], dtype=float), (t_count, 1)),
        },
    )


def _add_base_commitment_constraints(
    builder: ConstraintBuilder,
    data: UCInputs,
    args: argparse.Namespace,
    u_idx: np.ndarray,
    p0_idx: np.ndarray,
    r_idx: np.ndarray,
    su_idx: np.ndarray,
    sd_idx: np.ndarray,
) -> None:
    g_count, t_count = u_idx.shape

    for g, unit in enumerate(data.units):
        for t in range(t_count):
            builder.add([p0_idx[g, t], u_idx[g, t]], [1.0, -unit.pmax], upper=0.0)
            builder.add([p0_idx[g, t], u_idx[g, t]], [-1.0, unit.pmin], upper=0.0)
            builder.add([p0_idx[g, t], r_idx[g, t], u_idx[g, t]], [1.0, 1.0, -unit.pmax], upper=0.0)

            if t == 0:
                builder.add([u_idx[g, t], su_idx[g, t]], [1.0, -1.0], upper=float(unit.initial_on))
                builder.add([u_idx[g, t], sd_idx[g, t]], [-1.0, -1.0], upper=-float(unit.initial_on))
                builder.add([p0_idx[g, t]], [1.0], upper=float(unit.initial_p + unit.ramp))
                builder.add([p0_idx[g, t]], [-1.0], upper=float(unit.ramp - unit.initial_p))
            else:
                builder.add([u_idx[g, t], u_idx[g, t - 1], su_idx[g, t]], [1.0, -1.0, -1.0], upper=0.0)
                builder.add([u_idx[g, t], u_idx[g, t - 1], sd_idx[g, t]], [-1.0, 1.0, -1.0], upper=0.0)
                builder.add([p0_idx[g, t], p0_idx[g, t - 1]], [1.0, -1.0], upper=unit.ramp)
                builder.add([p0_idx[g, t], p0_idx[g, t - 1]], [-1.0, 1.0], upper=unit.ramp)

    total_load_t = data.base_load_node.sum(axis=1)
    for t in range(t_count):
        builder.add([int(r_idx[g, t]) for g in range(g_count)], [-1.0] * g_count, upper=-args.reserve_ratio * float(total_load_t[t]))

def solve_stochastic_uc(data: UCInputs, args: argparse.Namespace) -> ModelSolution:
    g_count = len(data.units)
    t_count = len(data.timestamps)
    n_bus = len(data.buses)
    l_count = len(data.lines)
    n_load = len(data.load_buses)
    s_count = data.stoch_load_node.shape[0]

    offset = 0
    u_idx = np.arange(offset, offset + g_count * t_count).reshape(g_count, t_count); offset += g_count * t_count
    p0_idx = np.arange(offset, offset + g_count * t_count).reshape(g_count, t_count); offset += g_count * t_count
    r_idx = np.arange(offset, offset + g_count * t_count).reshape(g_count, t_count); offset += g_count * t_count
    su_idx = np.arange(offset, offset + g_count * t_count).reshape(g_count, t_count); offset += g_count * t_count
    sd_idx = np.arange(offset, offset + g_count * t_count).reshape(g_count, t_count); offset += g_count * t_count

    p_idx = np.arange(offset, offset + s_count * g_count * t_count).reshape(s_count, g_count, t_count); offset += s_count * g_count * t_count
    th_idx = np.arange(offset, offset + s_count * n_bus * t_count).reshape(s_count, n_bus, t_count); offset += s_count * n_bus * t_count
    f_idx = np.arange(offset, offset + s_count * l_count * t_count).reshape(s_count, l_count, t_count); offset += s_count * l_count * t_count
    ls_idx = np.arange(offset, offset + s_count * n_load * t_count).reshape(s_count, n_load, t_count); offset += s_count * n_load * t_count
    dp_idx = np.arange(offset, offset + s_count * g_count * t_count).reshape(s_count, g_count, t_count); offset += s_count * g_count * t_count
    dm_idx = np.arange(offset, offset + s_count * g_count * t_count).reshape(s_count, g_count, t_count); offset += s_count * g_count * t_count
    n_var = offset

    c = np.zeros(n_var, dtype=float)
    lb = np.full(n_var, 0.0, dtype=float)
    ub = np.full(n_var, np.inf, dtype=float)
    integrality = np.zeros(n_var, dtype=int)

    for g, unit in enumerate(data.units):
        for t in range(t_count):
            integrality[u_idx[g, t]] = 1
            ub[u_idx[g, t]] = 1.0
            c[p0_idx[g, t]] = 0.25 * unit.gen_cost
            c[r_idx[g, t]] = unit.reserve_cost
            c[su_idx[g, t]] = unit.startup_cost
            c[sd_idx[g, t]] = unit.shutdown_cost
            ub[p0_idx[g, t]] = unit.pmax
            ub[r_idx[g, t]] = unit.pmax

    bus_to_col = {b: i for i, b in enumerate(data.buses)}
    for s in range(s_count):
        ps = float(data.stoch_probs[s])
        for g, unit in enumerate(data.units):
            for t in range(t_count):
                c[p_idx[s, g, t]] = ps * unit.gen_cost
                c[dp_idx[s, g, t]] = ps * args.redispatch_penalty
                c[dm_idx[s, g, t]] = ps * args.redispatch_penalty
                ub[p_idx[s, g, t]] = unit.pmax
        for n in range(n_bus):
            for t in range(t_count):
                lb[th_idx[s, n, t]] = -np.pi
                ub[th_idx[s, n, t]] = np.pi
        for l, line in enumerate(data.lines):
            for t in range(t_count):
                lb[f_idx[s, l, t]] = -line.fmax_effective
                ub[f_idx[s, l, t]] = line.fmax_effective
        for j, bus in enumerate(data.load_buses):
            for t in range(t_count):
                c[ls_idx[s, j, t]] = ps * args.voll * data.voll_weights[bus]
                ub[ls_idx[s, j, t]] = data.stoch_load_node[s, t, bus_to_col[bus]]

    builder = ConstraintBuilder(n_var)
    gen_at_bus, out_lines, in_lines, load_pos, bus_to_idx = _core_sets(data)
    _add_base_commitment_constraints(builder, data, args, u_idx, p0_idx, r_idx, su_idx, sd_idx)

    for s in range(s_count):
        for g, unit in enumerate(data.units):
            for t in range(t_count):
                builder.add([p_idx[s, g, t], u_idx[g, t]], [1.0, -unit.pmax], upper=0.0)
                builder.add([p_idx[s, g, t], u_idx[g, t]], [-1.0, unit.pmin], upper=0.0)
                builder.add([p_idx[s, g, t], p0_idx[g, t], dp_idx[s, g, t], dm_idx[s, g, t]], [1.0, -1.0, -1.0, 1.0], lower=0.0, upper=0.0)
                builder.add([dp_idx[s, g, t], dm_idx[s, g, t], r_idx[g, t]], [1.0, 1.0, -1.0], upper=0.0)
                if t == 0:
                    builder.add([p_idx[s, g, t]], [1.0], upper=float(unit.initial_p + unit.ramp))
                    builder.add([p_idx[s, g, t]], [-1.0], upper=float(unit.ramp - unit.initial_p))
                else:
                    builder.add([p_idx[s, g, t], p_idx[s, g, t - 1]], [1.0, -1.0], upper=unit.ramp)
                    builder.add([p_idx[s, g, t], p_idx[s, g, t - 1]], [-1.0, 1.0], upper=unit.ramp)

        for t in range(t_count):
            builder.add([int(th_idx[s, 0, t])], [1.0], lower=0.0, upper=0.0)
            for l, line in enumerate(data.lines):
                i = bus_to_idx[line.from_bus]
                j = bus_to_idx[line.to_bus]
                builder.add([int(f_idx[s, l, t]), int(th_idx[s, i, t]), int(th_idx[s, j, t])], [1.0, -line.susceptance, line.susceptance], lower=0.0, upper=0.0)
            for n, bus in enumerate(data.buses):
                idx: list[int] = []
                coef: list[float] = []
                for g in gen_at_bus[n]:
                    idx.append(int(p_idx[s, g, t])); coef.append(1.0)
                lp = load_pos.get(bus)
                if lp is not None:
                    idx.append(int(ls_idx[s, lp, t])); coef.append(1.0)
                for l in out_lines[n]:
                    idx.append(int(f_idx[s, l, t])); coef.append(-1.0)
                for l in in_lines[n]:
                    idx.append(int(f_idx[s, l, t])); coef.append(1.0)
                rhs = float(data.stoch_load_node[s, t, n] - data.stoch_ren_node[s, t, n])
                builder.add(idx, coef, lower=rhs, upper=rhs)

    res, fallback = _solve_milp(c, lb, ub, integrality, builder, args.time_limit_sec, args.mip_gap)
    x = np.asarray(res.x, dtype=float)

    u = x[u_idx].reshape(g_count, t_count)
    p0 = x[p0_idx].reshape(g_count, t_count)
    r = x[r_idx].reshape(g_count, t_count)
    su = x[su_idx].reshape(g_count, t_count)
    sd = x[sd_idx].reshape(g_count, t_count)
    ls_s = x[ls_idx].reshape(s_count, n_load, t_count).transpose(0, 2, 1)
    p_s = x[p_idx].reshape(s_count, g_count, t_count)
    f_s = x[f_idx].reshape(s_count, l_count, t_count).transpose(0, 2, 1)
    dp_s = x[dp_idx].reshape(s_count, g_count, t_count)
    dm_s = x[dm_idx].reshape(s_count, g_count, t_count)

    generation_cost = 0.0
    reserve_cost = float(sum(data.units[g].reserve_cost * r[g].sum() for g in range(g_count)))
    startup_shutdown = float(sum(data.units[g].startup_cost * su[g].sum() + data.units[g].shutdown_cost * sd[g].sum() for g in range(g_count)))
    ls_penalty = 0.0
    for g, unit in enumerate(data.units):
        generation_cost += float(0.25 * unit.gen_cost * p0[g].sum())
    for s in range(s_count):
        ps = float(data.stoch_probs[s])
        for g, unit in enumerate(data.units):
            generation_cost += float(ps * unit.gen_cost * p_s[s, g].sum())
            generation_cost += float(ps * args.redispatch_penalty * (dp_s[s, g].sum() + dm_s[s, g].sum()))
        for j, bus in enumerate(data.load_buses):
            ls_penalty += float(ps * args.voll * data.voll_weights[bus] * ls_s[s, :, j].sum())

    ls_expected = np.tensordot(data.stoch_probs, ls_s, axes=(0, 0))
    f_expected = np.tensordot(data.stoch_probs, f_s, axes=(0, 0))

    return ModelSolution(
        status=str(res.status),
        objective=float(res.fun),
        solve_success=bool(res.success),
        fallback_relaxation=fallback,
        u=u,
        p=p0,
        r=r,
        su=su,
        sd=sd,
        ls=ls_expected,
        generation_cost=float(generation_cost),
        reserve_cost=float(reserve_cost),
        startup_shutdown_cost=float(startup_shutdown),
        load_shed_penalty=float(ls_penalty),
        extra={
            "ls_scenarios": ls_s,
            "scenario_probs": data.stoch_probs,
            "p_scenarios": p_s,
            "line_flow_scenarios": f_s,
            "line_flow_expected": f_expected,
            "line_limits": np.tile(np.array([line.fmax_effective for line in data.lines], dtype=float), (t_count, 1)),
        },
    )


def solve_robust_uc(data: UCInputs, args: argparse.Namespace) -> ModelSolution:
    # Robust UC solved by reusing stochastic template on a worst-case scenario subset.
    robust_data = UCInputs(
        timestamps=data.timestamps,
        buses=data.buses,
        load_buses=data.load_buses,
        load_levels=data.load_levels,
        priority_weights=data.priority_weights,
        voll_weights=data.voll_weights,
        units=data.units,
        lines=build_lines(
            grid={"lines": [{"id": l.line_id, "from": l.from_bus, "to": l.to_bus, "length_km": 1.0, "capacity": l.fmax_nominal} for l in data.lines]},
            line_risk_map=data.line_risk_map,
            line_derate_coeff=args.line_derate_coeff,
            robust_line_factor=args.robust_line_factor,
            robust=True,
        ),
        base_load_node=data.base_load_node,
        base_ren_node=data.base_ren_node,
        stoch_load_node=data.robust_load_node,
        stoch_ren_node=data.robust_ren_node,
        stoch_probs=np.full(data.robust_load_node.shape[0], 1.0 / data.robust_load_node.shape[0]),
        robust_load_node=data.robust_load_node,
        robust_ren_node=data.robust_ren_node,
        line_risk_map=data.line_risk_map,
    )

    # First solve as scenario-average, then pick worst scenario with max operating penalty and override LS profile.
    avg_sol = solve_stochastic_uc(robust_data, args)
    ls_s = avg_sol.extra["ls_scenarios"]
    scenario_costs = np.zeros(ls_s.shape[0], dtype=float)
    for s in range(ls_s.shape[0]):
        ls_cost = sum(args.voll * robust_data.voll_weights[b] * ls_s[s, :, j].sum() for j, b in enumerate(robust_data.load_buses))
        scenario_costs[s] = float(ls_cost)
    worst = int(np.argmax(scenario_costs))

    robust_ls = ls_s[worst]
    f_s = np.asarray(avg_sol.extra.get("line_flow_scenarios"), dtype=float)
    if f_s.ndim == 3 and f_s.shape[0] > worst:
        robust_f = f_s[worst]
    else:
        robust_f = np.asarray(avg_sol.extra.get("line_flow_expected"), dtype=float)
    if robust_f.ndim != 2:
        robust_f = np.zeros((len(data.timestamps), len(data.lines)), dtype=float)
    robust_limits = np.asarray(avg_sol.extra.get("line_limits"), dtype=float)
    if robust_limits.shape != robust_f.shape:
        robust_limits = np.tile(np.array([line.fmax_effective for line in robust_data.lines], dtype=float), (len(data.timestamps), 1))

    return ModelSolution(
        status=avg_sol.status,
        objective=float(avg_sol.objective + scenario_costs[worst]),
        solve_success=avg_sol.solve_success,
        fallback_relaxation=avg_sol.fallback_relaxation,
        u=avg_sol.u,
        p=avg_sol.p,
        r=avg_sol.r,
        su=avg_sol.su,
        sd=avg_sol.sd,
        ls=robust_ls,
        generation_cost=avg_sol.generation_cost,
        reserve_cost=avg_sol.reserve_cost,
        startup_shutdown_cost=avg_sol.startup_shutdown_cost,
        load_shed_penalty=float(scenario_costs[worst]),
        extra={
            "scenario_costs": scenario_costs,
            "worst_scenario_index": worst,
            "ls_scenarios": ls_s,
            "line_flow_scenarios": f_s,
            "line_flow_worst": robust_f,
            "line_limits_worst": robust_limits,
        },
    )

def _extract_line_flow_and_limits(data: UCInputs, sol: ModelSolution) -> tuple[np.ndarray, np.ndarray]:
    t_count = len(data.timestamps)
    l_count = len(data.lines)
    default_limits = np.tile(np.array([line.fmax_effective for line in data.lines], dtype=float), (t_count, 1))

    if sol.extra.get("line_flow") is not None:
        flow = _extract_matrix(sol, "line_flow", t_count, l_count, fallback=np.zeros((t_count, l_count), dtype=float))
    elif sol.extra.get("line_flow_expected") is not None:
        flow = _extract_matrix(sol, "line_flow_expected", t_count, l_count, fallback=np.zeros((t_count, l_count), dtype=float))
    elif sol.extra.get("line_flow_worst") is not None:
        flow = _extract_matrix(sol, "line_flow_worst", t_count, l_count, fallback=np.zeros((t_count, l_count), dtype=float))
    else:
        flow = np.zeros((t_count, l_count), dtype=float)

    if sol.extra.get("line_limits") is not None:
        limits = _extract_matrix(sol, "line_limits", t_count, l_count, fallback=default_limits)
    elif sol.extra.get("line_limits_worst") is not None:
        limits = _extract_matrix(sol, "line_limits_worst", t_count, l_count, fallback=default_limits)
    else:
        limits = default_limits

    return flow, limits


def compute_metrics(data: UCInputs, sol: ModelSolution, model_name: str, runtime_sec: float | None = None) -> dict[str, Any]:
    t_count = len(data.timestamps)
    n_load = len(data.load_buses)

    demand_load = np.zeros((t_count, n_load), dtype=float)
    bus_to_idx = {b: i for i, b in enumerate(data.buses)}
    for j, bus in enumerate(data.load_buses):
        demand_load[:, j] = data.base_load_node[:, bus_to_idx[bus]]

    served = np.clip(demand_load - sol.ls, 0.0, None)
    total_demand = float(demand_load.sum())
    total_shed = float(sol.ls.sum())

    w = np.array([data.priority_weights[b] for b in data.load_buses], dtype=float)
    weighted_served = float((served * w[None, :]).sum())
    weighted_demand = float((demand_load * w[None, :]).sum())

    primary_idx = [j for j, bus in enumerate(data.load_buses) if int(data.load_levels.get(bus, 3)) == 1]
    if not primary_idx:
        primary_idx = list(range(n_load))
    primary_demand = float(demand_load[:, primary_idx].sum())
    primary_served = float(served[:, primary_idx].sum())
    primary_supply_rate = float(primary_served / max(primary_demand, 1e-12))

    priority_index = float(weighted_served / max(weighted_demand, 1e-12))
    reliability_score = float(1.0 - total_shed / max(total_demand, 1e-12))
    robustness = reliability_score
    shed_ratio_t = np.divide(sol.ls.sum(axis=1), np.clip(demand_load.sum(axis=1), 1e-12, None))
    rapidity = calc_rapidity(shed_ratio_t)
    sustainability = float(np.clip(1.0 - shed_ratio_t.mean(), 0.0, 1.0))

    flow, limits = _extract_line_flow_and_limits(data=data, sol=sol)
    safe_limits = np.clip(np.abs(limits), 1e-9, None)
    loading = np.abs(flow) / safe_limits
    overload_flag = np.abs(flow) > (np.abs(limits) + 1e-9)
    overload_count = int(overload_flag.sum())
    max_line_loading = float(loading.max(initial=0.0))

    return {
        "model": model_name,
        "total_cost": float(sol.objective),
        "generation_cost": float(sol.generation_cost),
        "reserve_cost": float(sol.reserve_cost),
        "startup_shutdown_cost": float(sol.startup_shutdown_cost),
        "load_shedding_penalty": float(sol.load_shed_penalty),
        "EENS": float(total_shed),
        "critical_load_supply_rate": primary_supply_rate,
        "priority_index": priority_index,
        "robustness": robustness,
        "rapidity": rapidity,
        "sustainability": sustainability,
        "reliability_score": reliability_score,
        "overload_count": overload_count,
        "max_line_loading": max_line_loading,
        "total_demand": total_demand,
        "solve_success": bool(sol.solve_success),
        "fallback_relaxation": bool(sol.fallback_relaxation),
        "solver_status": sol.status,
        "runtime_sec": float(runtime_sec) if runtime_sec is not None else np.nan,
    }


def load_warning_context(line_risk_csv: Path | None) -> dict[str, float]:
    ctx = {
        "max_line_risk_prob": 0.0,
        "high_line_ratio": 0.0,
        "expected_nk_fail_lines": 0.0,
        "max_critical_outage_prob": 0.0,
    }
    if line_risk_csv is None or not line_risk_csv.exists():
        return ctx

    line_df = pd.read_csv(line_risk_csv)
    if {"risk_prob", "risk_level"}.issubset(line_df.columns):
        risk_prob = line_df["risk_prob"].to_numpy(dtype=float)
        ctx["max_line_risk_prob"] = float(np.clip(risk_prob.max(initial=0.0), 0.0, 1.0))
        high_ratio = float((line_df["risk_level"].astype(str) == "HIGH").mean())
        ctx["high_line_ratio"] = float(np.clip(high_ratio, 0.0, 1.0))

    nk_csv = line_risk_csv.with_name("nk_failure_risk.csv")
    if nk_csv.exists():
        nk_df = pd.read_csv(nk_csv)
        if {"expected_fail_lines", "probability"}.issubset(nk_df.columns):
            exp_nk = float((nk_df["expected_fail_lines"].to_numpy(dtype=float) * nk_df["probability"].to_numpy(dtype=float)).sum())
            ctx["expected_nk_fail_lines"] = max(exp_nk, 0.0)

    critical_csv = line_risk_csv.with_name("critical_load_risk.csv")
    if critical_csv.exists():
        c_df = pd.read_csv(critical_csv)
        if "outage_prob" in c_df.columns:
            ctx["max_critical_outage_prob"] = float(np.clip(c_df["outage_prob"].to_numpy(dtype=float).max(initial=0.0), 0.0, 1.0))

    return ctx


def load_hourly_line_risk(failure_csv: Path, target_ts: pd.DatetimeIndex) -> np.ndarray:
    df = pd.read_csv(failure_csv)
    if not {"timestamp", "p_line"}.issubset(df.columns):
        return np.zeros(len(target_ts), dtype=float)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"])
    if df.empty:
        return np.zeros(len(target_ts), dtype=float)
    hourly = df.groupby("timestamp", as_index=True)["p_line"].max().sort_index()
    aligned = hourly.reindex(target_ts).interpolate(method="time").ffill().bfill()
    return np.clip(aligned.to_numpy(dtype=float), 0.0, 1.0)


def compute_hourly_uncertainty(data: UCInputs) -> np.ndarray:
    net = data.stoch_load_node.sum(axis=2) - data.stoch_ren_node.sum(axis=2)  # [S,T]
    mu = net.mean(axis=0)
    sigma = net.std(axis=0)
    cv = sigma / np.clip(np.abs(mu), 1e-6, None)
    return np.clip(cv, 0.0, 2.0)


def route_strategy_by_context(
    timestamps: pd.DatetimeIndex,
    hourly_line_risk: np.ndarray,
    hourly_uncertainty: np.ndarray,
    warning_ctx: dict[str, float],
    args: argparse.Namespace,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    global_extreme = (
        warning_ctx["expected_nk_fail_lines"] >= args.robust_nk_threshold
        or warning_ctx["max_critical_outage_prob"] >= args.robust_critical_threshold
        or warning_ctx["high_line_ratio"] >= args.robust_high_line_ratio_threshold
    )

    for t, ts in enumerate(timestamps):
        line_risk_t = float(hourly_line_risk[t])
        unc_t = float(hourly_uncertainty[t])

        if line_risk_t >= args.robust_line_risk_threshold or (
            global_extreme and line_risk_t >= args.stochastic_line_risk_threshold
        ):
            strategy = "Robust_UC"
            reason = "extreme weather / high outage risk"
        elif unc_t >= args.stochastic_uncertainty_threshold or line_risk_t >= args.stochastic_line_risk_threshold:
            strategy = "Stochastic_UC"
            reason = "high renewable uncertainty / elevated risk"
        else:
            strategy = "SCUC"
            reason = "normal operating condition"

        rows.append(
            {
                "timestamp": str(ts),
                "hour_index": int(t),
                "hourly_line_risk": round(line_risk_t, 6),
                "hourly_uncertainty": round(unc_t, 6),
                "global_expected_nk_fail_lines": round(float(warning_ctx["expected_nk_fail_lines"]), 6),
                "global_max_critical_outage_prob": round(float(warning_ctx["max_critical_outage_prob"]), 6),
                "global_high_line_ratio": round(float(warning_ctx["high_line_ratio"]), 6),
                "selected_strategy": strategy,
                "reason": reason,
            }
        )
    return pd.DataFrame(rows)


def _solution_hourly_costs(sol: ModelSolution, data: UCInputs, args: argparse.Namespace) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    t_count = len(data.timestamps)
    g_count = len(data.units)
    n_load = len(data.load_buses)

    gen_t = np.zeros(t_count, dtype=float)
    reserve_t = np.zeros(t_count, dtype=float)
    startup_t = np.zeros(t_count, dtype=float)
    ls_t = np.zeros(t_count, dtype=float)

    for t in range(t_count):
        for g, unit in enumerate(data.units):
            gen_t[t] += float(unit.gen_cost * sol.p[g, t])
            reserve_t[t] += float(unit.reserve_cost * sol.r[g, t])
            startup_t[t] += float(unit.startup_cost * sol.su[g, t] + unit.shutdown_cost * sol.sd[g, t])
        for j, bus in enumerate(data.load_buses):
            ls_t[t] += float(args.voll * data.voll_weights[bus] * sol.ls[t, j])
    return gen_t, reserve_t, startup_t, ls_t


def _extract_matrix(
    sol: ModelSolution,
    key: str,
    n_row: int,
    n_col: int,
    fallback: np.ndarray | None = None,
) -> np.ndarray:
    raw = sol.extra.get(key)
    if raw is None:
        if fallback is not None:
            return np.asarray(fallback, dtype=float).copy()
        return np.zeros((n_row, n_col), dtype=float)
    arr = np.asarray(raw, dtype=float)
    if arr.shape == (n_row, n_col):
        return arr.copy()
    if arr.shape == (n_col, n_row):
        return arr.T.copy()
    if fallback is not None:
        return np.asarray(fallback, dtype=float).copy()
    return np.zeros((n_row, n_col), dtype=float)


def build_contextual_solution(
    data: UCInputs,
    args: argparse.Namespace,
    selection_df: pd.DataFrame,
    scuc: ModelSolution,
    stoch: ModelSolution,
    robust: ModelSolution,
) -> tuple[ModelSolution, pd.DataFrame]:
    strategy_to_sol = {"SCUC": scuc, "Stochastic_UC": stoch, "Robust_UC": robust}
    t_count = len(data.timestamps)
    g_count = len(data.units)
    n_load = len(data.load_buses)
    l_count = len(data.lines)

    u = np.zeros((g_count, t_count), dtype=float)
    p = np.zeros((g_count, t_count), dtype=float)
    r = np.zeros((g_count, t_count), dtype=float)
    su = np.zeros((g_count, t_count), dtype=float)
    sd = np.zeros((g_count, t_count), dtype=float)
    ls = np.zeros((t_count, n_load), dtype=float)
    line_flow = np.zeros((t_count, l_count), dtype=float)
    line_limits = np.tile(np.array([line.fmax_effective for line in data.lines], dtype=float), (t_count, 1))

    hourly_cost_rows: list[dict[str, Any]] = []
    costs_cache: dict[str, tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]] = {
        k: _solution_hourly_costs(v, data=data, args=args) for k, v in strategy_to_sol.items()
    }
    flow_cache: dict[str, np.ndarray] = {
        "SCUC": _extract_matrix(scuc, "line_flow", t_count, l_count),
        "Stochastic_UC": _extract_matrix(stoch, "line_flow_expected", t_count, l_count),
        "Robust_UC": _extract_matrix(
            robust,
            "line_flow_worst",
            t_count,
            l_count,
            fallback=_extract_matrix(robust, "line_flow_expected", t_count, l_count),
        ),
    }
    limit_cache: dict[str, np.ndarray] = {
        "SCUC": _extract_matrix(scuc, "line_limits", t_count, l_count, fallback=line_limits),
        "Stochastic_UC": _extract_matrix(stoch, "line_limits", t_count, l_count, fallback=line_limits),
        "Robust_UC": _extract_matrix(robust, "line_limits_worst", t_count, l_count, fallback=line_limits),
    }

    for t in range(t_count):
        strategy = str(selection_df.iloc[t]["selected_strategy"])
        sol = strategy_to_sol[strategy]
        u[:, t] = sol.u[:, t]
        p[:, t] = sol.p[:, t]
        r[:, t] = sol.r[:, t]
        su[:, t] = sol.su[:, t]
        sd[:, t] = sol.sd[:, t]
        ls[t, :] = sol.ls[t, :]
        line_flow[t, :] = flow_cache[strategy][t, :]
        line_limits[t, :] = limit_cache[strategy][t, :]

        g_t, rr_t, ss_t, ls_t = costs_cache[strategy]
        hourly_cost_rows.append(
            {
                "timestamp": str(data.timestamps[t]),
                "selected_strategy": strategy,
                "generation_cost": float(g_t[t]),
                "reserve_cost": float(rr_t[t]),
                "startup_shutdown_cost": float(ss_t[t]),
                "load_shedding_penalty": float(ls_t[t]),
                "total_cost": float(g_t[t] + rr_t[t] + ss_t[t] + ls_t[t]),
            }
        )

    hourly_cost_df = pd.DataFrame(hourly_cost_rows)
    total_cost = float(hourly_cost_df["total_cost"].sum())
    gen_cost = float(hourly_cost_df["generation_cost"].sum())
    reserve_cost = float(hourly_cost_df["reserve_cost"].sum())
    startup_shutdown = float(hourly_cost_df["startup_shutdown_cost"].sum())
    ls_penalty = float(hourly_cost_df["load_shedding_penalty"].sum())

    contextual = ModelSolution(
        status="contextual_selection",
        objective=total_cost,
        solve_success=True,
        fallback_relaxation=False,
        u=u,
        p=p,
        r=r,
        su=su,
        sd=sd,
        ls=ls,
        generation_cost=gen_cost,
        reserve_cost=reserve_cost,
        startup_shutdown_cost=startup_shutdown,
        load_shed_penalty=ls_penalty,
        extra={
            "hourly_costs": hourly_cost_df,
            "line_flow": line_flow,
            "line_limits": line_limits,
            "selected_strategy": selection_df["selected_strategy"].astype(str).to_numpy(),
        },
    )
    return contextual, hourly_cost_df


def save_unit_schedule(path: Path, data: UCInputs, sol: ModelSolution, p_label: str = "p") -> None:
    rows: list[dict[str, Any]] = []
    for t, ts in enumerate(data.timestamps):
        for g, unit in enumerate(data.units):
            rows.append(
                {
                    "timestamp": str(ts),
                    "unit_id": unit.unit_id,
                    "bus": unit.bus,
                    "u": float(sol.u[g, t]),
                    p_label: float(sol.p[g, t]),
                    "reserve": float(sol.r[g, t]),
                    "startup": float(sol.su[g, t]),
                    "shutdown": float(sol.sd[g, t]),
                }
            )
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8")


def save_load_shedding(path: Path, data: UCInputs, sol: ModelSolution) -> None:
    rows: list[dict[str, Any]] = []
    bus_to_idx = {b: i for i, b in enumerate(data.buses)}
    for t, ts in enumerate(data.timestamps):
        for j, bus in enumerate(data.load_buses):
            demand = float(data.base_load_node[t, bus_to_idx[bus]])
            shed = float(sol.ls[t, j])
            rows.append(
                {
                    "timestamp": str(ts),
                    "load_bus": bus,
                    "priority_level": data.load_levels[bus],
                    "priority_weight": data.priority_weights[bus],
                    "demand": demand,
                    "shed": shed,
                    "served": demand - shed,
                }
            )
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8")


def save_line_flow(path: Path, data: UCInputs, sol: ModelSolution, selection_df: pd.DataFrame | None = None) -> None:
    t_count = len(data.timestamps)
    l_count = len(data.lines)
    default_limits = np.tile(np.array([line.fmax_effective for line in data.lines], dtype=float), (t_count, 1))
    flow = _extract_matrix(sol, "line_flow", t_count, l_count)
    limits = _extract_matrix(sol, "line_limits", t_count, l_count, fallback=default_limits)
    if selection_df is not None and len(selection_df) == t_count and "selected_strategy" in selection_df.columns:
        selected_strategy = selection_df["selected_strategy"].astype(str).to_list()
    else:
        selected_strategy = [""] * t_count

    rows: list[dict[str, Any]] = []
    for t, ts in enumerate(data.timestamps):
        for l, line in enumerate(data.lines):
            f = float(flow[t, l])
            limit = float(max(limits[t, l], 1e-9))
            loading = float(abs(f) / limit)
            rows.append(
                {
                    "timestamp": str(ts),
                    "line_id": line.line_id,
                    "from_bus": line.from_bus,
                    "to_bus": line.to_bus,
                    "flow_mw": f,
                    "limit_mw": limit,
                    "loading": loading,
                    "overload_flag": int(loading > 1.0 + 1e-9),
                    "selected_strategy": selected_strategy[t],
                }
            )
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Dispatch optimization module: SCUC + Stochastic UC + Robust UC under weather uncertainty."
    )
    parser.add_argument(
        "--strategy-mode",
        choices=("contextual",),
        default="contextual",
        help="contextual: choose dispatch strategy by operating context.",
    )
    parser.add_argument(
        "--export-diagnostics",
        action="store_true",
        help="Also export auxiliary model comparison diagnostics (not used for strategy decision).",
    )
    parser.add_argument("--grid", default="data_final/formal_guangdong_2024/grid_topology.json", help="Grid topology json path.")
    parser.add_argument("--trim-input", default="data_final/formal_guangdong_2024/TRIM_input.csv", help="Trim input csv path.")
    parser.add_argument("--failure-csv", default="results/component_failure_probability/formal2024/line_failure_timeseries_schloemer.csv", help="Failure csv for timeline anchoring.")
    parser.add_argument("--uncertainty-dir", default="results/wind_pv_uncertainty/formal2024", help="DPGMM uncertainty output directory.")
    parser.add_argument("--line-risk-csv", default="results/early_warning/formal2024/line_risk_prediction.csv", help="Optional warning line-risk csv.")
    parser.add_argument("--load-priority-csv", default="results/load_prioritization_scheduling/formal2024/load_bus_priority_profile.csv", help="Optional load-priority profile csv.")
    parser.add_argument("--output-dir", default="results/dispatch_optimization/formal2024", help="Output directory.")
    parser.add_argument("--horizon-hours", type=int, default=24, help="Optimization horizon in hours.")
    parser.add_argument("--horizon-start-index", type=int, default=0, help="Start index on failure timeline.")
    parser.add_argument("--reserve-ratio", type=float, default=0.15, help="Reserve requirement ratio.")
    parser.add_argument("--voll", type=float, default=1200.0, help="Base VOLL coefficient.")
    parser.add_argument("--redispatch-penalty", type=float, default=30.0, help="Redispatch adjustment penalty.")
    parser.add_argument("--line-derate-coeff", type=float, default=0.35, help="Line-risk derating coefficient.")
    parser.add_argument("--robust-line-factor", type=float, default=0.90, help="Additional line derate factor in robust UC.")
    parser.add_argument("--stochastic-scenarios", type=int, default=6, help="Number of stochastic scenarios.")
    parser.add_argument("--robust-set-size", type=int, default=5, help="Number of robust uncertainty-set points.")
    parser.add_argument("--robust-wind-low", type=float, default=0.7, help="Robust lower factor for wind/pv.")
    parser.add_argument("--robust-wind-high", type=float, default=1.3, help="Robust upper factor for wind/pv.")
    parser.add_argument("--robust-load-low", type=float, default=0.9, help="Robust lower factor for load.")
    parser.add_argument("--robust-load-high", type=float, default=1.2, help="Robust upper factor for load.")
    parser.add_argument("--slack-dispatchable-capacity", type=float, default=1.20, help="Fallback dispatchable capacity at slack/ext-grid units.")
    parser.add_argument("--emergency-dg-capacities", default="0.18,0.15,0.10", help="Comma-separated emergency DG capacities.")
    parser.add_argument("--time-limit-sec", type=float, default=45.0, help="MILP solver time limit per model (seconds).")
    parser.add_argument("--mip-gap", type=float, default=0.02, help="MILP relative gap.")
    parser.add_argument("--stochastic-uncertainty-threshold", type=float, default=0.22, help="Threshold of hourly uncertainty to trigger stochastic UC.")
    parser.add_argument("--stochastic-line-risk-threshold", type=float, default=0.45, help="Hourly line risk threshold to trigger stochastic UC.")
    parser.add_argument("--robust-line-risk-threshold", type=float, default=0.72, help="Hourly line risk threshold to trigger robust UC.")
    parser.add_argument("--robust-nk-threshold", type=float, default=3.0, help="Global expected N-k fail lines threshold to trigger robust UC context.")
    parser.add_argument("--robust-critical-threshold", type=float, default=0.22, help="Global critical-load outage probability threshold to trigger robust UC context.")
    parser.add_argument("--robust-high-line-ratio-threshold", type=float, default=0.30, help="Global high-risk-line ratio threshold to trigger robust UC context.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = project_root()
    output_dir = (root / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    data = build_inputs(args)

    print("[1/3] solving SCUC ...")
    t_scuc_start = time.perf_counter()
    scuc = solve_scuc(data=data, args=args)
    t_scuc = time.perf_counter() - t_scuc_start

    print("[2/3] solving Stochastic UC ...")
    t_stoch_start = time.perf_counter()
    stoch = solve_stochastic_uc(data=data, args=args)
    t_stoch = time.perf_counter() - t_stoch_start

    print("[3/3] solving Robust UC ...")
    t_robust_start = time.perf_counter()
    robust = solve_robust_uc(data=data, args=args)
    t_robust = time.perf_counter() - t_robust_start

    scuc_sched_csv = output_dir / "scuc_schedule.csv"
    stoch_sched_csv = output_dir / "stochastic_uc_first_stage_schedule.csv"
    robust_sched_csv = output_dir / "robust_uc_first_stage_schedule.csv"
    scuc_ls_csv = output_dir / "scuc_load_shedding.csv"
    stoch_ls_csv = output_dir / "stochastic_uc_expected_load_shedding.csv"
    robust_ls_csv = output_dir / "robust_uc_worst_load_shedding.csv"

    save_unit_schedule(scuc_sched_csv, data, scuc, p_label="p")
    save_unit_schedule(stoch_sched_csv, data, stoch, p_label="p_base")
    save_unit_schedule(robust_sched_csv, data, robust, p_label="p_base")
    save_load_shedding(scuc_ls_csv, data, scuc)
    save_load_shedding(stoch_ls_csv, data, stoch)
    save_load_shedding(robust_ls_csv, data, robust)

    stoch_scen_df = pd.DataFrame(
        {
            "scenario_id": np.arange(len(data.stoch_probs), dtype=int),
            "probability": data.stoch_probs,
            "total_ls": [float(arr.sum()) for arr in stoch.extra["ls_scenarios"]],
        }
    )
    stoch_scen_csv = output_dir / "stochastic_uc_scenario_summary.csv"
    stoch_scen_df.to_csv(stoch_scen_csv, index=False, encoding="utf-8")

    robust_scen_df = pd.DataFrame(
        {
            "scenario_id": np.arange(len(robust.extra["scenario_costs"]), dtype=int),
            "scenario_cost": robust.extra["scenario_costs"],
            "is_worst": [1 if i == int(robust.extra["worst_scenario_index"]) else 0 for i in range(len(robust.extra["scenario_costs"]))],
            "total_ls": [float(arr.sum()) for arr in robust.extra["ls_scenarios"]],
        }
    )
    robust_scen_csv = output_dir / "robust_uc_scenario_summary.csv"
    robust_scen_df.to_csv(robust_scen_csv, index=False, encoding="utf-8")

    # Context-driven strategy selection (primary output).
    warning_ctx = load_warning_context((root / args.line_risk_csv).resolve() if args.line_risk_csv else None)
    hourly_line_risk = load_hourly_line_risk((root / args.failure_csv).resolve(), data.timestamps)
    hourly_uncertainty = compute_hourly_uncertainty(data)
    selection_df = route_strategy_by_context(
        timestamps=data.timestamps,
        hourly_line_risk=hourly_line_risk,
        hourly_uncertainty=hourly_uncertainty,
        warning_ctx=warning_ctx,
        args=args,
    )
    t_contextual_start = time.perf_counter()
    contextual_sol, hourly_cost_df = build_contextual_solution(
        data=data,
        args=args,
        selection_df=selection_df,
        scuc=scuc,
        stoch=stoch,
        robust=robust,
    )
    t_contextual = time.perf_counter() - t_contextual_start

    # Save contextual operation outputs.
    strategy_selection_csv = output_dir / "dispatch_strategy_selection.csv"
    strategy_summary_csv = output_dir / "dispatch_active_strategy_summary.csv"
    contextual_sched_csv = output_dir / "contextual_dispatch_unit_schedule.csv"
    contextual_ls_csv = output_dir / "contextual_dispatch_load_shedding.csv"
    contextual_hourly_cost_csv = output_dir / "contextual_dispatch_hourly_cost.csv"
    line_flow_csv = output_dir / "line_flow.csv"

    selection_df.to_csv(strategy_selection_csv, index=False, encoding="utf-8")
    selection_df.groupby("selected_strategy", as_index=False).size().rename(columns={"size": "hours_selected"}).to_csv(
        strategy_summary_csv, index=False, encoding="utf-8"
    )
    save_unit_schedule(contextual_sched_csv, data, contextual_sol, p_label="p_selected")
    save_load_shedding(contextual_ls_csv, data, contextual_sol)
    save_line_flow(line_flow_csv, data, contextual_sol, selection_df=selection_df)
    hourly_cost_df.to_csv(contextual_hourly_cost_csv, index=False, encoding="utf-8")

    contextual_runtime_total = float(t_scuc + t_stoch + t_robust + t_contextual)
    contextual_metrics = compute_metrics(
        data,
        contextual_sol,
        "Contextual_Adaptive",
        runtime_sec=contextual_runtime_total,
    )
    comparison_csv: Path | None = None
    topsis_csv: Path | None = None
    if args.export_diagnostics:
        # Auxiliary diagnostics only; contextual schedule remains the operational output.
        metrics = [
            compute_metrics(data, scuc, "SCUC", runtime_sec=float(t_scuc)),
            compute_metrics(data, stoch, "Stochastic_UC", runtime_sec=float(t_stoch)),
            compute_metrics(data, robust, "Robust_UC", runtime_sec=float(t_robust)),
            contextual_metrics,
        ]
        comp_df = pd.DataFrame(metrics)
        comparison_csv = output_dir / "dispatch_model_comparison.csv"
        comp_df.to_csv(comparison_csv, index=False, encoding="utf-8")
        topsis_csv = output_dir / "dispatch_ewm_topsis_result.csv"
        comp_df[comp_df["model"] == "Contextual_Adaptive"].to_csv(topsis_csv, index=False, encoding="utf-8")

    # Keep an indicator weight file as placeholder for downstream compatibility.
    weight_csv = output_dir / "dispatch_indicator_weights.csv"
    pd.DataFrame(
        {
            "indicator": ["priority_index", "reliability_score", "rapidity", "economic_score_proxy"],
            "weight": [0.30, 0.30, 0.20, 0.20],
            "note": ["fixed contextual policy weight"] * 4,
        }
    ).to_csv(weight_csv, index=False, encoding="utf-8")

    report = {
        "module": "Dispatch Optimization",
        "objective": "min generation + reserve + startup/shutdown + load shedding penalty",
        "inputs": {
            "grid": str((root / args.grid).resolve()),
            "trim_input": str((root / args.trim_input).resolve()),
            "failure_csv": str((root / args.failure_csv).resolve()),
            "uncertainty_dir": str((root / args.uncertainty_dir).resolve()),
            "line_risk_csv": str((root / args.line_risk_csv).resolve()) if args.line_risk_csv else None,
            "time_horizon": {
                "start": str(data.timestamps.min()),
                "end": str(data.timestamps.max()),
                "hours": int(len(data.timestamps)),
            },
            "stochastic_scenarios": int(args.stochastic_scenarios),
            "robust_set_size": int(args.robust_set_size),
        },
        "solver": {
            "time_limit_sec": float(args.time_limit_sec),
            "mip_gap": float(args.mip_gap),
            "seed": int(args.seed),
        },
        "strategy_mode": str(args.strategy_mode),
        "strategy_rules": {
            "stochastic_uncertainty_threshold": float(args.stochastic_uncertainty_threshold),
            "stochastic_line_risk_threshold": float(args.stochastic_line_risk_threshold),
            "robust_line_risk_threshold": float(args.robust_line_risk_threshold),
            "robust_nk_threshold": float(args.robust_nk_threshold),
            "robust_critical_threshold": float(args.robust_critical_threshold),
            "robust_high_line_ratio_threshold": float(args.robust_high_line_ratio_threshold),
        },
        "warning_context_snapshot": warning_ctx,
        "selected_strategy_hours": (
            selection_df.groupby("selected_strategy", as_index=False).size().rename(columns={"size": "hours_selected"}).to_dict(orient="records")
        ),
        "contextual_final_metrics": contextual_metrics,
    }
    outputs: dict[str, str] = {
        "dispatch_strategy_selection_csv": str(strategy_selection_csv),
        "dispatch_active_strategy_summary_csv": str(strategy_summary_csv),
        "contextual_dispatch_unit_schedule_csv": str(contextual_sched_csv),
        "contextual_dispatch_load_shedding_csv": str(contextual_ls_csv),
        "contextual_dispatch_hourly_cost_csv": str(contextual_hourly_cost_csv),
        "dispatch_line_flow_csv": str(line_flow_csv),
        "scuc_schedule_csv": str(scuc_sched_csv),
        "stochastic_uc_first_stage_schedule_csv": str(stoch_sched_csv),
        "robust_uc_first_stage_schedule_csv": str(robust_sched_csv),
        "scuc_load_shedding_csv": str(scuc_ls_csv),
        "stochastic_uc_expected_load_shedding_csv": str(stoch_ls_csv),
        "robust_uc_worst_load_shedding_csv": str(robust_ls_csv),
        "stochastic_uc_scenario_summary_csv": str(stoch_scen_csv),
        "robust_uc_scenario_summary_csv": str(robust_scen_csv),
        "dispatch_indicator_weights_csv": str(weight_csv),
    }
    if comparison_csv is not None and topsis_csv is not None:
        outputs["dispatch_model_comparison_csv"] = str(comparison_csv)
        outputs["dispatch_ewm_topsis_result_csv"] = str(topsis_csv)
    report["outputs"] = outputs

    report_path = output_dir / "dispatch_optimization_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print("Done.")
    print(f"selected strategy timeline -> {strategy_selection_csv}")
    print(f"report -> {report_path}")


if __name__ == "__main__":
    main()
