from __future__ import annotations

import argparse
import json
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage8 steady-state physical feasibility check and correction.")
    parser.add_argument("--grid", required=True, help="Path to grid topology json.")
    parser.add_argument("--dispatch-dir", required=True, help="Directory of stage7 dispatch outputs.")
    parser.add_argument("--output-dir", required=True, help="Stage8 output directory.")
    parser.add_argument("--horizon-hours", type=int, default=24, help="Validation horizon hours.")
    parser.add_argument("--value-tol", type=float, default=1e-9, help="Numerical tolerance for value checks.")
    parser.add_argument("--line-overload-tol", type=float, default=1e-9, help="Tolerance for line overload checks.")
    parser.add_argument("--auto-correct", action="store_true", help="Enable clipping-based correction for load shedding.")
    parser.add_argument("--no-auto-correct", action="store_true", help="Disable clipping-based correction for load shedding.")
    return parser.parse_args()


def _load_required_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"required file missing: {path}")
    return pd.read_csv(path)


def _to_num(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    out = df.copy()
    for c in cols:
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce")
    return out


def add_violation(
    rows: list[dict[str, Any]],
    category: str,
    severity: str,
    timestamp: str,
    entity: str,
    rule: str,
    value: float | str,
    threshold: float | str,
    detail: str,
) -> None:
    rows.append(
        {
            "category": category,
            "severity": severity,
            "timestamp": timestamp,
            "entity": entity,
            "rule": rule,
            "value": value,
            "threshold": threshold,
            "detail": detail,
        }
    )


def validate_load_shedding(
    load_df: pd.DataFrame,
    tol: float,
    violations: list[dict[str, Any]],
) -> dict[str, int]:
    stats = {
        "negative_demand": 0,
        "negative_shed": 0,
        "shed_exceeds_demand": 0,
        "negative_served": 0,
        "served_mismatch": 0,
    }
    required = {"timestamp", "load_bus", "demand", "shed", "served"}
    if not required.issubset(load_df.columns):
        missing = sorted(required - set(load_df.columns))
        raise ValueError(f"load shedding csv missing columns: {missing}")

    for _, row in load_df.iterrows():
        ts = str(row["timestamp"])
        bus = str(row["load_bus"])
        demand = float(row["demand"])
        shed = float(row["shed"])
        served = float(row["served"])

        if demand < -tol:
            stats["negative_demand"] += 1
            add_violation(violations, "load", "critical", ts, f"bus:{bus}", "demand>=0", demand, 0.0, "Negative demand.")
        if shed < -tol:
            stats["negative_shed"] += 1
            add_violation(violations, "load", "critical", ts, f"bus:{bus}", "shed>=0", shed, 0.0, "Negative shedding.")
        if shed > demand + tol:
            stats["shed_exceeds_demand"] += 1
            add_violation(violations, "load", "critical", ts, f"bus:{bus}", "shed<=demand", shed, demand, "Load shedding exceeds demand.")
        if served < -tol:
            stats["negative_served"] += 1
            add_violation(violations, "load", "critical", ts, f"bus:{bus}", "served>=0", served, 0.0, "Negative served load.")
        if abs((demand - shed) - served) > tol:
            stats["served_mismatch"] += 1
            add_violation(
                violations,
                "load",
                "warning",
                ts,
                f"bus:{bus}",
                "served=demand-shed",
                served,
                demand - shed,
                "Served value mismatch with demand-shed.",
            )
    return stats


def validate_unit_schedule(
    unit_df: pd.DataFrame,
    tol: float,
    violations: list[dict[str, Any]],
) -> dict[str, int]:
    stats = {
        "u_out_of_range": 0,
        "u_off_with_positive_p": 0,
        "u_off_with_positive_reserve": 0,
        "negative_p": 0,
        "negative_reserve": 0,
        "startup_and_shutdown": 0,
    }
    required = {"timestamp", "unit_id", "u", "p_selected", "reserve", "startup", "shutdown"}
    if not required.issubset(unit_df.columns):
        missing = sorted(required - set(unit_df.columns))
        raise ValueError(f"unit schedule csv missing columns: {missing}")

    for _, row in unit_df.iterrows():
        ts = str(row["timestamp"])
        unit = str(row["unit_id"])
        u = float(row["u"])
        p = float(row["p_selected"])
        reserve = float(row["reserve"])
        su = float(row["startup"])
        sd = float(row["shutdown"])

        if u < -tol or u > 1.0 + tol:
            stats["u_out_of_range"] += 1
            add_violation(violations, "unit", "critical", ts, f"unit:{unit}", "0<=u<=1", u, "[0,1]", "Commitment out of range.")
        if u < 0.5 and p > tol:
            stats["u_off_with_positive_p"] += 1
            add_violation(violations, "unit", "critical", ts, f"unit:{unit}", "u=0 => p=0", p, 0.0, "Off unit has positive output.")
        if u < 0.5 and reserve > tol:
            stats["u_off_with_positive_reserve"] += 1
            add_violation(violations, "unit", "critical", ts, f"unit:{unit}", "u=0 => reserve=0", reserve, 0.0, "Off unit has reserve.")
        if p < -tol:
            stats["negative_p"] += 1
            add_violation(violations, "unit", "critical", ts, f"unit:{unit}", "p>=0", p, 0.0, "Negative generation.")
        if reserve < -tol:
            stats["negative_reserve"] += 1
            add_violation(violations, "unit", "critical", ts, f"unit:{unit}", "reserve>=0", reserve, 0.0, "Negative reserve.")
        if su > 0.5 and sd > 0.5:
            stats["startup_and_shutdown"] += 1
            add_violation(
                violations,
                "unit",
                "warning",
                ts,
                f"unit:{unit}",
                "not(startup&shutdown)",
                f"{su}/{sd}",
                "exclusive",
                "Startup and shutdown both active.",
            )
    return stats


def validate_line_flow(
    line_df: pd.DataFrame,
    tol: float,
    overload_tol: float,
    violations: list[dict[str, Any]],
) -> dict[str, int]:
    stats = {
        "nonpositive_limit": 0,
        "loading_over_1": 0,
        "overload_flag_mismatch": 0,
        "loading_calc_mismatch": 0,
    }
    required = {"timestamp", "line_id", "flow_mw", "limit_mw", "loading", "overload_flag"}
    if not required.issubset(line_df.columns):
        missing = sorted(required - set(line_df.columns))
        raise ValueError(f"line flow csv missing columns: {missing}")

    for _, row in line_df.iterrows():
        ts = str(row["timestamp"])
        line_id = str(row["line_id"])
        flow = float(row["flow_mw"])
        limit = float(row["limit_mw"])
        loading = float(row["loading"])
        flag = int(row["overload_flag"])

        if limit <= tol:
            stats["nonpositive_limit"] += 1
            add_violation(violations, "line", "critical", ts, f"line:{line_id}", "limit>0", limit, 0.0, "Non-positive line limit.")
            continue

        calc_loading = abs(flow) / max(abs(limit), tol)
        if abs(calc_loading - loading) > 1e-6:
            stats["loading_calc_mismatch"] += 1
            add_violation(
                violations,
                "line",
                "warning",
                ts,
                f"line:{line_id}",
                "loading=abs(flow)/limit",
                loading,
                calc_loading,
                "Reported loading does not match flow/limit.",
            )
        if loading > 1.0 + overload_tol:
            stats["loading_over_1"] += 1
            add_violation(
                violations,
                "line",
                "critical",
                ts,
                f"line:{line_id}",
                "loading<=1",
                loading,
                1.0,
                "Line overload.",
            )
        flag_should = 1 if loading > 1.0 + overload_tol else 0
        if flag != flag_should:
            stats["overload_flag_mismatch"] += 1
            add_violation(
                violations,
                "line",
                "warning",
                ts,
                f"line:{line_id}",
                "overload_flag consistency",
                flag,
                flag_should,
                "overload_flag inconsistent with loading.",
            )
    return stats


def apply_load_correction(load_df: pd.DataFrame, tol: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    corrected = load_df.copy()
    corrected["shed_original"] = corrected["shed"]
    corrected["served_original"] = corrected["served"]

    corrected["shed"] = corrected[["shed", "demand"]].min(axis=1)
    corrected["shed"] = corrected["shed"].clip(lower=0.0)
    corrected["demand"] = corrected["demand"].clip(lower=0.0)
    corrected["served"] = corrected["demand"] - corrected["shed"]
    corrected["served"] = corrected["served"].clip(lower=0.0)

    corrected["shed_correction"] = corrected["shed"] - corrected["shed_original"]
    corrected["served_correction"] = corrected["served"] - corrected["served_original"]
    corrected["is_corrected"] = (
        corrected["shed_correction"].abs() > tol
    ) | (corrected["served_correction"].abs() > tol)

    log_cols = [
        "timestamp",
        "load_bus",
        "demand",
        "shed_original",
        "shed",
        "served_original",
        "served",
        "shed_correction",
        "served_correction",
        "is_corrected",
    ]
    correction_log = corrected[log_cols].copy()
    return corrected.drop(columns=["shed_original", "served_original"]), correction_log


def _load_optional_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def _normalize(series: pd.Series) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce").fillna(0.0).astype(float)
    vmax = float(s.max()) if not s.empty else 0.0
    vmin = float(s.min()) if not s.empty else 0.0
    span = vmax - vmin
    if span <= 1e-12:
        return pd.Series(np.zeros(len(s), dtype=float), index=s.index)
    return (s - vmin) / span


def _build_graph(grid: dict[str, Any]) -> tuple[dict[int, list[int]], dict[int, dict[str, Any]], pd.DataFrame]:
    nodes_df = pd.DataFrame(grid.get("nodes", []))
    lines_df = pd.DataFrame(grid.get("lines", []))
    adjacency: dict[int, list[int]] = {}
    for _, row in lines_df.iterrows():
        fb = int(row["from"])
        tb = int(row["to"])
        adjacency.setdefault(fb, []).append(tb)
        adjacency.setdefault(tb, []).append(fb)
    return adjacency, {int(r["id"]): dict(r) for _, r in nodes_df.iterrows()}, lines_df


def _shortest_hops(adjacency: dict[int, list[int]], source: int) -> dict[int, int]:
    dist = {int(source): 0}
    queue: deque[int] = deque([int(source)])
    while queue:
        cur = queue.popleft()
        for nxt in adjacency.get(cur, []):
            if nxt in dist:
                continue
            dist[nxt] = dist[cur] + 1
            queue.append(nxt)
    return dist


def build_line_diagnostics(
    line_df: pd.DataFrame,
    line_static_risk_df: pd.DataFrame,
    line_hourly_risk_df: pd.DataFrame,
) -> pd.DataFrame:
    diag = line_df.copy()
    static_df = line_static_risk_df.copy()
    if not static_df.empty:
        static_df["line_id"] = static_df["line_id"].astype(str)
        static_df = static_df.rename(columns={"risk_prob": "static_risk_prob", "risk_level": "static_risk_level"})
        diag = diag.merge(static_df[["line_id", "static_risk_prob", "static_risk_level", "predicted_fail_hour"]], on="line_id", how="left")
    else:
        diag["static_risk_prob"] = 0.0
        diag["static_risk_level"] = "UNKNOWN"
        diag["predicted_fail_hour"] = ""

    if not line_hourly_risk_df.empty:
        hourly_df = line_hourly_risk_df.copy()
        hourly_df["timestamp"] = hourly_df["timestamp"].astype(str)
        hourly_df["line_id"] = hourly_df["line_id"].astype(str)
        diag = diag.merge(hourly_df[["timestamp", "line_id", "hourly_risk_prob"]], on=["timestamp", "line_id"], how="left")
    else:
        diag["hourly_risk_prob"] = np.nan

    diag["hourly_risk_prob"] = pd.to_numeric(diag["hourly_risk_prob"], errors="coerce")
    diag["static_risk_prob"] = pd.to_numeric(diag["static_risk_prob"], errors="coerce").fillna(0.0)
    diag["effective_risk_prob"] = diag["hourly_risk_prob"].fillna(diag["static_risk_prob"]).clip(lower=0.0, upper=1.0)
    diag["flow_abs_mw"] = pd.to_numeric(diag["flow_mw"], errors="coerce").abs().fillna(0.0)
    diag["loading"] = pd.to_numeric(diag["loading"], errors="coerce").fillna(0.0)
    diag["stress_score"] = (
        0.45 * diag["effective_risk_prob"]
        + 0.35 * diag["loading"].clip(lower=0.0)
        + 0.20 * (diag["effective_risk_prob"] * diag["loading"].clip(lower=0.0))
    ).clip(lower=0.0)
    diag["high_risk_flag"] = diag["effective_risk_prob"] >= 0.60
    diag["near_overload_flag"] = diag["loading"] >= 0.75
    diag["action_priority"] = np.select(
        [
            diag["stress_score"] >= 0.90,
            diag["stress_score"] >= 0.75,
            diag["stress_score"] >= 0.55,
        ],
        ["urgent", "high", "medium"],
        default="low",
    )
    diag["recommended_action"] = np.select(
        [
            diag["high_risk_flag"] & diag["near_overload_flag"],
            diag["high_risk_flag"],
            diag["near_overload_flag"],
        ],
        [
            "redispatch away from corridor and hold nearby reserve",
            "monitor corridor and pre-position reserve",
            "reduce loading through local redispatch",
        ],
        default="monitor",
    )
    diag["critical_line_flag"] = diag["action_priority"].isin(["urgent", "high"])
    return diag.sort_values(["timestamp", "stress_score", "loading"], ascending=[True, False, False]).reset_index(drop=True)


def build_vulnerable_buses(
    line_diag_df: pd.DataFrame,
    load_df: pd.DataFrame,
    nodes_by_id: dict[int, dict[str, Any]],
    lines_df: pd.DataFrame,
) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    load_view = load_df.copy()
    load_view["timestamp"] = load_view["timestamp"].astype(str)
    load_view["load_bus"] = pd.to_numeric(load_view["load_bus"], errors="coerce").astype("Int64")
    for ts, group in line_diag_df.groupby("timestamp", sort=True):
        load_ts = load_view[load_view["timestamp"] == str(ts)].copy()
        load_by_bus = {
            int(r["load_bus"]): r
            for _, r in load_ts.iterrows()
            if pd.notna(r["load_bus"])
        }
        for bus_id in sorted(nodes_by_id.keys()):
            incident = group[(group["from_bus"] == bus_id) | (group["to_bus"] == bus_id)].copy()
            load_row = load_by_bus.get(int(bus_id))
            demand = float(load_row["demand"]) if load_row is not None else 0.0
            served = float(load_row["served"]) if load_row is not None else 0.0
            served_ratio = served / max(demand, 1e-12) if demand > 0 else 1.0
            priority_level = int(load_row["priority_level"]) if load_row is not None else 0
            priority_weight = float(load_row["priority_weight"]) if load_row is not None else 0.0
            max_stress = float(incident["stress_score"].max()) if not incident.empty else 0.0
            mean_stress = float(incident["stress_score"].mean()) if not incident.empty else 0.0
            critical_line_count = int(incident["critical_line_flag"].sum()) if not incident.empty else 0
            vulnerability_score = float(
                np.clip(
                    0.45 * max_stress
                    + 0.20 * mean_stress
                    + 0.20 * (1.0 - np.clip(served_ratio, 0.0, 1.0))
                    + 0.15 * np.clip(priority_weight, 0.0, 1.0),
                    0.0,
                    1.5,
                )
            )
            records.append(
                {
                    "timestamp": str(ts),
                    "bus_id": int(bus_id),
                    "node_type": str(nodes_by_id[bus_id].get("type", "bus")),
                    "incident_line_count": int(len(incident)),
                    "critical_incident_line_count": critical_line_count,
                    "max_incident_stress": max_stress,
                    "mean_incident_stress": mean_stress,
                    "demand": demand,
                    "served": served,
                    "served_ratio": float(np.clip(served_ratio, 0.0, 1.0)),
                    "priority_level": priority_level,
                    "priority_weight": priority_weight,
                    "vulnerability_score": vulnerability_score,
                }
            )
    bus_df = pd.DataFrame(records)
    if bus_df.empty:
        return bus_df
    bus_df["vulnerability_level"] = np.select(
        [
            bus_df["vulnerability_score"] >= 0.85,
            bus_df["vulnerability_score"] >= 0.65,
            bus_df["vulnerability_score"] >= 0.45,
        ],
        ["critical", "high", "medium"],
        default="low",
    )
    bus_df["recommended_action"] = np.select(
        [
            (bus_df["priority_weight"] >= 1.0) & (bus_df["vulnerability_score"] >= 0.65),
            bus_df["served_ratio"] < 0.90,
            bus_df["vulnerability_score"] >= 0.65,
        ],
        [
            "protect critical load and support with nearby generation",
            "prepare corrective support and controlled shedding review",
            "increase local reserve and watch adjacent corridors",
        ],
        default="monitor",
    )
    return bus_df.sort_values(["timestamp", "vulnerability_score", "priority_weight"], ascending=[True, False, False]).reset_index(drop=True)


def build_load_area_risk(vulnerable_bus_df: pd.DataFrame) -> pd.DataFrame:
    if vulnerable_bus_df.empty:
        return pd.DataFrame()
    load_df = vulnerable_bus_df[vulnerable_bus_df["demand"] > 0].copy()
    if load_df.empty:
        return load_df
    load_df["adjacent_high_stress_flag"] = load_df["max_incident_stress"] >= 0.75
    load_df["loss_of_supply_score"] = (
        0.45 * load_df["max_incident_stress"]
        + 0.35 * (1.0 - load_df["served_ratio"].clip(lower=0.0, upper=1.0))
        + 0.20 * load_df["priority_weight"].clip(lower=0.0, upper=1.0)
    ).clip(lower=0.0)
    load_df["action_priority"] = np.select(
        [
            load_df["loss_of_supply_score"] >= 0.80,
            load_df["loss_of_supply_score"] >= 0.60,
            load_df["loss_of_supply_score"] >= 0.40,
        ],
        ["urgent", "high", "medium"],
        default="low",
    )
    load_df["recommended_action"] = np.select(
        [
            (load_df["priority_weight"] >= 1.0) & (load_df["loss_of_supply_score"] >= 0.60),
            load_df["loss_of_supply_score"] >= 0.60,
        ],
        [
            "prioritize local support and protect critical service",
            "prepare reserve support and staged load transfer",
        ],
        default="monitor",
    )
    return load_df.rename(columns={"bus_id": "load_bus"}).sort_values(
        ["timestamp", "loss_of_supply_score", "priority_weight"], ascending=[True, False, False]
    ).reset_index(drop=True)


def build_generator_action_candidates(
    unit_df: pd.DataFrame,
    vulnerable_bus_df: pd.DataFrame,
    adjacency: dict[int, list[int]],
) -> pd.DataFrame:
    if unit_df.empty or vulnerable_bus_df.empty:
        return pd.DataFrame()
    cap_proxy = unit_df.groupby("unit_id", as_index=False).agg(capacity_proxy=("p_selected", "max"), reserve_proxy=("reserve", "max"))
    cap_proxy["capacity_proxy"] = (cap_proxy["capacity_proxy"] + cap_proxy["reserve_proxy"]).clip(lower=0.0)
    cap_map = {str(r["unit_id"]): float(r["capacity_proxy"]) for _, r in cap_proxy.iterrows()}

    vuln_ts_map = {
        str(ts): df.sort_values("vulnerability_score", ascending=False).copy()
        for ts, df in vulnerable_bus_df.groupby("timestamp", sort=True)
    }
    hop_cache: dict[int, dict[int, int]] = {}
    rows: list[dict[str, Any]] = []
    for _, row in unit_df.iterrows():
        ts = str(row["timestamp"])
        unit_id = str(row["unit_id"])
        bus = int(row["bus"])
        p = float(row["p_selected"])
        reserve = float(row["reserve"])
        capacity_proxy = max(cap_map.get(unit_id, 0.0), p + reserve, 0.0)
        headroom = max(capacity_proxy - max(p, 0.0) - max(reserve, 0.0), 0.0)
        hop_map = hop_cache.setdefault(bus, _shortest_hops(adjacency=adjacency, source=bus))

        vuln_ts = vuln_ts_map.get(ts, pd.DataFrame())
        if vuln_ts.empty:
            continue
        vuln_ts = vuln_ts[vuln_ts["vulnerability_score"] >= 0.45].copy()
        if vuln_ts.empty:
            continue
        vuln_ts["hop_distance"] = vuln_ts["bus_id"].map(lambda x: hop_map.get(int(x), 999))
        vuln_ts["supportability"] = vuln_ts["vulnerability_score"] / (1.0 + vuln_ts["hop_distance"].clip(lower=0.0))
        target = vuln_ts.sort_values(["supportability", "priority_weight"], ascending=[False, False]).iloc[0]
        score = float((headroom + max(reserve, 0.0)) * float(target["supportability"]))
        rows.append(
            {
                "timestamp": ts,
                "unit_id": unit_id,
                "unit_bus": bus,
                "target_bus": int(target["bus_id"]),
                "target_vulnerability_score": float(target["vulnerability_score"]),
                "target_priority_weight": float(target["priority_weight"]),
                "hop_distance": int(target["hop_distance"]),
                "p_selected": p,
                "reserve": reserve,
                "capacity_proxy": capacity_proxy,
                "headroom": headroom,
                "support_score": score,
            }
        )
    cand_df = pd.DataFrame(rows)
    if cand_df.empty:
        return cand_df
    cand_df["action_priority"] = np.select(
        [
            cand_df["support_score"] >= 0.10,
            cand_df["support_score"] >= 0.05,
            cand_df["support_score"] >= 0.02,
        ],
        ["high", "medium", "low"],
        default="monitor",
    )
    cand_df["recommended_action"] = np.select(
        [
            (cand_df["headroom"] > 0.0) & (cand_df["target_vulnerability_score"] >= 0.65),
            (cand_df["reserve"] > 0.0) & (cand_df["target_vulnerability_score"] >= 0.55),
        ],
        [
            "candidate to raise output toward vulnerable area",
            "candidate to hold reserve for vulnerable area",
        ],
        default="monitor",
    )
    return cand_df.sort_values(["timestamp", "support_score", "headroom"], ascending=[True, False, False]).reset_index(drop=True)


def build_rule_based_actions(
    line_diag_df: pd.DataFrame,
    vulnerable_bus_df: pd.DataFrame,
    load_area_df: pd.DataFrame,
    generator_action_df: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []

    for ts, group in line_diag_df.groupby("timestamp", sort=True):
        g = group.copy()
        if g.empty:
            continue
        loading_cut = max(float(g["loading"].quantile(0.80)), 0.02)
        selected = g[(g["effective_risk_prob"] >= 0.68) & (g["loading"] >= loading_cut)].copy()
        for _, row in selected.sort_values(["stress_score", "loading"], ascending=False).head(3).iterrows():
            rows.append(
                {
                    "timestamp": str(ts),
                    "action_type": "line_relief",
                    "target_type": "line",
                    "target_id": str(row["line_id"]),
                    "priority": "high" if float(row["stress_score"]) >= 0.34 else "medium",
                    "trigger_rule": "high line risk + high relative loading",
                    "recommended_action": "reduce corridor loading via redispatch or transfer",
                    "supporting_units": "",
                    "risk_prob": float(row["effective_risk_prob"]),
                    "loading": float(row["loading"]),
                    "score": float(row["stress_score"]),
                    "reason": f"line {row['line_id']} has risk={float(row['effective_risk_prob']):.3f}, loading={float(row['loading']):.3f}",
                }
            )

    gen_ts_map = {
        str(ts): df.sort_values(["support_score", "headroom"], ascending=False).copy()
        for ts, df in generator_action_df.groupby("timestamp", sort=True)
    }

    for ts, group in vulnerable_bus_df.groupby("timestamp", sort=True):
        selected = group[(group["vulnerability_score"] >= 0.46) & (group["served_ratio"] < 0.95)].copy()
        gen_candidates = gen_ts_map.get(str(ts), pd.DataFrame())
        for _, row in selected.sort_values(["vulnerability_score", "priority_weight"], ascending=False).head(3).iterrows():
            local_units = gen_candidates[gen_candidates["target_bus"] == int(row["bus_id"])].head(2)
            unit_text = ",".join(local_units["unit_id"].astype(str).tolist())
            action = "raise nearby generation to support vulnerable area"
            if not unit_text:
                nearby = gen_candidates.head(2)
                unit_text = ",".join(nearby["unit_id"].astype(str).tolist())
                action = "prepare nearest available generation support"
            rows.append(
                {
                    "timestamp": str(ts),
                    "action_type": "local_generation_support",
                    "target_type": "bus_area",
                    "target_id": str(int(row["bus_id"])),
                    "priority": "high" if float(row["vulnerability_score"]) >= 0.50 else "medium",
                    "trigger_rule": "vulnerable area with curtailed or fragile supply",
                    "recommended_action": action,
                    "supporting_units": unit_text,
                    "risk_prob": float(row["max_incident_stress"]),
                    "loading": float(1.0 - row["served_ratio"]),
                    "score": float(row["vulnerability_score"]),
                    "reason": f"bus {int(row['bus_id'])} vulnerability={float(row['vulnerability_score']):.3f}, served_ratio={float(row['served_ratio']):.3f}",
                }
            )

    for ts, group in load_area_df.groupby("timestamp", sort=True):
        selected = group[(group["priority_weight"] >= 1.0) & (group["loss_of_supply_score"] >= 0.50)].copy()
        gen_candidates = gen_ts_map.get(str(ts), pd.DataFrame())
        for _, row in selected.sort_values(["loss_of_supply_score", "priority_weight"], ascending=False).head(3).iterrows():
            if gen_candidates.empty or "target_bus" not in gen_candidates.columns or "reserve" not in gen_candidates.columns:
                reserve_units = pd.DataFrame(columns=["unit_id"])
            else:
                reserve_units = gen_candidates[
                    (gen_candidates["target_bus"] == int(row["load_bus"])) & (gen_candidates["reserve"] > 0.0)
                ].head(3)
                if reserve_units.empty:
                    reserve_units = gen_candidates[gen_candidates["reserve"] > 0.0].head(3)
            rows.append(
                {
                    "timestamp": str(ts),
                    "action_type": "reserve_hold",
                    "target_type": "critical_load_bus",
                    "target_id": str(int(row["load_bus"])),
                    "priority": "high",
                    "trigger_rule": "critical load bus with elevated outage risk",
                    "recommended_action": "increase spinning reserve near critical load",
                    "supporting_units": ",".join(reserve_units["unit_id"].astype(str).tolist()),
                    "risk_prob": float(row["max_incident_stress"]),
                    "loading": float(1.0 - row["served_ratio"]),
                    "score": float(row["loss_of_supply_score"]),
                    "reason": f"critical load bus {int(row['load_bus'])} loss_of_supply_score={float(row['loss_of_supply_score']):.3f}",
                }
            )

    action_df = pd.DataFrame(rows)
    if action_df.empty:
        return action_df
    return action_df.sort_values(["timestamp", "priority", "score"], ascending=[True, True, False]).reset_index(drop=True)


def _split_units(raw: str) -> list[str]:
    if raw is None:
        return []
    return [x.strip() for x in str(raw).split(",") if x.strip()]


def apply_rule_based_corrections(
    load_df: pd.DataFrame,
    unit_df: pd.DataFrame,
    line_df: pd.DataFrame,
    rule_action_df: pd.DataFrame,
    generator_action_df: pd.DataFrame,
    tol: float,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    corrected_load = load_df.copy()
    corrected_unit = unit_df.copy()
    corrected_line = line_df.copy()
    action_logs: list[dict[str, Any]] = []

    if rule_action_df.empty:
        summary = {
            "actions_requested": 0,
            "actions_executed": 0,
            "load_shed_reduction": 0.0,
            "served_increase": 0.0,
            "reserve_increase": 0.0,
            "line_loading_reduction": 0.0,
        }
        return corrected_load, corrected_unit, corrected_line, pd.DataFrame(action_logs), summary

    gen_cols = [
        "timestamp",
        "unit_id",
        "target_bus",
        "capacity_proxy",
        "headroom",
        "reserve",
        "support_score",
    ]
    gen_candidates = generator_action_df[gen_cols].copy() if not generator_action_df.empty else pd.DataFrame(columns=gen_cols)
    if not gen_candidates.empty:
        gen_candidates["timestamp"] = gen_candidates["timestamp"].astype(str)
        gen_candidates["unit_id"] = gen_candidates["unit_id"].astype(str)

    load_shed_reduction = 0.0
    served_increase = 0.0
    reserve_increase = 0.0
    line_loading_reduction = 0.0
    actions_executed = 0

    for _, action in rule_action_df.iterrows():
        ts = str(action["timestamp"])
        action_type = str(action["action_type"])
        target_id = str(action["target_id"])
        units = _split_units(action.get("supporting_units", ""))
        score = float(action.get("score", 0.0))

        if action_type == "local_generation_support":
            if not units:
                continue
            target_bus = int(target_id)
            load_mask = (corrected_load["timestamp"].astype(str) == ts) & (pd.to_numeric(corrected_load["load_bus"], errors="coerce") == target_bus)
            if not load_mask.any():
                continue
            demand = float(corrected_load.loc[load_mask, "demand"].iloc[0])
            shed = float(corrected_load.loc[load_mask, "shed"].iloc[0])
            if demand <= tol or shed <= tol:
                continue
            unit_mask = (corrected_unit["timestamp"].astype(str) == ts) & (corrected_unit["unit_id"].astype(str).isin(units))
            if not unit_mask.any():
                continue
            unit_slice = corrected_unit.loc[unit_mask, ["unit_id", "p_selected", "reserve"]].copy()
            available_rows: list[dict[str, Any]] = []
            for unit_id in unit_slice["unit_id"].astype(str):
                gen_row = gen_candidates[(gen_candidates["timestamp"] == ts) & (gen_candidates["unit_id"] == unit_id)]
                if gen_row.empty:
                    continue
                cap = float(gen_row["capacity_proxy"].iloc[0])
                p_now = float(corrected_unit.loc[(corrected_unit["timestamp"].astype(str) == ts) & (corrected_unit["unit_id"].astype(str) == unit_id), "p_selected"].iloc[0])
                r_now = float(corrected_unit.loc[(corrected_unit["timestamp"].astype(str) == ts) & (corrected_unit["unit_id"].astype(str) == unit_id), "reserve"].iloc[0])
                available = max(cap - max(p_now, 0.0) - max(r_now, 0.0), 0.0)
                if available > tol:
                    available_rows.append({"unit_id": unit_id, "available": available})
            if not available_rows:
                continue
            avail_df = pd.DataFrame(available_rows)
            total_available = float(avail_df["available"].sum())
            support_mw = min(shed, total_available * 0.85, max(0.02, 0.20 + 0.30 * score))
            if support_mw <= tol:
                continue
            avail_df["delta_p"] = support_mw * avail_df["available"] / max(total_available, tol)
            for _, unit_row in avail_df.iterrows():
                u_mask = (corrected_unit["timestamp"].astype(str) == ts) & (corrected_unit["unit_id"].astype(str) == str(unit_row["unit_id"]))
                corrected_unit.loc[u_mask, "p_selected"] = corrected_unit.loc[u_mask, "p_selected"] + float(unit_row["delta_p"])
            new_shed = max(shed - support_mw, 0.0)
            corrected_load.loc[load_mask, "shed"] = new_shed
            corrected_load.loc[load_mask, "served"] = demand - new_shed
            load_shed_reduction += float(shed - new_shed)
            served_increase += float(shed - new_shed)
            actions_executed += 1
            action_logs.append(
                {
                    "timestamp": ts,
                    "action_type": action_type,
                    "target_id": target_id,
                    "executed": True,
                    "delta_load_shed": float(shed - new_shed),
                    "delta_reserve": 0.0,
                    "delta_line_loading": 0.0,
                    "notes": f"allocated support across {len(avail_df)} units",
                }
            )

        elif action_type == "reserve_hold":
            if not units:
                action_logs.append(
                    {
                        "timestamp": ts,
                        "action_type": action_type,
                        "target_id": target_id,
                        "executed": False,
                        "delta_load_shed": 0.0,
                        "delta_reserve": 0.0,
                        "delta_line_loading": 0.0,
                        "notes": "no supporting units available",
                    }
                )
                continue
            reserve_delta_total = 0.0
            for unit_id in units:
                gen_row = gen_candidates[(gen_candidates["timestamp"] == ts) & (gen_candidates["unit_id"] == unit_id)]
                u_mask = (corrected_unit["timestamp"].astype(str) == ts) & (corrected_unit["unit_id"].astype(str) == unit_id)
                if gen_row.empty or not u_mask.any():
                    continue
                cap = float(gen_row["capacity_proxy"].iloc[0])
                p_now = float(corrected_unit.loc[u_mask, "p_selected"].iloc[0])
                r_now = float(corrected_unit.loc[u_mask, "reserve"].iloc[0])
                available = max(cap - max(p_now, 0.0) - max(r_now, 0.0), 0.0)
                reserve_add = min(available, max(0.01, 0.04 * (1.0 + score)))
                if reserve_add <= tol:
                    continue
                corrected_unit.loc[u_mask, "reserve"] = corrected_unit.loc[u_mask, "reserve"] + reserve_add
                reserve_delta_total += reserve_add
            if reserve_delta_total > tol:
                reserve_increase += reserve_delta_total
                actions_executed += 1
                action_logs.append(
                    {
                        "timestamp": ts,
                        "action_type": action_type,
                        "target_id": target_id,
                        "executed": True,
                        "delta_load_shed": 0.0,
                        "delta_reserve": reserve_delta_total,
                        "delta_line_loading": 0.0,
                        "notes": f"increased reserve on {len(units)} candidate units",
                    }
                )

        elif action_type == "line_relief":
            line_mask = (corrected_line["timestamp"].astype(str) == ts) & (corrected_line["line_id"].astype(str) == target_id)
            if not line_mask.any():
                continue
            flow_old = float(corrected_line.loc[line_mask, "flow_mw"].iloc[0])
            loading_old = float(corrected_line.loc[line_mask, "loading"].iloc[0])
            relief_factor = min(0.15, 0.04 + 0.10 * score)
            flow_new = flow_old * (1.0 - relief_factor)
            limit = float(corrected_line.loc[line_mask, "limit_mw"].iloc[0])
            loading_new = abs(flow_new) / max(abs(limit), tol)
            corrected_line.loc[line_mask, "flow_mw"] = flow_new
            corrected_line.loc[line_mask, "loading"] = loading_new
            corrected_line.loc[line_mask, "overload_flag"] = int(loading_new > 1.0 + tol)
            line_loading_reduction += max(loading_old - loading_new, 0.0)
            actions_executed += 1
            action_logs.append(
                {
                    "timestamp": ts,
                    "action_type": action_type,
                    "target_id": target_id,
                    "executed": True,
                    "delta_load_shed": 0.0,
                    "delta_reserve": 0.0,
                    "delta_line_loading": float(loading_old - loading_new),
                    "notes": "heuristic line relief scaling applied",
                }
            )

    action_log_df = pd.DataFrame(action_logs)
    summary = {
        "actions_requested": int(len(rule_action_df)),
        "actions_executed": int(actions_executed),
        "load_shed_reduction": float(load_shed_reduction),
        "served_increase": float(served_increase),
        "reserve_increase": float(reserve_increase),
        "line_loading_reduction": float(line_loading_reduction),
    }
    return corrected_load, corrected_unit, corrected_line, action_log_df, summary


def build_experiment_metrics_comparison(
    load_df: pd.DataFrame,
    diagnostic_load_df: pd.DataFrame,
    corrected_load_df: pd.DataFrame,
    unit_df: pd.DataFrame,
    corrected_unit_df: pd.DataFrame,
    line_df: pd.DataFrame,
    corrected_line_df: pd.DataFrame,
    critical_count: int,
    warning_count: int,
    load_stats: dict[str, int],
    unit_stats: dict[str, int],
    line_stats: dict[str, int],
    rule_closure_report: dict[str, Any],
) -> pd.DataFrame:
    rows = [
        {
            "group": "G0_stage7_raw",
            "description": "Original Stage7 outputs",
            "total_shed": float(pd.to_numeric(load_df["shed"], errors="coerce").fillna(0.0).sum()),
            "total_served": float(pd.to_numeric(load_df["served"], errors="coerce").fillna(0.0).sum()),
            "total_reserve": float(pd.to_numeric(unit_df["reserve"], errors="coerce").fillna(0.0).sum()),
            "mean_line_loading": float(pd.to_numeric(line_df["loading"], errors="coerce").fillna(0.0).mean()),
            "critical_violations": int(critical_count),
            "warning_violations": int(warning_count),
            "shed_exceeds_demand": int(load_stats.get("shed_exceeds_demand", 0)),
            "negative_served": int(load_stats.get("negative_served", 0)),
            "u_off_with_positive_p": int(unit_stats.get("u_off_with_positive_p", 0)),
            "loading_over_1": int(line_stats.get("loading_over_1", 0)),
            "actions_executed": 0,
        },
        {
            "group": "G1_stage8_diagnostic",
            "description": "Stage8 diagnostic/autocorrect baseline",
            "total_shed": float(pd.to_numeric(diagnostic_load_df["shed"], errors="coerce").fillna(0.0).sum()),
            "total_served": float(pd.to_numeric(diagnostic_load_df["served"], errors="coerce").fillna(0.0).sum()),
            "total_reserve": float(pd.to_numeric(unit_df["reserve"], errors="coerce").fillna(0.0).sum()),
            "mean_line_loading": float(pd.to_numeric(line_df["loading"], errors="coerce").fillna(0.0).mean()),
            "critical_violations": int(critical_count),
            "warning_violations": int(warning_count),
            "shed_exceeds_demand": 0,
            "negative_served": 0,
            "u_off_with_positive_p": int(unit_stats.get("u_off_with_positive_p", 0)),
            "loading_over_1": int(line_stats.get("loading_over_1", 0)),
            "actions_executed": 0,
        },
        {
            "group": "G2_rule_closed_loop",
            "description": "Stage8 heuristic rule closed-loop outputs",
            "total_shed": float(pd.to_numeric(corrected_load_df["shed"], errors="coerce").fillna(0.0).sum()),
            "total_served": float(pd.to_numeric(corrected_load_df["served"], errors="coerce").fillna(0.0).sum()),
            "total_reserve": float(pd.to_numeric(corrected_unit_df["reserve"], errors="coerce").fillna(0.0).sum()),
            "mean_line_loading": float(pd.to_numeric(corrected_line_df["loading"], errors="coerce").fillna(0.0).mean()),
            "critical_violations": int(critical_count),
            "warning_violations": int(warning_count),
            "shed_exceeds_demand": 0,
            "negative_served": 0,
            "u_off_with_positive_p": int(unit_stats.get("u_off_with_positive_p", 0)),
            "loading_over_1": int((pd.to_numeric(corrected_line_df["loading"], errors="coerce").fillna(0.0) > 1.0).sum()),
            "actions_executed": int(rule_closure_report.get("actions_executed", 0)),
        },
    ]
    return pd.DataFrame(rows)


def build_action_type_summary(rule_action_df: pd.DataFrame, rule_action_log_df: pd.DataFrame) -> pd.DataFrame:
    requested = (
        rule_action_df.groupby("action_type", as_index=False)
        .agg(requested_count=("action_type", "size"), mean_score=("score", "mean"))
        if not rule_action_df.empty
        else pd.DataFrame(columns=["action_type", "requested_count", "mean_score"])
    )
    executed = (
        rule_action_log_df[rule_action_log_df.get("executed", False) == True].groupby("action_type", as_index=False)
        .agg(
            executed_count=("action_type", "size"),
            total_delta_load_shed=("delta_load_shed", "sum"),
            total_delta_reserve=("delta_reserve", "sum"),
            total_delta_line_loading=("delta_line_loading", "sum"),
        )
        if not rule_action_log_df.empty
        else pd.DataFrame(columns=["action_type", "executed_count", "total_delta_load_shed", "total_delta_reserve", "total_delta_line_loading"])
    )
    if requested.empty and executed.empty:
        return pd.DataFrame()
    out = requested.merge(executed, on="action_type", how="outer").fillna(0.0)
    out["execution_rate"] = out["executed_count"] / np.clip(out["requested_count"], 1.0, None)
    return out.sort_values("requested_count", ascending=False).reset_index(drop=True)


def build_hourly_closure_comparison(
    diagnostic_load_df: pd.DataFrame,
    corrected_load_df: pd.DataFrame,
    unit_df: pd.DataFrame,
    corrected_unit_df: pd.DataFrame,
    line_df: pd.DataFrame,
    corrected_line_df: pd.DataFrame,
) -> pd.DataFrame:
    load_g1 = diagnostic_load_df.groupby("timestamp", as_index=False).agg(g1_total_shed=("shed", "sum"), g1_total_served=("served", "sum"))
    load_g2 = corrected_load_df.groupby("timestamp", as_index=False).agg(g2_total_shed=("shed", "sum"), g2_total_served=("served", "sum"))
    reserve_g1 = unit_df.groupby("timestamp", as_index=False).agg(g1_total_reserve=("reserve", "sum"))
    reserve_g2 = corrected_unit_df.groupby("timestamp", as_index=False).agg(g2_total_reserve=("reserve", "sum"))
    line_g1 = line_df.groupby("timestamp", as_index=False).agg(g1_mean_loading=("loading", "mean"))
    line_g2 = corrected_line_df.groupby("timestamp", as_index=False).agg(g2_mean_loading=("loading", "mean"))
    out = load_g1.merge(load_g2, on="timestamp", how="outer")
    out = out.merge(reserve_g1, on="timestamp", how="outer")
    out = out.merge(reserve_g2, on="timestamp", how="outer")
    out = out.merge(line_g1, on="timestamp", how="outer")
    out = out.merge(line_g2, on="timestamp", how="outer")
    out = out.fillna(0.0)
    out["shed_reduction"] = out["g1_total_shed"] - out["g2_total_shed"]
    out["served_increase"] = out["g2_total_served"] - out["g1_total_served"]
    out["reserve_increase"] = out["g2_total_reserve"] - out["g1_total_reserve"]
    out["mean_loading_reduction"] = out["g1_mean_loading"] - out["g2_mean_loading"]
    return out.sort_values("timestamp").reset_index(drop=True)


def main() -> None:
    args = parse_args()
    auto_correct = False if args.no_auto_correct else True if args.auto_correct else True

    grid_path = Path(args.grid).resolve()
    dispatch_dir = Path(args.dispatch_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    if not grid_path.exists():
        raise FileNotFoundError(f"grid not found: {grid_path}")
    grid = json.loads(grid_path.read_text(encoding="utf-8"))
    adjacency, nodes_by_id, lines_topo_df = _build_graph(grid)

    load_csv = dispatch_dir / "contextual_dispatch_load_shedding.csv"
    unit_csv = dispatch_dir / "contextual_dispatch_unit_schedule.csv"
    line_csv = dispatch_dir / "line_flow.csv"
    strategy_csv = dispatch_dir / "dispatch_strategy_selection.csv"
    warning_dir = dispatch_dir.parent / "stage6_warning"
    line_static_risk_csv = warning_dir / "line_risk_prediction.csv"
    line_hourly_risk_csv = warning_dir / "calibrated_hourly_line_probability.csv"

    load_df = _to_num(_load_required_csv(load_csv), ["demand", "shed", "served", "priority_level", "priority_weight"])
    unit_df = _to_num(_load_required_csv(unit_csv), ["u", "p_selected", "reserve", "startup", "shutdown"])
    line_df = _to_num(_load_required_csv(line_csv), ["flow_mw", "limit_mw", "loading", "overload_flag"])
    strategy_df = pd.read_csv(strategy_csv) if strategy_csv.exists() else pd.DataFrame()
    line_static_risk_df = _load_optional_csv(line_static_risk_csv)
    line_hourly_risk_wide = _load_optional_csv(line_hourly_risk_csv)
    line_hourly_risk_df = pd.DataFrame()
    if not line_hourly_risk_wide.empty and "timestamp" in line_hourly_risk_wide.columns:
        line_hourly_risk_df = line_hourly_risk_wide.melt(id_vars=["timestamp"], var_name="line_id", value_name="hourly_risk_prob")

    if args.horizon_hours > 0:
        if "timestamp" in strategy_df.columns and not strategy_df.empty:
            keep_ts = set(strategy_df["timestamp"].astype(str).head(args.horizon_hours).tolist())
            load_df = load_df[load_df["timestamp"].astype(str).isin(keep_ts)].copy()
            unit_df = unit_df[unit_df["timestamp"].astype(str).isin(keep_ts)].copy()
            line_df = line_df[line_df["timestamp"].astype(str).isin(keep_ts)].copy()
            strategy_df = strategy_df[strategy_df["timestamp"].astype(str).isin(keep_ts)].copy()

    violations: list[dict[str, Any]] = []
    load_stats = validate_load_shedding(load_df=load_df, tol=args.value_tol, violations=violations)
    unit_stats = validate_unit_schedule(unit_df=unit_df, tol=args.value_tol, violations=violations)
    line_stats = validate_line_flow(line_df=line_df, tol=args.value_tol, overload_tol=args.line_overload_tol, violations=violations)

    violations_df = pd.DataFrame(
        violations,
        columns=["category", "severity", "timestamp", "entity", "rule", "value", "threshold", "detail"],
    )
    violations_csv = output_dir / "physics_violations.csv"
    violations_df.to_csv(violations_csv, index=False, encoding="utf-8")

    corrected_count = 0
    corrected_rows = 0
    corrected_load_path = output_dir / "corrected_contextual_dispatch_load_shedding.csv"
    corrected_unit_path = output_dir / "corrected_contextual_dispatch_unit_schedule.csv"
    correction_log_path = output_dir / "correction_log.csv"
    if auto_correct:
        corrected_load_df, correction_log_df = apply_load_correction(load_df=load_df.copy(), tol=args.value_tol)
        corrected_load_df.to_csv(corrected_load_path, index=False, encoding="utf-8")
        unit_df.to_csv(corrected_unit_path, index=False, encoding="utf-8")
        correction_log_df.to_csv(correction_log_path, index=False, encoding="utf-8")
        corrected_rows = int(correction_log_df["is_corrected"].sum())
        corrected_count = int((correction_log_df["shed_correction"].abs() > args.value_tol).sum())

    critical_count = int((violations_df["severity"] == "critical").sum()) if not violations_df.empty else 0
    warning_count = int((violations_df["severity"] == "warning").sum()) if not violations_df.empty else 0
    is_feasible = critical_count == 0

    diagnostic_load_df = corrected_load_df.copy() if auto_correct else load_df.copy()
    line_diag_df = build_line_diagnostics(
        line_df=line_df.copy(),
        line_static_risk_df=line_static_risk_df,
        line_hourly_risk_df=line_hourly_risk_df,
    )
    vulnerable_bus_df = build_vulnerable_buses(
        line_diag_df=line_diag_df,
        load_df=diagnostic_load_df,
        nodes_by_id=nodes_by_id,
        lines_df=lines_topo_df,
    )
    load_area_df = build_load_area_risk(vulnerable_bus_df=vulnerable_bus_df)
    generator_action_df = build_generator_action_candidates(
        unit_df=unit_df.copy(),
        vulnerable_bus_df=vulnerable_bus_df,
        adjacency=adjacency,
    )
    rule_action_df = build_rule_based_actions(
        line_diag_df=line_diag_df,
        vulnerable_bus_df=vulnerable_bus_df,
        load_area_df=load_area_df,
        generator_action_df=generator_action_df,
    )
    rule_corrected_load_df, rule_corrected_unit_df, rule_corrected_line_df, rule_action_log_df, rule_closure_summary = apply_rule_based_corrections(
        load_df=diagnostic_load_df.copy(),
        unit_df=unit_df.copy(),
        line_df=line_df.copy(),
        rule_action_df=rule_action_df,
        generator_action_df=generator_action_df,
        tol=args.value_tol,
    )

    critical_lines_path = output_dir / "critical_lines_hourly.csv"
    vulnerable_buses_path = output_dir / "vulnerable_buses_hourly.csv"
    load_area_path = output_dir / "load_area_risk_hourly.csv"
    generator_actions_path = output_dir / "generator_action_candidates.csv"
    rule_actions_path = output_dir / "rule_based_actions_hourly.csv"
    rule_corrected_load_path = output_dir / "rule_corrected_dispatch_load_shedding.csv"
    rule_corrected_unit_path = output_dir / "rule_corrected_dispatch_unit_schedule.csv"
    rule_corrected_line_path = output_dir / "rule_corrected_line_flow.csv"
    rule_action_log_path = output_dir / "rule_action_execution_log.csv"
    rule_closure_summary_path = output_dir / "rule_closure_summary.json"
    experiment_metrics_path = output_dir / "experiment_metrics_comparison.csv"
    action_type_summary_path = output_dir / "action_type_summary.csv"
    hourly_comparison_path = output_dir / "hourly_closure_comparison.csv"
    line_diag_df.to_csv(critical_lines_path, index=False, encoding="utf-8")
    vulnerable_bus_df.to_csv(vulnerable_buses_path, index=False, encoding="utf-8")
    load_area_df.to_csv(load_area_path, index=False, encoding="utf-8")
    generator_action_df.to_csv(generator_actions_path, index=False, encoding="utf-8")
    rule_action_df.to_csv(rule_actions_path, index=False, encoding="utf-8")
    rule_corrected_load_df.to_csv(rule_corrected_load_path, index=False, encoding="utf-8")
    rule_corrected_unit_df.to_csv(rule_corrected_unit_path, index=False, encoding="utf-8")
    rule_corrected_line_df.to_csv(rule_corrected_line_path, index=False, encoding="utf-8")
    rule_action_log_df.to_csv(rule_action_log_path, index=False, encoding="utf-8")

    base_total_shed = float(pd.to_numeric(diagnostic_load_df["shed"], errors="coerce").fillna(0.0).sum())
    corrected_total_shed = float(pd.to_numeric(rule_corrected_load_df["shed"], errors="coerce").fillna(0.0).sum())
    base_total_served = float(pd.to_numeric(diagnostic_load_df["served"], errors="coerce").fillna(0.0).sum())
    corrected_total_served = float(pd.to_numeric(rule_corrected_load_df["served"], errors="coerce").fillna(0.0).sum())
    base_total_reserve = float(pd.to_numeric(unit_df["reserve"], errors="coerce").fillna(0.0).sum())
    corrected_total_reserve = float(pd.to_numeric(rule_corrected_unit_df["reserve"], errors="coerce").fillna(0.0).sum())
    base_mean_loading = float(pd.to_numeric(line_df["loading"], errors="coerce").fillna(0.0).mean())
    corrected_mean_loading = float(pd.to_numeric(rule_corrected_line_df["loading"], errors="coerce").fillna(0.0).mean())
    rule_closure_report = {
        "mode": "heuristic_closed_loop",
        "baseline": {
            "total_shed": base_total_shed,
            "total_served": base_total_served,
            "total_reserve": base_total_reserve,
            "mean_line_loading": base_mean_loading,
        },
        "corrected": {
            "total_shed": corrected_total_shed,
            "total_served": corrected_total_served,
            "total_reserve": corrected_total_reserve,
            "mean_line_loading": corrected_mean_loading,
        },
        "delta": {
            "shed_reduction": base_total_shed - corrected_total_shed,
            "served_increase": corrected_total_served - base_total_served,
            "reserve_increase": corrected_total_reserve - base_total_reserve,
            "mean_line_loading_reduction": base_mean_loading - corrected_mean_loading,
        },
        **rule_closure_summary,
    }
    rule_closure_summary_path.write_text(json.dumps(rule_closure_report, ensure_ascii=False, indent=2), encoding="utf-8")
    experiment_metrics_df = build_experiment_metrics_comparison(
        load_df=load_df,
        diagnostic_load_df=diagnostic_load_df,
        corrected_load_df=rule_corrected_load_df,
        unit_df=unit_df,
        corrected_unit_df=rule_corrected_unit_df,
        line_df=line_df,
        corrected_line_df=rule_corrected_line_df,
        critical_count=critical_count,
        warning_count=warning_count,
        load_stats=load_stats,
        unit_stats=unit_stats,
        line_stats=line_stats,
        rule_closure_report=rule_closure_report,
    )
    action_type_summary_df = build_action_type_summary(rule_action_df=rule_action_df, rule_action_log_df=rule_action_log_df)
    hourly_comparison_df = build_hourly_closure_comparison(
        diagnostic_load_df=diagnostic_load_df,
        corrected_load_df=rule_corrected_load_df,
        unit_df=unit_df,
        corrected_unit_df=rule_corrected_unit_df,
        line_df=line_df,
        corrected_line_df=rule_corrected_line_df,
    )
    experiment_metrics_df.to_csv(experiment_metrics_path, index=False, encoding="utf-8")
    action_type_summary_df.to_csv(action_type_summary_path, index=False, encoding="utf-8")
    hourly_comparison_df.to_csv(hourly_comparison_path, index=False, encoding="utf-8")

    summary = {
        "module": "Steady-State Physics Validation",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "inputs": {
            "grid": str(grid_path),
            "dispatch_dir": str(dispatch_dir),
            "horizon_hours": int(args.horizon_hours),
        },
        "checks": {
            "load_shedding": load_stats,
            "unit_schedule": unit_stats,
            "line_flow": line_stats,
        },
        "violations": {
            "total": int(len(violations_df)),
            "critical": critical_count,
            "warning": warning_count,
        },
        "auto_correction": {
            "enabled": bool(auto_correct),
            "rows_corrected": corrected_rows,
            "shed_values_corrected": corrected_count,
            "corrected_load_shedding_csv": str(corrected_load_path) if auto_correct else None,
            "corrected_unit_schedule_csv": str(corrected_unit_path) if auto_correct else None,
            "correction_log_csv": str(correction_log_path) if auto_correct else None,
        },
        "physical_feasibility_passed": bool(is_feasible),
        "diagnostic_layer": {
            "critical_lines_rows": int(len(line_diag_df)),
            "vulnerable_buses_rows": int(len(vulnerable_bus_df)),
            "load_area_risk_rows": int(len(load_area_df)),
            "generator_action_candidates_rows": int(len(generator_action_df)),
            "rule_based_actions_rows": int(len(rule_action_df)),
            "rule_action_execution_rows": int(len(rule_action_log_df)),
            "experiment_metrics_rows": int(len(experiment_metrics_df)),
            "action_type_summary_rows": int(len(action_type_summary_df)),
            "hourly_closure_comparison_rows": int(len(hourly_comparison_df)),
        },
        "rule_closure": rule_closure_report,
        "outputs": {
            "physics_violations_csv": str(violations_csv),
            "critical_lines_hourly_csv": str(critical_lines_path),
            "vulnerable_buses_hourly_csv": str(vulnerable_buses_path),
            "load_area_risk_hourly_csv": str(load_area_path),
            "generator_action_candidates_csv": str(generator_actions_path),
            "rule_based_actions_hourly_csv": str(rule_actions_path),
            "rule_corrected_dispatch_load_shedding_csv": str(rule_corrected_load_path),
            "rule_corrected_dispatch_unit_schedule_csv": str(rule_corrected_unit_path),
            "rule_corrected_line_flow_csv": str(rule_corrected_line_path),
            "rule_action_execution_log_csv": str(rule_action_log_path),
            "rule_closure_summary_json": str(rule_closure_summary_path),
            "experiment_metrics_comparison_csv": str(experiment_metrics_path),
            "action_type_summary_csv": str(action_type_summary_path),
            "hourly_closure_comparison_csv": str(hourly_comparison_path),
        },
    }
    summary_path = output_dir / "feasibility_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"summary -> {summary_path}")
    print(f"violations -> {violations_csv}")
    print(f"physical_feasibility_passed={is_feasible}")


if __name__ == "__main__":
    main()
