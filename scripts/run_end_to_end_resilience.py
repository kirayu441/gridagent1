from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def run_cmd(cmd: list[str], cwd: Path) -> None:
    print(">>", " ".join(cmd))
    proc = subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(
            f"command failed ({proc.returncode}): {' '.join(cmd)}\n"
            f"STDOUT:\n{proc.stdout}\n\nSTDERR:\n{proc.stderr}"
        )
    if proc.stdout.strip():
        print(proc.stdout.strip())
    if proc.stderr.strip():
        print(proc.stderr.strip())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="One-click end-to-end resilience workflow: failure -> contingency -> scheduling -> multi-criteria assessment."
    )
    parser.add_argument("--grid", default="data_final/formal_guangdong_2024/grid_topology.json", help="Grid topology path.")
    parser.add_argument(
        "--run-suffix",
        default="",
        help="Optional suffix for output folders. If empty, timestamp is used.",
    )
    parser.add_argument("--model", choices=("batts", "schloemer"), default="schloemer", help="Wind field model for failure stage.")
    parser.add_argument("--hours", type=int, default=72, help="Typhoon duration hours in failure stage.")
    parser.add_argument("--start-time", default="2024-09-01 00:00:00", help="Typhoon start timestamp.")
    parser.add_argument("--n-scenarios", type=int, default=256, help="Contingency scenario count.")
    parser.add_argument("--reserve-ratio", type=float, default=0.15, help="Reserve ratio in scheduling stage.")
    parser.add_argument("--seed", type=int, default=42, help="Global random seed.")
    parser.add_argument("--skip-failure", action="store_true", help="Skip failure stage (use existing output directory).")
    parser.add_argument("--skip-contingency", action="store_true", help="Skip contingency stage.")
    parser.add_argument("--skip-scheduling", action="store_true", help="Skip scheduling stage.")
    parser.add_argument("--skip-assessment", action="store_true", help="Skip multi-criteria assessment stage.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = project_root()
    scripts_dir = root / "scripts"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = args.run_suffix.strip() or timestamp

    failure_dir = root / "results" / "component_failure_probability" / f"formal2024_{suffix}"
    contingency_dir = root / "results" / "spatiotemporal_contingency" / f"formal2024_{args.model}_{suffix}"
    scheduling_dir = root / "results" / "load_prioritization_scheduling" / f"formal2024_{args.model}_{suffix}"
    assessment_dir = root / "results" / "multi_criteria_resilience" / f"formal2024_{args.model}_{suffix}"

    grid_path = root / args.grid
    failure_csv = failure_dir / f"line_failure_timeseries_{args.model}.csv"
    contingency_tensor = contingency_dir / "contingency_tensor_wang_qmc.npy"
    policy_comparison = scheduling_dir / "policy_comparison.csv"
    worst_detail = scheduling_dir / "worst_scenario_shedding_detail.csv"

    if not args.skip_failure:
        run_cmd(
            [
                "python",
                str(scripts_dir / "component_failure_probability.py"),
                "--model",
                args.model,
                "--grid",
                str(grid_path),
                "--output-dir",
                str(failure_dir),
                "--hours",
                str(args.hours),
                "--start-time",
                args.start_time,
            ],
            cwd=root,
        )
    else:
        if not failure_csv.exists():
            raise FileNotFoundError(f"skip-failure enabled but file missing: {failure_csv}")

    if not args.skip_contingency:
        run_cmd(
            [
                "python",
                str(scripts_dir / "spatiotemporal_contingency_generator.py"),
                "--methods",
                "all",
                "--failure-csv",
                str(failure_csv),
                "--grid",
                str(grid_path),
                "--output-dir",
                str(contingency_dir),
                "--n-scenarios",
                str(args.n_scenarios),
                "--seed",
                str(args.seed),
            ],
            cwd=root,
        )
    else:
        if not contingency_tensor.exists():
            raise FileNotFoundError(f"skip-contingency enabled but file missing: {contingency_tensor}")

    if not args.skip_scheduling:
        run_cmd(
            [
                "python",
                str(scripts_dir / "load_prioritization_scheduling.py"),
                "--grid",
                str(grid_path),
                "--trim-input",
                str(root / "data_final" / "formal_guangdong_2024" / "TRIM_input.csv"),
                "--contingency-tensor",
                str(contingency_tensor),
                "--failure-csv",
                str(failure_csv),
                "--uncertainty-dir",
                str(root / "results" / "wind_pv_uncertainty" / "formal2024"),
                "--output-dir",
                str(scheduling_dir),
                "--reserve-ratio",
                str(args.reserve_ratio),
                "--seed",
                str(args.seed),
            ],
            cwd=root,
        )
    else:
        if not policy_comparison.exists() or not worst_detail.exists():
            raise FileNotFoundError(
                f"skip-scheduling enabled but required files missing: {policy_comparison} / {worst_detail}"
            )

    if not args.skip_assessment:
        run_cmd(
            [
                "python",
                str(scripts_dir / "multi_criteria_resilience_assessment.py"),
                "--policy-comparison",
                str(policy_comparison),
                "--worst-detail",
                str(worst_detail),
                "--output-dir",
                str(assessment_dir),
            ],
            cwd=root,
        )

    summary = {
        "run_suffix": suffix,
        "model": args.model,
        "hours": args.hours,
        "n_scenarios": args.n_scenarios,
        "outputs": {
            "failure_dir": str(failure_dir),
            "contingency_dir": str(contingency_dir),
            "scheduling_dir": str(scheduling_dir),
            "assessment_dir": str(assessment_dir),
            "assessment_indicator_table": str(assessment_dir / "indicator_table.csv"),
            "assessment_topsis": str(assessment_dir / "ewm_topsis_result.csv"),
        },
    }
    summary_path = root / "results" / "end_to_end_resilience_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nDone. summary -> {summary_path}")


if __name__ == "__main__":
    main()

