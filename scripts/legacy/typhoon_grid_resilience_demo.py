"""
论文《Electronics 2024, 13, 745》方法链路的简化可运行复现代码。

核心复现环节：
1) 台风参数风场模型（Batts / Schloemer / Jelesnianski-II / Holland）
2) 边界层与阵风修正
3) 滚动 DPGMM（BayesianGaussianMixture 近似）
4) 应力-强度干涉失效概率
5) 时序故障集（准蒙特卡洛）
6) MATPOWER OPF 负荷切除 + R1~R6 指标 + EWM-TOPSIS

说明：本脚本已接入真实 MATPOWER 潮流/最优潮流求解，不使用“供需平衡+输电折损”的近似作为主流程。
      但为了可运行性与解释性，仍保留部分简化参数与示例数据构造。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Dict, Iterable, List, Tuple

import numpy as np
import pandapower.networks as ppn
from scipy.io import loadmat, savemat
from scipy.stats import norm, qmc
from sklearn.cluster import KMeans
from sklearn.mixture import BayesianGaussianMixture


@dataclass
class TyphoonState:
    """台风轨迹上的一个时刻状态。"""

    t: int
    lat: float
    lon: float
    central_pressure_hpa: float
    peripheral_pressure_hpa: float
    vmax_ms: float
    move_speed_ms: float
    move_dir_deg: float


@dataclass
class LineAsset:
    """输电线路资产参数，用于风荷载与失效概率评估。"""

    line_id: str
    lat1: float
    lon1: float
    lat2: float
    lon2: float
    towers: int
    spans: int
    design_line_load_n: float
    design_tower_load_kn: float

    @property
    def mid_lat(self) -> float:
        return (self.lat1 + self.lat2) / 2.0

    @property
    def mid_lon(self) -> float:
        return (self.lon1 + self.lon2) / 2.0


@dataclass
class LoadNode:
    """负荷节点，priority_level: 1(高) / 2(中) / 3(低)。"""

    node_id: str
    demand_mw: float
    priority_level: int


def estimate_rmax_km(peripheral_pressure_hpa: float, central_pressure_hpa: float) -> float:
    """论文公式(1): Rmax = exp(5.0237 - 0.0247 * ΔP)。"""
    delta_p = max(peripheral_pressure_hpa - central_pressure_hpa, 1e-3)
    return float(np.exp(5.0237 - 0.0247 * delta_p))


def latlon_delta_km(origin_lat: float, origin_lon: float, target_lat: float, target_lon: float) -> Tuple[float, float]:
    """将经纬度差近似换算为平面坐标差，返回 (东向km, 北向km)。"""
    mean_lat_rad = np.deg2rad((origin_lat + target_lat) / 2.0)
    dx_east_km = (target_lon - origin_lon) * 111.32 * np.cos(mean_lat_rad)
    dy_north_km = (target_lat - origin_lat) * 110.57
    return float(dx_east_km), float(dy_north_km)


def _circular_vector_with_inflow(vr: float, dx_east_km: float, dy_north_km: float, inflow_deg: float = 20.0) -> Tuple[float, float]:
    """
    论文公式(12)思路：将环流风速按入流角投影到平面坐标。
    返回 (东向分量, 北向分量)。
    """
    r = np.hypot(dx_east_km, dy_north_km)
    if r < 1e-6:
        return 0.0, 0.0
    theta = np.deg2rad(inflow_deg)
    x = dy_north_km
    y = dx_east_km
    a_coeff = -(y * np.cos(theta) + x * np.sin(theta)) / r
    b_coeff = (x * np.cos(theta) - y * np.sin(theta)) / r
    return float(vr * b_coeff), float(vr * a_coeff)


def _moving_vector(vm: float, move_dir_deg: float) -> Tuple[float, float]:
    """台风移动风速分解（北=0度，顺时针）。"""
    rad = np.deg2rad(move_dir_deg)
    return float(vm * np.sin(rad)), float(vm * np.cos(rad))


def batts_model_components(r_km: float, rmax_km: float, vmax_ms: float, move_speed_ms: float, a: float = 0.5) -> Tuple[float, float]:
    """Batts 模型（公式(3)）。"""
    r_km = max(r_km, 1e-6)
    rmax_km = max(rmax_km, 1e-6)
    if r_km <= rmax_km:
        vr = vmax_ms * (r_km / rmax_km)
    else:
        vr = vmax_ms * (rmax_km / r_km) ** a
    return float(vr), float(move_speed_ms)


def schloemer_model_components(r_km: float, rmax_km: float, vmax_ms: float, move_speed_ms: float) -> Tuple[float, float]:
    """Schloemer 模型（公式(4)(5)）。"""
    r_km = max(r_km, 1e-6)
    rmax_km = max(rmax_km, 1e-6)
    vr = vmax_ms * (rmax_km / r_km) * np.exp(1.0 - rmax_km / r_km)
    numerator = 3.0 * (rmax_km**1.5) * (r_km**1.5)
    denominator = (rmax_km**3) + (r_km**3) + (rmax_km**1.5) * (r_km**1.5)
    vm = move_speed_ms * numerator / max(denominator, 1e-9)
    return float(vr), float(vm)


def jelesnianski_model_components(r_km: float, rmax_km: float, vmax_ms: float, move_speed_ms: float) -> Tuple[float, float]:
    """Jelesnianski-II 模型（公式(7)(8)）。"""
    r_km = max(r_km, 1e-6)
    rmax_km = max(rmax_km, 1e-6)
    vr = vmax_ms * (2.0 * rmax_km * r_km) / (rmax_km**2 + r_km**2)
    if r_km <= rmax_km:
        vm = move_speed_ms * r_km / (r_km + rmax_km)
    else:
        vm = move_speed_ms * rmax_km / (r_km + rmax_km)
    return float(vr), float(vm)


def holland_model_components(
    r_km: float,
    rmax_km: float,
    vmax_ms: float,
    move_speed_ms: float,
    center_lat_deg: float,
    pc_hpa: float,
    p_inf_hpa: float,
    rg_km: float = 300.0,
) -> Tuple[float, float]:
    """Holland 模型（公式(9)(10)(11)）。"""
    r_km = max(r_km, 1e-3)
    rmax_km = max(rmax_km, 1e-3)
    b_param = max(1.0036 + 0.0173 * vmax_ms - 0.0313 * np.log(rmax_km), 0.1)

    x = r_km / rmax_km
    pressure_diff_pa = (p_inf_hpa - pc_hpa) * 100.0
    exp_term = np.exp(-(x ** (-b_param)))
    d_p_dr = pressure_diff_pa * exp_term * b_param * (x ** (-b_param - 1.0)) / (rmax_km * 1000.0)

    omega = 7.292e-5
    coriolis_f = 2.0 * omega * np.sin(np.deg2rad(center_lat_deg))
    air_density = 1.29
    r_m = r_km * 1000.0
    inside = max((coriolis_f**2) * (r_m**2) / 4.0 + (r_m / air_density) * d_p_dr, 0.0)
    vr = max(np.sqrt(inside) - coriolis_f * r_m / 2.0, 0.0)
    vm = move_speed_ms * np.exp(-np.pi * r_km / max(rg_km, 1e-3))
    return float(vr), float(vm)


def typhoon_wind_speed_gradient(state: TyphoonState, target_lat: float, target_lon: float, model_name: str) -> float:
    """在目标点计算梯度层风速。"""
    dx_east_km, dy_north_km = latlon_delta_km(state.lat, state.lon, target_lat, target_lon)
    r_km = max(np.hypot(dx_east_km, dy_north_km), 1e-6)
    rmax_km = estimate_rmax_km(state.peripheral_pressure_hpa, state.central_pressure_hpa)

    if model_name == "batts":
        vr, vm = batts_model_components(r_km, rmax_km, state.vmax_ms, state.move_speed_ms)
    elif model_name == "schloemer":
        vr, vm = schloemer_model_components(r_km, rmax_km, state.vmax_ms, state.move_speed_ms)
    elif model_name == "jelesnianski":
        vr, vm = jelesnianski_model_components(r_km, rmax_km, state.vmax_ms, state.move_speed_ms)
    elif model_name == "holland":
        vr, vm = holland_model_components(
            r_km=r_km,
            rmax_km=rmax_km,
            vmax_ms=state.vmax_ms,
            move_speed_ms=state.move_speed_ms,
            center_lat_deg=state.lat,
            pc_hpa=state.central_pressure_hpa,
            p_inf_hpa=state.peripheral_pressure_hpa,
        )
    else:
        raise ValueError(f"Unsupported model_name={model_name}")

    vr_east, vr_north = _circular_vector_with_inflow(vr, dx_east_km, dy_north_km, inflow_deg=20.0)
    vm_east, vm_north = _moving_vector(vm, state.move_dir_deg)
    return float(np.hypot(vr_east + vm_east, vr_north + vm_north))


def boundary_layer_and_gust_correction(v_gradient_ms: float) -> float:
    """论文公式(13)(14)近似：边界层折减 + 1h到10min风速转换。"""
    alpha = 0.8 if v_gradient_ms > 40.0 else 0.71
    return float(1.08 * alpha * v_gradient_ms)


class RollingDPGMM:
    """
    用 BayesianGaussianMixture 近似滚动 DPGMM。
    - 每个时刻用局部窗口拟合一套混合模型；
    - 从各时刻模型采样并拼成轨迹。
    """

    def __init__(self, window_radius: int = 3, max_components: int = 8, random_state: int = 42) -> None:
        self.window_radius = window_radius
        self.max_components = max_components
        self.random_state = random_state

    def fit_models(self, wind_speed_ms: np.ndarray, pv_output_mw: np.ndarray) -> List[BayesianGaussianMixture]:
        if len(wind_speed_ms) != len(pv_output_mw):
            raise ValueError("wind_speed_ms 与 pv_output_mw 长度不一致")
        x = np.column_stack([wind_speed_ms, pv_output_mw])
        total_steps = x.shape[0]
        models: List[BayesianGaussianMixture] = []

        for t in range(total_steps):
            lo = max(0, t - self.window_radius)
            hi = min(total_steps, t + self.window_radius + 1)
            window_data = x[lo:hi]
            if window_data.shape[0] < 3:
                rng = np.random.default_rng(self.random_state + t)
                jitter = rng.normal(0.0, 1e-3, size=(3 - window_data.shape[0], 2))
                window_data = np.vstack([window_data, window_data[:1] + jitter])

            n_comp = min(self.max_components, window_data.shape[0])
            model = BayesianGaussianMixture(
                n_components=n_comp,
                covariance_type="full",
                weight_concentration_prior_type="dirichlet_process",
                max_iter=600,
                random_state=self.random_state + t,
            )
            model.fit(window_data)
            models.append(model)
        return models

    def sample_trajectories(self, models: List[BayesianGaussianMixture], n_scenarios: int) -> np.ndarray:
        """返回 [n_scenarios, T, 2]，末维是(风速, PV)。"""
        total_steps = len(models)
        scenarios = np.zeros((n_scenarios, total_steps, 2), dtype=float)
        for t, model in enumerate(models):
            samples, _ = model.sample(n_scenarios)
            scenarios[:, t, :] = np.maximum(samples, 0.0)
        return scenarios


def reduce_scenarios_kmeans(scenarios: np.ndarray, n_typical: int = 10, random_state: int = 42) -> Tuple[np.ndarray, np.ndarray]:
    """KMeans 场景压缩，返回(典型场景, 概率)。"""
    n_samples, total_steps, dims = scenarios.shape
    n_clusters = min(n_typical, n_samples)
    flat = scenarios.reshape(n_samples, total_steps * dims)
    kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=20)
    labels = kmeans.fit_predict(flat)
    centers = kmeans.cluster_centers_.reshape(n_clusters, total_steps, dims)
    probs = np.array([(labels == i).mean() for i in range(n_clusters)], dtype=float)
    return centers, probs


def wind_turbine_power_curve(
    wind_speed_ms: float,
    vci: float = 3.0,
    vr: float = 12.0,
    vco: float = 25.0,
    rated_power_mw_per_turbine: float = 2.0,
    n_turbines: int = 10,
) -> float:
    """论文公式(16)风机功率曲线。"""
    v = wind_speed_ms
    p_rated_total = rated_power_mw_per_turbine * n_turbines
    if v <= vci or v > vco:
        return 0.0
    if v <= vr:
        return float(p_rated_total * (v**3 - vci**3) / max(vr**3 - vci**3, 1e-6))
    return float(p_rated_total)


def _alpha_uneven_coefficient(v_ms: float) -> float:
    """导线风压不均匀系数简化分段（论文仅描述随风速变化）。"""
    if v_ms < 20.0:
        return 1.0
    if v_ms < 30.0:
        return 1.2
    return 1.4


def line_wind_load_n(v_ms: float, theta_deg: float = 90.0, mu_z: float = 1.38, mu_sc: float = 1.1, beta_c: float = 1.0, d_mm: float = 18.0, lp_m: float = 300.0) -> float:
    """论文公式(17)：导线水平风荷载 Wx（N）。"""
    alpha = _alpha_uneven_coefficient(v_ms)
    sin_term = np.sin(np.deg2rad(theta_deg)) ** 2
    return float((alpha * mu_z * mu_sc * beta_c * d_mm * lp_m * (v_ms**2) * sin_term) / 1600.0)


def tower_wind_load_kn(v_ms: float, mu_z: float = 1.8, mu_s: float = 2.0, beta_z: float = 1.25, area_m2: float = 20.0) -> float:
    """论文公式(18)：杆塔风荷载 Ws（kN）。"""
    return float((mu_z * mu_s * beta_z * area_m2 * (v_ms**2)) / 1600.0)


def stress_strength_failure_probability(mu_actual: float, sigma_actual: float, mu_design: float, sigma_design: float) -> float:
    """
    论文公式(20)应力-强度干涉法：
    p(w>W) = 1 - Φ((mu_design-mu_actual)/sqrt(σw²+σW²))
    """
    sigma_total = np.sqrt(max(sigma_actual**2 + sigma_design**2, 1e-12))
    z = (mu_design - mu_actual) / sigma_total
    return float(1.0 - norm.cdf(z))


def line_failure_probability_series_system(p_tower: float, p_span: float, n_towers: int, n_spans: int) -> float:
    """论文公式(21)串联系统合成失效概率。"""
    return float(1.0 - ((1.0 - p_tower) ** n_towers) * ((1.0 - p_span) ** n_spans))


def compute_spatiotemporal_line_failure_probabilities(
    track: List[TyphoonState],
    lines: List[LineAsset],
    wind_model_name: str,
    design_scale: float = 1.0,
) -> Tuple[np.ndarray, np.ndarray]:
    """计算 [T,L] 风速与 [T,L] 线路失效概率。"""
    total_steps = len(track)
    n_lines = len(lines)
    line_wind_speed = np.zeros((total_steps, n_lines), dtype=float)
    line_failure_prob = np.zeros((total_steps, n_lines), dtype=float)

    for t, state in enumerate(track):
        for i, line in enumerate(lines):
            v_gradient = typhoon_wind_speed_gradient(state, line.mid_lat, line.mid_lon, wind_model_name)
            v_surface = boundary_layer_and_gust_correction(v_gradient)

            actual_line_load_n = line_wind_load_n(v_surface)
            actual_tower_load_kn = tower_wind_load_kn(v_surface)

            mu_design_line = line.design_line_load_n * design_scale
            sigma_design_line = mu_design_line * 0.03
            mu_design_tower = line.design_tower_load_kn * design_scale
            sigma_design_tower = mu_design_tower * 0.10

            sigma_actual_line = max(actual_line_load_n * 0.12, 1e-6)
            sigma_actual_tower = max(actual_tower_load_kn * 0.12, 1e-6)

            p_span = stress_strength_failure_probability(
                mu_actual=actual_line_load_n,
                sigma_actual=sigma_actual_line,
                mu_design=mu_design_line,
                sigma_design=sigma_design_line,
            )
            p_tower = stress_strength_failure_probability(
                mu_actual=actual_tower_load_kn,
                sigma_actual=sigma_actual_tower,
                mu_design=mu_design_tower,
                sigma_design=sigma_design_tower,
            )

            p_line = line_failure_probability_series_system(p_tower, p_span, line.towers, line.spans)
            line_wind_speed[t, i] = v_surface
            line_failure_prob[t, i] = np.clip(p_line, 0.0, 1.0)

    return line_wind_speed, line_failure_prob


def generate_spatiotemporal_contingencies(
    line_failure_prob: np.ndarray,
    n_scenarios: int,
    warning_end_t: int,
    repair_hours: int,
    seed: int = 42,
) -> np.ndarray:
    """
    准蒙特卡洛采样时空故障集，含状态延续：
    pm(t)=1-pi(t-1)*(1-p(t))（论文公式(22)思想）。
    返回 [S,T,L]，1=故障，0=正常。
    """
    total_steps, n_lines = line_failure_prob.shape
    dim = total_steps * n_lines
    m_power = int(np.ceil(np.log2(max(n_scenarios, 2))))
    sampler = qmc.Sobol(d=dim, scramble=True, seed=seed)
    u = sampler.random_base2(m=m_power)[:n_scenarios].reshape(n_scenarios, total_steps, n_lines)

    states = np.ones((n_scenarios, total_steps, n_lines), dtype=int)  # 1正常0故障
    for s in range(n_scenarios):
        prev = np.ones(n_lines, dtype=int)
        for t in range(total_steps):
            if t >= warning_end_t + repair_hours:
                states[s, t, :] = 1
                prev = states[s, t, :]
                continue
            pm = 1.0 - prev * (1.0 - line_failure_prob[t, :])
            states[s, t, :] = np.where(u[s, t, :] < pm, 0, 1)
            prev = states[s, t, :]
    return 1 - states


def priority_weight(level: int) -> float:
    """论文权重：一级4，二级2，三级1。"""
    if level == 1:
        return 4.0
    if level == 2:
        return 2.0
    return 1.0


def solve_weighted_load_shedding(loads: List[LoadNode], required_shedding_mw: float) -> np.ndarray:
    """
    负荷切除最小化的贪心解（等价于该简化线性问题最优解）：
    先切低权重负荷，最后切高权重负荷。
    """
    demand = np.array([ld.demand_mw for ld in loads], dtype=float)
    weights = np.array([priority_weight(ld.priority_level) for ld in loads], dtype=float)
    shed = np.zeros_like(demand)
    remain = max(required_shedding_mw, 0.0)

    for idx in np.argsort(weights):
        if remain <= 1e-9:
            break
        delta = min(demand[idx], remain)
        shed[idx] = delta
        remain -= delta
    return shed


def simulate_performance_curve(
    loads: List[LoadNode],
    contingency: np.ndarray,
    wind_pv_scenario: np.ndarray,
    base_dispatchable_generation_mw: float,
    pv_capacity_mw: float = 20.0,
    line_outage_penalty_factor: float = 0.45,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    在某个“故障场景+风光场景”下逐时仿真，输出切负荷矩阵与保供曲线。
    """
    total_steps = contingency.shape[0]
    demand = np.array([ld.demand_mw for ld in loads], dtype=float)
    total_demand = demand.sum()
    shed_matrix = np.zeros((total_steps, len(loads)), dtype=float)
    survived = np.zeros(total_steps, dtype=float)

    for t in range(total_steps):
        wind_speed = float(max(wind_pv_scenario[t, 0], 0.0))
        pv_output = float(np.clip(wind_pv_scenario[t, 1], 0.0, pv_capacity_mw))

        # 示例：两个风场，总风电出力 = 2 * 单风场出力
        wind_output = 2.0 * wind_turbine_power_curve(
            wind_speed_ms=wind_speed,
            rated_power_mw_per_turbine=2.0,
            n_turbines=10,
        )
        available_supply = base_dispatchable_generation_mw + wind_output + pv_output

        # 线路故障比例映射为输电能力损失
        outage_ratio = float(contingency[t].mean())
        transfer_loss = line_outage_penalty_factor * outage_ratio * total_demand
        effective_supply = max(available_supply - transfer_loss, 0.0)

        required_shed = max(total_demand - effective_supply, 0.0)
        shed = solve_weighted_load_shedding(loads, required_shed)

        shed_matrix[t, :] = shed
        survived[t] = total_demand - shed.sum()

    return shed_matrix, survived


def compute_resilience_indicators(shed_matrix: np.ndarray, loads: List[LoadNode]) -> Dict[str, float]:
    """计算 R1~R6 指标（论文表1的可运行简化版本）。"""
    total_shed_t = shed_matrix.sum(axis=1)
    total_shed = total_shed_t.sum()

    node_weights = np.array([priority_weight(ld.priority_level) for ld in loads], dtype=float)
    node_total_shed = shed_matrix.sum(axis=0)

    # R1：关键负荷切除比（越小越好）
    r1 = float((node_weights * node_total_shed).sum() / total_shed) if total_shed > 1e-9 else 1.0
    # R2：切负荷面积（越小越好）
    r2 = float(total_shed_t.sum())
    # R3：最大切负荷（越小越好）
    r3 = float(total_shed_t.max(initial=0.0))

    # R4/R5/R6：基于切负荷时序关键点
    idx = np.where(total_shed_t > 1e-9)[0]
    if idx.size == 0:
        r4 = float(len(total_shed_t) - 1)
        r5 = 0.0
        r6 = 0.0
    else:
        t1 = int(idx[0])
        t4 = int(idx[-1])
        t2 = int(np.argmax(total_shed_t))
        t3 = t2
        r4 = float(max(t2 - t1, 0))  # 负荷损失时间（越大越好）
        r5 = float(max(t4 - t3, 0))  # 负荷恢复时间（越小越好）
        r6 = float(max(t4 - t1, 0))  # 停电持续时间（越小越好）

    return {"R1": r1, "R2": r2, "R3": r3, "R4": r4, "R5": r5, "R6": r6}


def ewm_topsis(indicator_matrix: np.ndarray, benefit_flags: Iterable[bool]) -> Dict[str, np.ndarray]:
    """EWM + TOPSIS 综合评价。"""
    x = np.array(indicator_matrix, dtype=float)
    n_case, n_ind = x.shape
    benefit = np.array(list(benefit_flags), dtype=bool)
    if benefit.size != n_ind:
        raise ValueError("benefit_flags 长度错误")
    if n_case < 2:
        raise ValueError("至少需要两个评价对象")

    # 1) 正向化
    x_forward = np.zeros_like(x)
    for j in range(n_ind):
        col = x[:, j]
        cmin, cmax = col.min(), col.max()
        span = cmax - cmin
        if span < 1e-12:
            x_forward[:, j] = 1.0
        elif benefit[j]:
            x_forward[:, j] = (col - cmin) / span
        else:
            x_forward[:, j] = (cmax - col) / span

    # 2) EWM 权重
    p = x_forward / np.clip(x_forward.sum(axis=0, keepdims=True), 1e-12, None)
    k = 1.0 / np.log(n_case)
    safe_p = np.clip(p, 1e-12, 1.0)
    entropy = -k * np.sum(p * np.log(safe_p), axis=0)
    divergence = 1.0 - entropy
    weights = divergence / divergence.sum() if divergence.sum() > 1e-12 else np.full(n_ind, 1.0 / n_ind)

    # 3) TOPSIS
    r = x_forward / np.clip(np.sqrt((x_forward**2).sum(axis=0, keepdims=True)), 1e-12, None)
    v = r * weights
    ideal_best = v.max(axis=0)
    ideal_worst = v.min(axis=0)
    d_plus = np.sqrt(((v - ideal_best) ** 2).sum(axis=1))
    d_minus = np.sqrt(((v - ideal_worst) ** 2).sum(axis=1))
    scores = d_minus / np.clip(d_plus + d_minus, 1e-12, None)
    return {"weights": weights, "scores": scores, "x_forward": x_forward}


def build_synthetic_grid(seed: int = 42) -> Tuple[List[LineAsset], List[LoadNode]]:
    """
    构造与 MATPOWER `case30` 分支数量一致的线路集合。

    这里使用 pandapower 的 `case30()` 提供 41 条线路的拓扑顺序，
    便于后续把 Python 生成的故障场景与 MATPOWER 的 branch 索引对齐。
    """
    rng = np.random.default_rng(seed)
    net = ppn.case30()

    # 为 30 个母线生成固定“地理坐标”（仅用于风场计算，不影响 MATPOWER 拓扑）
    bus_lat = 22.10 + rng.uniform(-0.28, 0.28, size=len(net.bus))
    bus_lon = 114.10 + rng.uniform(-0.42, 0.42, size=len(net.bus))

    lines: List[LineAsset] = []
    for i, row in net.line.iterrows():
        fb = int(row.from_bus)  # pandapower 从 0 开始
        tb = int(row.to_bus)
        lat1, lon1 = float(bus_lat[fb]), float(bus_lon[fb])
        lat2, lon2 = float(bus_lat[tb]), float(bus_lon[tb])
        lines.append(
            LineAsset(
                line_id=f"L{i+1:02d}",
                lat1=lat1,
                lon1=lon1,
                lat2=lat2,
                lon2=lon2,
                towers=int(rng.integers(2, 5)),
                spans=int(rng.integers(3, 7)),
                design_line_load_n=float(rng.uniform(6500.0, 9000.0)),
                design_tower_load_kn=float(rng.uniform(80.0, 120.0)),
            )
        )
    loads = [
        LoadNode("B05", 14.0, 1),
        LoadNode("B08", 10.0, 1),
        LoadNode("B12", 12.0, 2),
        LoadNode("B16", 9.0, 2),
        LoadNode("B21", 11.0, 3),
        LoadNode("B30", 8.0, 3),
    ]
    return lines, loads


def build_synthetic_track(hours: int, intensity_scale: float) -> List[TyphoonState]:
    """构造简化台风轨迹，强度由 intensity_scale 控制。"""
    track: List[TyphoonState] = []
    for t in range(hours):
        progress = t / max(hours - 1, 1)
        lat = 22.45 - 0.70 * progress
        lon = 114.55 - 1.10 * progress
        bell = np.exp(-((progress - 0.5) ** 2) / 0.06)
        vmax = (22.0 + 20.0 * intensity_scale) + 10.0 * bell
        pc = 1005.0 - (18.0 * intensity_scale) - 20.0 * bell
        track.append(
            TyphoonState(
                t=t,
                lat=float(lat),
                lon=float(lon),
                central_pressure_hpa=float(pc),
                peripheral_pressure_hpa=1010.0,
                vmax_ms=float(vmax),
                move_speed_ms=6.0,
                move_dir_deg=300.0,
            )
        )
    return track


def build_reference_wind_pv_series(track: List[TyphoonState], wind_model: str, seed: int = 0) -> Tuple[np.ndarray, np.ndarray]:
    """
    用于滚动 DPGMM 的“历史观测序列”：
    - 风速来自风场模型 + 测量噪声；
    - PV 与风暴强度负相关（风大通常云雨更强）。
    """
    rng = np.random.default_rng(seed)
    ref_lat, ref_lon = 22.20, 114.00
    wind, pv = [], []
    for st in track:
        vg = typhoon_wind_speed_gradient(st, ref_lat, ref_lon, wind_model)
        v10 = boundary_layer_and_gust_correction(vg)
        v_obs = max(v10 + rng.normal(0.0, 1.2), 0.0)
        pv_nominal = 20.0 * max(0.0, 1.0 - v_obs / 45.0)
        pv_obs = np.clip(pv_nominal + rng.normal(0.0, 0.8), 0.0, 20.0)
        wind.append(v_obs)
        pv.append(pv_obs)
    return np.array(wind, dtype=float), np.array(pv, dtype=float)


def _find_matlab_executable() -> str:
    """定位 MATLAB 可执行文件，优先使用 PATH 中的 `matlab`。"""
    matlab_path = shutil.which("matlab")
    if matlab_path:
        return matlab_path
    # 兼容当前机器的常见安装路径
    fallback = Path(r"D:\Matlab\bin\matlab.exe")
    if fallback.exists():
        return str(fallback)
    raise FileNotFoundError("未找到 MATLAB 可执行文件，无法调用 MATPOWER。")


def run_matpower_batch_resilience(
    contingencies: np.ndarray,
    typical_scenarios: np.ndarray,
    scenario_probs: np.ndarray,
    loads: List[LoadNode],
    workdir: Path,
) -> Tuple[np.ndarray, float]:
    """
    调用 MATLAB + MATPOWER 对“所有场景组合”批量执行 OPF，返回 R1~R6 指标张量。

    输入维度:
    - contingencies: [S, T, L]，1=线路故障
    - typical_scenarios: [N, T, 2]，第0列风速，第1列PV总出力
    - scenario_probs: [N]

    输出:
    - indicator_tensor: [N, S, 6]（R1~R6）
    - opf_success_rate: OPF 成功率
    """
    matlab_exe = _find_matlab_executable()
    workdir = workdir.resolve()
    m_script = workdir / "run_matpower_resilience_batch.m"
    if not m_script.exists():
        raise FileNotFoundError(f"缺少 MATLAB 批处理脚本: {m_script}")

    load_bus_ids = []
    for ld in loads:
        if ld.node_id.upper().startswith("B"):
            load_bus_ids.append(int(ld.node_id[1:]))
        else:
            load_bus_ids.append(int(ld.node_id))

    load_demands = np.array([ld.demand_mw for ld in loads], dtype=float)
    load_weights = np.array([priority_weight(ld.priority_level) for ld in loads], dtype=float)

    with tempfile.TemporaryDirectory(prefix="matpower_batch_") as tmp:
        input_mat = Path(tmp) / "input.mat"
        output_mat = Path(tmp) / "output.mat"

        savemat(
            input_mat,
            {
                "contingencies": contingencies.astype(float),
                "typical_scenarios": typical_scenarios.astype(float),
                "scenario_probs": scenario_probs.reshape(-1, 1).astype(float),
                "load_bus_ids": np.array(load_bus_ids, dtype=float).reshape(-1, 1),
                "load_demands_mw": load_demands.reshape(-1, 1),
                "load_priority_weights": load_weights.reshape(-1, 1),
            },
        )

        # 注意：MATLAB -batch 中字符串使用单引号，路径中的反斜杠需替换为正斜杠更稳妥。
        wd_unix = str(workdir).replace("\\", "/")
        in_unix = str(input_mat).replace("\\", "/")
        out_unix = str(output_mat).replace("\\", "/")
        matlab_stmt = (
            f"addpath('{wd_unix}'); "
            f"run_matpower_resilience_batch('{in_unix}','{out_unix}');"
        )

        proc = subprocess.run(
            [matlab_exe, "-batch", matlab_stmt],
            capture_output=True,
            text=True,
            cwd=str(workdir),
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(
                "MATLAB/MATPOWER 批处理失败。\n"
                f"STDOUT:\n{proc.stdout}\n\nSTDERR:\n{proc.stderr}"
            )

        out = loadmat(output_mat)
        if "indicator_tensor" not in out:
            raise RuntimeError(
                "MATPOWER 输出中缺少 `indicator_tensor`。\n"
                f"MATLAB STDOUT:\n{proc.stdout}\n\nMATLAB STDERR:\n{proc.stderr}"
            )
        indicator_tensor = np.asarray(out["indicator_tensor"], dtype=float)
        opf_success_rate = float(np.asarray(out.get("opf_success_rate", [[np.nan]]), dtype=float).squeeze())
        return indicator_tensor, opf_success_rate


def evaluate_one_typhoon_case(
    case_name: str,
    intensity_scale: float,
    lines: List[LineAsset],
    loads: List[LoadNode],
    wind_model: str,
    design_scale: float,
    rng_seed: int,
    workdir: Path,
    total_hours: int = 18,
    n_contingency_scenarios: int = 6,
    n_sampled_scenarios: int = 60,
    n_typical_scenarios: int = 4,
) -> Dict[str, object]:
    """执行一个台风工况的完整评估流程。"""
    track = build_synthetic_track(hours=total_hours, intensity_scale=intensity_scale)

    line_wind_speed, line_failure_prob = compute_spatiotemporal_line_failure_probabilities(
        track=track,
        lines=lines,
        wind_model_name=wind_model,
        design_scale=design_scale,
    )
    contingencies = generate_spatiotemporal_contingencies(
        line_failure_prob=line_failure_prob,
        n_scenarios=n_contingency_scenarios,
        warning_end_t=max(total_hours - 6, 1),
        repair_hours=6,
        seed=rng_seed,
    )

    wind_hist, pv_hist = build_reference_wind_pv_series(track, wind_model, seed=rng_seed + 100)
    dpgmm = RollingDPGMM(window_radius=3, max_components=8, random_state=rng_seed + 200)
    models = dpgmm.fit_models(wind_hist, pv_hist)
    sampled = dpgmm.sample_trajectories(models, n_scenarios=n_sampled_scenarios)
    typical_scenarios, scenario_probs = reduce_scenarios_kmeans(sampled, n_typical=n_typical_scenarios, random_state=rng_seed + 300)

    indicator_keys = ["R1", "R2", "R3", "R4", "R5", "R6"]
    indicator_tensor, opf_success_rate = run_matpower_batch_resilience(
        contingencies=contingencies,
        typical_scenarios=typical_scenarios,
        scenario_probs=scenario_probs,
        loads=loads,
        workdir=workdir,
    )

    # 期望指标：E[R] = Σ_s Σ_f P(s) * P(f) * R_{s,f}，其中故障场景等权。
    weights_sf = scenario_probs.reshape(-1, 1, 1) * (1.0 / contingencies.shape[0])
    expected = (indicator_tensor * weights_sf).sum(axis=(0, 1))

    mean_fail = line_failure_prob.mean(axis=0)
    vulnerability = sorted(
        ((lines[i].line_id, float(mean_fail[i]), float(line_wind_speed[:, i].max())) for i in range(len(lines))),
        key=lambda x: x[1],
        reverse=True,
    )

    return {
        "case_name": case_name,
        "indicators": dict(zip(indicator_keys, expected)),
        "vulnerability_top5": vulnerability[:5],
        "wind_model": wind_model,
        "design_scale": design_scale,
        "opf_success_rate": opf_success_rate,
    }


def main() -> None:
    """主函数：三类台风工况比较 + EWM-TOPSIS 综合排序。"""
    workdir = Path(__file__).resolve().parent
    lines, loads = build_synthetic_grid(seed=42)
    print(f"Using MATPOWER solver via MATLAB in: {workdir}")

    # 为了让示例在普通 PC 上可运行，默认采用中等规模场景数。
    # 如需更接近论文的大规模仿真，可增大如下参数。
    total_hours = 18
    n_contingency_scenarios = 6
    n_sampled_scenarios = 60
    n_typical_scenarios = 4

    cases = [
        {"name": "SuperTyphoon", "intensity_scale": 1.30, "wind_model": "schloemer", "design_scale": 1.00, "seed": 10},
        {"name": "Typhoon", "intensity_scale": 1.00, "wind_model": "batts", "design_scale": 1.00, "seed": 20},
        {"name": "TropicalStorm", "intensity_scale": 0.75, "wind_model": "batts", "design_scale": 1.00, "seed": 30},
    ]

    results: List[Dict[str, object]] = []
    for cfg in cases:
        results.append(
            evaluate_one_typhoon_case(
                case_name=cfg["name"],
                intensity_scale=cfg["intensity_scale"],
                lines=lines,
                loads=loads,
                wind_model=cfg["wind_model"],
                design_scale=cfg["design_scale"],
                rng_seed=cfg["seed"],
                workdir=workdir,
                total_hours=total_hours,
                n_contingency_scenarios=n_contingency_scenarios,
                n_sampled_scenarios=n_sampled_scenarios,
                n_typical_scenarios=n_typical_scenarios,
            )
        )

    keys = ["R1", "R2", "R3", "R4", "R5", "R6"]
    matrix = np.array([[float(r["indicators"][k]) for k in keys] for r in results], dtype=float)
    eval_result = ewm_topsis(matrix, benefit_flags=[False, False, False, True, False, False])
    scores = eval_result["scores"]

    print("\n===== Resilience Assessment (Simplified Reproduction) =====")
    print("EWM weights:", np.round(eval_result["weights"], 4))
    for i, r in enumerate(results):
        indi = r["indicators"]
        print(f"\nCase: {r['case_name']} | Model={r['wind_model']}")
        print("  " + ", ".join([f"{k}={indi[k]:.3f}" for k in keys]) + f", CRI={scores[i]:.4f}")
        print(f"  OPF success rate: {r['opf_success_rate']:.2%}")
        print("  Top-5 vulnerable lines:")
        for item in r["vulnerability_top5"]:
            print(f"    {item[0]}  p={item[1]:.4f}  vmax={item[2]:.2f} m/s")

    order = np.argsort(-scores)
    print("\nRanking by CRI:")
    for rank, idx in enumerate(order, start=1):
        print(f"  {rank}. {results[idx]['case_name']} (CRI={scores[idx]:.4f})")


if __name__ == "__main__":
    main()
