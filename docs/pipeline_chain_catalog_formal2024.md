# formal2024 完整链路清单（24条）

## 说明

- 配置来源：`configs/gridagent_framework.formal2024.json`
- 组合方式：`failure_model × contingency_method × reserve_ratio = 2 × 4 × 3 = 24`
- 该表用于 adaptive 自动筛选候选空间。

## 当前 baseline 锁定链路

- failure_model: `schloemer`
- contingency_method: `c3po_ref`
- reserve_ratio: `0.3`
- n_scenarios: `256`

## 24条完整链路

| chain_id | failure_model | contingency_method | reserve_ratio | run_tag_pattern |
|---|---|---|---:|---|
| C01 | schloemer | wang_qmc | 0.05 | `schloemer__wang_qmc__rr0p05` |
| C02 | schloemer | wang_qmc | 0.15 | `schloemer__wang_qmc__rr0p15` |
| C03 | schloemer | wang_qmc | 0.3 | `schloemer__wang_qmc__rr0p3` |
| C04 | schloemer | wang_mc | 0.05 | `schloemer__wang_mc__rr0p05` |
| C05 | schloemer | wang_mc | 0.15 | `schloemer__wang_mc__rr0p15` |
| C06 | schloemer | wang_mc | 0.3 | `schloemer__wang_mc__rr0p3` |
| C07 | schloemer | c3po_ref | 0.05 | `schloemer__c3po_ref__rr0p05` |
| C08 | schloemer | c3po_ref | 0.15 | `schloemer__c3po_ref__rr0p15` |
| C09 | schloemer | c3po_ref | 0.3 | `schloemer__c3po_ref__rr0p3` |
| C10 | schloemer | trim_ref | 0.05 | `schloemer__trim_ref__rr0p05` |
| C11 | schloemer | trim_ref | 0.15 | `schloemer__trim_ref__rr0p15` |
| C12 | schloemer | trim_ref | 0.3 | `schloemer__trim_ref__rr0p3` |
| C13 | batts | wang_qmc | 0.05 | `batts__wang_qmc__rr0p05` |
| C14 | batts | wang_qmc | 0.15 | `batts__wang_qmc__rr0p15` |
| C15 | batts | wang_qmc | 0.3 | `batts__wang_qmc__rr0p3` |
| C16 | batts | wang_mc | 0.05 | `batts__wang_mc__rr0p05` |
| C17 | batts | wang_mc | 0.15 | `batts__wang_mc__rr0p15` |
| C18 | batts | wang_mc | 0.3 | `batts__wang_mc__rr0p3` |
| C19 | batts | c3po_ref | 0.05 | `batts__c3po_ref__rr0p05` |
| C20 | batts | c3po_ref | 0.15 | `batts__c3po_ref__rr0p15` |
| C21 | batts | c3po_ref | 0.3 | `batts__c3po_ref__rr0p3` |
| C22 | batts | trim_ref | 0.05 | `batts__trim_ref__rr0p05` |
| C23 | batts | trim_ref | 0.15 | `batts__trim_ref__rr0p15` |
| C24 | batts | trim_ref | 0.3 | `batts__trim_ref__rr0p3` |

## 快速使用

- 自动搜索全部候选：

```powershell
python scripts/gridagent_framework.py --config configs/gridagent_framework.formal2024.json --mode adaptive --run-tag formal2024_adaptive_auto
```

- 单链路复现（baseline 手动锁定）请在配置中修改 `baseline` 字段。