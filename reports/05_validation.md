# 05 — Validation Report (DAX ⇄ pandas re-derivation)

Re-derived **17 measures** from RAW CSVs replicating exact DAX logic; compared to mockup `page_data.json`.
**Result: 17/17 match.**

> Substitute for opening .pbix (no Power BI Desktop on Linux). pandas logic mirrors the DAX filter context (FINISHED filter, UTC-3 shift, outlier guards ≤1440min / ≤50km, DISTINCTCOUNT for chargeback).

## Measure checks

| Measure | pandas (=DAX logic) | mockup/expected | |
|---|--:|--:|:-:|
| Total Orders | 368999 | 368999 | ✅ |
| Finished Orders | 352020 | 352020 | ✅ |
| Canceled Orders | 16979 | 16979 | ✅ |
| GMV | 35293230 | 35293230 | ✅ |
| AOV | 100.26 | 100.26 | ✅ |
| Cancellation Rate % | 4.60 | 4.60 | ✅ |
| Fulfillment Rate % | 95.40 | 95.40 | ✅ |
| Active Stores | 883 | 883 | ✅ |
| Median Cycle (min) | 41.8 | 41.8 | ✅ |
| P90 Cycle (min, ≤180 window) | 67.5 | 67.5 | ✅ |
| Median Distance (km) | 2.06 | 2.06 | ✅ |
| Delivery Success Rate % | 98.03 | 98.03 | ✅ |
| Chargeback Rate % | 0.115 | 0.115 | ✅ |
| Mean Delivery Fee | 6.22 | 6.22 | ✅ |
| Mean Delivery Cost | 7.58 | 7.58 | ✅ |
| Free-ship Order % | 35.6 | 35.6 | ✅ |
| GMV Concentration Top1 % | 68.2 | 68.2 | ✅ |

## Integrity & filter-context traps

| Check | Evidence | Verdict |
|---|---|---|
| Double-count trap: SUM(payments) ≠ revenue | Σpay=R$37,313,341 vs GMV=R$35,293,230 | payments > GMV → measure uses order_amount only |
| FK: orders.store_id ⊆ stores | orphans=0 | ✅ |
| FK: orders.channel_id ⊆ channels | orphans=0 | ✅ |
| FK: deliveries.order_id ⊆ orders | orphans=0 | ✅ |
| FK: payments.order_id ⊆ orders | orphans=0 | ✅ |
| Grain: orders 1:N deliveries | 18724 orders >1 delivery | single-direction rel OK |
| Grain: orders 1:N payments | 48818 orders >1 payment | revenue not from payments |

## Notes / limits carried into the model
- **Revenue = `[GMV]` (SUM order_amount, FINISHED)** — never `SUM(payment_amount)` (would inflate ~R$2M via split payments).
- Ranking pages must apply **min-volume** (hub≥500, store≥100) — enforce via visual filter or a measure guard.
- `order_moment_delivered` ~94.7% null → completion proxy = `order_moment_finished`; cycle uses `order_metric_cycle_time`.
- Timezone UTC−3 is an **assumption** (applied in Power Query `created_local`).
- No `customer_id` / product detail / >4 months → retention, basket, YoY out of scope.
- P90 measure in TMDL uses ≤1440min guard; mockup histogram used ≤180min window — both reported, values differ by design (tail trimming).