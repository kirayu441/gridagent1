"""Detailed analysis of Stage1-3 comparison results"""
import pandas as pd
import numpy as np

print("="*80)
print("STAGE1: DPGMM SCENARIO ANALYSIS")
print("="*80)

df_typical = pd.read_csv("results/ablation/stage123_comparison/stage1_uncertainty/dpgmm/formal2024/typical_scenarios_long.csv")
print(f"Total records: {len(df_typical)}")
print(f"Unique scenarios: {df_typical['scenario_id'].nunique()}")
print(f"Scenario probabilities: {df_typical['scenario_probability'].unique()}")
print(f"Timestamps per scenario: {len(df_typical) // df_typical['scenario_id'].nunique()}")

print("\nWind Statistics:")
print(f"  Mean: {df_typical['wind'].mean():.4f}")
print(f"  Std:  {df_typical['wind'].std():.4f}")
print(f"  Min:  {df_typical['wind'].min():.4f}")
print(f"  Max:  {df_typical['wind'].max():.4f}")

print("\nPV Statistics:")
print(f"  Mean: {df_typical['pv'].mean():.4f}")
print(f"  Std:  {df_typical['pv'].std():.4f}")
print(f"  Min:  {df_typical['pv'].min():.4f}")
print(f"  Max:  {df_typical['pv'].max():.4f}")

# Stage2 comparison
print("\n" + "="*80)
print("STAGE2: FAILURE PROBABILITY COMPARISON")
print("="*80)

df_schloemer = pd.read_csv("results/ablation/stage123_comparison/stage2_failure/schloemer/line_failure_timeseries_schloemer.csv")
df_batts = pd.read_csv("results/ablation/stage123_comparison/stage2_failure/batts/line_failure_timeseries_batts.csv")

print(f"\nLines analyzed: {df_schloemer['line_id'].nunique()}")
print(f"Time steps: {df_schloemer['timestamp'].nunique()}")

print("\n--- Wind Speed Comparison (v_surface_ms) ---")
print(f"Schloemer: mean={df_schloemer['v_surface_ms'].mean():.2f}, std={df_schloemer['v_surface_ms'].std():.2f}, max={df_schloemer['v_surface_ms'].max():.2f}")
print(f"Batts:     mean={df_batts['v_surface_ms'].mean():.2f}, std={df_batts['v_surface_ms'].std():.2f}, max={df_batts['v_surface_ms'].max():.2f}")

print("\n--- Failure Probability Comparison (p_line) ---")
print(f"Schloemer: mean={df_schloemer['p_line'].mean():.4f}, median={df_schloemer['p_line'].median():.4f}, max={df_schloemer['p_line'].max():.4f}")
print(f"Batts:     mean={df_batts['p_line'].mean():.4f}, median={df_batts['p_line'].median():.4f}, max={df_batts['p_line'].max():.4f}")

# Line-by-line comparison
print("\n--- Line-by-Line Comparison (Mean Failure Probability) ---")
print(f"{'Line ID':<10} {'Schloemer':<12} {'Batts':<12} {'Ratio':<10}")
print("-" * 44)
for line_id in df_schloemer['line_id'].unique():
    s_prob = df_schloemer[df_schloemer['line_id']==line_id]['p_line'].mean()
    b_prob = df_batts[df_batts['line_id']==line_id]['p_line'].mean()
    ratio = s_prob / b_prob if b_prob > 1e-10 else float('inf')
    print(f"{line_id:<10} {s_prob:<12.4f} {b_prob:<12.4f} {ratio:<10.1f}")

# Stage3 contingency analysis
print("\n" + "="*80)
print("STAGE3: CONTINGENCY SCENARIO ANALYSIS")
print("="*80)

df_c3po = pd.read_csv("results/ablation/stage123_comparison/stage3_contingency/c3po_ref/contingency_scenarios.csv")
print(f"\nTotal scenarios: {len(df_c3po)}")
print(f"Unique scenario IDs: {df_c3po['scenario_id'].nunique()}")
print(f"Time steps: {df_c3po['timestamp'].nunique()}")

# Temporal evolution
df_c3po['hour'] = pd.to_datetime(df_c3po['timestamp']).dt.hour
print("\n--- Failure Count Evolution (mean across scenarios) ---")
hourly_failures = df_c3po.groupby('hour')['outage_line_count'].mean()
print(f"{'Hour':<8} {'Mean Failed Lines':<18}")
print("-" * 26)
for h in [0, 3, 6, 9, 12, 15, 18, 21, 23]:
    if h in hourly_failures.index:
        print(f"{h:02d}:00     {hourly_failures[h]:.2f}")

# Disconnected load analysis
print("\n--- Disconnected Load Analysis ---")
print(f"Total scenarios with load disconnection: {(df_c3po['disconnected_load_count'] > 0).sum()}")
print(f"Max disconnected loads: {df_c3po['disconnected_load_count'].max()}")
print(f"Mean disconnected loads: {df_c3po['disconnected_load_count'].mean():.2f}")

# Save detailed report
with open("results/ablation/stage123_comparison/detailed_analysis.md", "w", encoding="utf-8") as f:
    f.write("# Stage1-3 Method Comparison - Detailed Analysis\n\n")
    f.write(f"Generated: Analysis completed\n\n")
    
    f.write("## Stage1: DPGMM Uncertainty Modeling\n\n")
    f.write("### Scenario Statistics\n")
    f.write(f"- Total scenarios: {df_typical['scenario_id'].nunique()}\n")
    f.write(f"- Scenario probabilities: {df_typical['scenario_probability'].unique()}\n")
    f.write(f"- Timestamps per scenario: {len(df_typical) // df_typical['scenario_id'].nunique()}\n\n")
    
    f.write("### Wind Power Statistics\n")
    f.write(f"- Mean: {df_typical['wind'].mean():.4f}\n")
    f.write(f"- Std: {df_typical['wind'].std():.4f}\n")
    f.write(f"- Range: [{df_typical['wind'].min():.4f}, {df_typical['wind'].max():.4f}]\n\n")
    
    f.write("### PV Power Statistics\n")
    f.write(f"- Mean: {df_typical['pv'].mean():.4f}\n")
    f.write(f"- Std: {df_typical['pv'].std():.4f}\n")
    f.write(f"- Range: [{df_typical['pv'].min():.4f}, {df_typical['pv'].max():.4f}]\n\n")
    
    f.write("## Stage2: Failure Probability Comparison\n\n")
    f.write("### Wind Speed Prediction\n")
    f.write(f"| Model | Mean | Std | Max |\n")
    f.write(f"|-------|------|-----|-----|\n")
    f.write(f"| Schloemer | {df_schloemer['v_surface_ms'].mean():.2f} | {df_schloemer['v_surface_ms'].std():.2f} | {df_schloemer['v_surface_ms'].max():.2f} |\n")
    f.write(f"| Batts | {df_batts['v_surface_ms'].mean():.2f} | {df_batts['v_surface_ms'].std():.2f} | {df_batts['v_surface_ms'].max():.2f} |\n\n")
    
    f.write("### Failure Probability\n")
    f.write(f"| Model | Mean | Median | Max |\n")
    f.write(f"|-------|------|--------|-----|\n")
    f.write(f"| Schloemer | {df_schloemer['p_line'].mean():.4f} | {df_schloemer['p_line'].median():.4f} | {df_schloemer['p_line'].max():.4f} |\n")
    f.write(f"| Batts | {df_batts['p_line'].mean():.4f} | {df_batts['p_line'].median():.4f} | {df_batts['p_line'].max():.4f} |\n\n")
    
    f.write("### Line-by-Line Comparison\n")
    f.write(f"| Line | Schloemer | Batts | Ratio |\n")
    f.write(f"|------|-----------|-------|-------|\n")
    for line_id in df_schloemer['line_id'].unique():
        s_prob = df_schloemer[df_schloemer['line_id']==line_id]['p_line'].mean()
        b_prob = df_batts[df_batts['line_id']==line_id]['p_line'].mean()
        ratio = s_prob / b_prob if b_prob > 1e-10 else float('inf')
        f.write(f"| {line_id} | {s_prob:.4f} | {b_prob:.4f} | {ratio:.1f} |\n")
    
    f.write("\n## Stage3: Contingency Scenario Analysis\n\n")
    f.write("### Scenario Generation Summary\n")
    f.write(f"- Total scenarios: {len(df_c3po)}\n")
    f.write(f"- Unique scenario IDs: {df_c3po['scenario_id'].nunique()}\n")
    f.write(f"- Time steps: {df_c3po['timestamp'].nunique()}\n\n")
    
    f.write("### Hourly Failure Evolution\n")
    f.write(f"| Hour | Mean Failed Lines |\n")
    f.write(f"|------|-------------------|\n")
    for h in [0, 3, 6, 9, 12, 15, 18, 21, 23]:
        if h in hourly_failures.index:
            f.write(f"| {h:02d}:00 | {hourly_failures[h]:.2f} |\n")
    
    f.write("\n### Load Disconnection\n")
    f.write(f"- Scenarios with load disconnection: {(df_c3po['disconnected_load_count'] > 0).sum()}\n")
    f.write(f"- Max disconnected loads: {df_c3po['disconnected_load_count'].max()}\n")
    f.write(f"- Mean disconnected loads: {df_c3po['disconnected_load_count'].mean():.2f}\n")

print("\nDetailed analysis saved to: results/ablation/stage123_comparison/detailed_analysis.md")
