# 问题定义初稿（中文）

## 2 问题定义

本文研究的核心任务是**线路级时空风险预测**。与将风光不确定性建模、元件失效概率估计、故障场景生成、图神经网络预警和调度优化分别看作彼此独立的问题不同，本文将这些模块重新组织为一条围绕线路级风险预测展开的分析链路：利用新能源场景刻画运行背景，利用失效先验与故障传播结果刻画风险上下文，在此基础上构造统一的线路级输入表示，并预测未来线路风险，最后通过下游调度与韧性分析验证预测结果的任务价值 [1,2]。

因此，本节的目标不是定义整条链路中的所有工程细节，而是从任务角度明确以下问题：

1. 线路级风险预测的输入由哪些对象构成；
2. 这些对象如何组织为统一的线路级时空风险表示；
3. 预测结果如何定义并如何进入下游任务。

---

## 2.1 基础输入

设全年离散时间索引为

\[
\mathcal{T} = \{1,2,\dots,T\},
\]

其中 \(T\) 表示总时间步数。在本文实验中，\(T=8784\)，对应 2024 年全年逐小时序列。

对任一时刻 \(t \in \mathcal{T}\)，给定基础时序输入：

\[
\mathbf{x}_t = [w_t, p_t, \ell_t, m_t],
\]

其中：

- \(w_t\) 表示风电相关特征；
- \(p_t\) 表示光伏相关特征；
- \(\ell_t\) 表示负荷相关特征；
- \(m_t\) 表示气象相关特征。

将所有时间步拼接后，可得原始时序输入表：

\[
\mathbf{X} = [\mathbf{x}_1, \mathbf{x}_2, \dots, \mathbf{x}_T].
\]

此外，给定静态网络拓扑

\[
G = (V, E),
\]

其中：

- \(V\) 为节点集合；
- \(E\) 为线路集合。

在本文中，拓扑 \(G\) 对应 IEEE 118 节点全网结构，后续所有线路级风险分析均建立在该拓扑基础之上。采用显式拓扑结构作为风险分析输入，是近年来图学习与图 surrogate 方法在电网运行风险分析中的共同做法 [3,4]。

---

## 2.2 场景背景表示

由于原始全年时序数据规模大、波动强，难以直接用于后续风险分析，因此本文首先从时序输入中构造少量带概率的代表场景，用于提供线路风险分析的运行背景。类似的场景压缩与场景化表示在现代电力系统的不确定性分析、随机调度和规划中已被广泛采用 [5,6]。

设新能源核心子序列为：

\[
\mathbf{r}_t = [w_t^{(e)}, p_t^{(e)}],
\]

其中 \(w_t^{(e)}\) 和 \(p_t^{(e)}\) 分别表示时刻 \(t\) 的风电与光伏出力表示。全年新能源序列记为：

\[
\mathbf{R} = [\mathbf{r}_1, \mathbf{r}_2, \dots, \mathbf{r}_T].
\]

在此基础上，构造代表场景集合：

\[
\mathcal{S} = \{(S_1,\pi_1), (S_2,\pi_2), \dots, (S_K,\pi_K)\},
\]

其中：

- \(S_k \in \mathbb{R}^{T \times d_r}\) 表示第 \(k\) 个代表性年度场景；
- \(\pi_k\) 表示对应场景概率；
- \(\sum_{k=1}^{K} \pi_k = 1\)。

在本文实验中，\(d_r = 2\)，对应风电与光伏两个核心维度，\(K=10\)。

需要强调的是，在本文中，\(\mathcal{S}\) 的角色不是独立主任务输出，而是**线路级风险预测的外部运行背景**。它用于描述当前系统处于何种新能源不确定场景之下，并为后续线路级风险分析提供场景条件。

---

## 2.3 失效先验与故障传播上下文

仅有新能源场景背景不足以刻画线路风险，因为极端天气驱动下的线路脆弱性和故障传播关系同样决定了风险演化过程。因此，本文进一步引入两类上下文信息。该设计与近年来强调“故障并非仅由局部负荷或局部天气决定，而是受网络交互和传播机制共同影响”的研究认识是一致的 [1,7]。

### 2.3.1 线路失效先验

对任意线路 \(e \in E\) 和故障建模窗口中的时刻 \(t \in \mathcal{T}'\)，定义其失效先验为：

\[
q_{e,t} \in [0,1],
\]

其中 \(\mathcal{T}'\) 表示用于风险传播分析的局部时间窗口，例如台风影响期间的若干小时。所有线路在该窗口中的失效先验可组织为：

\[
\mathbf{Q} \in \mathbb{R}^{|E| \times |\mathcal{T}'|}.
\]

\(\mathbf{Q}\) 表示在给定天气和脆弱性模型条件下，各线路在不同时刻发生故障的基础风险水平。将线路失效概率组织为时间序列形式，有助于后续将静态脆弱性结果转化为时变风险上下文 [1]。

### 2.3.2 故障传播上下文

在失效先验基础上，进一步构造时空故障场景。设共有 \(M\) 个故障场景，则第 \(m\) 个场景表示为：

\[
C_m \in \{0,1\}^{|E| \times |\mathcal{T}'|},
\]

其中 \(C_m(e,t)=1\) 表示线路 \(e\) 在时刻 \(t\) 发生故障，否则为 0。将所有场景堆叠后，得到故障传播张量：

\[
\mathbf{C} \in \{0,1\}^{M \times |E| \times |\mathcal{T}'|}.
\]

在本文中，\(\mathbf{C}\) 不被视为最终预测目标，而被视为**故障传播上下文**：它描述了在特定先验条件下，线路故障如何在时间和网络结构上共同演化。类似地，关于级联故障传播的图建模研究也强调应显式表示线路之间的交互关系与传播路径，而非仅停留在单条线路独立概率层面 [7,8]。

---

## 2.4 线路级时空风险表示

本文的核心目标是：对每条线路在给定时间步下构造统一的风险输入表示，并据此预测未来风险。

对任意线路 \(e \in E\) 和目标预测时刻 \(t\)，定义其线路级风险表示为：

\[
\mathbf{z}_{e,t} = \Phi(e, t; \mathcal{S}, \mathbf{Q}, \mathbf{C}, G, \mathbf{X}),
\]

其中 \(\Phi(\cdot)\) 表示一个多源融合映射，用于整合以下几类信息：

1. **场景背景特征**  
   来自 \(\mathcal{S}\) 的新能源不确定场景信息，用于刻画当前运行背景。

2. **失效先验特征**  
   来自 \(\mathbf{Q}\) 的线路失效先验，用于刻画线路在极端天气下的基础脆弱性。

3. **故障传播上下文特征**  
   来自 \(\mathbf{C}\) 的时空故障传播信息，用于刻画线路所处的风险扩散环境。

4. **拓扑结构特征**  
   来自网络拓扑 \(G\) 的结构语义，用于反映线路在系统中的连接关系与结构位置。

5. **运行状态特征**  
   来自 \(\mathbf{X}\) 的负荷、天气及其他辅助时序信息，用于刻画当前时刻的运行状态。

对所有线路与时间步构造上述表示后，可得到线路级时空风险输入集合：

\[
\mathcal{Z} = \{\mathbf{z}_{e,t} \mid e \in E, t \in \mathcal{T}^*\},
\]

其中 \(\mathcal{T}^*\) 表示风险预测任务关注的时间范围。

这一表示的关键作用在于，它将原本分散于多个阶段的输入统一到线路级分析对象中，使得线路风险预测不再依赖单一天气表、单一拓扑图或单一故障张量，而能够在统一上下文中进行。该思路与图学习在复杂基础设施风险分析中的一般趋势一致，即通过融合拓扑、时序和任务上下文来形成更有判别力的节点或边表示 [3,4]。

---

## 2.5 线路级时空风险预测任务

在给定线路级输入表示 \(\mathbf{z}_{e,t}\) 后，本文希望预测未来线路风险：

\[
\hat{y}_{e,t+\Delta} = f(\mathbf{z}_{e,t}; \Theta),
\]

其中：

- \(\Delta\) 表示预测步长；
- \(f(\cdot)\) 表示风险预测模型；
- \(\Theta\) 表示模型参数；
- \(\hat{y}_{e,t+\Delta}\) 表示对线路 \(e\) 在未来时刻 \(t+\Delta\) 风险水平的预测。

从任务角度看，本文的重点不在于讨论所有可能的风险标签定义，而在于：

1. 给出统一的线路级风险输入表示；
2. 在该表示之上构建风险预测模型；
3. 分析预测输出是否能够形成可被下游任务直接消费的风险摘要。

因此，本文的核心任务可以表述为：

> 给定多源时空运行数据、故障先验与传播上下文，构建线路级时空风险表示，并预测未来线路风险。

---

## 2.6 面向下游任务的风险摘要接口

线路级风险预测的价值不仅在于得到每条线路的风险分数，更在于这些结果能否支撑后续调度与韧性分析。因此，本文进一步定义结构化风险摘要接口。这一点与近年来运行风险评估研究逐步从“单点预测”走向“任务可消费风险摘要”的发展趋势是一致的 [3,4]。

设模型输出结果记为：

\[
\mathcal{A} = (\mathbf{y}^{line}, \mathbf{y}^{load}, \mathbf{y}^{nk}, \mathbf{y}^{sum}),
\]

其中：

- \(\mathbf{y}^{line}\) 表示线路级风险预测结果；
- \(\mathbf{y}^{load}\) 表示关键负荷相关风险摘要；
- \(\mathbf{y}^{nk}\) 表示多元故障或组合风险摘要；
- \(\mathbf{y}^{sum}\) 表示整体告警与聚合结果。

基于上述摘要，可进一步定义下游任务输入：

\[
\mathcal{D} = g(\mathcal{A}, \mathcal{S}, \mathbf{X}),
\]

其中 \(\mathcal{D}\) 表示可被调度与韧性分析模块直接消费的输入集合。其具体形式可以包括：

- 调度策略选择所需的风险输入；
- 关键负荷保障分析所需的摘要结果；
- 韧性排序与标准化结果导出所需的中间表。

在本文中，下游任务并不是独立主问题，而是用于验证：

> 线路级时空风险预测结果是否真正具有决策支持价值。

---

## 2.7 研究目标

综合上述定义，本文的研究目标可概括为：

给定基础输入

\[
(\mathbf{X}, G),
\]

以及由此构造的场景背景 \(\mathcal{S}\)、失效先验 \(\mathbf{Q}\) 和故障传播上下文 \(\mathbf{C}\)，构建统一的线路级时空风险表示 \(\mathbf{z}_{e,t}\)，并学习预测函数 \(f(\cdot)\)，使其能够：

1. 有效预测未来线路风险；
2. 统一融合多源时空上下文；
3. 输出可被下游任务直接消费的结构化风险摘要；
4. 在实际调度与韧性分析中体现出任务价值。

因此，后续各节将围绕“线路级时空风险预测”这一主任务展开：前序模块负责构造风险背景与上下文，图分析模块负责完成核心预测任务，下游模块负责验证预测结果的实际分析价值。

---

## 问题定义参考文献（草稿）

[1] Panteli, M., Pickering, C., Wilkinson, S., Dawson, R., and Mancarella, P. *Power System Resilience to Extreme Weather: Fragility Modeling, Probabilistic Impact Assessment, and Adaptation Measures*. IEEE Transactions on Power Systems, 2017. [链接](https://eprints.ncl.ac.uk/229241)

[2] Bie, Z., Lin, Y., Li, G., and Li, F. *Battling the Extreme: A Study on the Power System Resilience*. Proceedings of the IEEE, 2017. [链接](https://dblp.org/rec/journals/pieee/BieLLL17)

[3] Marot, A., Rozemberczki, B., Chakraborty, S., et al. *Graph neural networks for power grid operational risk assessment under evolving grid topology*. arXiv, 2024. [链接](https://arxiv.org/abs/2405.07343)

[4] Donnot, B., Marot, A., and Venzke, A. *Power grid operational risk assessment using graph neural network surrogates*. arXiv, 2023. [链接](https://arxiv.org/abs/2311.12309)

[5] Chen, J., Song, Z., Zhang, Y., and Ouyang, H. *A review of scenario analysis methods in planning and operation of modern power systems: Methodologies, applications, and challenges*. Electric Power Systems Research, 2022. [链接](https://www.sciencedirect.com/science/article/abs/pii/S0378779621007033)

[6] Huang, Y., Wang, J., and Zeng, B. *Planning of distributed renewable energy systems under uncertainty based on statistical machine learning*. Protection and Control of Modern Power Systems, 2022. [链接](https://link.springer.com/article/10.1186/s41601-022-00262-x)

[7] Guo, C., and Xie, L. *Interaction Graphs for Cascading Failure Analysis in Power Grids: A Survey*. arXiv, 2019. [链接](https://arxiv.org/abs/1911.00475)

[8] Xiang, B., Cautis, B., Xiao, X., Mula, O., Niyato, D., and Lakshmanan, L. V. S. *Predicting Cascading Failures with a Hyperparametric Diffusion Model*. KDD, 2024. [链接](https://doi.org/10.1145/3637528.3672048)
