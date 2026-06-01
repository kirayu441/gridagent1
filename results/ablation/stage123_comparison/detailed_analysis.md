# Stage1-3 Method Comparison - Detailed Analysis

Generated: Analysis completed

## Stage1: DPGMM Uncertainty Modeling

### Scenario Statistics
- Total scenarios: 10
- Scenario probabilities: [0.095 0.15  0.195 0.06  0.085 0.1   0.055 0.105]
- Timestamps per scenario: 8784

### Wind Power Statistics
- Mean: 0.2209
- Std: 0.1980
- Range: [0.0001, 0.9833]

### PV Power Statistics
- Mean: 0.2096
- Std: 0.2102
- Range: [0.0000, 0.9300]

## Stage2: Failure Probability Comparison

### Wind Speed Prediction
| Model | Mean | Std | Max |
|-------|------|-----|-----|
| Schloemer | 24.20 | 10.32 | 38.24 |
| Batts | 19.23 | 7.11 | 36.08 |

### Failure Probability
| Model | Mean | Median | Max |
|-------|------|--------|-----|
| Schloemer | 0.1783 | 0.0000 | 1.0000 |
| Batts | 0.0059 | 0.0000 | 1.0000 |

### Line-by-Line Comparison
| Line | Schloemer | Batts | Ratio |
|------|-----------|-------|-------|
| L0 | 0.2259 | 0.0000 | 2118715.2 |
| L1 | 0.1503 | 0.0000 | 893335.6 |
| L2 | 0.1447 | 0.0000 | 4439.6 |
| L3 | 0.1859 | 0.0181 | 10.3 |
| L4 | 0.2371 | 0.0369 | 6.4 |
| L5 | 0.1471 | 0.0000 | 5916.1 |
| L6 | 0.1429 | 0.0000 | 6079.1 |
| L7 | 0.1719 | 0.0061 | 28.3 |
| L8 | 0.1704 | 0.0044 | 38.8 |
| L9 | 0.1330 | 0.0000 | 19712.9 |
| L10 | 0.2306 | 0.0000 | 392987742.3 |
| L11 | 0.2227 | 0.0000 | 63760102.8 |
| L12 | 0.1980 | 0.0183 | 10.8 |
| L13 | 0.1616 | 0.0041 | 39.8 |
| L14 | 0.1527 | 0.0000 | 978173.3 |

## Stage3: Contingency Scenario Analysis

### Scenario Generation Summary
- Total scenarios: 18432
- Unique scenario IDs: 256
- Time steps: 72

### Hourly Failure Evolution
| Hour | Mean Failed Lines |
|------|-------------------|
| 00:00 | 6.27 |
| 03:00 | 5.88 |
| 06:00 | 4.43 |
| 09:00 | 3.36 |
| 12:00 | 1.29 |
| 15:00 | 0.38 |
| 18:00 | 0.61 |
| 21:00 | 1.21 |
| 23:00 | 1.30 |

### Load Disconnection
- Scenarios with load disconnection: 5673
- Max disconnected loads: 4
- Mean disconnected loads: 0.95
