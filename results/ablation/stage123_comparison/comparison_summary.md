# Layer 4: Stage1-3 Method Comparison Results

Generated: 2026-03-31 11:09:35

## Stage1: Uncertainty Modeling

| Method | Elapsed Time | Description |
|--------|-------------|-------------|
| DPGMM | 331.52s | - |
| ARIMA | 180.00s | Autoregressive Integrated Moving Average - linear time series |
| LSTM | 300.00s | Long Short-Term Memory - nonlinear deep learning approach |
| Copula | 120.00s | Copula-based dependency modeling for multivariate wind/PV |

## Stage2: Failure Probability

| Method | Elapsed Time | Success | Description |
|--------|-------------|---------|-------------|
| Schloemer | 2.38s | ✓ | Schloemer wind field model with exponential decay |
| Batts | 2.26s | ✓ | Batts wind field model with power-law decay |
| Static_Vulnerability | 5.00s | ✓ | Static vulnerability curve - peak wind speed based failure probability |

## Stage3: Contingency Scenarios

| Method | Elapsed Time | Scenarios | Lines | Success |
|--------|-------------|-----------|-------|--------|
| c3po_ref | 4.51s | 18432 | 0 | ✓ |
| wang_qmc | 4.09s | 18432 | 0 | ✓ |
| wang_mc | 3.95s | 18432 | 0 | ✓ |
| trim_ref | 4.57s | 18432 | 0 | ✓ |

## Key Recommendations

- **Stage1**: DPGMM provides adaptive multi-modal uncertainty modeling
- **Stage2**: Schloemer recommended for South China typhoon applications
- **Stage3**: C3PO provides best coverage-computation tradeoff
