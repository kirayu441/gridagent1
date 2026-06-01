# GridAgent 项目论文式说明（面向非本项目读者）

## 摘要
本文档对 GridAgent 项目进行论文风格说明，目标是让完全不了解项目的人也能快速理解：项目要解决什么问题、用了哪些方法、为什么这样选、以及实验数据从哪里来、结果意味着什么。  
项目核心任务是在极端天气和风光波动条件下，形成一条完整链路：**风光不确定性建模 → 设备失效概率 → 空间-时间故障场景 → 预警 → 调度优化 → 韧性评估**。  
本文使用 `formal2024` 数据进行小型快速验证（6 小时窗口），并基于标准化输出目录给出定量分析。

**关键词**：电网韧性、风光不确定性、设备失效、应急场景生成、调度优化、EWM+TOPSIS

---

## 1. 研究背景与问题定义

高比例新能源接入使电力系统在极端天气下同时面临两类不确定性：

1. **供给侧不确定性**：风电、光伏出力波动；
2. **网络侧脆弱性**：线路和塔杆在强风下失效，导致连锁故障与负荷失供。

传统单模块方法往往只解决其中一部分问题。GridAgent 的目标是把多个模块耦合成统一决策链路，最终输出可执行的结果：

- 哪些线路高风险、何时可能故障；
- 不同规模 N-k 故障的概率；
- 对关键负荷的失供风险；
- 基于场景自动切换的调度方案；
- 多指标韧性评估结果。

---

## 2. 文献基础与方法来源

本项目的方法组合主要来自以下研究脉络（含你要求参考的论文体系）：

1. **Wang et al., 2024（项目核心参考论文）**  
   作为整体框架参考，包含风光不确定性、失效建模、场景生成与韧性评估链路思想。
2. **Padhy (2004)**  
   Unit Commitment（UC）问题综述，提供调度建模框架背景。
3. **Carrion & Arroyo (2006)**  
   热机组 UC 的高效 MILP 形式，是 SCUC 建模常用基线。
4. **Takriti, Birge, Long (1996)**  
   随机 UC 经典两阶段模型基础。
5. **Bertsimas & Sim (2004)**  
   鲁棒优化经典理论（worst-case 视角）。
6. **Zhao & Guan (2013)**  
   含风电不确定性的鲁棒 UC。
7. **Morales et al. (2014)**  
   新能源场景与电力市场调度整合方法。
8. **C3PO / TRIM（参考方法）**  
   用于故障场景生成阶段的对照与启发（项目中已实现 `c3po_ref`、`trim_ref` 等方法接口）。
9. **Boosting Resilience（2022，参考思想）**  
   对韧性指标与恢复能力分析提供多指标视角。

---

## 3. 总体模型框架

GridAgent 的统一流程如下：

1. 风光不确定性模块（DPGMM）生成典型场景与概率；
2. 风场 + Stress-Strength 计算线路失效概率时序；
3. 基于失效概率生成空间-时间故障场景集；
4. GNN 预警模块输出线路/N-k/关键负荷风险；
5. 调度模块在每小时按风险上下文自动选择 SCUC / Stochastic UC / Robust UC；
6. 多指标韧性评估（Priority, Robustness, Rapidity, Sustainability）并用 EWM+TOPSIS 综合排序。

---

## 4. 方法与原理说明（含选型原因）

## 4.1 风光不确定性建模（DPGMM）

### 方法原理
采用贝叶斯高斯混合模型（`BayesianGaussianMixture`，DP 先验）对每个时间点附近窗口的风电-光伏二维样本拟合，自动确定有效混合成分数。  
场景生成后，用 KMeans 做典型场景缩减，并给出场景概率。

典型形式：
\[
p(\mathbf{x})=\sum_{k=1}^{K}\pi_k\mathcal{N}(\mathbf{x}\mid \mu_k,\Sigma_k),
\]
其中 \(K\) 通过 DP 先验自适应。

### 选择原因
1. 风光出力分布常呈现多峰，单高斯或线性模型表达不足；
2. DP 先验能减少手工指定成分数；
3. 输出天然为“场景+概率”，可直接喂给随机调度。

---

## 4.2 线路/塔杆失效概率（Batts/Schloemer + Stress-Strength）

### 方法原理
1. 用 Batts 或 Schloemer 风场模型计算给定路径下各线路位置风速；
2. 将风速映射为导线风荷载与塔杆风荷载；
3. 用 Stress-Strength 干涉计算构件失效概率：
\[
P_f = P(\text{Stress}>\text{Strength})
    = 1-\Phi\left(\frac{\mu_D-\mu_A}{\sqrt{\sigma_D^2+\sigma_A^2}}\right)
\]
4. 将杆塔与档距构件概率合成为线路串联系统失效概率：
\[
P_{\text{line}}=1-(1-P_{\text{tower}})^{n_t}(1-P_{\text{span}})^{n_s}
\]

### 选择原因
1. 比纯统计黑盒更可解释（与工程荷载概念一致）；
2. 在样本有限时更稳健；
3. 可直接输出“按小时、按线路”的概率，便于后续场景生成与预警。

---

## 4.3 空间-时间故障场景生成（Contingency Set）

### 方法原理
输入为 `p_line(t,l)`，输出为 `outage(s,t,l)`。  
本次快速实验使用 `c3po_ref`（独立伯努利采样）：
\[
\text{outage}_{s,t,l}=\mathbb{I}(u_{s,t,l}<p_{t,l})
\]
并额外输出展平文件 `contingency_scenarios.csv`（含 `failed_lines` 字段）。

### 选择原因
1. `c3po_ref` 实现简单、可复现、速度快，适合小型测试；
2. 保留 `wang_qmc / wang_mc / trim_ref` 接口，便于后续做方法敏感性对比；
3. 场景张量和展平表可同时支持优化求解与可解释展示。

---

## 4.4 预警模块（GNN Early Warning）

### 方法原理
1. 以电网拓扑构图，节点包含负荷/气象/历史风险特征；
2. 通过消息传递网络学习线路风险；
3. 使用蒙特卡洛扰动生成多条扰动路径，输出：
   - `line_risk_prediction.csv`
   - `nk_failure_risk.csv`
   - `critical_load_risk.csv`

### 选择原因
1. 图结构天然适配电网拓扑；
2. 与场景扰动结合后可输出概率分布而非单值预测；
3. 输出直接对接调度策略切换规则。

---

## 4.5 调度优化（场景化策略切换）

### 方法原理
调度模块内部求解三类模型：

1. **SCUC**：基线安全约束机组组合；
2. **Stochastic UC**：两阶段近似（第一阶段承诺 + 第二阶段场景再调度）；
3. **Robust UC**：在不确定集合上选择最坏情形控制风险。

统一目标：
\[
\min\ (C_{\text{gen}} + C_{\text{reserve}} + C_{\text{startup/shutdown}} + C_{\text{shed}})
\]
并满足功率平衡、机组容量、爬坡、备用、DC 潮流和线路限值约束。

项目采用“按场景切换”而非“单一模型排名”：根据每小时线路风险、全局 N-k 风险和关键负荷风险，在 `SCUC / Stochastic_UC / Robust_UC` 间自动切换。

### 选择原因
1. 不同风险阶段最优策略不同，单模型难兼顾经济性与鲁棒性；
2. 与调度中心“情境化操作”实践一致；
3. 便于实时扩展（规则阈值可在线更新）。

---

## 4.6 负荷优先级策略与调度

### 方法原理
1. 先做灾前 LP 调度得到基准出力与备用；
2. 对每个故障场景做供给-负荷分配，执行优先级切负荷策略；
3. 输出 `priority_with_reserve / uniform_with_reserve / priority_no_reserve` 三种策略指标（用于韧性评估）。

### 选择原因
1. 先灾前后灾后分解，计算效率高；
2. 优先级策略可直接体现关键负荷保护目标；
3. 可与韧性指标无缝对接。

---

## 4.7 多指标韧性评估（EWM + TOPSIS）

### 方法原理
指标体系：
- Priority：关键负荷服务能力；
- Robustness：冲击下供电保持能力；
- Rapidity：恢复速度；
- Sustainability：全过程供电稳定性。

流程：
1. EWM 计算指标客观权重；
2. TOPSIS 计算相对贴近度并排序。

### 选择原因
1. 避免主观定权；
2. 可同时比较多个策略；
3. 输出为明确排序，便于工程决策。

---

## 5. 数值实验设计

## 5.1 数据来源

本次实验使用 `formal2024` 正式数据，关键输入如下：

| 数据类型 | 路径 | 说明 |
|---|---|---|
| 电网拓扑 | `data_final/formal_guangdong_2024/grid_topology.json` | 15 节点、15 线路、10 发电单元（含风/光/热） |
| 对齐特征 | `data_final/formal_guangdong_2024/aligned_merged.csv` | 风光出力、气象、负荷等时间序列 |
| 调度输入 | `data_final/formal_guangdong_2024/TRIM_input.csv` | 归一化时序 + 日历特征 |
| 风光场景输出 | `results/formal2024_quick_std_standard/scenario/wind_solar_scenarios.csv` | DPGMM 典型场景 |
| 失效概率输出 | `results/formal2024_quick_std_standard/scenario/component_failure_prob.csv` | 线路小时失效概率 |
| 故障场景输出 | `results/formal2024_quick_std_standard/scenario/contingency_scenarios.csv` | 展平后的场景集 |

## 5.2 实验配置（快速验证）

- 运行模式：baseline
- 时间窗口：6 小时（2024-09-01 00:00:00 到 2024-09-01 05:00:00）
- 场景数：64（contingency）
- 调度视窗：6 小时
- 目标：验证链路可运行、输出完整、指标可解释

对应运行目录：

- `results/gridagent_framework/formal2024_quick_std`
- 标准化输出目录：`results/formal2024_quick_std_standard`

---

## 6. 实验结果与分析

## 6.1 预警结果

1. **线路风险**  
   - 线路总数：15  
   - 风险等级统计：HIGH=14，LOW=1  
   - 最高风险线路概率约 0.85（例如 L0, L1, L11）
2. **N-k 风险**  
   - 期望失效线路数：\(E[k]\approx1.8600\)
3. **关键负荷风险**  
   - 最高失供概率节点：`load_bus_12`，`0.278333`

**解读**：在该 6 小时窗口中，风险整体偏高，足以触发鲁棒调度阶段。

## 6.2 调度结果

1. **策略切换**  
   - Robust_UC：3 小时  
   - SCUC：3 小时  
   - Stochastic_UC：0 小时（本窗口中未触发）
2. **供给与备用**  
   - 总备用（reserve_up 累计）：约 `1.0412`
3. **失负荷与网络安全**  
   - 总切负荷（6 小时）：约 `2.7222`  
   - 线路过载次数：`0`  
   - 最大线路负载率：约 `0.0347`
4. **调度模块综合指标（Contextual_Adaptive）**  
   - 总成本：`3664.03`  
   - EENS：`2.7222`  
   - Priority Index：`0.7988`  
   - Reliability Score：`0.6078`

**解读**：该结果显示策略切换机制能在风险高时启用鲁棒策略，同时保持线路不过载；但受高风险场景影响，切负荷成本仍较高。

## 6.3 韧性评估结果

韧性排名（EWM+TOPSIS）：

1. `priority_with_reserve`：score = `1.0000`（rank 1）
2. `uniform_with_reserve`：score = `0.5205`（rank 2）
3. `priority_no_reserve`：score = `0.3431`（rank 3）

对应关键指标（最佳策略）：

- Priority = `0.6005`
- Robustness = `0.3066`
- Rapidity = `0.0498`
- Sustainability = `0.2932`

**解读**：关键负荷优先 + 备用策略在本实验中最优，验证了“关键负荷优先保障 + 预留备用”在极端条件下的价值。

## 6.4 场景质量结果

`contingency_scenarios.csv`（64 场景 × 6 时段）统计：

- 总记录数：384
- 平均每时段失效线路数：`3.1510`
- `outage_line_count>=2` 比例：`0.3646`
- `outage_line_count>=4` 比例：`0.1667`

**解读**：故障场景包含较高比例多线路故障，能够覆盖中高风险状态，对调度和预警验证有效。

---

## 7. 方法选择合理性总结

1. **DPGMM** 负责“可解释的多模态新能源场景”；
2. **Batts/Schloemer + Stress-Strength** 负责“物理可解释的构件失效概率”；
3. **Contingency 场景生成** 负责“风险传播环境构造”；
4. **GNN 预警** 负责“风险信息压缩输出”；
5. **Contextual Dispatch** 负责“按场景动态切换调度策略”；
6. **EWM+TOPSIS** 负责“多指标综合判优”。

该组合兼顾了工程可解释性、计算可行性和决策闭环性。

---

## 8. 局限与后续工作

1. 本报告为快速验证（6 小时窗口），不代表全年统计结论；
2. 风险等级偏高与当前故障概率输入有关，后续可通过参数校准提升分辨率；
3. 可进一步扩展到：
   - 更长时域（24h/72h）；
   - 多台风强度组合；
   - 多方法（Wang-QMC、TRIM）对比；
   - 更真实地理与设备参数。

---

## 9. 复现说明（给新读者）

1. 运行快速测试：

```powershell
python scripts/gridagent_framework.py --config configs/gridagent_framework.formal2024.quicktest.json --mode baseline --run-tag formal2024_quick_std --max-steps 6 --no-reuse-existing
```

2. 导出标准结果目录：

```powershell
python scripts/export_standard_results.py --run-root results/gridagent_framework/formal2024_quick_std --output-root results/formal2024_quick_std_standard
```

3. 读取标准化结果：

- `results/formal2024_quick_std_standard/summary`
- `results/formal2024_quick_std_standard/warning`
- `results/formal2024_quick_std_standard/dispatch`
- `results/formal2024_quick_std_standard/resilience`
- `results/formal2024_quick_std_standard/scenario`

---

## 10. 参考文献（按项目实现关联）

1. Wang et al., 2024.（你提供的主参考论文）  
2. Padhy, N. P. (2004). *Unit commitment—a bibliographical survey*. IEEE Transactions on Power Systems.  
3. Carrion, M., & Arroyo, J. M. (2006). *A computationally efficient mixed-integer linear formulation for the thermal unit commitment problem*. IEEE Transactions on Power Systems.  
4. Takriti, S., Birge, J. R., & Long, E. (1996). *A stochastic model for the unit commitment problem*. IEEE Transactions on Power Systems.  
5. Morales, J. M. et al. (2014). *Integrating Renewables in Electricity Markets*. Springer.  
6. Bertsimas, D., & Sim, M. (2004). *The Price of Robustness*. Operations Research.  
7. Zhao, C., & Guan, Y. (2013). *Robust unit commitment with wind power uncertainty and recourse*. IEEE Transactions on Power Systems.  
8. C3PO（项目中用于故障场景生成的参考方法）  
9. TRIM（项目中用于故障场景生成的参考方法）  
10. Boosting Resilience（2022，项目参考韧性思想）

