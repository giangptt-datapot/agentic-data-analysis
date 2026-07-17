# Power BI Showcase — Kickoff Send-back
**Dataset:** Kaggle `nosbielcs/brazilian-delivery-center` · 7 bảng · 2021-01-01 → 2021-04-30 (mốc `finished` kéo đến 2021-05-07)
Toàn bộ audit/ETL/EDA đã chạy (`scripts/01–06`, `data/processed/`, `reports/01_data_overview.md`).

---

## 1. Data model sơ bộ (đề xuất cho Power BI — star schema)

**Hai fact khác grain, KHÔNG nối trực tiếp fact↔fact.** Payments/deliveries đã rollup vào `fact_orders` để tránh fan-out; giữ thêm `fact_deliveries` cho phân tích tài xế/cự ly.

```
                         dim_date (Calendar 2021-01-01 → 2021-05-07)
                            │ 1─*                    │ 1─*
                            ▼                        ▼
  dim_channel 1─*──► fact_orders  ◄──*─1 dim_store ──*─1 dim_hub
   (id,name,type)   (grain: ĐƠN)     (id,segment,   (id,city,state,
                     368,999 dòng      plan_price)    lat,long)
                            ▲
                            │ (không nối trực tiếp — dùng dim chung)
                    fact_deliveries (grain: LƯỢT GIAO) 378,843 ──*─1 dim_driver
                                                                   (id,modal,type)
```

| Bảng | Loại | Grain | Khóa | Đo lường chính |
|---|---|---|---|---|
| `fact_orders` | Fact | 1 đơn | order_id; FK store_id, channel_id, order_date | order_amount, delivery_fee, delivery_cost, cycle_time, +rollup: pay_total, n_payments, n_deliveries, dist_total_m |
| `fact_deliveries` | Fact | 1 lượt giao | delivery_id; FK driver_id, order_id | delivery_distance_meters, delivery_status |
| `dim_store` | Dim | 1 cửa hàng | store_id | segment (FOOD/GOOD), plan_price, hub_id (denorm hub_city/state) |
| `dim_hub` | Dim | 1 hub | hub_id | city, state, lat/long (bản đồ) |
| `dim_channel` | Dim | 1 kênh | channel_id | name, type (MARKETPLACE/OWN) |
| `dim_driver` | Dim | 1 tài xế | driver_id | modal (MOTOBOY/BIKER), type (FREELANCE/LOGISTIC OP) |
| `dim_date` | Dim | 1 ngày | date | year, month, week, dow, is_weekend + `dim_time` giờ 0–23 |

**Quyết định mô hình + phản biện:**
- `dim_hub` để **snowflake sau `dim_store`** (hub→store→orders). Trade-off: snowflake nhẹ hơn là bổ sung, chấp nhận được vì hub chỉ 32 dòng; nếu cần perf tuyệt đối sẽ **denormalize** hub_city/state vào `dim_store`.
- `dim_date` bắt buộc mark as date table cho time-intelligence (dù chỉ 4 tháng).
- **Doanh thu = `SUM(fact_orders[order_amount])` lọc `order_status="FINISHED"`** — KHÔNG dùng `payments`. Chứng minh double-count: `SUM(payment_amount)=R$37.3M` > `SUM(order_amount)=R$35.3M` do 48,818 đơn tách nhiều payment.
- Quan hệ 1 chiều (single direction) từ dim → fact; tránh bi-directional trừ khi bắt buộc.

---

## 2. Vấn đề chất lượng dữ liệu (đã kiểm kê — chưa xóa dòng nào)

| Vấn đề | Bằng chứng | Ảnh hưởng PBI |
|---|---|---|
| Encoding latin-1 (hubs, stores) | dấu "SÃO PAULO" | Power Query: chọn File Origin = 1252/UTF-8 phù hợp |
| `order_moment_delivered` thiếu **94.7%** | 349,398/369k null | Dùng `finished` làm mốc hoàn tất; KHÔNG dùng delivered cho SLA |
| Missing tăng theo phễu trạng thái | accepted 2.6% → in_expedition 18.3% | Metric funnel chỉ tin cậy tới bước có dữ liệu dày |
| Outlier order_amount max **R$1.79M** | median 71.9 | Flag `flag_extreme_amount` (368 đơn); measure "GMV (clean)" loại flag để đối chiếu |
| Outlier distance max **7,251 km** | median 2.07 km | Flag `flag_extreme_distance` (509 lượt); loại khỏi KPI cự ly |
| Outlier cycle_time max **107 ngày** | median 42 phút | Flag `flag_long_cycle` (7,574 đơn) |
| 764 đơn amount = 0; 18,665 đơn thiếu payment; 10,345 thiếu delivery; 15,886 lượt giao thiếu driver | | Cột cờ + đo coverage; xử lý bằng filter, không xóa |
| Fan-out: 48,818 đơn ≥2 payment, 18,724 đơn ≥2 delivery | | **Rollup trước join** (đã làm trong ETL) |

---

## 3. Bối cảnh nghiệp vụ (agent hiểu)

**Delivery Center** = nền tảng trung gian last-mile ở Brazil, kết nối **cửa hàng** (nhà hàng `FOOD` + bán lẻ `GOOD`) với người mua, giao qua **shipper** (motoboy/xe đạp, chủ yếu freelance), nhận đơn từ **marketplace** (kiểu iFood/Rappi) lẫn **kênh riêng** (web/app/WhatsApp/điện thoại), vận hành qua **32 hub** tại 4 đô thị (São Paulo, Rio, Porto Alegre, Curitiba). Cửa hàng trả **phí thuê bao** (`store_plan_price`) + có thể mất phí hoa hồng marketplace. Đơn vị kiếm tiền từ chênh phí giao + phí nền tảng; chịu chi phí shipper. Đòn bẩy nghiệp vụ: **tối ưu thời gian/chi phí giao, giảm hủy đơn, tăng AOV, cân đội xe theo cao điểm, quản trị rủi ro phụ thuộc kênh**.

**5 nhóm người dùng & câu hỏi lõi:** Ban điều hành (sức khỏe GMV & rủi ro tập trung) · Operations Manager (SLA giao, cao điểm, năng suất) · Hub Manager (hub nào quá tải/kém hiệu suất) · Store/Partner Manager (đối tác nào đóng góp/rủi ro, cần cải thiện) · Delivery Performance Manager (thời gian/cự ly giao, đội xe).

---

## 4. Ba concept phân tích khả thi

**Concept A — "Commercial & Growth Health" (thương mại/tăng trưởng).**
Trọng tâm GMV, AOV, cơ cấu segment/kênh, đóng góp & rủi ro của cửa hàng-đối tác, hủy đơn như rủi ro doanh thu. Người dùng chính: Ban điều hành + Store/Partner Manager. 4 trang. *Ưu:* câu chuyện tiền bạc rõ, dễ "viral". *Nhược:* bỏ mảng vận hành/tài xế — chỉ phục vụ 2/5 nhóm.

**Concept B — "Delivery Operations Excellence" (vận hành).**
Trọng tâm cycle time & phễu thời gian, cự ly, tỷ lệ giao thành công, đội xe, throughput hub, cao điểm & bố trí nhân lực. Người dùng: Ops + Hub + Delivery Performance Manager. 4 trang. *Ưu:* chiều sâu vận hành, nhiều visual "khó" (box plot, heatmap, scatter). *Nhược:* nhẹ phần thương mại — kém hấp dẫn với lãnh đạo & không thể hiện bức tranh doanh thu.

**Concept C — "Marketplace 360 — Command Center" (tích hợp toàn diện). ⭐ĐỀ XUẤT**
6 trang phủ cả 5 nhóm, đi từ điều hành → doanh thu → vận hành → hub/địa lý → cửa hàng/đối tác → Insight Lab (decomposition tree, key influencers, scatter, what-if, drill-through). *Ưu:* đúng yêu cầu 4–6 trang + đủ 5 nhóm + đủ đất cho đa dạng visual & tính năng PBI (bookmark/nav/tooltip/drill) → **chuẩn showcase cộng đồng**. *Nhược:* rộng dễ loãng.

---

## 5. Đề xuất concept tốt nhất

**Chọn Concept C ("Marketplace 360 — Command Center").**
Lý do: brief yêu cầu tường minh 4–6 trang, phục vụ cả 5 nhóm người dùng, và "showcase" — chỉ concept tích hợp mới đáp ứng đồng thời. A và B là **tập con** của C, nên C không tốn thêm chi phí phân tích (dữ liệu đã sẵn), chỉ cần kỷ luật thiết kế.

**Kiểm soát nhược điểm "rộng dễ loãng":** mỗi trang có **1 chủ sở hữu (persona) + 1 hero-insight duy nhất + tối đa 5–6 visual**; điều hướng menu cố định; drill-through xuyên trang để giữ chiều sâu thay vì nhồi visual.

**Cấu trúc trang dự kiến (sẽ chi tiết hoá ở bước sau):**
`P1 Executive Overview` · `P2 Order & Revenue` · `P3 Delivery Performance` · `P4 Hub & Geographic` · `P5 Store & Partner` · `P6 Insight Lab (deep-dive)` + tooltip pages + drill-through page.

---

## Senior DA Review (cuối giai đoạn kickoff)

- **Đã được dữ liệu xác nhận:** grain & quan hệ 7 bảng (0 FK mồ côi); GMV/AOV/cancel/cycle/distance; **tương quan cự ly↔cycle time chỉ 0.28** (cự ly giải thích <8% biến thiên thời gian → thời gian *chuẩn bị* mới là nút thắt, không phải quãng đường); double-count nếu dùng payments làm doanh thu.
- **Mới là giả thuyết:** múi giờ UTC-3; nguyên nhân GOOD hủy cao; "phụ thuộc kênh = rủi ro" (đúng về mặt tập trung, nhưng chưa có dữ liệu hoa hồng để định lượng thiệt hại).
- **Nguy cơ tính sai/double count:** (1) dùng `payment_amount` làm doanh thu; (2) join deliveries/payments thô vào orders gây nhân đôi; (3) so sánh hub/tài xế **không đặt ngưỡng sản lượng tối thiểu** → "HUBLESS 60% hủy" chỉ do 2 đơn, "R SHOPPING" 183 đơn. → Bắt buộc lọc min-volume khi ranking.
- **Insight yếu/hiển nhiên cần loại:** "doanh thu tăng theo tháng", "SP nhiều đơn nhất" — chỉ giữ nếu bóc tách được nguyên nhân/phân khúc.
- **Dữ liệu còn thiếu (giới hạn cứng):** **KHÔNG có customer_id** → không thể làm retention/cohort/LTV/RFM; **không có chi tiết sản phẩm/giỏ hàng** (chỉ tổng `order_amount`); không có chi phí/margin ngoài phí giao; **chỉ 4 tháng/1 năm** → không YoY, mùa vụ hạn chế; không có route/GPS thực.
- **Bước tiếp theo cần kiểm chứng:** ngưỡng min-volume cho ranking hub/store/driver; định nghĩa "delivery success" (mẫu số = deliveries hay orders?); có nên trình cả GMV-raw vs GMV-clean(loại flag) để minh bạch outlier.
