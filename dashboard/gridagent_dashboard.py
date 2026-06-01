
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st


st.set_page_config(page_title="GridAgent1 Visual Analytics", layout="wide", initial_sidebar_state="expanded")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&display=swap');
    :root { --ink:#0b1f35; --muted:#63788b; --bg0:#f4f8fb; --bg1:#e8f0f8; --risk:#d64b45; --warn:#f08a24; --base:#1b64b0; --ok:#2ca25f; }
    html, body, [class*='css'] { font-family: 'Manrope', sans-serif; color: var(--ink); }
    [data-testid='stAppViewContainer'] { background: radial-gradient(circle at 20% 10%, #ffffff 0%, var(--bg0) 55%, var(--bg1) 100%); }
    [data-testid='stSidebar'] { background: linear-gradient(180deg, #f7fbff 0%, #edf4fa 100%); }
    .ga-card { border:1px solid rgba(11,31,53,.08); border-radius:12px; padding:10px 12px; background:rgba(255,255,255,.9); }
    .ga-kpi-label { font-size:12px; color:var(--muted); }
    .ga-kpi-value { font-size:20px; font-weight:800; }
    .ga-status { border:1px solid rgba(11,31,53,.08); border-radius:14px; padding:10px 14px; background:rgba(255,255,255,.92); margin:8px 0 14px; }
    .ga-status-grid { display:grid; grid-template-columns:repeat(6,minmax(0,1fr)); gap:10px; }
    .ga-status-item { background:#f7fbff; border-radius:10px; padding:8px 10px; }
    .ga-status-key { font-size:11px; color:var(--muted); }
    .ga-status-value { font-size:14px; font-weight:700; }
    .ga-summary { border-left:4px solid var(--base); background:rgba(27,100,176,.06); padding:10px 12px; border-radius:10px; margin:8px 0 16px; }
    </style>
    """,
    unsafe_allow_html=True,
)

ROOT = Path(__file__).resolve().parents[1]
RESULTS_ROOT = ROOT / "results"
DATA_ROOT = ROOT / "data_final"

STRATEGY_COLOR = {"SCUC": "#1b64b0", "Stochastic_UC": "#f08a24", "Robust_UC": "#d64b45"}
RISK_LEVEL_COLOR = {"LOW": "#4e79a7", "MEDIUM": "#f08a24", "HIGH": "#d64b45"}
ACTION_PRIORITY_COLOR = {"low": "#4e79a7", "medium": "#f08a24", "high": "#d64b45", "urgent": "#8b1e1e"}
GROUP_COLOR = {"G0_stage7_raw": "#8c8c8c", "G1_stage8_diagnostic": "#1b64b0", "G2_rule_closed_loop": "#2ca25f"}


def safe_csv(path: Path, parse_dates=None) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path, parse_dates=parse_dates)
    except Exception:
        return pd.DataFrame()


def safe_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def discover_standard_runs() -> list[Path]:
    runs = []
    for d in sorted(RESULTS_ROOT.glob("*_standard")):
        if all((d / p).exists() for p in ["summary", "scenario", "warning", "dispatch", "resilience"]):
            runs.append(d)
    return runs


def discover_framework_runs() -> list[Path]:
    root = RESULTS_ROOT / "gridagent_framework"
    if not root.exists():
        return []
    runs: list[Path] = []
    for d in sorted(root.glob("*")):
        if not d.is_dir():
            continue
        if all((d / p).exists() for p in ["stage2_failure", "stage3_contingency", "stage4_scheduling", "stage6_warning", "stage7_dispatch_optimization"]):
            runs.append(d)
    return runs


def compute_bundle_cache_key(run_path: Path, run_kind: str) -> str:
    paths: list[Path] = []
    if str(run_kind) == "framework":
        paths = [
            run_path / "stage1_wind_pv" / "formal2024" / "typical_scenarios_long.csv",
            run_path / "stage2_failure" / "schloemer" / "line_failure_timeseries_schloemer.csv",
            run_path / "stage3_contingency" / "schloemer" / "contingency_scenarios.csv",
            run_path / "stage4_scheduling" / "schloemer__c3po_ref__rr0p30" / "policy_comparison.csv",
            run_path / "stage5_assessment" / "ewm_topsis_result.csv",
            run_path / "stage6_warning" / "warning_report.json",
            run_path / "stage6_warning" / "model_comparison.csv",
            run_path / "stage7_dispatch_optimization" / "dispatch_optimization_report.json",
            run_path / "stage8_steady_state_physics" / "feasibility_summary.json",
            run_path / "stage8_steady_state_physics" / "rule_closure_summary.json",
        ]
    else:
        paths = [
            run_path / "summary" / "experiment_summary.json",
            run_path / "warning" / "warning_report.json",
            run_path / "warning" / "model_comparison.csv",
            run_path / "dispatch" / "generation_schedule.csv",
            run_path / "resilience" / "topsis_ranking.csv",
        ]
    mtimes = []
    for p in paths:
        if p.exists():
            try:
                mtimes.append(str(int(p.stat().st_mtime)))
            except Exception:
                continue
    if not mtimes:
        return "0"
    return "_".join(mtimes)


def resolve_run_root(raw: str) -> Path:
    if not raw:
        return Path()
    p = Path(raw)
    if p.exists():
        return p
    normalized = raw.replace("\\", "/")
    key = "gridagent1/"
    if key in normalized:
        candidate = ROOT / normalized.split(key, 1)[1]
        if candidate.exists():
            return candidate
    return p


def _pick_fallback_csv(filename: str) -> Path:
    early_warning_root = ROOT / "results" / "early_warning"
    if not early_warning_root.exists():
        return Path()

    preferred_dirs = [
        early_warning_root / "formal2024_metapath_v1_tuned",
        early_warning_root / "formal2024_metapath_v1_compare",
        early_warning_root / "formal2024_metapath_v1_opt1",
    ]
    for d in preferred_dirs:
        p = d / filename
        if p.exists():
            return p

    candidates = [p for p in early_warning_root.rglob(filename) if p.is_file()]
    if not candidates:
        return Path()
    try:
        return max(candidates, key=lambda p: p.stat().st_mtime)
    except Exception:
        return candidates[0]


def load_metapath_attention_for_ui(bundle: dict, warning_report: dict) -> tuple[pd.DataFrame, str]:
    attention = bundle.get("metapath_attention", pd.DataFrame())
    if not attention.empty and {"metapath", "attention_weight"}.issubset(attention.columns):
        return attention.copy(), "当前运行结果"

    training = warning_report.get("training", {}) if isinstance(warning_report, dict) else {}
    attention_mean = training.get("metapath_attention_mean")
    if isinstance(attention_mean, dict) and attention_mean:
        att_df = pd.DataFrame(
            {
                "metapath": [str(k) for k in attention_mean.keys()],
                "attention_weight": [float(v) for v in attention_mean.values()],
            }
        )
        return att_df, "warning_report.training.metapath_attention_mean"

    fallback_path = _pick_fallback_csv("metapath_attention_summary.csv")
    if fallback_path.exists():
        att_df = safe_csv(fallback_path)
        if not att_df.empty and {"metapath", "attention_weight"}.issubset(att_df.columns):
            return att_df, f"回填文件: {fallback_path}"

    return pd.DataFrame(), ""


def _row_from_training(training: dict, default_model: str) -> dict[str, Any] | None:
    if not isinstance(training, dict) or not training:
        return None
    train_metrics = training.get("train_metrics", {})
    val_metrics = training.get("val_metrics", {})
    if not isinstance(train_metrics, dict):
        train_metrics = {}
    if not isinstance(val_metrics, dict):
        val_metrics = {}

    row = {
        "model": str(training.get("model_variant") or default_model),
        "train_mae": train_metrics.get("mae"),
        "train_rmse": train_metrics.get("rmse"),
        "val_mae": val_metrics.get("mae"),
        "val_rmse": val_metrics.get("rmse"),
        "val_high_risk_mae": val_metrics.get("high_risk_mae"),
        "val_top_risk_mae": val_metrics.get("top_risk_mae"),
        "horizon_mae": training.get("horizon_mae"),
        "horizon_rmse": training.get("horizon_rmse"),
        "horizon_high_risk_mae": training.get("horizon_high_risk_mae"),
        "horizon_top_risk_mae": training.get("horizon_top_risk_mae"),
        "best_val_mse": training.get("best_val_mse"),
    }
    has_any = any(
        row[k] is not None
        for k in [
            "train_mae",
            "train_rmse",
            "val_mae",
            "val_rmse",
            "val_high_risk_mae",
            "val_top_risk_mae",
            "horizon_mae",
            "horizon_rmse",
            "horizon_high_risk_mae",
            "horizon_top_risk_mae",
            "best_val_mse",
        ]
    )
    return row if has_any else None


def load_model_comparison_for_ui(bundle: dict, warning_report: dict) -> tuple[pd.DataFrame, str]:
    comp = bundle.get("model_comparison", pd.DataFrame())
    if not comp.empty and "model" in comp.columns:
        return comp.copy(), "当前运行结果"

    comparison = warning_report.get("comparison", {}) if isinstance(warning_report, dict) else {}
    comp_csv = str(comparison.get("comparison_csv", "") or "")
    if comp_csv:
        p = resolve_run_root(comp_csv)
        if p.exists():
            cdf = safe_csv(p)
            if not cdf.empty and "model" in cdf.columns:
                return cdf, f"warning_report.comparison_csv: {p}"

    fallback_path = _pick_fallback_csv("model_comparison.csv")
    if fallback_path.exists():
        cdf = safe_csv(fallback_path)
        if not cdf.empty and "model" in cdf.columns:
            return cdf, f"回填文件: {fallback_path}"

    rows: list[dict[str, Any]] = []
    training = warning_report.get("training", {}) if isinstance(warning_report, dict) else {}
    row_main = _row_from_training(training, "current_run")
    if row_main:
        rows.append(row_main)
    row_cmp = _row_from_training(comparison.get("comparison_model_training", {}), "baseline_gnn")
    if row_cmp:
        if row_main and row_cmp.get("model") == row_main.get("model"):
            row_cmp["model"] = "baseline_gnn"
        rows.append(row_cmp)
    if rows:
        return pd.DataFrame(rows), "warning_report(training字段回填)"

    return pd.DataFrame(), ""


def load_node_weather_for_ui(bundle: dict, warning_report: dict) -> tuple[dict[str, pd.DataFrame], dict[str, str]]:
    out_frames: dict[str, pd.DataFrame] = {
        "timeseries": bundle.get("node_weather_timeseries", pd.DataFrame()),
        "horizon": bundle.get("node_weather_horizon", pd.DataFrame()),
        "summary": bundle.get("node_weather_summary", pd.DataFrame()),
    }
    source: dict[str, str] = {}

    name_to_key = {
        "timeseries": "node_weather_timeseries_csv",
        "horizon": "node_weather_horizon_csv",
        "summary": "node_weather_summary_csv",
    }
    for name, key in name_to_key.items():
        if not out_frames[name].empty:
            source[name] = "当前运行结果"
            continue
        p_raw = str(warning_report.get("outputs", {}).get(key, "") or "") if isinstance(warning_report, dict) else ""
        if p_raw:
            p = resolve_run_root(p_raw)
            if p.exists():
                parse_dates = ["timestamp"] if name in {"timeseries", "horizon"} else None
                df = safe_csv(p, parse_dates=parse_dates)
                if not df.empty:
                    out_frames[name] = df
                    source[name] = f"warning_report.outputs: {p}"
                    continue
        fallback_name = f"node_weather_{name}.csv"
        fp = _pick_fallback_csv(fallback_name)
        if fp.exists():
            parse_dates = ["timestamp"] if name in {"timeseries", "horizon"} else None
            df = safe_csv(fp, parse_dates=parse_dates)
            if not df.empty:
                out_frames[name] = df
                source[name] = f"回填文件: {fp}"

    return out_frames, source


def normalize(s: pd.Series) -> pd.Series:
    v = pd.to_numeric(s, errors="coerce")
    if v.isna().all():
        return pd.Series(np.zeros(len(s)), index=s.index)
    lo, hi = v.min(), v.max()
    if hi - lo < 1e-12:
        return pd.Series(np.zeros(len(s)), index=s.index)
    return (v - lo) / (hi - lo)


def _convert_wind_solar_from_typical(typical_long: pd.DataFrame) -> pd.DataFrame:
    if typical_long.empty:
        return pd.DataFrame()
    required = {"scenario_id", "timestamp", "wind", "pv"}
    if not required.issubset(typical_long.columns):
        return pd.DataFrame()
    tmp = typical_long.copy()
    tmp["timestamp"] = pd.to_datetime(tmp["timestamp"], errors="coerce")
    tmp["scenario_id"] = pd.to_numeric(tmp["scenario_id"], errors="coerce").astype("Int64")
    tmp["wind"] = pd.to_numeric(tmp["wind"], errors="coerce")
    tmp["pv"] = pd.to_numeric(tmp["pv"], errors="coerce")
    tmp = tmp.dropna(subset=["timestamp", "scenario_id"]).copy()
    tmp["scenario_id"] = tmp["scenario_id"].astype(int)
    if tmp.empty:
        return pd.DataFrame()

    wind_piv = tmp.pivot_table(index="timestamp", columns="scenario_id", values="wind", aggfunc="mean")
    pv_piv = tmp.pivot_table(index="timestamp", columns="scenario_id", values="pv", aggfunc="mean")
    wind_piv = wind_piv.sort_index().sort_index(axis=1)
    pv_piv = pv_piv.sort_index().sort_index(axis=1)
    wind_piv.columns = [f"wind_s{int(c)}" for c in wind_piv.columns]
    pv_piv.columns = [f"solar_s{int(c)}" for c in pv_piv.columns]
    out = pd.concat([wind_piv, pv_piv], axis=1).sort_index()
    return out.reset_index()


def _pivot_generation_from_contextual(unit_sched: pd.DataFrame) -> pd.DataFrame:
    if unit_sched.empty or not {"timestamp", "unit_id", "p_selected"}.issubset(unit_sched.columns):
        return pd.DataFrame()
    tmp = unit_sched.copy()
    tmp["timestamp"] = pd.to_datetime(tmp["timestamp"], errors="coerce")
    tmp["p_selected"] = pd.to_numeric(tmp["p_selected"], errors="coerce").fillna(0.0)
    tmp["unit_id"] = tmp["unit_id"].astype(str)
    tmp = tmp.dropna(subset=["timestamp"]).copy()
    if tmp.empty:
        return pd.DataFrame()
    piv = tmp.pivot_table(index="timestamp", columns="unit_id", values="p_selected", aggfunc="sum")
    return piv.sort_index().reset_index()


def _build_reserve_from_contextual(unit_sched: pd.DataFrame) -> pd.DataFrame:
    if unit_sched.empty or not {"timestamp", "reserve"}.issubset(unit_sched.columns):
        return pd.DataFrame()
    tmp = unit_sched.copy()
    tmp["timestamp"] = pd.to_datetime(tmp["timestamp"], errors="coerce")
    tmp["reserve"] = pd.to_numeric(tmp["reserve"], errors="coerce").fillna(0.0)
    tmp = tmp.dropna(subset=["timestamp"]).copy()
    if tmp.empty:
        return pd.DataFrame()
    out = tmp.groupby("timestamp", as_index=False)["reserve"].sum().rename(columns={"reserve": "reserve_up"})
    out["reserve_down"] = 0.0
    return out.sort_values("timestamp")


def _build_shedding_from_contextual(load_shed: pd.DataFrame) -> pd.DataFrame:
    if load_shed.empty or not {"timestamp", "shed"}.issubset(load_shed.columns):
        return pd.DataFrame()
    tmp = load_shed.copy()
    tmp["timestamp"] = pd.to_datetime(tmp["timestamp"], errors="coerce")
    tmp["shed"] = pd.to_numeric(tmp["shed"], errors="coerce").fillna(0.0)
    tmp = tmp.dropna(subset=["timestamp"]).copy()
    if tmp.empty:
        return pd.DataFrame()
    out = tmp.groupby("timestamp", as_index=False)["shed"].sum().rename(columns={"shed": "shed_MW"})
    return out.sort_values("timestamp")


def _read_grid_from_report(report: dict) -> dict:
    if not isinstance(report, dict):
        return {}
    grid_raw = str(report.get("inputs", {}).get("grid", "") or "")
    if not grid_raw:
        return {}
    p = resolve_run_root(grid_raw)
    if not p.exists():
        return {}
    return safe_json(p)


def _load_framework_bundle(run_root: Path) -> dict:
    stage1 = run_root / "stage1_wind_pv" / "formal2024"
    stage2 = run_root / "stage2_failure" / "schloemer"
    stage3 = run_root / "stage3_contingency" / "schloemer"
    stage4 = run_root / "stage4_scheduling" / "schloemer__c3po_ref__rr0p30"
    stage5 = run_root / "stage5_assessment"
    stage6 = run_root / "stage6_warning"
    stage7 = run_root / "stage7_dispatch_optimization"
    stage8 = run_root / "stage8_steady_state_physics"

    typical_long = safe_csv(stage1 / "typical_scenarios_long.csv", parse_dates=["timestamp"])
    wind_solar = _convert_wind_solar_from_typical(typical_long)

    component_failure_raw = safe_csv(stage2 / "line_failure_timeseries_schloemer.csv")
    component_failure = pd.DataFrame()
    if not component_failure_raw.empty:
        component_failure = component_failure_raw.rename(
            columns={"timestamp": "hour", "line_id": "line", "p_line": "failure_prob"}
        )
        if "hour" in component_failure.columns:
            component_failure["hour"] = pd.to_datetime(component_failure["hour"], errors="coerce")

    contingency = safe_csv(stage3 / "contingency_scenarios.csv", parse_dates=["timestamp"])
    line_risk = safe_csv(stage6 / "line_risk_prediction.csv")
    nk_risk = safe_csv(stage6 / "nk_failure_risk.csv")
    critical_risk = safe_csv(stage6 / "critical_load_risk.csv")

    contextual_unit = safe_csv(stage7 / "contextual_dispatch_unit_schedule.csv", parse_dates=["timestamp"])
    generation = _pivot_generation_from_contextual(contextual_unit)
    reserve = _build_reserve_from_contextual(contextual_unit)

    contextual_load = safe_csv(stage7 / "contextual_dispatch_load_shedding.csv", parse_dates=["timestamp"])
    load_shedding = _build_shedding_from_contextual(contextual_load)
    line_flow = safe_csv(stage7 / "line_flow.csv", parse_dates=["timestamp"])

    topsis = safe_csv(stage5 / "ewm_topsis_result.csv")
    if not topsis.empty:
        if "TOPSIS_Score" in topsis.columns:
            topsis["score"] = pd.to_numeric(topsis["TOPSIS_Score"], errors="coerce")
        if "TOPSIS_Rank" in topsis.columns:
            topsis["rank"] = pd.to_numeric(topsis["TOPSIS_Rank"], errors="coerce")

    resilience = safe_csv(stage5 / "indicator_table.csv")
    summary_indicator = safe_csv(stage5 / "indicator_table.csv")
    warning_report = safe_json(stage6 / "warning_report.json")
    dispatch_report = safe_json(stage7 / "dispatch_optimization_report.json")
    multi_report = safe_json(stage5 / "multi_criteria_report.json")
    physics_summary = safe_json(stage8 / "feasibility_summary.json")
    rule_closure_summary = safe_json(stage8 / "rule_closure_summary.json")

    n_scen = int(contingency["scenario_id"].nunique()) if not contingency.empty and "scenario_id" in contingency.columns else None
    summary = {
        "mode": "framework_stagewise",
        "run_root": str(run_root),
        "selected_chain": {
            "failure_model": "schloemer",
            "contingency_method": "c3po_ref",
            "reserve_ratio": 0.30,
            "n_scenarios": n_scen,
        },
    }

    topology = _read_grid_from_report(warning_report)
    if not topology:
        topology = _read_grid_from_report(dispatch_report)
    if not topology:
        topology = safe_json(DATA_ROOT / "formal_guangdong_2024" / "grid_topology.json")
    if not topology:
        topology = safe_json(DATA_ROOT / "grid_topology.json")

    out = {
        "standard": run_root,
        "summary": summary,
        "summary_indicator": summary_indicator,
        "wind_solar": wind_solar,
        "component_failure": component_failure,
        "contingency": contingency,
        "line_risk": line_risk,
        "nk_risk": nk_risk,
        "critical_risk": critical_risk,
        "generation": generation,
        "line_flow": line_flow,
        "load_shedding": load_shedding,
        "reserve": reserve,
        "resilience": resilience,
        "topsis": topsis,
        "run_root": run_root,
        "hourly_line_prob": safe_csv(stage6 / "calibrated_hourly_line_probability.csv", parse_dates=["timestamp"]),
        "metapath_attention": safe_csv(stage6 / "metapath_attention_summary.csv"),
        "model_comparison": safe_csv(stage6 / "model_comparison.csv"),
        "node_weather_timeseries": safe_csv(stage6 / "node_weather_timeseries.csv", parse_dates=["timestamp"]),
        "node_weather_horizon": safe_csv(stage6 / "node_weather_horizon.csv", parse_dates=["timestamp"]),
        "node_weather_summary": safe_csv(stage6 / "node_weather_summary.csv"),
        "warning_report": warning_report,
        "strategy_selection": safe_csv(stage7 / "dispatch_strategy_selection.csv", parse_dates=["timestamp"]),
        "dispatch_report": dispatch_report,
        "multi_report": multi_report,
        "context_load_shedding": contextual_load,
        "topology": topology,
        "physics_summary": physics_summary,
        "rule_closure_summary": rule_closure_summary,
        "critical_lines_hourly": safe_csv(stage8 / "critical_lines_hourly.csv", parse_dates=["timestamp"]),
        "vulnerable_buses_hourly": safe_csv(stage8 / "vulnerable_buses_hourly.csv", parse_dates=["timestamp"]),
        "load_area_risk_hourly": safe_csv(stage8 / "load_area_risk_hourly.csv", parse_dates=["timestamp"]),
        "generator_action_candidates": safe_csv(stage8 / "generator_action_candidates.csv", parse_dates=["timestamp"]),
        "rule_based_actions_hourly": safe_csv(stage8 / "rule_based_actions_hourly.csv", parse_dates=["timestamp"]),
        "rule_corrected_dispatch_load_shedding": safe_csv(stage8 / "rule_corrected_dispatch_load_shedding.csv", parse_dates=["timestamp"]),
        "rule_corrected_dispatch_unit_schedule": safe_csv(stage8 / "rule_corrected_dispatch_unit_schedule.csv", parse_dates=["timestamp"]),
        "rule_corrected_line_flow": safe_csv(stage8 / "rule_corrected_line_flow.csv", parse_dates=["timestamp"]),
        "rule_action_execution_log": safe_csv(stage8 / "rule_action_execution_log.csv", parse_dates=["timestamp"]),
        "experiment_metrics_comparison": safe_csv(stage8 / "experiment_metrics_comparison.csv"),
        "action_type_summary": safe_csv(stage8 / "action_type_summary.csv"),
        "hourly_closure_comparison": safe_csv(stage8 / "hourly_closure_comparison.csv", parse_dates=["timestamp"]),
    }
    return out


@st.cache_data(show_spinner=False)
def load_bundle(run_dir: str, run_kind: str = "standard", cache_key: str = "0") -> dict:
    _ = cache_key
    if str(run_kind) == "framework":
        out = _load_framework_bundle(Path(run_dir))
    else:
        standard = Path(run_dir)
        out = {
            "standard": standard,
            "summary": safe_json(standard / "summary" / "experiment_summary.json"),
            "summary_indicator": safe_csv(standard / "summary" / "indicator_table.csv"),
            "wind_solar": safe_csv(standard / "scenario" / "wind_solar_scenarios.csv", parse_dates=["timestamp"]),
            "component_failure": safe_csv(standard / "scenario" / "component_failure_prob.csv"),
            "contingency": safe_csv(standard / "scenario" / "contingency_scenarios.csv", parse_dates=["timestamp"]),
            "line_risk": safe_csv(standard / "warning" / "line_risk_prediction.csv"),
            "nk_risk": safe_csv(standard / "warning" / "nk_failure_risk.csv"),
            "critical_risk": safe_csv(standard / "warning" / "critical_load_risk.csv"),
            "generation": safe_csv(standard / "dispatch" / "generation_schedule.csv", parse_dates=["timestamp"]),
            "line_flow": safe_csv(standard / "dispatch" / "line_flow.csv", parse_dates=["timestamp"]),
            "load_shedding": safe_csv(standard / "dispatch" / "load_shedding.csv", parse_dates=["timestamp"]),
            "reserve": safe_csv(standard / "dispatch" / "reserve_schedule.csv", parse_dates=["timestamp"]),
            "resilience": safe_csv(standard / "resilience" / "resilience_metrics.csv"),
            "topsis": safe_csv(standard / "resilience" / "topsis_ranking.csv"),
        }

        run_root = resolve_run_root(out["summary"].get("run_root", ""))
        out["run_root"] = run_root
        out["hourly_line_prob"] = safe_csv(run_root / "stage6_warning" / "calibrated_hourly_line_probability.csv", parse_dates=["timestamp"])
        out["metapath_attention"] = safe_csv(run_root / "stage6_warning" / "metapath_attention_summary.csv")
        out["model_comparison"] = safe_csv(run_root / "stage6_warning" / "model_comparison.csv")
        out["node_weather_timeseries"] = safe_csv(run_root / "stage6_warning" / "node_weather_timeseries.csv", parse_dates=["timestamp"])
        out["node_weather_horizon"] = safe_csv(run_root / "stage6_warning" / "node_weather_horizon.csv", parse_dates=["timestamp"])
        out["node_weather_summary"] = safe_csv(run_root / "stage6_warning" / "node_weather_summary.csv")
        out["warning_report"] = safe_json(run_root / "stage6_warning" / "warning_report.json")
        out["strategy_selection"] = safe_csv(run_root / "stage7_dispatch_optimization" / "dispatch_strategy_selection.csv", parse_dates=["timestamp"])
        out["dispatch_report"] = safe_json(run_root / "stage7_dispatch_optimization" / "dispatch_optimization_report.json")
        out["multi_report"] = safe_json(run_root / "stage5_assessment" / "multi_criteria_report.json")
        out["context_load_shedding"] = safe_csv(run_root / "stage7_dispatch_optimization" / "contextual_dispatch_load_shedding.csv", parse_dates=["timestamp"])
        out["physics_summary"] = safe_json(run_root / "stage8_steady_state_physics" / "feasibility_summary.json")
        out["rule_closure_summary"] = safe_json(run_root / "stage8_steady_state_physics" / "rule_closure_summary.json")
        out["critical_lines_hourly"] = safe_csv(run_root / "stage8_steady_state_physics" / "critical_lines_hourly.csv", parse_dates=["timestamp"])
        out["vulnerable_buses_hourly"] = safe_csv(run_root / "stage8_steady_state_physics" / "vulnerable_buses_hourly.csv", parse_dates=["timestamp"])
        out["load_area_risk_hourly"] = safe_csv(run_root / "stage8_steady_state_physics" / "load_area_risk_hourly.csv", parse_dates=["timestamp"])
        out["generator_action_candidates"] = safe_csv(run_root / "stage8_steady_state_physics" / "generator_action_candidates.csv", parse_dates=["timestamp"])
        out["rule_based_actions_hourly"] = safe_csv(run_root / "stage8_steady_state_physics" / "rule_based_actions_hourly.csv", parse_dates=["timestamp"])
        out["rule_corrected_dispatch_load_shedding"] = safe_csv(run_root / "stage8_steady_state_physics" / "rule_corrected_dispatch_load_shedding.csv", parse_dates=["timestamp"])
        out["rule_corrected_dispatch_unit_schedule"] = safe_csv(run_root / "stage8_steady_state_physics" / "rule_corrected_dispatch_unit_schedule.csv", parse_dates=["timestamp"])
        out["rule_corrected_line_flow"] = safe_csv(run_root / "stage8_steady_state_physics" / "rule_corrected_line_flow.csv", parse_dates=["timestamp"])
        out["rule_action_execution_log"] = safe_csv(run_root / "stage8_steady_state_physics" / "rule_action_execution_log.csv", parse_dates=["timestamp"])
        out["experiment_metrics_comparison"] = safe_csv(run_root / "stage8_steady_state_physics" / "experiment_metrics_comparison.csv")
        out["action_type_summary"] = safe_csv(run_root / "stage8_steady_state_physics" / "action_type_summary.csv")
        out["hourly_closure_comparison"] = safe_csv(run_root / "stage8_steady_state_physics" / "hourly_closure_comparison.csv", parse_dates=["timestamp"])
        if out["metapath_attention"].empty:
            out["metapath_attention"] = safe_csv(standard / "warning" / "metapath_attention_summary.csv")
        if out["model_comparison"].empty:
            out["model_comparison"] = safe_csv(standard / "warning" / "model_comparison.csv")
        if out["node_weather_timeseries"].empty:
            out["node_weather_timeseries"] = safe_csv(standard / "warning" / "node_weather_timeseries.csv", parse_dates=["timestamp"])
        if out["node_weather_horizon"].empty:
            out["node_weather_horizon"] = safe_csv(standard / "warning" / "node_weather_horizon.csv", parse_dates=["timestamp"])
        if out["node_weather_summary"].empty:
            out["node_weather_summary"] = safe_csv(standard / "warning" / "node_weather_summary.csv")
        if not out["warning_report"]:
            out["warning_report"] = safe_json(standard / "warning" / "warning_report.json")
        out["topology"] = safe_json(DATA_ROOT / "formal_guangdong_2024" / "grid_topology.json")
        if not out["topology"]:
            out["topology"] = safe_json(DATA_ROOT / "grid_topology.json")

    if not out["component_failure"].empty and "hour" in out["component_failure"].columns:
        out["component_failure"]["hour"] = pd.to_datetime(out["component_failure"]["hour"], errors="coerce")
    if not out["line_flow"].empty:
        out["line_flow"]["loading"] = pd.to_numeric(out["line_flow"]["loading"], errors="coerce")
        if "overload_flag" in out["line_flow"].columns:
            out["line_flow"]["overload_bool"] = out["line_flow"]["overload_flag"].astype(str).str.lower().isin(["1", "true", "yes"])
    if not out["load_shedding"].empty:
        if "shed_MW" in out["load_shedding"].columns:
            out["load_shedding"]["shed_MW"] = pd.to_numeric(out["load_shedding"]["shed_MW"], errors="coerce").fillna(0.0)
        elif "shed" in out["load_shedding"].columns:
            out["load_shedding"]["shed_MW"] = pd.to_numeric(out["load_shedding"]["shed"], errors="coerce").fillna(0.0)
    return out


def strategy_hourly(bundle: dict) -> pd.DataFrame:
    s = bundle.get("strategy_selection", pd.DataFrame())
    if not s.empty:
        out = s.copy()
        out["timestamp"] = pd.to_datetime(out["timestamp"], errors="coerce")
        out["hour_index"] = pd.to_numeric(out.get("hour_index"), errors="coerce")
        if out["hour_index"].isna().all():
            out["hour_index"] = ((out["timestamp"] - out["timestamp"].min()).dt.total_seconds() / 3600).astype(int)
        out["hourly_line_risk"] = pd.to_numeric(out.get("hourly_line_risk"), errors="coerce")
        return out.sort_values("timestamp")

    lf = bundle.get("line_flow", pd.DataFrame())
    if lf.empty:
        return pd.DataFrame()
    out = (
        lf.sort_values("timestamp")
        .groupby("timestamp", as_index=False)
        .agg(selected_strategy=("selected_strategy", "first"), hourly_line_risk=("loading", "max"))
    )
    out["hour_index"] = ((out["timestamp"] - out["timestamp"].min()).dt.total_seconds() / 3600).astype(int)
    out["reason"] = "derived_from_line_flow"
    return out


def metric_card(label: str, value: str) -> None:
    st.markdown(
        f"""
        <div class='ga-card'>
          <div class='ga-kpi-label'>{label}</div>
          <div class='ga-kpi-value'>{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_bar(items: list[tuple[str, str]]) -> None:
    cards = "".join(
        [
            f"<div class='ga-status-item'><div class='ga-status-key'>{k}</div><div class='ga-status-value'>{v}</div></div>"
            for k, v in items
        ]
    )
    st.markdown(f"<div class='ga-status'><div class='ga-status-grid'>{cards}</div></div>", unsafe_allow_html=True)


def render_summary(text: str) -> None:
    st.markdown(f"<div class='ga-summary'>{text}</div>", unsafe_allow_html=True)


def render_dataframe_panel(title: str, df: pd.DataFrame, expanded: bool = False) -> None:
    if df.empty:
        return
    with st.expander(title, expanded=expanded):
        st.dataframe(df, use_container_width=True, hide_index=True)

def build_kpis(bundle: dict, sh: pd.DataFrame) -> dict:
    summary = bundle.get("summary", {})
    chain = summary.get("selected_chain", {}) if isinstance(summary, dict) else {}
    n_scenarios = chain.get("n_scenarios")
    if n_scenarios is None and not bundle["contingency"].empty and "scenario_id" in bundle["contingency"].columns:
        n_scenarios = int(bundle["contingency"]["scenario_id"].nunique())

    split = "n/a"
    if not sh.empty:
        c = sh["selected_strategy"].value_counts()
        split = " / ".join([f"{k} {v}h" for k, v in c.items()])

    overload = int(bundle["line_flow"]["overload_bool"].sum()) if not bundle["line_flow"].empty else 0
    best = "n/a"
    if not bundle["topsis"].empty:
        t = bundle["topsis"].copy()
        t["rank"] = pd.to_numeric(t["rank"], errors="coerce")
        best = str(t.sort_values("rank").iloc[0]["policy"])

    return {
        "运行模式": str(summary.get("mode", "baseline")),
        "运行链路": f"{chain.get('failure_model', 'n/a')} + {chain.get('contingency_method', 'n/a')}",
        "场景数": str(n_scenarios),
        "调度模型分配": split,
        "线路过载次数": str(overload),
        "最优策略": best,
    }


def build_risk_hourly(bundle: dict) -> pd.DataFrame:
    cf = bundle.get("component_failure", pd.DataFrame())
    if cf.empty:
        return pd.DataFrame()
    cf = cf.copy()
    cf["line_risk"] = pd.to_numeric(cf["failure_prob"], errors="coerce")
    line = cf.groupby("hour", as_index=False)["line_risk"].mean().rename(columns={"hour": "timestamp"})

    cont = bundle.get("contingency", pd.DataFrame())
    if cont.empty:
        line["nk_risk"] = np.nan
        line["critical_risk"] = np.nan
    else:
        tmp = cont.copy()
        tmp["outage_line_count"] = pd.to_numeric(tmp["outage_line_count"], errors="coerce")
        tmp["disconnected_load_count"] = pd.to_numeric(tmp["disconnected_load_count"], errors="coerce")
        nk = tmp.groupby("timestamp", as_index=False)["outage_line_count"].mean().rename(columns={"outage_line_count": "nk_risk"})
        cr = tmp.groupby("timestamp", as_index=False)["disconnected_load_count"].mean().rename(columns={"disconnected_load_count": "critical_risk"})
        line = line.merge(nk, on="timestamp", how="left").merge(cr, on="timestamp", how="left")

    line["line_norm"] = normalize(line["line_risk"])
    line["nk_norm"] = normalize(line["nk_risk"])
    line["critical_norm"] = normalize(line["critical_risk"])
    return line.sort_values("timestamp")


def fig_strip(sh: pd.DataFrame, title: str) -> go.Figure:
    if sh.empty:
        return go.Figure()
    mapping = {"SCUC": 0, "Stochastic_UC": 1, "Robust_UC": 2}
    labels = sh["selected_strategy"].fillna("SCUC").tolist()
    z = [[mapping.get(x, 0) for x in labels]]
    x = sh["timestamp"].dt.strftime("%H:%M")
    fig = go.Figure(
        go.Heatmap(
            z=z,
            x=x,
            y=["optimizer"],
            text=[labels],
            showscale=False,
            hovertemplate="hour=%{x}<br>strategy=%{text}<extra></extra>",
            colorscale=[
                [0.0, STRATEGY_COLOR["SCUC"]], [0.33, STRATEGY_COLOR["SCUC"]],
                [0.34, STRATEGY_COLOR["Stochastic_UC"]], [0.66, STRATEGY_COLOR["Stochastic_UC"]],
                [0.67, STRATEGY_COLOR["Robust_UC"]], [1.0, STRATEGY_COLOR["Robust_UC"]],
            ],
        )
    )
    fig.update_layout(title=title, height=150, margin=dict(l=10, r=10, t=38, b=10))
    return fig


def fig_topology(topology: dict, line_risk: pd.DataFrame, critical: pd.DataFrame, threshold: float) -> go.Figure:
    if not topology:
        return go.Figure()

    lr: dict[str, float] = {}
    if not line_risk.empty and {"line_id", "risk_prob"}.issubset(line_risk.columns):
        t = line_risk.copy()
        t["line_id"] = t["line_id"].astype(str)
        t["risk_prob"] = pd.to_numeric(t["risk_prob"], errors="coerce").fillna(0.0)
        lr = dict(zip(t["line_id"], t["risk_prob"]))

    nr: dict[int, float] = {}
    if not critical.empty and {"node", "outage_prob"}.issubset(critical.columns):
        c = critical.copy()
        c["outage_prob"] = pd.to_numeric(c["outage_prob"], errors="coerce")
        for _, row in c.iterrows():
            name = str(row["node"])
            if name.startswith("load_bus_"):
                try:
                    nr[int(name.split("_")[-1])] = float(row["outage_prob"])
                except Exception:
                    pass

    fig = go.Figure()
    label_low_x: list[float] = []
    label_low_y: list[float] = []
    label_low_text: list[str] = []
    label_high_x: list[float] = []
    label_high_y: list[float] = []
    label_high_text: list[str] = []
    for ln in topology.get("lines", []):
        lid = str(ln.get("id"))
        prob = float(lr.get(lid, 0.0))
        fx = float(ln.get("from_lon", 0.0) or 0.0)
        fy = float(ln.get("from_lat", 0.0) or 0.0)
        tx = float(ln.get("to_lon", 0.0) or 0.0)
        ty = float(ln.get("to_lat", 0.0) or 0.0)
        is_high = prob >= threshold
        fig.add_trace(
            go.Scatter(
                x=[fx, tx],
                y=[fy, ty],
                mode="lines",
                line=dict(color="#d64b45" if is_high else "#8aa4be", width=4 if is_high else 1.6),
                hovertemplate=f"{lid}<br>risk={prob:.3f}<extra></extra>",
                showlegend=False,
            )
        )

        mx = (fx + tx) / 2.0
        my = (fy + ty) / 2.0
        if is_high:
            label_high_x.append(mx)
            label_high_y.append(my)
            label_high_text.append(lid)
        else:
            label_low_x.append(mx)
            label_low_y.append(my)
            label_low_text.append(lid)

    # 线路编号标注（先画淡色全量，再画高亮重点），便于直观看到 L1/L2 等编号。
    if label_low_x:
        fig.add_trace(
            go.Scatter(
                x=label_low_x,
                y=label_low_y,
                mode="text",
                text=label_low_text,
                textposition="middle center",
                textfont=dict(size=10, color="#8fa1b3"),
                hoverinfo="skip",
                showlegend=False,
            )
        )
    if label_high_x:
        fig.add_trace(
            go.Scatter(
                x=label_high_x,
                y=label_high_y,
                mode="text",
                text=label_high_text,
                textposition="middle center",
                textfont=dict(size=12, color="#0b1f35"),
                hoverinfo="skip",
                showlegend=False,
            )
        )

    nodes = pd.DataFrame(topology.get("nodes", []))
    if not nodes.empty:
        nodes["risk"] = nodes["id"].map(nr).fillna(0.0)
        nodes["node"] = "N" + nodes["id"].astype(str)
        fig.add_trace(
            go.Scatter(
                x=nodes["lon"], y=nodes["lat"], mode="markers+text", text=nodes["node"], textposition="top center",
                marker=dict(size=10, color=nodes["risk"], colorscale="YlOrRd", cmin=0, cmax=max(0.15, nodes["risk"].max())),
                hovertemplate="%{text}<br>risk=%{marker.color:.3f}<extra></extra>", showlegend=False,
            )
        )

    fig.update_layout(title="电网风险拓扑图", height=380, margin=dict(l=10, r=10, t=40, b=10))
    return fig


def build_metapath_neighbors(topology: dict, warning_report: dict, topk: int) -> dict[str, Any]:
    lines = topology.get("lines", [])
    if not lines:
        return {}

    line_ids = [str(ln.get("id", f"L{i}")) for i, ln in enumerate(lines)]
    from_bus = np.array([int(ln.get("from", -1)) for ln in lines], dtype=int)
    to_bus = np.array([int(ln.get("to", -1)) for ln in lines], dtype=int)
    n_edge = len(line_ids)

    bus_to_lines: dict[int, list[int]] = {}
    for idx, (u, v) in enumerate(zip(from_bus.tolist(), to_bus.tolist(), strict=False)):
        bus_to_lines.setdefault(int(u), []).append(int(idx))
        bus_to_lines.setdefault(int(v), []).append(int(idx))

    line_adj: dict[int, set[int]] = {i: set() for i in range(n_edge)}
    for line_group in bus_to_lines.values():
        uniq = sorted(set(int(x) for x in line_group))
        for i in range(len(uniq)):
            for j in range(i + 1, len(uniq)):
                a = int(uniq[i])
                b = int(uniq[j])
                line_adj[a].add(b)
                line_adj[b].add(a)

    inf = float(n_edge + 10)
    line_dist = np.full((n_edge, n_edge), inf, dtype=float)
    for i in range(n_edge):
        queue = [(i, 0)]
        visited = {i}
        while queue:
            node, d = queue.pop(0)
            line_dist[i, node] = float(d)
            if d >= 4:
                continue
            for nb in line_adj.get(node, set()):
                if nb in visited:
                    continue
                visited.add(nb)
                queue.append((nb, d + 1))

    share_bus_candidates = [sorted(line_adj.get(i, set())) for i in range(n_edge)]

    two_hop_candidates: list[list[int]] = []
    for i in range(n_edge):
        cands = [j for j in range(n_edge) if j != i and abs(line_dist[i, j] - 2.0) < 1e-9]
        if not cands:
            cands = share_bus_candidates[i]
        two_hop_candidates.append(cands)

    generators = topology.get("generators", [])
    source_special = {
        int(g["bus"])
        for g in generators
        if "bus" in g and str(g.get("type", "")).lower() in {"thermal", "slack", "ext_grid"}
    }
    source_positive = {
        int(g["bus"])
        for g in generators
        if "bus" in g and float(g.get("capacity", 0.0) or 0.0) > 0.0
    }
    source_buses = sorted(source_special | source_positive)

    primary_load_buses: list[int] = []
    load_priority_path = ""
    if isinstance(warning_report, dict):
        load_priority_path = str(warning_report.get("inputs", {}).get("load_priority_csv", "") or "")
    if load_priority_path:
        p = Path(load_priority_path)
        if not p.is_absolute():
            p = (ROOT / load_priority_path).resolve()
        if p.exists():
            lp = safe_csv(p)
            if not lp.empty and {"load_bus", "priority_level"}.issubset(lp.columns):
                prim = lp[pd.to_numeric(lp["priority_level"], errors="coerce") == 1]["load_bus"]
                primary_load_buses = sorted(set(pd.to_numeric(prim, errors="coerce").dropna().astype(int).tolist()))
    if not primary_load_buses:
        load_nodes = sorted(int(n.get("id")) for n in topology.get("nodes", []) if str(n.get("type", "")).lower() == "load")
        k = max(1, int(np.ceil(0.30 * len(load_nodes)))) if load_nodes else 0
        primary_load_buses = load_nodes[:k]

    def build_anchor_bridge(anchor_buses: list[int]) -> list[list[int]]:
        anchor_lines: set[int] = set()
        for b in anchor_buses:
            anchor_lines.update(int(x) for x in bus_to_lines.get(int(b), []))

        out: list[list[int]] = []
        for i in range(n_edge):
            if not anchor_lines:
                out.append(list(share_bus_candidates[i]))
                continue

            reachable = [(line_dist[i, j], j) for j in anchor_lines if line_dist[i, j] < inf]
            if not reachable:
                out.append(list(share_bus_candidates[i]))
                continue

            d_min = min(d for d, _ in reachable)
            near = [j for d, j in reachable if d <= d_min + 1.0]
            cands = set(int(j) for j in near)
            for j in near:
                cands.update(int(u) for u in line_adj.get(int(j), set()))
            if not cands:
                cands.update(int(j) for j in share_bus_candidates[i])
            out.append(sorted(cands))
        return out

    source_bridge_candidates = build_anchor_bridge(anchor_buses=source_buses)
    primary_load_bridge_candidates = build_anchor_bridge(anchor_buses=primary_load_buses)

    metapath_names = [
        "share_bus",
        "two_hop_topology",
        "source_bridge",
        "primary_load_bridge",
    ]
    candidates_by_path = [
        share_bus_candidates,
        two_hop_candidates,
        source_bridge_candidates,
        primary_load_bridge_candidates,
    ]

    k = max(int(topk), 1)
    metapath_index = np.full((len(metapath_names), n_edge, k), -1, dtype=np.int64)
    metapath_mask = np.zeros((len(metapath_names), n_edge, k), dtype=np.float32)

    for p_idx, cands_for_all in enumerate(candidates_by_path):
        for i in range(n_edge):
            uniq = sorted(
                {int(j) for j in cands_for_all[i] if int(j) != i},
                key=lambda j: (float(line_dist[i, j]), int(j)),
            )
            if not uniq:
                uniq = [int(i)]
            selected = uniq[:k]
            metapath_index[p_idx, i, : len(selected)] = np.asarray(selected, dtype=np.int64)
            metapath_mask[p_idx, i, : len(selected)] = 1.0

    return {
        "line_ids": line_ids,
        "line_id_to_idx": {lid: i for i, lid in enumerate(line_ids)},
        "metapath_names": metapath_names,
        "metapath_index": metapath_index,
        "metapath_mask": metapath_mask,
        "line_dist": line_dist,
        "source_buses": source_buses,
        "primary_load_buses": primary_load_buses,
    }


def fig_metapath_topology(
    topology: dict,
    line_risk: pd.DataFrame,
    target_line: str,
    neighbor_lines: list[str],
    risk_threshold: float,
    selected_path: str,
    source_buses: list[int],
    primary_load_buses: list[int],
    title: str,
) -> go.Figure:
    if not topology:
        return go.Figure()

    risk_map: dict[str, float] = {}
    if not line_risk.empty and {"line_id", "risk_prob"}.issubset(line_risk.columns):
        t = line_risk.copy()
        t["risk_prob"] = pd.to_numeric(t["risk_prob"], errors="coerce").fillna(0.0)
        risk_map = {str(r["line_id"]): float(r["risk_prob"]) for _, r in t.iterrows()}

    neighbor_set = set(neighbor_lines)
    source_bus_set = set(int(x) for x in source_buses)
    primary_load_set = set(int(x) for x in primary_load_buses)

    source_side_lines: set[str] = set()
    load_side_lines: set[str] = set()
    for ln in topology.get("lines", []):
        lid = str(ln.get("id"))
        u = int(ln.get("from", -1))
        v = int(ln.get("to", -1))
        if u in source_bus_set or v in source_bus_set:
            source_side_lines.add(lid)
        if u in primary_load_set or v in primary_load_set:
            load_side_lines.add(lid)

    fig = go.Figure()
    highlight_ann: list[dict[str, Any]] = []
    for ln in topology.get("lines", []):
        lid = str(ln.get("id"))
        prob = float(risk_map.get(lid, 0.0))
        fx = float(ln.get("from_lon", 0.0) or 0.0)
        fy = float(ln.get("from_lat", 0.0) or 0.0)
        tx = float(ln.get("to_lon", 0.0) or 0.0)
        ty = float(ln.get("to_lat", 0.0) or 0.0)
        color = "rgba(143,161,179,0.30)"
        width = 1.0
        dash = "solid"
        if lid in neighbor_set:
            if prob >= risk_threshold:
                color = "#d64b45"
                width = 3.5
            else:
                color = "rgba(143,161,179,0.85)"
                width = 2.0
                dash = "dash"
        if selected_path == "source_bridge" and lid in source_side_lines and lid not in neighbor_set and lid != target_line:
            color = "rgba(246,193,66,0.45)"
            width = 1.8
            dash = "dot"
        if selected_path == "primary_load_bridge" and lid in load_side_lines and lid not in neighbor_set and lid != target_line:
            color = "rgba(176,124,198,0.45)"
            width = 1.8
            dash = "dot"
        if lid == target_line:
            color = "#1b64b0"
            width = 5.5

        tag = "target" if lid == target_line else ("metapath-neighbor" if lid in neighbor_set else "other")
        fig.add_trace(
            go.Scatter(
                x=[fx, tx],
                y=[fy, ty],
                mode="lines",
                line=dict(color=color, width=width, dash=dash),
                hovertemplate=f"{lid}<br>tag={tag}<br>risk={prob:.3f}<extra></extra>",
                showlegend=False,
            )
        )

        mx = (fx + tx) / 2.0
        my = (fy + ty) / 2.0
        if lid == target_line or lid in neighbor_set:
            if lid == target_line:
                ann_bg = "rgba(27,100,176,0.95)"
            else:
                ann_bg = "rgba(214,75,69,0.92)" if prob >= risk_threshold else "rgba(126,146,164,0.92)"
            y_shift = (0.0028 if len(highlight_ann) % 2 == 0 else -0.0028)
            highlight_ann.append({"x": mx, "y": my + y_shift, "text": lid, "bg": ann_bg})

    nodes = pd.DataFrame(topology.get("nodes", []))
    if not nodes.empty:
        nodes["node"] = "B" + nodes["id"].astype(str)
        nodes["role"] = "普通母线"
        nodes.loc[nodes["id"].isin(source_bus_set), "role"] = "电源侧锚点"
        nodes.loc[nodes["id"].isin(primary_load_set), "role"] = "关键负荷锚点"
        fig.add_trace(
            go.Scatter(
                x=nodes["lon"],
                y=nodes["lat"],
                mode="markers",
                marker=dict(size=7, color="rgba(78,121,167,0.85)", symbol="circle"),
                hovertemplate="%{text}<br>role=%{customdata}<extra></extra>",
                text=nodes["node"],
                customdata=nodes["role"],
                showlegend=False,
            )
        )

        if selected_path == "source_bridge":
            src = nodes[nodes["id"].isin(source_bus_set)].copy()
            if not src.empty:
                fig.add_trace(
                    go.Scatter(
                        x=src["lon"],
                        y=src["lat"],
                        mode="markers+text",
                        text=src["node"],
                        textposition="bottom center",
                        marker=dict(size=14, color="#f6c142", symbol="star"),
                        name="电源侧锚点",
                        hovertemplate="%{text}<br>role=电源侧锚点<extra></extra>",
                        showlegend=True,
                    )
                )
        if selected_path == "primary_load_bridge":
            pl = nodes[nodes["id"].isin(primary_load_set)].copy()
            if not pl.empty:
                fig.add_trace(
                    go.Scatter(
                        x=pl["lon"],
                        y=pl["lat"],
                        mode="markers+text",
                        text=pl["node"],
                        textposition="bottom center",
                        marker=dict(size=13, color="#b07cc6", symbol="diamond"),
                        name="关键负荷锚点",
                        hovertemplate="%{text}<br>role=关键负荷锚点<extra></extra>",
                        showlegend=True,
                    )
                )

    legend_rows = []
    if selected_path == "source_bridge":
        legend_rows = [
            ("#1b64b0", "目标线路"),
            ("#d64b45", "高风险语义邻居"),
            ("#8fa1b3", "中低风险语义邻居"),
            ("#f6c142", "电源侧走廊线"),
        ]
    elif selected_path == "primary_load_bridge":
        legend_rows = [
            ("#1b64b0", "目标线路"),
            ("#d64b45", "高风险语义邻居"),
            ("#8fa1b3", "中低风险语义邻居"),
            ("#b07cc6", "关键负荷侧走廊线"),
        ]
    else:
        legend_rows = [
            ("#1b64b0", "目标线路"),
            ("#d64b45", "高风险语义邻居"),
            ("#8fa1b3", "中低风险语义邻居"),
        ]
    for color, name in legend_rows:
        fig.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode="lines",
                line=dict(color=color, width=4),
                name=name,
                showlegend=True,
            )
        )

    # 高亮线路标签（目标线与语义邻居）采用带底色标注，保证 L1/L2 等可读性。
    for ann in highlight_ann:
        fig.add_annotation(
            x=float(ann["x"]),
            y=float(ann["y"]),
            text=str(ann["text"]),
            showarrow=False,
            font=dict(size=11, color="white"),
            bgcolor=str(ann["bg"]),
            bordercolor="rgba(255,255,255,0.9)",
            borderwidth=1,
            borderpad=3,
            opacity=0.98,
        )

    fig.update_layout(
        title=title,
        height=500,
        margin=dict(l=10, r=10, t=45, b=10),
        legend=dict(orientation="h", y=1.03),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(visible=False, showgrid=False, zeroline=False, title_text="")
    fig.update_yaxes(visible=False, showgrid=False, zeroline=False, title_text="")
    return fig


def render_metapath(bundle: dict, flt: dict) -> None:
    st.markdown("## MetaPath")
    st.caption("用电网拓扑图展示：给定目标线路后，不同元路径语义会关联哪些线路，以及这些语义在模型中的权重。")

    topology = bundle.get("topology", {})
    if not topology or not topology.get("lines"):
        st.info("缺少拓扑数据，无法展示元路径页面。")
        return

    warning_report = bundle.get("warning_report", {})
    train_info = warning_report.get("training", {}) if isinstance(warning_report, dict) else {}
    k_default = int(max(1, train_info.get("metapath_topk", 4)))
    mp = build_metapath_neighbors(topology=topology, warning_report=warning_report, topk=k_default)
    if not mp:
        st.info("当前运行结果未识别到元路径结构。")
        return

    line_ids = mp["line_ids"]
    metapath_names = mp["metapath_names"]
    line_to_idx = mp["line_id_to_idx"]
    metapath_index = mp["metapath_index"]
    metapath_mask = mp["metapath_mask"]
    line_dist = mp["line_dist"]
    source_buses = mp.get("source_buses", [])
    primary_load_buses = mp.get("primary_load_buses", [])

    path_desc = {
        "share_bus": "L-B-L：两条线共享同一母线，表示直接拓扑耦合。",
        "two_hop_topology": "L-B-L-B-L：两跳传播，表示间接拓扑扩散。",
        "source_bridge": "L-B-(source)-B-L：通过电源侧节点产生联动传播。图中会用金色星形点标出电源侧锚点，并用金色虚线标出电源侧走廊线。",
        "primary_load_bridge": "L-B-(primary load)-B-L：通过关键负荷侧压力产生联动。图中会用紫色菱形点标出关键负荷锚点，并用紫色虚线标出负荷侧走廊线。",
    }

    c1, c2, c3 = st.columns([1.1, 1.1, 1.0])
    with c1:
        target_line = st.selectbox("目标线路", line_ids, index=0, key="mp_target_line")
    with c2:
        selected_path = st.selectbox("元路径语义", metapath_names, index=0, key="mp_path")
    with c3:
        k_use = st.slider("展示邻居数", 1, int(metapath_index.shape[2]), min(4, int(metapath_index.shape[2])), 1, key="mp_topk_show")

    st.caption(path_desc.get(selected_path, ""))

    tidx = int(line_to_idx[target_line])
    pidx = int(metapath_names.index(selected_path))
    neighbors_idx = [int(metapath_index[pidx, tidx, j]) for j in range(int(metapath_index.shape[2])) if metapath_mask[pidx, tidx, j] > 0.5]
    neighbors_idx = neighbors_idx[:k_use]
    neighbor_lines = [line_ids[j] for j in neighbors_idx if 0 <= j < len(line_ids)]

    st.plotly_chart(
        fig_metapath_topology(
            topology=topology,
            line_risk=bundle.get("line_risk", pd.DataFrame()),
            target_line=target_line,
            neighbor_lines=neighbor_lines,
            risk_threshold=float(flt.get("risk_threshold", 0.35)),
            selected_path=selected_path,
            source_buses=source_buses,
            primary_load_buses=primary_load_buses,
            title=f"元路径语义可视化：{selected_path}",
        ),
        use_container_width=True,
    )

    if selected_path == "source_bridge":
        st.caption(
            "电源侧锚点母线（Source Buses）: "
            + (", ".join([f"B{x}" for x in source_buses]) if source_buses else "无")
        )
    elif selected_path == "primary_load_bridge":
        st.caption(
            "关键负荷锚点母线（Primary Load Buses）: "
            + (", ".join([f"B{x}" for x in primary_load_buses]) if primary_load_buses else "无")
        )

    risk_map = {}
    line_risk = bundle.get("line_risk", pd.DataFrame())
    if not line_risk.empty and {"line_id", "risk_prob", "risk_level"}.issubset(line_risk.columns):
        rr = line_risk.copy()
        rr["risk_prob"] = pd.to_numeric(rr["risk_prob"], errors="coerce").fillna(0.0)
        risk_map = {
            str(r["line_id"]): (float(r["risk_prob"]), str(r.get("risk_level", "")))
            for _, r in rr.iterrows()
        }

    table_rows = []
    for lid in neighbor_lines:
        j = line_to_idx.get(lid, -1)
        hop = float(line_dist[tidx, j]) if j >= 0 else np.nan
        rp, rl = risk_map.get(lid, (np.nan, ""))
        table_rows.append(
            {
                "target_line": target_line,
                "metapath": selected_path,
                "neighbor_line": lid,
                "hop_distance": hop,
                "risk_prob": rp,
                "risk_level": rl,
            }
        )
    with st.expander("语义邻居明细（点击展开）", expanded=False):
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

    a1, a2 = st.columns([1.1, 1.0])
    with a1:
        attention, attention_source = load_metapath_attention_for_ui(bundle, warning_report)
        st.markdown("### 元路径语义权重")
        if not attention.empty and {"metapath", "attention_weight"}.issubset(attention.columns):
            att = attention.copy()
            att["metapath"] = att["metapath"].astype(str)
            att["attention_weight"] = pd.to_numeric(att["attention_weight"], errors="coerce").fillna(0.0)
            att = att.groupby("metapath", as_index=False)["attention_weight"].mean().sort_values("attention_weight", ascending=False)
            total_w = float(att["attention_weight"].sum())
            att["weight_norm"] = att["attention_weight"] / total_w if total_w > 1e-12 else 0.0
            st.plotly_chart(
                px.bar(att, x="metapath", y="weight_norm", title="语义注意力权重（归一化）", labels={"weight_norm": "attention"}),
                use_container_width=True,
            )
            if not att.empty:
                lead = att.iloc[0]
                st.caption(f"主导语义: `{lead['metapath']}` ({float(lead['weight_norm']):.1%})")
            st.dataframe(
                att.rename(columns={"attention_weight": "weight_raw", "weight_norm": "weight_norm(share)"}),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("未找到可用的元路径权重数据（当前运行 + warning_report + early_warning 回填均不可用）。")

    with a2:
        st.markdown("### 模型对比")
        comp, comp_source = load_model_comparison_for_ui(bundle, warning_report)
        if not comp.empty and "model" in comp.columns:
            cmp = comp.copy()
            for col in [
                "val_mae",
                "horizon_mae",
                "val_high_risk_mae",
                "horizon_high_risk_mae",
                "val_top_risk_mae",
                "horizon_top_risk_mae",
                "best_val_mse",
            ]:
                if col in cmp.columns:
                    cmp[col] = pd.to_numeric(cmp[col], errors="coerce")

            key_metrics = [
                c
                for c in [
                    "val_mae",
                    "horizon_mae",
                    "val_high_risk_mae",
                    "horizon_high_risk_mae",
                    "val_top_risk_mae",
                    "horizon_top_risk_mae",
                    "best_val_mse",
                ]
                if c in cmp.columns
            ]
            if key_metrics:
                melt = cmp[["model"] + key_metrics].melt(id_vars="model", var_name="metric", value_name="value").dropna(subset=["value"])
                if not melt.empty:
                    st.plotly_chart(
                        px.bar(melt, x="metric", y="value", color="model", barmode="group", title="关键误差指标对比（越低越好）"),
                        use_container_width=True,
                    )
            st.dataframe(cmp, use_container_width=True, hide_index=True)

            m = cmp[cmp["model"] == "metapath_v1"]
            b = cmp[cmp["model"] == "baseline_gnn"]
            if not m.empty and not b.empty:
                m = m.iloc[0]
                b = b.iloc[0]
                kpi_items = [
                    ("Val MAE (MetaPath)", "val_mae"),
                    ("Horizon MAE (MetaPath)", "horizon_mae"),
                    ("Horizon High-Risk MAE (MetaPath)", "horizon_high_risk_mae"),
                    ("Horizon Top-Risk MAE (MetaPath)", "horizon_top_risk_mae"),
                ]
                kpi_cols = st.columns(len(kpi_items))
                for idx, (title, key) in enumerate(kpi_items):
                    with kpi_cols[idx]:
                        if pd.notna(m.get(key)) and pd.notna(b.get(key)):
                            st.metric(title, f"{float(m[key]):.4f}", f"{float(b[key] - m[key]):+.4f}")
        else:
            st.info("未找到可用的模型对比数据（当前运行 + warning_report + early_warning 回填均不可用）。")

        gate_mean = train_info.get("metapath_gate_mean")
        if gate_mean is not None:
            st.caption(f"门控均值 metapath_gate_mean = {float(gate_mean):.4f}（数值越小，表示元路径修正越保守）")


def render_overview(bundle: dict, sh: pd.DataFrame, flt: dict) -> None:
    st.markdown("## Overview")
    kpis = build_kpis(bundle, sh)
    cols = st.columns(6)
    for c, (k, v) in zip(cols, kpis.items()):
        with c:
            metric_card(k, v)

    risk = build_risk_hourly(bundle)
    left, right = st.columns([1.25, 1.0])
    with left:
        if not risk.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=risk["timestamp"], y=risk["line_risk"], name="Line", line=dict(color="#d64b45")))
            fig.add_trace(go.Scatter(x=risk["timestamp"], y=risk["nk_risk"], name="N-k", line=dict(color="#f08a24")))
            fig.add_trace(go.Scatter(x=risk["timestamp"], y=risk["critical_risk"], name="Critical", line=dict(color="#1b64b0")))
            fig.update_layout(title="72h 风险趋势图", height=300, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig, use_container_width=True)

            stack = go.Figure()
            stack.add_trace(go.Scatter(x=risk["timestamp"], y=risk["line_norm"], stackgroup="one", name="Line", line=dict(color="#d64b45")))
            stack.add_trace(go.Scatter(x=risk["timestamp"], y=risk["nk_norm"], stackgroup="one", name="N-k", line=dict(color="#f08a24")))
            stack.add_trace(go.Scatter(x=risk["timestamp"], y=risk["critical_norm"], stackgroup="one", name="Critical", line=dict(color="#1b64b0")))
            stack.update_layout(title="风险类型堆叠图（归一化）", height=250, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(stack, use_container_width=True)

    with right:
        st.plotly_chart(fig_strip(sh, "24h 调度模型切换图"), use_container_width=True)
        st.plotly_chart(fig_topology(bundle.get("topology", {}), bundle["line_risk"], bundle["critical_risk"], flt["risk_threshold"]), use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        if not bundle["topsis"].empty:
            t = bundle["topsis"].copy()
            t["score"] = pd.to_numeric(t["score"], errors="coerce")
            st.plotly_chart(px.bar(t.sort_values("score"), x="score", y="policy", orientation="h", title="策略 TOPSIS 排名"), use_container_width=True)
    with c2:
        if not sh.empty:
            row = sh[sh["hour_index"] == flt["dispatch_hour"]]
            if row.empty:
                row = sh.head(1)
            row = row.iloc[0]
            st.markdown("### 小时联动摘要")
            st.write(f"- 时间: `{row['timestamp']}`")
            st.write(f"- 优化器: `{row['selected_strategy']}`")
            if "hourly_line_risk" in row and not pd.isna(row["hourly_line_risk"]):
                st.write(f"- 风险: `{float(row['hourly_line_risk']):.4f}`")
            if "reason" in row:
                st.write(f"- 原因: `{row['reason']}`")

    physics_summary = bundle.get("physics_summary", {})
    exp_cmp = bundle.get("experiment_metrics_comparison", pd.DataFrame())
    if physics_summary or not exp_cmp.empty:
        st.markdown("### Stage8 Physics Snapshot")
        p1, p2, p3, p4 = st.columns(4)
        with p1:
            metric_card("物理可行", "PASS" if physics_summary.get("physical_feasibility_passed") else "FAIL")
        with p2:
            metric_card("关键违规数", str(physics_summary.get("violations", {}).get("critical", "n/a")))
        with p3:
            metric_card("规则动作数", str(physics_summary.get("diagnostic_layer", {}).get("rule_based_actions_rows", "n/a")))
        with p4:
            metric_card("闭环执行数", str(bundle.get("rule_closure_summary", {}).get("actions_executed", "n/a")))
        if not exp_cmp.empty:
            cmp = exp_cmp.copy()
            num_cols = ["total_shed", "total_served", "total_reserve"]
            for c in num_cols:
                cmp[c] = pd.to_numeric(cmp[c], errors="coerce")
            long_cmp = cmp.melt(id_vars=["group"], value_vars=num_cols, var_name="metric", value_name="value")
            st.plotly_chart(
                px.bar(long_cmp, x="metric", y="value", color="group", barmode="group", title="Stage8 实验组对比（G0/G1/G2）"),
                use_container_width=True,
            )


def render_operational_cockpit(bundle: dict, sh: pd.DataFrame, flt: dict) -> None:
    st.markdown("## 运行驾驶舱")
    risk = build_risk_hourly(bundle)
    physics_summary = bundle.get("physics_summary", {})
    rule_closure = bundle.get("rule_closure_summary", {})
    actions = bundle.get("rule_based_actions_hourly", pd.DataFrame())
    critical_lines = bundle.get("critical_lines_hourly", pd.DataFrame())
    vuln = bundle.get("vulnerable_buses_hourly", pd.DataFrame())
    exp_cmp = bundle.get("experiment_metrics_comparison", pd.DataFrame())

    current_row = pd.Series(dtype=object)
    if not sh.empty:
        current = sh[sh["hour_index"] == flt["dispatch_hour"]]
        if current.empty:
            current = sh.head(1)
        if not current.empty:
            current_row = current.iloc[0]

    critical_count = int(physics_summary.get("violations", {}).get("critical", 0) or 0)
    action_count = int(physics_summary.get("diagnostic_layer", {}).get("rule_based_actions_rows", 0) or 0)
    executed_count = int(rule_closure.get("actions_executed", 0) or 0)
    risk_value = float(current_row.get("hourly_line_risk", np.nan)) if not current_row.empty and not pd.isna(current_row.get("hourly_line_risk", np.nan)) else np.nan
    strategy_value = str(current_row.get("selected_strategy", "n/a")) if not current_row.empty else "n/a"
    physics_flag = "PASS" if physics_summary.get("physical_feasibility_passed") else "FAIL"

    risk_text = f"线路风险 {risk_value:.4f}" if not np.isnan(risk_value) else "线路风险暂不可用"
    render_summary(
        f"当前页面聚焦运行层结论：调度小时 {flt['dispatch_hour']} 采用 {strategy_value}，"
        f"{risk_text}，物理可行性为 {physics_flag}，已执行规则动作 {executed_count} 条。"
    )

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        metric_card("当前风险", f"{risk_value:.3f}" if not np.isnan(risk_value) else "n/a")
    with k2:
        metric_card("关键违规", str(critical_count))
    with k3:
        metric_card("建议动作", str(action_count))
    with k4:
        metric_card("闭环执行", str(executed_count))
    with k5:
        metric_card("物理可行", physics_flag)

    top_left, top_right = st.columns([1.35, 1])
    with top_left:
        if not risk.empty:
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            fig.add_trace(go.Scatter(x=risk["timestamp"], y=risk["line_risk"], name="线路风险", line=dict(color="#d64b45", width=3)), secondary_y=False)
            fig.add_trace(go.Scatter(x=risk["timestamp"], y=risk["critical_risk"], name="关键负荷风险", line=dict(color="#1b64b0", width=2)), secondary_y=False)
            if not sh.empty and "served_load" in sh.columns:
                served = sh.copy()
                served["served_load"] = pd.to_numeric(served["served_load"], errors="coerce")
                fig.add_trace(go.Bar(x=served["timestamp"], y=served["served_load"], name="供电量", marker_color="rgba(39,174,96,0.35)"), secondary_y=True)
            fig.update_layout(title="风险与供电联动时间轴", height=360, margin=dict(l=10, r=10, t=40, b=10), legend=dict(orientation="h"))
            fig.update_yaxes(title_text="风险", secondary_y=False)
            fig.update_yaxes(title_text="供电量", secondary_y=True)
            st.plotly_chart(fig, use_container_width=True)
    with top_right:
        if not actions.empty:
            act = actions.copy()
            act["timestamp"] = pd.to_datetime(act["timestamp"], errors="coerce")
            ts = act["timestamp"].dropna().sort_values().unique()
            idx = min(max(int(flt.get("dispatch_hour", 0)), 0), len(ts) - 1) if len(ts) else 0
            picked_ts = ts[idx] if len(ts) else None
            if picked_ts is not None:
                one = act[act["timestamp"] == picked_ts].copy()
                st.markdown(f"### 当前小时建议 `{pd.Timestamp(picked_ts)}`")
                cols = [c for c in ["action_type", "target_id", "recommendation", "priority", "action_priority"] if c in one.columns]
                render_dataframe_panel("查看当前小时建议明细", one[cols] if cols else one)

    mid1, mid2, mid3 = st.columns(3)
    with mid1:
        if not critical_lines.empty:
            cl = critical_lines.copy()
            cl["stress_score"] = pd.to_numeric(cl["stress_score"], errors="coerce")
            top = cl.sort_values("stress_score", ascending=False).head(int(flt.get("top_k", 5)))
            st.plotly_chart(px.bar(top, x="line_id", y="stress_score", color="action_priority", color_discrete_map=ACTION_PRIORITY_COLOR, title="关键线路"), use_container_width=True)
    with mid2:
        if not vuln.empty:
            vb = vuln.copy()
            vb["vulnerability_score"] = pd.to_numeric(vb["vulnerability_score"], errors="coerce")
            topb = vb.sort_values("vulnerability_score", ascending=False).head(int(flt.get("top_k", 5)))
            st.plotly_chart(px.bar(topb, x="bus_id", y="vulnerability_score", color="vulnerability_level", color_discrete_map=RISK_LEVEL_COLOR, title="脆弱母线"), use_container_width=True)
    with mid3:
        if not exp_cmp.empty:
            cmp = exp_cmp.copy()
            for c in ["total_shed", "total_served", "total_reserve"]:
                if c in cmp.columns:
                    cmp[c] = pd.to_numeric(cmp[c], errors="coerce")
            long_cmp = cmp.melt(id_vars=["group"], value_vars=["total_shed", "total_served", "total_reserve"], var_name="metric", value_name="value")
            st.plotly_chart(px.bar(long_cmp, x="metric", y="value", color="group", color_discrete_map=GROUP_COLOR, barmode="group", title="闭环对比"), use_container_width=True)

    with st.expander("查看当前小时详细建议与执行日志"):
        log_df = bundle.get("rule_action_execution_log", pd.DataFrame())
        if not log_df.empty:
            st.dataframe(log_df, use_container_width=True, hide_index=True)


def render_pipeline() -> None:
    st.markdown("## Pipeline View")
    labels = [
        "Stage1 风光不确定性", "Stage2 组件失效概率", "Stage3 时空故障场景",
        "Stage4 负荷优先级调度", "Stage5 韧性评估", "Stage6 GNN预警", "Stage7 上下文调度优化", "Stage8 稳态物理闭环"
    ]
    fig = go.Figure(go.Sankey(
        node=dict(label=labels, pad=16, thickness=22, color=["#67a9cf", "#67a9cf", "#67a9cf", "#91bfdb", "#99d8c9", "#fdae61", "#fc8d59", "#6c9f6b"]),
        link=dict(source=[0,1,2,3,4,5,6], target=[1,2,3,4,5,6,7], value=[1,1,1,1,1,1,1], color="rgba(27,100,176,.35)")
    ))
    fig.update_layout(title="Stage1 → Stage8 实际执行顺序", height=420, margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig, use_container_width=True)

    scale = pd.DataFrame({"时间尺度": ["全年风光场景", "台风窗口", "调度日"], "小时数": [8784, 72, 24]})
    st.plotly_chart(px.bar(scale, x="时间尺度", y="小时数", color="时间尺度", title="三时间尺度"), use_container_width=True)

    st.dataframe(pd.DataFrame([
        ["Stage1", "DPGMM", "scenario", "8784h"],
        ["Stage2", "Batts/Schloemer", "scenario", "72h"],
        ["Stage3", "MC/QMC/C3PO/TRIM", "scenario", "72h"],
        ["Stage4", "policy scheduling", "stage5输入", "24h"],
        ["Stage5", "EWM+TOPSIS", "resilience", "策略级"],
        ["Stage6", "GNN", "warning", "24h"],
        ["Stage7", "SCUC/Robust/Stochastic", "dispatch", "24h"],
        ["Stage8", "Physics + Rule Closure", "stage8", "24h"],
    ], columns=["Stage", "方法", "standard映射", "时间尺度"]), use_container_width=True, hide_index=True)


def render_stage8(bundle: dict, flt: dict) -> None:
    st.markdown("## Stage8 Physics")
    physics_summary = bundle.get("physics_summary", {})
    rule_closure = bundle.get("rule_closure_summary", {})
    exp_cmp = bundle.get("experiment_metrics_comparison", pd.DataFrame())
    actions = bundle.get("rule_based_actions_hourly", pd.DataFrame())
    action_type = bundle.get("action_type_summary", pd.DataFrame())
    hourly_cmp = bundle.get("hourly_closure_comparison", pd.DataFrame())
    critical_lines = bundle.get("critical_lines_hourly", pd.DataFrame())
    vuln = bundle.get("vulnerable_buses_hourly", pd.DataFrame())
    load_area = bundle.get("load_area_risk_hourly", pd.DataFrame())
    gen_cand = bundle.get("generator_action_candidates", pd.DataFrame())

    if (
        not physics_summary
        and exp_cmp.empty
        and actions.empty
        and critical_lines.empty
        and vuln.empty
        and load_area.empty
        and gen_cand.empty
    ):
        st.warning("当前所选结果目录没有检测到 Stage8 输出。请切换到包含 `stage8_steady_state_physics` 的 framework run。")
        return

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        metric_card("物理可行", "PASS" if physics_summary.get("physical_feasibility_passed") else "FAIL")
    with k2:
        metric_card("关键违规", str(physics_summary.get("violations", {}).get("critical", "n/a")))
    with k3:
        metric_card("规则动作", str(physics_summary.get("diagnostic_layer", {}).get("rule_based_actions_rows", "n/a")))
    with k4:
        metric_card("闭环执行", str(rule_closure.get("actions_executed", "n/a")))

    summary_text = (
        f"Stage8 当前共识别关键违规 {physics_summary.get('violations', {}).get('critical', 'n/a')} 项，"
        f"生成规则动作 {physics_summary.get('diagnostic_layer', {}).get('rule_based_actions_rows', 'n/a')} 条，"
        f"实际执行 {rule_closure.get('actions_executed', 'n/a')} 条，"
        f"物理可行性结果为 {'PASS' if physics_summary.get('physical_feasibility_passed') else 'FAIL'}。"
    )
    render_summary(summary_text)

    st.markdown("### 流程总览")
    st.info("诊断层识别关键线路、脆弱母线和失供风险，再进入规则动作层生成操作建议，最后在闭环层评估修正后的切负荷、供电和备用改善。")
    flow1, flow2, flow3 = st.columns(3)
    with flow1:
        st.markdown("`诊断层` 发现哪里不稳、哪里最脆弱")
    with flow2:
        st.markdown("`规则动作层` 生成可执行的调度建议")
    with flow3:
        st.markdown("`闭环校核层` 对比修正前后是否更可行")

    cmp = exp_cmp.copy() if not exp_cmp.empty else pd.DataFrame()
    if not cmp.empty:
        for c in ["total_shed", "total_served", "total_reserve", "mean_line_loading"]:
            if c in cmp.columns:
                cmp[c] = pd.to_numeric(cmp[c], errors="coerce")
        cmp_idx = cmp.set_index("group")
        if "G0_stage7_raw" in cmp_idx.index and "G2_rule_closed_loop" in cmp_idx.index:
            base = cmp_idx.loc["G0_stage7_raw"]
            closed = cmp_idx.loc["G2_rule_closed_loop"]
            diff1, diff2, diff3 = st.columns(3)
            shed_delta = closed.get("total_shed", float("nan")) - base.get("total_shed", float("nan"))
            served_delta = closed.get("total_served", float("nan")) - base.get("total_served", float("nan"))
            reserve_delta = closed.get("total_reserve", float("nan")) - base.get("total_reserve", float("nan"))
            with diff1:
                st.metric("闭环切负荷变化", f"{closed.get('total_shed', float('nan')):.2f}", delta=f"{shed_delta:.2f}")
            with diff2:
                st.metric("闭环供电变化", f"{closed.get('total_served', float('nan')):.2f}", delta=f"{served_delta:.2f}")
            with diff3:
                st.metric("闭环备用变化", f"{closed.get('total_reserve', float('nan')):.2f}", delta=f"{reserve_delta:.2f}")

    s1, s2, s3 = st.tabs(["1. 诊断层", "2. 规则动作层", "3. 闭环校核层"])

    with s1:
        st.markdown("#### 这一层回答什么问题")
        st.caption("哪些线路、母线、负荷区和机组最需要优先关注，风险具体落在哪些电网对象上。")
        c1, c2 = st.columns(2)
        with c1:
            if not critical_lines.empty:
                cl = critical_lines.copy()
                cl["stress_score"] = pd.to_numeric(cl["stress_score"], errors="coerce")
                top = cl.sort_values("stress_score", ascending=False).head(int(flt.get("top_k", 5)))
                st.plotly_chart(px.bar(top, x="line_id", y="stress_score", color="action_priority", color_discrete_map=ACTION_PRIORITY_COLOR, title="关键线路应力 Top-K"), use_container_width=True)
        with c2:
            if not vuln.empty:
                vb = vuln.copy()
                vb["vulnerability_score"] = pd.to_numeric(vb["vulnerability_score"], errors="coerce")
                topb = vb.sort_values("vulnerability_score", ascending=False).head(int(flt.get("top_k", 5)))
                st.plotly_chart(px.bar(topb, x="bus_id", y="vulnerability_score", color="vulnerability_level", color_discrete_map=RISK_LEVEL_COLOR, title="脆弱母线 Top-K"), use_container_width=True)
        c3, c4 = st.columns(2)
        with c3:
            if not load_area.empty:
                la = load_area.copy()
                la["loss_of_supply_score"] = pd.to_numeric(la["loss_of_supply_score"], errors="coerce")
                st.plotly_chart(px.scatter(la, x="priority_weight", y="loss_of_supply_score", color="action_priority", color_discrete_map=ACTION_PRIORITY_COLOR, size="demand", hover_data=["load_bus"], title="负荷区域失供风险分布"), use_container_width=True)
        with c4:
            if not gen_cand.empty:
                gc = gen_cand.copy()
                gc["support_score"] = pd.to_numeric(gc["support_score"], errors="coerce")
                st.plotly_chart(px.bar(gc.sort_values("support_score", ascending=False).head(12), x="unit_id", y="support_score", color="target_bus", title="机组动作候选评分"), use_container_width=True)

    with s2:
        st.markdown("#### 这一层回答什么问题")
        st.caption("面对上一层发现的高风险对象，当前小时具体应该采取什么规则动作。")
        if not action_type.empty:
            st.plotly_chart(px.bar(action_type, x="action_type", y="requested_count", color="execution_rate", title="规则动作类型统计"), use_container_width=True)
        if not actions.empty:
            act = actions.copy()
            act["timestamp"] = pd.to_datetime(act["timestamp"], errors="coerce")
            ts = act["timestamp"].dropna().sort_values().unique()
            idx = min(max(int(flt.get("dispatch_hour", 0)), 0), len(ts) - 1) if len(ts) else 0
            picked_ts = ts[idx] if len(ts) else None
            if picked_ts is not None:
                one = act[act["timestamp"] == picked_ts].copy()
                st.markdown(f"#### 当前小时动作建议 `{pd.Timestamp(picked_ts)}`")
                render_dataframe_panel("查看当前小时动作建议明细", one)

    with s3:
        st.markdown("#### 这一层回答什么问题")
        st.caption("规则修正执行后，方案有没有变得更可执行，切负荷、供电和备用是否朝更合理方向变化。")
        c5, c6 = st.columns(2)
        with c5:
            if not cmp.empty:
                long_cmp = cmp.melt(id_vars=["group"], value_vars=["total_shed", "total_served", "total_reserve"], var_name="metric", value_name="value")
                st.plotly_chart(px.bar(long_cmp, x="metric", y="value", color="group", color_discrete_map=GROUP_COLOR, barmode="group", title="实验组总体对比"), use_container_width=True)
            corrected_load = bundle.get("rule_corrected_dispatch_load_shedding", pd.DataFrame())
            if not corrected_load.empty:
                tmp = corrected_load.copy()
                tmp["shed"] = pd.to_numeric(tmp["shed"], errors="coerce").fillna(0.0)
                total = tmp.groupby("timestamp", as_index=False)["shed"].sum()
                st.plotly_chart(px.bar(total, x="timestamp", y="shed", title="闭环后切负荷总量"), use_container_width=True)
        with c6:
            if not hourly_cmp.empty:
                hc = hourly_cmp.copy()
                st.plotly_chart(
                    px.line(
                        hc.melt(id_vars=["timestamp"], value_vars=["shed_reduction", "served_increase", "reserve_increase"], var_name="metric", value_name="value"),
                        x="timestamp",
                        y="value",
                        color="metric",
                        title="逐小时闭环改善幅度",
                    ),
                    use_container_width=True,
                )
            log_df = bundle.get("rule_action_execution_log", pd.DataFrame())
            if not log_df.empty:
                render_dataframe_panel("查看规则动作执行日志", log_df)
        if not cmp.empty:
            render_dataframe_panel("查看实验指标表", cmp)

def render_scenario_failure(bundle: dict, flt: dict) -> None:
    st.markdown("## Scenario & Failure")
    a, b, c = st.tabs(["风光场景", "失效概率", "故障场景"])

    with a:
        ws = bundle["wind_solar"]
        if ws.empty:
            st.info("缺少风光场景数据。")
        else:
            wind_cols = [x for x in ws.columns if x.startswith("wind_")]
            solar_cols = [x for x in ws.columns if x.startswith("solar_")]
            ws = ws.copy()
            ws["wind_mean"] = ws[wind_cols].mean(axis=1)
            ws["solar_mean"] = ws[solar_cols].mean(axis=1)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=ws["timestamp"], y=ws["wind_mean"], name="Wind", line=dict(color="#1b64b0")))
            fig.add_trace(go.Scatter(x=ws["timestamp"], y=ws["solar_mean"], name="Solar", line=dict(color="#f08a24")))
            fig.update_layout(title="全年风光时序概览", height=300, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig, use_container_width=True)

            for cols, name, color in [(wind_cols, "风电分位带", "#1b64b0"), (solar_cols, "光伏分位带", "#f08a24")]:
                p10 = ws[cols].quantile(0.1, axis=1)
                p50 = ws[cols].quantile(0.5, axis=1)
                p90 = ws[cols].quantile(0.9, axis=1)
                fg = go.Figure()
                fg.add_trace(go.Scatter(x=ws["timestamp"], y=p90, line=dict(width=0), showlegend=False))
                fg.add_trace(go.Scatter(x=ws["timestamp"], y=p10, line=dict(width=0), fill="tonexty", name="P10-P90"))
                fg.add_trace(go.Scatter(x=ws["timestamp"], y=p50, line=dict(color=color), name="P50"))
                fg.update_layout(title=name, height=260, margin=dict(l=10, r=10, t=40, b=10))
                st.plotly_chart(fg, use_container_width=True)

    with b:
        cf = bundle["component_failure"]
        if cf.empty:
            st.info("缺少失效概率数据。")
        else:
            tmp = cf.copy()
            tmp["hour_index"] = ((tmp["hour"] - tmp["hour"].min()).dt.total_seconds() / 3600).astype(int)
            tmp["failure_prob"] = pd.to_numeric(tmp["failure_prob"], errors="coerce")
            pv = tmp.pivot_table(index="line", columns="hour_index", values="failure_prob", aggfunc="mean")
            st.plotly_chart(px.imshow(pv, aspect="auto", color_continuous_scale="YlOrRd", title="72h 组件失效概率热图"), use_container_width=True)

            ts = tmp["hour"].min() + pd.Timedelta(hours=flt["typhoon_hour"])
            at = tmp[tmp["hour"] == ts]
            if at.empty:
                at = tmp.iloc[:0]
            top = at.sort_values("failure_prob", ascending=False).head(flt["top_k"])
            st.plotly_chart(px.bar(top, x="line", y="failure_prob", title=f"Top-{flt['top_k']} 高风险组件"), use_container_width=True)

            line = st.selectbox("选择组件", sorted(tmp["line"].unique().tolist()), key="cf_line")
            st.plotly_chart(px.line(tmp[tmp["line"] == line], x="hour", y="failure_prob", title=f"{line} 概率随时间变化"), use_container_width=True)

    with c:
        cont = bundle["contingency"]
        if cont.empty:
            st.info("缺少故障场景数据。")
        else:
            cnt = cont.groupby("timestamp", as_index=False)["scenario_id"].count().rename(columns={"scenario_id": "count"})
            st.plotly_chart(px.bar(cnt, x="timestamp", y="count", title="故障场景数量按小时分布"), use_container_width=True)

            sample = cont.head(2000)
            pairs = {}
            lines = set()
            for s in sample["failed_lines"].dropna():
                parts = sorted(set([x for x in str(s).split("|") if x]))
                for p in parts:
                    lines.add(p)
                for i, a in enumerate(parts):
                    for b in parts[i:]:
                        pairs[(a, b)] = pairs.get((a, b), 0) + 1
                        if a != b:
                            pairs[(b, a)] = pairs.get((b, a), 0) + 1
            if lines:
                labs = sorted(lines)
                mat = pd.DataFrame(0, index=labs, columns=labs)
                for (a, b), v in pairs.items():
                    mat.loc[a, b] = v
                st.plotly_chart(px.imshow(mat, aspect="auto", color_continuous_scale="OrRd", title="故障组合频次矩阵"), use_container_width=True)

            view = cont.copy()
            view["hour_index"] = ((view["timestamp"] - view["timestamp"].min()).dt.total_seconds() / 3600).astype(int)
            view = view[(view["scenario"] == flt["scenario_name"]) & (view["hour_index"] == flt["typhoon_hour"])]
            st.dataframe(view.head(30), use_container_width=True, hide_index=True)


def render_warning(bundle: dict, sh: pd.DataFrame, flt: dict) -> None:
    st.markdown("## Warning")
    line_risk, nk, critical = bundle["line_risk"], bundle["nk_risk"], bundle["critical_risk"]
    hp = bundle["hourly_line_prob"]
    top_line = "n/a"
    if not line_risk.empty and "risk_prob" in line_risk.columns:
        tmp = line_risk.copy()
        tmp["risk_prob"] = pd.to_numeric(tmp["risk_prob"], errors="coerce")
        tmp = tmp.sort_values("risk_prob", ascending=False)
        if not tmp.empty:
            top_line = str(tmp.iloc[0].get("line_id", "n/a"))
    render_summary(f"当前预警页主要回答“哪里危险”。当前最危险线路为 {top_line}，风险诊断会继续展开到 N-k 组合和关键负荷层面。")

    t1, t2, t3 = st.tabs(["Line Risk", "N-k Risk", "Critical Load Risk"])
    with t1:
        if not line_risk.empty:
            lr = line_risk.copy()
            lr["risk_prob"] = pd.to_numeric(lr["risk_prob"], errors="coerce")
            top = lr.sort_values("risk_prob", ascending=False).head(flt["top_k"])
            st.plotly_chart(px.bar(top, x="line_id", y="risk_prob", color="risk_level", color_discrete_map=RISK_LEVEL_COLOR, title="线路风险 Top-K"), use_container_width=True)
            if not hp.empty:
                m = hp.melt(id_vars="timestamp", var_name="line_id", value_name="risk_prob")
                m["risk_prob"] = pd.to_numeric(m["risk_prob"], errors="coerce")
                st.plotly_chart(px.line(m[m["line_id"].isin(top["line_id"])], x="timestamp", y="risk_prob", color="line_id", title="线路风险时序"), use_container_width=True)
            st.plotly_chart(fig_topology(bundle.get("topology", {}), line_risk, critical, flt["risk_threshold"]), use_container_width=True)

    with t2:
        if not nk.empty:
            x = nk.copy()
            x["expected_fail_lines"] = pd.to_numeric(x["expected_fail_lines"], errors="coerce")
            x["probability"] = pd.to_numeric(x["probability"], errors="coerce")
            st.plotly_chart(px.bar(x.sort_values("probability", ascending=False), x="scenario", y="probability", title="N-k 组合排名"), use_container_width=True)
            x["type"] = x["expected_fail_lines"].apply(lambda v: "N-0" if v == 0 else f"N-{int(v)}" if v <= 3 else "N-4+")
            st.plotly_chart(px.pie(x.groupby("type", as_index=False)["probability"].sum(), values="probability", names="type", title="风险类型分布"), use_container_width=True)
            thr = float(bundle.get("dispatch_report", {}).get("strategy_rules", {}).get("robust_nk_threshold", 3.0))
            x["是否触发上下文切换"] = np.where(x["expected_fail_lines"] >= thr, "是", "否")
            render_dataframe_panel("查看 N-k 风险明细", x)

    with t3:
        if not critical.empty:
            c = critical.copy()
            c["outage_prob"] = pd.to_numeric(c["outage_prob"], errors="coerce")
            top = c.sort_values("outage_prob", ascending=False).head(flt["top_k"])
            st.plotly_chart(px.bar(top, x="node", y="outage_prob", color="load_type", title="关键负荷节点排名"), use_container_width=True)

            cls = bundle.get("context_load_shedding", pd.DataFrame())
            if not cls.empty:
                tmp = cls.copy()
                tmp["load_bus"] = tmp["load_bus"].astype(str).str.lower()
                tmp["shed"] = pd.to_numeric(tmp["shed"], errors="coerce")
                selected = set(top["node"].str.lower().tolist())
                tmp = tmp[tmp["load_bus"].isin(selected)]
                if not tmp.empty:
                    curve = tmp.groupby(["timestamp", "load_bus"], as_index=False)["shed"].sum()
                    st.plotly_chart(px.line(curve, x="timestamp", y="shed", color="load_bus", title="关键节点时序（切负荷代理）"), use_container_width=True)

            st.plotly_chart(fig_topology(bundle.get("topology", {}), line_risk, critical, flt["risk_threshold"]), use_container_width=True)

    if not sh.empty:
        rules = bundle.get("dispatch_report", {}).get("strategy_rules", {})
        robust_thr = float(rules.get("robust_line_risk_threshold", 0.72))
        stoch_thr = float(rules.get("stochastic_line_risk_threshold", 0.45))
        ctx = np.where(sh["hourly_line_risk"] >= robust_thr, "HIGH", np.where(sh["hourly_line_risk"] >= stoch_thr, "MEDIUM", "LOW"))
        ctx_id = pd.Series(ctx).map({"LOW": 0, "MEDIUM": 1, "HIGH": 2})
        stg_id = sh["selected_strategy"].map({"SCUC": 0, "Stochastic_UC": 1, "Robust_UC": 2}).fillna(0)

        fig = make_subplots(rows=3, cols=1, shared_xaxes=True, row_heights=[0.5, 0.2, 0.3], vertical_spacing=0.04)
        fig.add_trace(go.Scatter(x=sh["timestamp"], y=sh["hourly_line_risk"], mode="lines+markers", name="risk", line=dict(color="#d64b45")), row=1, col=1)
        fig.add_trace(go.Heatmap(z=[ctx_id.tolist()], x=sh["timestamp"], y=["context"], showscale=False), row=2, col=1)
        fig.add_trace(go.Heatmap(z=[stg_id.tolist()], x=sh["timestamp"], y=["optimizer"], showscale=False), row=3, col=1)
        fig.update_layout(title="风险驱动调度联动图：GNN预警 → 上下文判断 → 模型切换", height=500, margin=dict(l=10, r=10, t=45, b=10))
        st.plotly_chart(fig, use_container_width=True)


def render_node_weather(bundle: dict, flt: dict) -> None:
    st.markdown("## Node Weather")
    st.caption("展示节点天气的来源、空间差异和时间变化，回答“每个节点天气是怎么得到的”。")

    warning_report = bundle.get("warning_report", {})
    weather_meta = warning_report.get("node_weather_generation", {}) if isinstance(warning_report, dict) else {}
    frames, source = load_node_weather_for_ui(bundle=bundle, warning_report=warning_report)

    timeseries = frames.get("timeseries", pd.DataFrame()).copy()
    horizon = frames.get("horizon", pd.DataFrame()).copy()
    summary = frames.get("summary", pd.DataFrame()).copy()
    detail = horizon.copy() if not horizon.empty else timeseries.copy()

    if detail.empty and summary.empty:
        st.info("未找到节点天气文件。请先运行包含 `node_weather_*.csv` 输出的预警任务。")
        return

    if not detail.empty:
        if "timestamp" in detail.columns:
            detail["timestamp"] = pd.to_datetime(detail["timestamp"], errors="coerce")
        if "node_id" in detail.columns:
            detail["node_id"] = pd.to_numeric(detail["node_id"], errors="coerce").astype("Int64")
        for col in [
            "influence",
            "wind_factor",
            "pv_factor",
            "load_factor",
            "wind_speed_factor",
            "wind_raw",
            "pv_raw",
            "load_raw",
            "wind_speed_raw",
        ]:
            if col in detail.columns:
                detail[col] = pd.to_numeric(detail[col], errors="coerce")
        detail = detail.dropna(subset=["timestamp", "node_id"]).copy()
        detail["node_id"] = detail["node_id"].astype(int)

    if summary.empty and not detail.empty:
        summary = (
            detail.groupby("node_id", as_index=False)
            .agg(
                mean_influence=("influence", "mean"),
                mean_wind_factor=("wind_factor", "mean"),
                mean_pv_factor=("pv_factor", "mean"),
                mean_load_factor=("load_factor", "mean"),
                mean_wind_speed_factor=("wind_speed_factor", "mean"),
                mean_wind_raw=("wind_raw", "mean"),
                mean_pv_raw=("pv_raw", "mean"),
                mean_load_raw=("load_raw", "mean"),
                mean_wind_speed_raw=("wind_speed_raw", "mean"),
            )
            .sort_values("mean_influence", ascending=False)
            .reset_index(drop=True)
        )
    elif not summary.empty:
        if "node_id" in summary.columns:
            summary["node_id"] = pd.to_numeric(summary["node_id"], errors="coerce").astype("Int64")
            summary = summary.dropna(subset=["node_id"]).copy()
            summary["node_id"] = summary["node_id"].astype(int)
        for col in [c for c in summary.columns if c.startswith("mean_")]:
            summary[col] = pd.to_numeric(summary[col], errors="coerce")

    n_nodes = int(summary["node_id"].nunique()) if not summary.empty and "node_id" in summary.columns else 0
    n_timestamps = int(detail["timestamp"].nunique()) if not detail.empty and "timestamp" in detail.columns else 0
    avg_influence = float(summary["mean_influence"].mean()) if not summary.empty and "mean_influence" in summary.columns else float("nan")
    max_load_raw = float(summary["mean_load_raw"].max()) if not summary.empty and "mean_load_raw" in summary.columns else float("nan")

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        metric_card("节点数量", str(n_nodes))
    with k2:
        metric_card("时间步数量", str(n_timestamps))
    with k3:
        metric_card("平均影响强度", f"{avg_influence:.3f}" if np.isfinite(avg_influence) else "n/a")
    with k4:
        metric_card("最大平均负荷", f"{max_load_raw:.2f}" if np.isfinite(max_load_raw) else "n/a")

    c1, c2 = st.columns([1.35, 1.0])
    with c1:
        topology = bundle.get("topology", {})
        nodes = pd.DataFrame(topology.get("nodes", [])) if isinstance(topology, dict) else pd.DataFrame()
        if not nodes.empty and not summary.empty and "id" in nodes.columns:
            nodes["node_id"] = pd.to_numeric(nodes["id"], errors="coerce").astype("Int64")
            nodes = nodes.dropna(subset=["node_id"]).copy()
            nodes["node_id"] = nodes["node_id"].astype(int)
            show = nodes.merge(summary, on="node_id", how="left")
            lon_col = "lon" if "lon" in show.columns else ("local_x" if "local_x" in show.columns else None)
            lat_col = "lat" if "lat" in show.columns else ("local_y" if "local_y" in show.columns else None)
            if lon_col is not None and lat_col is not None:
                show[lon_col] = pd.to_numeric(show[lon_col], errors="coerce")
                show[lat_col] = pd.to_numeric(show[lat_col], errors="coerce")
                show["mean_influence"] = pd.to_numeric(show.get("mean_influence"), errors="coerce")
                if "mean_load_raw" in show.columns:
                    show["mean_load_raw"] = pd.to_numeric(show["mean_load_raw"], errors="coerce")
                show = show.dropna(subset=[lon_col, lat_col]).copy()
                if not show.empty:
                    hover_cols = [c for c in ["node_id", "mean_wind_raw", "mean_pv_raw", "mean_wind_speed_raw", "mean_load_raw"] if c in show.columns]
                    fig = px.scatter(
                        show,
                        x=lon_col,
                        y=lat_col,
                        color="mean_influence",
                        size="mean_load_raw" if "mean_load_raw" in show.columns else None,
                        hover_data=hover_cols,
                        color_continuous_scale="YlOrRd",
                        title="节点天气空间分布（颜色=平均影响强度）",
                    )
                    fig.update_traces(marker=dict(line=dict(width=0.5, color="white")))
                    fig.update_layout(height=420, margin=dict(l=10, r=10, t=45, b=10))
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("节点坐标为空，无法绘制空间图。")
            else:
                st.info("拓扑中缺少坐标列（lon/lat 或 local_x/local_y）。")
        else:
            st.info("缺少拓扑或节点天气汇总数据。")

    with c2:
        if not summary.empty and "mean_influence" in summary.columns:
            available_metrics = [c for c in ["mean_influence", "mean_wind_raw", "mean_pv_raw", "mean_load_raw", "mean_wind_speed_raw"] if c in summary.columns]
            if available_metrics:
                value_col = st.selectbox(
                    "排序指标",
                    available_metrics,
                    index=0,
                    key="node_weather_sort_metric",
                )
                top = (
                    summary[["node_id", value_col]]
                    .dropna(subset=[value_col])
                    .sort_values(value_col, ascending=False)
                    .head(int(flt.get("top_k", 5)))
                    .copy()
                )
                st.plotly_chart(
                    px.bar(
                        top,
                        x="node_id",
                        y=value_col,
                        title=f"节点 Top-{int(flt.get('top_k', 5))}（按 {value_col}）",
                    ),
                    use_container_width=True,
                )
                st.dataframe(top, use_container_width=True, hide_index=True)
            else:
                st.info("汇总文件缺少可排序指标列。")
        else:
            st.info("汇总文件缺少 mean_influence 等字段。")

    st.markdown("### 节点时间钻取")
    if not detail.empty and "node_id" in detail.columns:
        node_options = sorted(detail["node_id"].dropna().astype(int).unique().tolist())
        if node_options:
            node_pick = st.selectbox("选择节点", node_options, index=0, key="node_weather_pick_node")
            node_df = detail[detail["node_id"] == int(node_pick)].sort_values("timestamp").copy()
            left, right = st.columns(2)
            with left:
                raw_cols = [c for c in ["wind_raw", "pv_raw", "load_raw", "wind_speed_raw"] if c in node_df.columns]
                if raw_cols:
                    long_raw = node_df[["timestamp"] + raw_cols].melt(id_vars="timestamp", var_name="feature", value_name="value")
                    st.plotly_chart(
                        px.line(long_raw, x="timestamp", y="value", color="feature", title=f"节点 {node_pick} 原始天气量"),
                        use_container_width=True,
                    )
            with right:
                factor_cols = [c for c in ["influence", "wind_factor", "pv_factor", "load_factor", "wind_speed_factor"] if c in node_df.columns]
                if factor_cols:
                    long_fac = node_df[["timestamp"] + factor_cols].melt(id_vars="timestamp", var_name="feature", value_name="value")
                    st.plotly_chart(
                        px.line(long_fac, x="timestamp", y="value", color="feature", title=f"节点 {node_pick} 因子变化"),
                        use_container_width=True,
                    )
            st.dataframe(node_df.tail(12), use_container_width=True, hide_index=True)
    else:
        st.info("缺少可用于时间钻取的节点天气明细。")

    st.markdown("### 生成来源说明")
    if weather_meta:
        st.write(f"- 生成方法: `{weather_meta.get('method', 'n/a')}`")
        tcols = weather_meta.get("time_feature_columns", {})
        coord_count = weather_meta.get("coordinate_source_count", {})
        formulas = weather_meta.get("factor_formulas", {})
        p1, p2, p3 = st.columns(3)
        with p1:
            st.markdown("**时间序列列名**")
            if isinstance(tcols, dict) and tcols:
                tc_df = pd.DataFrame({"field": list(tcols.keys()), "value": [str(v) for v in tcols.values()]})
                st.dataframe(tc_df, use_container_width=True, hide_index=True)
            else:
                st.info("缺少 time_feature_columns 信息。")
        with p2:
            st.markdown("**坐标来源统计**")
            if isinstance(coord_count, dict) and coord_count:
                cc_df = pd.DataFrame({"coord_source": list(coord_count.keys()), "count": [int(v) for v in coord_count.values()]})
                st.dataframe(cc_df, use_container_width=True, hide_index=True)
            else:
                st.info("缺少 coordinate_source_count 信息。")
        with p3:
            st.markdown("**因子公式**")
            if isinstance(formulas, dict) and formulas:
                fm_df = pd.DataFrame({"factor": list(formulas.keys()), "formula": [str(v) for v in formulas.values()]})
                st.dataframe(fm_df, use_container_width=True, hide_index=True)
            else:
                st.info("缺少 factor_formulas 信息。")
    else:
        st.info("warning_report 中没有 node_weather_generation 字段。")

    source_text = "；".join([f"{k}: {v}" for k, v in source.items()]) if source else "无"
    st.caption(f"数据来源: {source_text}")


def render_dispatch(bundle: dict, sh: pd.DataFrame, flt: dict) -> None:
    st.markdown("## Dispatch")
    strategy_now = "n/a"
    risk_now = "n/a"
    if not sh.empty:
        row = sh[sh["hour_index"] == flt["dispatch_hour"]]
        if row.empty:
            row = sh.head(1)
        if not row.empty:
            row = row.iloc[0]
            strategy_now = str(row.get("selected_strategy", "n/a"))
            if not pd.isna(row.get("hourly_line_risk", np.nan)):
                risk_now = f"{float(row['hourly_line_risk']):.4f}"
    render_summary(f"当前调度页主要回答“准备怎么调”。当前调度小时采用 {strategy_now}，对应风险摘要为 {risk_now}。")
    st.plotly_chart(fig_strip(sh, "24h 优化器切换条带图"), use_container_width=True)

    gen, res, flow, shed = bundle["generation"], bundle["reserve"], bundle["line_flow"], bundle["load_shedding"]
    c1, c2 = st.columns(2)

    with c1:
        if not gen.empty:
            g = gen.copy()
            val_cols = [x for x in g.columns if x != "timestamp"]
            for c in val_cols:
                g[c] = pd.to_numeric(g[c], errors="coerce")
            gl = g.melt(id_vars="timestamp", var_name="unit", value_name="mw")
            st.plotly_chart(px.area(gl, x="timestamp", y="mw", color="unit", title="发电计划堆叠面积图"), use_container_width=True)

    with c2:
        if not res.empty:
            r = res.copy()
            r["reserve_up"] = pd.to_numeric(r["reserve_up"], errors="coerce")
            r["reserve_down"] = pd.to_numeric(r["reserve_down"], errors="coerce")
            merged = r.merge(sh[["timestamp", "hourly_line_risk"]], on="timestamp", how="left") if not sh.empty else r
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            fig.add_trace(go.Scatter(x=merged["timestamp"], y=merged["reserve_up"], name="reserve_up"), secondary_y=False)
            fig.add_trace(go.Scatter(x=merged["timestamp"], y=merged["reserve_down"], name="reserve_down"), secondary_y=False)
            if "hourly_line_risk" in merged.columns:
                fig.add_trace(go.Scatter(x=merged["timestamp"], y=merged["hourly_line_risk"], name="risk", line=dict(color="#d64b45", dash="dot")), secondary_y=True)
            fig.update_layout(title="备用容量折线图（叠加风险）", height=320, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig, use_container_width=True)

    if not flow.empty:
        pv = flow.pivot_table(index="line_id", columns="timestamp", values="loading", aggfunc="max")
        st.plotly_chart(px.imshow(pv, aspect="auto", color_continuous_scale="Blues", title="线路负载率热图"), use_container_width=True)

    d1, d2 = st.columns([1.2, 0.8])
    with d1:
        if not shed.empty:
            total = shed.groupby("timestamp", as_index=False)["shed_MW"].sum()
            st.plotly_chart(px.bar(total, x="timestamp", y="shed_MW", title="负荷削减总量"), use_container_width=True)

    with d2:
        st.markdown("### 小时详情")
        if not sh.empty:
            row = sh[sh["hour_index"] == flt["dispatch_hour"]]
            if row.empty:
                row = sh.head(1)
            row = row.iloc[0]
            ts = row["timestamp"]
            total_gen = 0.0
            if not gen.empty:
                g = gen[gen["timestamp"] == ts]
                if not g.empty:
                    total_gen = pd.to_numeric(g.drop(columns=["timestamp"]).iloc[0], errors="coerce").sum()
            reserve_up = 0.0
            if not res.empty:
                r = res[res["timestamp"] == ts]
                if not r.empty:
                    reserve_up = float(pd.to_numeric(r["reserve_up"], errors="coerce").iloc[0])
            shed_amt = float(shed[shed["timestamp"] == ts]["shed_MW"].sum()) if not shed.empty else 0.0
            max_loading = float(flow[flow["timestamp"] == ts]["loading"].max()) if not flow.empty else 0.0

            st.write(f"- 时间: `{ts}`")
            st.write(f"- 选用模型: `{row['selected_strategy']}`")
            st.write(f"- 风险摘要: `{float(row['hourly_line_risk']):.4f}`")
            st.write(f"- 总发电量: `{total_gen:.6f}`")
            st.write(f"- 总备用量(上调): `{reserve_up:.6f}`")
            st.write(f"- 负荷削减量: `{shed_amt:.6f}`")
            st.write(f"- 关键线路最大负载率: `{max_loading:.6f}`")


def render_resilience(bundle: dict) -> None:
    st.markdown("## Resilience")
    top, met = bundle["topsis"], bundle["resilience"]
    multi = bundle.get("multi_report", {})

    c1, c2 = st.columns(2)
    with c1:
        if not top.empty:
            t = top.copy()
            t["score"] = pd.to_numeric(t["score"], errors="coerce")
            st.plotly_chart(px.bar(t.sort_values("score", ascending=False), x="policy", y="score", color="policy", title="策略总排名（TOPSIS）"), use_container_width=True)

    with c2:
        if not met.empty:
            m = met.copy()
            cols = [x for x in m.columns if x != "policy"]
            for c in cols:
                m[c] = pd.to_numeric(m[c], errors="coerce")
            st.plotly_chart(px.bar(m.melt(id_vars="policy", var_name="metric", value_name="value"), x="metric", y="value", color="policy", barmode="group", title="指标分组柱状图"), use_container_width=True)

    d1, d2 = st.columns(2)
    with d1:
        w = multi.get("ewm_weights", {}) if isinstance(multi, dict) else {}
        if w:
            wd = pd.DataFrame({"indicator": list(w.keys()), "weight": list(w.values())})
            st.plotly_chart(px.bar(wd, x="indicator", y="weight", title="EWM 权重图", color="indicator"), use_container_width=True)

    with d2:
        if not met.empty:
            m = met.copy()
            cols = [x for x in m.columns if x != "policy"]
            for c in cols:
                m[c] = pd.to_numeric(m[c], errors="coerce")
            fig = go.Figure()
            for _, row in m.iterrows():
                vals = row[cols].tolist()
                fig.add_trace(go.Scatterpolar(r=vals + [vals[0]], theta=cols + [cols[0]], fill="toself", name=row["policy"]))
            fig.update_layout(title="雷达图", height=320)
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 结论区")
    if not top.empty:
        t = top.copy()
        t["rank"] = pd.to_numeric(t["rank"], errors="coerce")
        t = t.sort_values("rank")
        for _, row in t.iterrows():
            st.write(f"{int(row['rank'])}. `{row['policy']}`")
    st.info("结果表明，关键负荷优先与备用容量配置的结合在多指标韧性评估中表现最佳。")


def render_export(bundle: dict, sh: pd.DataFrame) -> None:
    st.markdown("## Export")
    options = [
        "图1 Pipeline 全流程图", "图2 72h 失效概率热图", "图3 风险驱动模型切换图", "图4 线路负载率热图", "图5 策略 TOPSIS 对比图", "图6 Stage8 实验对比图"
    ]
    sel = st.selectbox("选择导出图", options)

    if sel == options[0]:
        fig = go.Figure(go.Sankey(node=dict(label=["S1","S2","S3","S4","S5","S6","S7"]), link=dict(source=[0,1,2,3,4,5], target=[1,2,3,4,5,6], value=[1,1,1,1,1,1])))
    elif sel == options[1]:
        cf = bundle["component_failure"].copy()
        cf["hour_index"] = ((cf["hour"] - cf["hour"].min()).dt.total_seconds() / 3600).astype(int)
        cf["failure_prob"] = pd.to_numeric(cf["failure_prob"], errors="coerce")
        fig = px.imshow(cf.pivot_table(index="line", columns="hour_index", values="failure_prob", aggfunc="mean"), aspect="auto", color_continuous_scale="YlOrRd")
    elif sel == options[2]:
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True)
        fig.add_trace(go.Scatter(x=sh["timestamp"], y=sh["hourly_line_risk"], name="risk"), row=1, col=1)
        fig.add_trace(go.Heatmap(z=[sh["selected_strategy"].map({"SCUC":0,"Stochastic_UC":1,"Robust_UC":2}).fillna(0).tolist()], x=sh["timestamp"], y=["strategy"], showscale=False), row=2, col=1)
    elif sel == options[3]:
        flow = bundle["line_flow"]
        fig = px.imshow(flow.pivot_table(index="line_id", columns="timestamp", values="loading", aggfunc="max"), aspect="auto", color_continuous_scale="Blues")
    elif sel == options[5]:
        exp_cmp = bundle.get("experiment_metrics_comparison", pd.DataFrame())
        long_cmp = exp_cmp.melt(id_vars=["group"], value_vars=["total_shed", "total_served", "total_reserve"], var_name="metric", value_name="value") if not exp_cmp.empty else pd.DataFrame()
        fig = px.bar(long_cmp, x="metric", y="value", color="group", barmode="group")
    else:
        fig = px.bar(bundle["topsis"], x="policy", y="score", color="policy")

    fig.update_layout(height=440, margin=dict(l=10, r=10, t=40, b=10), title=sel)
    st.plotly_chart(fig, use_container_width=True)
    st.download_button("下载当前图 (HTML)", data=fig.to_html(include_plotlyjs="cdn").encode("utf-8"), file_name=f"{sel}.html", mime="text/html")
    st.caption("PNG 可通过图表右上角相机按钮导出。")

    summary = bundle.get("summary", {})
    chain = summary.get("selected_chain", {}) if isinstance(summary, dict) else {}
    run_cfg = pd.DataFrame([
        ["mode", summary.get("mode", "baseline")],
        ["failure_model", chain.get("failure_model", "")],
        ["contingency_method", chain.get("contingency_method", "")],
        ["reserve_ratio", chain.get("reserve_ratio", "")],
        ["n_scenarios", chain.get("n_scenarios", "")],
    ], columns=["key", "value"])
    dist = sh["selected_strategy"].value_counts().rename_axis("selected_strategy").reset_index(name="hours_selected") if not sh.empty else pd.DataFrame()

    for name, table in [
        ("表1 运行配置表", run_cfg),
        ("表2 策略指标汇总表", bundle["summary_indicator"]),
        ("表3 调度模型小时分布表", dist),
        ("表4 高风险组件 Top-K 表", bundle["line_risk"].sort_values("risk_prob", ascending=False).head(10) if not bundle["line_risk"].empty else pd.DataFrame()),
        ("表5 Stage8 实验对比表", bundle.get("experiment_metrics_comparison", pd.DataFrame())),
        ("表6 Stage8 动作统计表", bundle.get("action_type_summary", pd.DataFrame())),
    ]:
        st.markdown(f"### {name}")
        if not table.empty:
            st.dataframe(table, use_container_width=True, hide_index=True)
            st.download_button(f"下载 {name} (CSV)", data=table.to_csv(index=False).encode("utf-8"), file_name=f"{name}.csv", mime="text/csv")


def build_filters(bundle: dict, sh: pd.DataFrame) -> dict:
    scen = sorted(bundle["contingency"]["scenario"].dropna().astype(str).unique().tolist()) if not bundle["contingency"].empty else ["S1"]
    pol = bundle["topsis"]["policy"].astype(str).tolist() if not bundle["topsis"].empty else ["priority_with_reserve"]

    d_min, d_max = (0, 23)
    if not sh.empty:
        d_min = int(pd.to_numeric(sh["hour_index"], errors="coerce").min())
        d_max = int(pd.to_numeric(sh["hour_index"], errors="coerce").max())

    t_min, t_max = (0, 71)
    if not bundle["component_failure"].empty:
        x = ((bundle["component_failure"]["hour"] - bundle["component_failure"]["hour"].min()).dt.total_seconds() / 3600).dropna()
        if not x.empty:
            t_min, t_max = int(x.min()), int(x.max())

    st.sidebar.markdown("## 全局筛选器")
    return {
        "policy_name": st.sidebar.selectbox("策略", pol, index=0),
        "scenario_name": st.sidebar.selectbox("场景", scen, index=0),
        "dispatch_hour": st.sidebar.slider("调度小时(24h)", d_min, d_max, d_min),
        "typhoon_hour": st.sidebar.slider("台风小时(72h)", t_min, t_max, t_min),
        "risk_threshold": st.sidebar.slider("风险阈值", 0.0, 1.0, 0.35, 0.01),
        "top_k": st.sidebar.slider("Top-K", 3, 15, 5, 1),
    }


def main() -> None:
    st.title("GridAgent1 可视化原型")
    st.caption("按 Stage1~Stage8 研究逻辑组织，支持分析、展示与论文导出。")

    standard_runs = discover_standard_runs()
    framework_runs = discover_framework_runs()
    if not standard_runs and not framework_runs:
        st.error("未找到可用结果目录（*_standard 或 results/gridagent_framework/*）。")
        return

    run_options: list[str] = []
    run_map: dict[str, tuple[str, Path]] = {}
    for p in standard_runs:
        label = f"[standard] {p.name}"
        run_options.append(label)
        run_map[label] = ("standard", p)
    for p in framework_runs:
        label = f"[framework] {p.name}"
        run_options.append(label)
        run_map[label] = ("framework", p)

    default_label = None
    preferred_fw = "formal2024_full_metapath_tuned_20260407"
    if framework_runs:
        preferred_path = next((p for p in framework_runs if p.name == preferred_fw), None)
        latest_fw = preferred_path or sorted(framework_runs)[-1]
        default_label = f"[framework] {latest_fw.name}"
    else:
        for p in standard_runs:
            if "formal2024_full_baseline_20260310_233109_standard" in p.name:
                default_label = f"[standard] {p.name}"
                break
    if default_label is None and run_options:
        default_label = run_options[0]
    default_idx = run_options.index(default_label) if default_label in run_options else 0

    picked = st.sidebar.selectbox("结果目录", run_options, index=default_idx)
    run_kind, run_path = run_map[picked]
    cache_key = compute_bundle_cache_key(run_path=run_path, run_kind=run_kind)
    bundle = load_bundle(str(run_path), run_kind=run_kind, cache_key=cache_key)
    st.sidebar.caption(f"当前来源: `{run_kind}`")
    stage8_ready = (run_path / "stage8_steady_state_physics").exists()
    st.sidebar.caption(f"Stage8 输出: {'已检测到' if stage8_ready else '未检测到'}")
    sh = strategy_hourly(bundle)

    mode = st.sidebar.radio("界面模式", ["运行驾驶舱", "研究分析台"], index=0)
    if mode == "运行驾驶舱":
        page = st.sidebar.radio(
            "页面导航",
            ["驾驶舱总览", "风险诊断", "调度与动作", "闭环评估"],
            index=0,
        )
    else:
        page = st.sidebar.radio(
            "页面导航",
            ["Overview", "Pipeline View", "Scenario & Failure", "Warning", "Node Weather", "MetaPath", "Dispatch", "Stage8 Physics", "Resilience", "Export"],
            index=7,
        )
    flt = build_filters(bundle, sh)
    render_status_bar(
        [
            ("当前 Run", run_path.name),
            ("界面模式", mode),
            ("当前页面", page),
            ("调度小时", str(flt["dispatch_hour"])),
            ("场景", str(flt["scenario_name"])),
            ("Stage8", "已接入" if stage8_ready else "未接入"),
        ]
    )

    if page == "驾驶舱总览":
        render_operational_cockpit(bundle, sh, flt)
    elif page == "风险诊断":
        render_warning(bundle, sh, flt)
    elif page == "调度与动作":
        render_dispatch(bundle, sh, flt)
    elif page == "闭环评估":
        render_stage8(bundle, flt)
    elif page == "Overview":
        render_overview(bundle, sh, flt)
    elif page == "Pipeline View":
        render_pipeline()
    elif page == "Scenario & Failure":
        render_scenario_failure(bundle, flt)
    elif page == "Warning":
        render_warning(bundle, sh, flt)
    elif page == "Node Weather":
        render_node_weather(bundle, flt)
    elif page == "MetaPath":
        render_metapath(bundle, flt)
    elif page == "Dispatch":
        render_dispatch(bundle, sh, flt)
    elif page == "Stage8 Physics":
        render_stage8(bundle, flt)
    elif page == "Resilience":
        render_resilience(bundle)
    elif page == "Export":
        render_export(bundle, sh)


if __name__ == "__main__":
    main()
