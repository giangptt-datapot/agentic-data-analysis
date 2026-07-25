# Power BI Project — Brazilian Delivery Center (PBIP/TMDL)

Bàn giao dạng **PBIP** (Power BI Project, text-based) — mở bằng **Power BI Desktop** (bật *Preview features → Power BI Project (.pbip)* và *TMDL / PBIR*).

> ## 🆕 v2 — dựng lại theo user story (8 trang)
> Report đã được **dựng lại toàn bộ** theo `reports/07_user_stories_insights.md`: mỗi trang = 1 user story,
> có KPI card trả lời câu hỏi + chart chứng minh + textbox mang finding/hành động/giới hạn.
> Xem trước không cần Desktop: **`dashboard/pbi_v2_preview.html`** và **`outputs/figures/v2_p1..v2_p8.png`**
> (render trực tiếp từ PBIR definition — cùng toạ độ/loại visual, số liệu thật).
>
> | Trang | User story | Hero insight |
> |---|---|---|
> | 1 Executive Overview | US-1 ban điều hành | **1 thương hiệu = 34,5% GMV** (IUMPICA, 14 chi nhánh) |
> | 2 Demand & Order Mix | US-2 ops planner | 73,5% cầu trong 7/24 giờ · đơn 0–9h hủy 18,9% |
> | 3 Fulfilment SLA | US-3 delivery perf. | KPI cycle gộp là sai: P90 FOOD 64,6′ vs GOOD 947′ |
> | 4 Hub Operations | US-4 hub manager | ELIXIR hủy 30,8% (min-vol ≥500 đơn) |
> | 5 Partner & Brand | US-5 account mgr | Fix-first 53 store = 17,8% GMV, hủy 9,8% |
> | 6 Cancellation Root-cause | US-6 ops/commercial | **GOOD×MARKETPLACE 22,5%** vs GOOD×OWN 4,8% |
> | 7 Delivery Economics | US-7 finance/pricing | free-ship lỗ R$920k · đơn có phí **lãi R$466k** |
> | 8 Data Trust & Actions | US-8 BI analyst | 1 đơn R$1,79M = 51% “tiền rủi ro” |
>
> **Model v2 (`scripts/13_extend_model.py`)** — thêm vào TMDL:
> * **Grain Brand**: `dim_store[brand]` (= TRIM(store_name)) + `store_label` (tên + #store_id, vì 137 tên trùng tới 15 store_id) + `plan_tier`.
> * **Distance ở order-grain**: Power Query roll-up `deliveries.csv` → `dist_mean_m`/`n_deliveries` trên `fact_orders` (quan hệ orders→deliveries 1 chiều nên cột delivery KHÔNG lọc được measure tiền) + `order_distance_band`.
> * **Banding**: `order_value_band`, `daypart`, `cycle_bucket` (kèm cột `*_no` để sortByColumn).
> * **28 measure mới**, đáng chú ý:
>   * `Canceled GMV (at risk)` — loại `flag_extreme_amount` (1 đơn hủy R$1.788.306 chiếm 51% con số thô) + `Canceled GMV (raw, incl. outliers)` để audit.
>   * `Median/P90 Cycle FOOD|GOOD (min)`, `SLA Breach % (over 60min)`, `Median Prep/Transit (min)`, `P95 Cycle (min)`.
>   * `Delivery Margin`, `Free-ship Margin`, `Paid-ship Margin`, `Delivery Margin / Order`.
>   * Guard chống mẫu nhỏ: `Cancellation Rate (min 500 orders)` / `(min 100 orders)` / `Median Prep (min 200 orders)`.
>   * Top-N bằng RANKX guard (category rỗng tự ẩn, không cần visual-level filter): `GMV (Top 12 Brands)` / `(Top 10 Channels)` / `(Top 15 Stores)`; `GMV Concentration Top1 Brand %`.
> * `dim_date`: bỏ `isPrivate` (nếu private thì slicer/axis không dùng được) và đánh dấu `dataCategory: Time`.
>
> **Cần làm trong Desktop sau khi mở:** bật *Sync slicers* cho 4 slicer (Date/City/Segment/Channel) để chúng liên kết giữa 8 trang; drill-through + tooltip page vẫn phải cấu hình tay.
>
> Pipeline tái tạo: `13_extend_model.py` → `14_gen_visuals_v2.py` → `15_gen_preview_data.py` → `16_gen_pbi_preview.py`.
> (`11_gen_visuals.py` là bản v1 7 trang — đã bị `14_*` ghi đè.)

## 📦 1 file dùng ngay: `BrazilianDeliveryCenter_PBIP.zip`
Tải file zip → **giải nén** → mở `BrazilianDeliveryCenter/BrazilianDeliveryCenter.pbip`. (PBIP bản chất là 1 thư mục nên đóng gói dưới dạng zip; PBI Desktop trên Linux không có nên không xuất `.pbix` được.) **7 trang đã có sẵn visual** bind vào measure — mở là thấy chart, chỉ cần trỏ `SourceFolder` tới thư mục CSV rồi Refresh.

> ⚠️ **Về môi trường build:** project được soạn trên Linux (không có Power BI Desktop để render `.pbix`). Vì vậy **semantic model (TMDL) + Power Query (M) + DAX** được soạn theo spec và **validate bằng cách tái tính toàn bộ measure bằng pandas** (xem `reports/05_validation.md` — 17/17 khớp). Phần **report visual** để dạng skeleton 7 trang; dựng visual theo `dashboard/mockup_light.html` (đặc tả pixel) + `reports/04`.

## Nội dung
```
BrazilianDeliveryCenter.pbip                      ← mở file này
BrazilianDeliveryCenter.SemanticModel/            ← data model (TMDL)
  definition/
    model.tmdl · database.tmdl · relationships.tmdl · expressions.tmdl
    tables/  fact_orders, fact_deliveries, fact_payments,
             dim_store, dim_hub, dim_channel, dim_driver, dim_date
BrazilianDeliveryCenter.Report/                   ← report skeleton (7 pages) + theme resource
DeliveryCenter_Light.theme.json                   ← theme import (View → Themes → Browse)
```

## Trước khi mở — bật Preview features (bắt buộc)
Power BI Desktop → **File → Options and settings → Options → Preview features** → tích:
- **Power BI Project (.pbip) save option**
- **Store semantic model using TMDL format**
- **Store reports using enhanced metadata format (PBIR)**

Khởi động lại Desktop. (Nếu bản Desktop quá cũ không có PBIR → xem *Fallback* cuối file.)

## Cách mở & nạp dữ liệu
1. Tải 7 CSV Kaggle (`orders, deliveries, payments, stores, hubs, channels, drivers`) vào 1 thư mục.
2. Mở `BrazilianDeliveryCenter.pbip` bằng Power BI Desktop.
3. **Transform data → Edit Parameters → `SourceFolder`** = đường dẫn thư mục CSV (ví dụ `C:\BDC\`, có dấu `\` cuối).
4. **Refresh**. (Import mode; `stores.csv`/`hubs.csv` đọc encoding 1252 cho dấu tiếng Bồ.)
5. **Theme light tự áp dụng** (đã nhúng vào report qua RegisteredResources) — không cần import tay. Nếu vì lý do nào đó không áp: *View → Themes → Browse → `DeliveryCenter_Light.theme.json`*.
6. **Menu/pagination:** mỗi trang có **Page Navigator** (thanh trên cùng) để chuyển 7 trang.
7. **Data labels + nền card bo góc + đổ bóng** đã bật sẵn theo palette light.

> **Đã sửa lỗi mở (căn theo 1 PBIP mẫu chạy thành công):**
> 1. `.platform` `logicalId` → **GUID hợp lệ** (lỗi *"...to type System.Guid"*).
> 2. `.pbip` `$schema` → `fabric/pbip/pbipProperties/1.0.0` (lỗi *"$schema ... to follow patterns"*).
> 3. `definition.pbir` → `$schema` `item/report/definitionProperties/2.0.0` + **`version: "4.0"`** (bắt buộc để dùng folder `definition/` PBIR).
> 4. **Thêm `definition/version.json`** — file PBIR **bắt buộc** (trước đó thiếu).
> 5. `report.json` `report/3.3.0` + baseTheme; `pages.json` `pagesMetadata/1.1.0`; `page.json` `page/2.1.0`.
> 6. `database.tmdl` compatibilityLevel `1600`; `model.tmdl` thêm `sourceQueryCulture`/`dataAccessOptions` + `cultures/en-US.tmdl`.

## Fallback (nếu report PBIR vẫn báo lỗi trên bản Desktop cũ)
Giá trị cốt lõi nằm ở **semantic model** (đã validate 17/17). Nếu trang report không mở:
1. Tạo file **.pbix trắng** mới → **Get data → Blank query** hoặc dùng **Tabular Editor** mở thư mục `BrazilianDeliveryCenter.SemanticModel` (TMDL) để nạp model + measures.
2. Hoặc cập nhật Power BI Desktop lên bản mới nhất (PBIR đã GA từ 2024) rồi mở lại `.pbip`.
3. Dựng visual 7 trang theo `dashboard/mockup_light.html`.

## Data model (star schema)
- **Fact:** `fact_orders` (grain đơn), `fact_deliveries` (grain lượt giao), `fact_payments` (grain thanh toán).
- **Dim:** `dim_store → dim_hub` (snowflake), `dim_channel`, `dim_driver`, `dim_date` (calculated, marked).
- **Quan hệ:** dim→fact 1 chiều; `fact_orders → fact_deliveries/fact_payments` 1:N (để delivery/payment kế thừa dim của đơn).
- **Doanh thu = `[GMV]` (SUM order_amount, FINISHED)** — KHÔNG dùng `SUM(payment_amount)` (fan-out 48,818 đơn tách payment → phồng ~R$2M).

## Power Query (M) — trong mỗi table partition
- Đọc CSV theo `SourceFolder`; ép kiểu; parse `order_moment_created` → **UTC-3** (`created_local`) → `order_date/hour/dow`.
- Cột cờ chất lượng (`flag_zero_amount / flag_extreme_amount / flag_long_cycle / flag_extreme_distance`) — **gắn cờ, không xóa dòng**.

## DAX measures (đã validate 17/17 — `reports/05_validation.md`)
`Total/Finished/Canceled Orders · GMV · AOV · Median Order Value · Cancellation/Fulfillment Rate · Active Stores · Median/P90 Cycle · Deliveries/Delivered/Delivery Success Rate · Median Distance (km) · Active Drivers · Payments · Chargeback Orders/Rate · Mean Delivery Fee/Cost · Delivery Subsidy/Order · Free-ship Order % · GMV Concentration Top1 Channel %`.

## ✅ Đã verify vs ⚠️ cần Power BI Desktop hoàn thiện
| Hạng mục | Trạng thái |
|---|---|
| Số liệu measure (17 KPI v1) | ✅ validate bằng pandas, khớp mockup |
| Số liệu v2 (brand/at-risk/margin/SLA theo segment) | ✅ tính lại từ `data/processed` — `outputs/userstory_insights.json` |
| Toàn vẹn khóa/FK, bẫy double-count | ✅ kiểm (0 orphan) |
| TMDL model/M/DAX viết theo spec | ⚠️ mở bằng Desktop để round-trip xác nhận (không có PBI Desktop trên Linux) |
| Report visual 8 trang v2 | ✅ 138 visual (gồm 6 shell/trang) bind vào measure; JSON parse OK; mọi tham chiếu measure/column đã đối chiếu với TMDL (0 thiếu) |
| Slicer sync / drill-through / tooltip page / bookmark | ⚠️ cấu hình trong Desktop (slicer đã có sẵn trên mọi trang, chỉ cần bật *Sync slicers*) |
| Preview offline | ✅ `dashboard/pbi_v2_preview.html` + `outputs/figures/v2_p*.png` render từ PBIR definition |

## Ranking & min-volume (bắt buộc)
Trang Hub/Store: áp **min-volume** (hub ≥500, store ≥100 đơn) qua visual filter hoặc measure guard, tránh mẫu nhỏ gây nhiễu (vd HUBLESS 60% hủy do 2 đơn).
