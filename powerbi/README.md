# Power BI Project — Brazilian Delivery Center (PBIP/TMDL)

Bàn giao dạng **PBIP** (Power BI Project, text-based) — mở bằng **Power BI Desktop** (bật *Preview features → Power BI Project (.pbip)* và *TMDL / PBIR*).

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
5. Import theme: *View → Themes → Browse for themes → `DeliveryCenter_Light.theme.json`*.

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
| Số liệu measure (17 KPI) | ✅ validate bằng pandas, khớp mockup |
| Toàn vẹn khóa/FK, bẫy double-count | ✅ kiểm (0 orphan) |
| TMDL model/M/DAX viết theo spec | ⚠️ mở bằng Desktop để round-trip xác nhận |
| Report visual 7 trang | ⚠️ skeleton — dựng theo `dashboard/mockup_light.html` |
| Bookmark / drill-through / tooltip page / nav | ⚠️ cấu hình trong Desktop (mockup mô phỏng đầy đủ UX) |

## Ranking & min-volume (bắt buộc)
Trang Hub/Store: áp **min-volume** (hub ≥500, store ≥100 đơn) qua visual filter hoặc measure guard, tránh mẫu nhỏ gây nhiễu (vd HUBLESS 60% hủy do 2 đơn).
