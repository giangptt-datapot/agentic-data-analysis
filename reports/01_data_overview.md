# Brazilian Delivery Center — Data Audit & Analysis Plan (Checkpoint 1)

**Nguồn:** Kaggle `nosbielcs/brazilian-delivery-center` · 7 bảng CSV · ~120 MB
**Khoảng thời gian:** `order_moment_created` từ **2021-01-01** đến **2021-04-30** (4 tháng, 1 năm duy nhất)
**Bối cảnh nghiệp vụ:** Một "delivery center" ở Brazil trung gian giữa **cửa hàng (stores)** và **người mua**, giao hàng qua đội **shipper (drivers)**, đơn đến từ nhiều **kênh (channels)** gồm marketplace (kiểu iFood/Uber Eats) và kênh riêng, hoạt động tại các **hub** ở 4 thành phố.

---

## 1. Tổng quan dữ liệu

### 1.1 Các bảng & grain

| Bảng | Số dòng | Grain (1 dòng = ?) | Khóa chính | Cột chính |
|---|--:|---|---|---|
| **orders** | 368,999 | 1 đơn hàng | `order_id` | store_id, channel_id, order_status, order_amount, delivery_fee/cost, 8 mốc thời gian + 7 metric thời lượng |
| **deliveries** | 378,843 | 1 lượt giao | `delivery_id` | delivery_order_id (FK), driver_id, distance_meters, delivery_status |
| **payments** | 400,834 | 1 giao dịch thanh toán | `payment_id` | payment_order_id (FK), amount, fee, method, status |
| **stores** | 951 | 1 cửa hàng | `store_id` | hub_id (FK), segment, plan_price, lat/long |
| **hubs** | 32 | 1 hub | `hub_id` | name, city, state, lat/long |
| **channels** | 40 | 1 kênh bán | `channel_id` | channel_name, channel_type |
| **drivers** | 4,824 | 1 shipper | `driver_id` | driver_modal (moto/xe đạp), driver_type |

### 1.2 Quan hệ (đã kiểm tra tính toàn vẹn — 0 FK mồ côi)
```
hubs 1─* stores 1─* orders *─1 channels
                       orders 1─* deliveries *─1 drivers
                       orders 1─* payments
```
- **orders → stores → hubs → city/state**: 100% khớp.
- **orders → channels**: 100% khớp (39/40 kênh có phát sinh đơn).
- ⚠️ **1 đơn có thể có NHIỀU delivery và NHIỀU payment** (fan-out — xem mục 2).

### 1.3 Chiều dữ liệu chính
- **Địa lý:** 4 thành phố / 4 bang — São Paulo (SP, 15 hub), Rio de Janeiro (RJ, 9), Porto Alegre (RS, 4), Curitiba (PR, 4).
- **Loại cửa hàng:** `FOOD` (nhà hàng/đồ ăn) vs `GOOD` (bán lẻ/hàng hóa).
- **Loại kênh:** `MARKETPLACE` (26 kênh) vs `OWN CHANNEL` (14 kênh).
- **Đội giao:** modal `MOTOBOY` / `BIKER`; type `FREELANCE` / `LOGISTIC OPERATOR`.

---

## 2. Vấn đề chất lượng dữ liệu (đã kiểm kê — **CHƯA xóa dòng bất thường nào**)

| # | Vấn đề | Bằng chứng | Xử lý trong ETL |
|---|---|---|---|
| 1 | **Encoding** hubs.csv & stores.csv không phải UTF-8 (dấu tiếng Bồ: "SÃO PAULO") | UnicodeDecodeError ở byte 0xC3 | Đọc fallback `latin-1` |
| 2 | **`order_moment_delivered` thiếu 94.7%** dù 371k lượt "DELIVERED" | 349,398/368,999 null | Dùng `order_moment_finished` (thiếu 4.2%) làm mốc hoàn tất |
| 3 | **Missing tăng dần theo phễu** trạng thái | accepted 2.6% → collected 11.6% → in_expedition 18.3% null | Giữ nguyên; chỉ dùng mốc đủ dày |
| 4 | **Outlier order_amount** cực đại 1,788,306 BRL (median 71.9, mean 105) | std 2,953 | FLAG `flag_extreme_amount` (>p99.9 = 1,500 BRL): 368 đơn |
| 5 | **Outlier khoảng cách giao** cực đại 7,251 km (median 2.07 km) | 509 dòng > 50 km | FLAG `flag_extreme_distance`; loại khỏi thống kê distance nhưng GIỮ dòng |
| 6 | **Outlier cycle_time** cực đại 154,277 phút ≈ 107 ngày (median 42 phút) | 7,574 đơn > 24h | FLAG `flag_long_cycle` |
| 7 | **764 đơn order_amount = 0** | không âm | FLAG `flag_zero_amount` |
| 8 | **Fan-out 1-nhiều:** 48,818 đơn có ≥2 payment, 18,724 đơn có ≥2 delivery | payments 400k > 350k order distinct | **Rollup trước khi join** để không nhân đôi doanh thu |
| 9 | Đơn **không có payment** (18,665) / **không có delivery** (10,345) | | Cờ `has_payment`, `has_delivery` |
| 10 | **15,886 dòng delivery thiếu driver_id** (4.2%) | | Giữ; loại khi phân tích theo shipper |
| 11 | `store_plan_price` thiếu 12%, `store_lat/long` thiếu 1.7% | | Giữ; ảnh hưởng riêng bản đồ |
| 12 | **Nghi ngờ timezone (UTC vs BRT)** — đỉnh giờ 15h & 22-23h | 15h UTC = 12h trưa BRT; 22h UTC = 19h tối BRT | **Giả thuyết**, cần xác nhận; hiện diễn giải theo giờ địa phương |
| 13 | Chỉ **4 tháng / 1 năm** | 2021-01 → 2021-04 | Không thể phân tích YoY / mùa vụ dài |

**Nguyên tắc đã áp dụng:** mọi bất thường được **gắn cờ, không xóa**. Rollup payments/deliveries về mức đơn trước khi join để tránh double-counting.

---

## 3. Hướng phân tích đề xuất

Đối tượng chính của dashboard: **Ban điều hành / Ops & Commercial của delivery center**. Ba trục câu hỏi:

1. **Tăng trưởng & Doanh thu (GMV):** GMV theo thời gian, AOV, cơ cấu theo segment / kênh / thành phố.
2. **Vận hành giao hàng:** thời gian chu trình, khoảng cách, cơ cấu đội xe, tỷ lệ hủy.
3. **Rủi ro & Kinh tế đơn vị:** hủy đơn theo segment/thời gian, chargeback, biên phí giao (fee vs cost), phụ thuộc kênh.

---

## 4. KPI đề xuất (đã tính sơ bộ)

| KPI | Giá trị (4 tháng) |
|---|--:|
| Tổng đơn | 368,999 |
| Đơn hoàn tất (FINISHED) | 352,020 |
| **GMV (đơn hoàn tất)** | **R$ 35,29 triệu** |
| **AOV** | R$ 100.3 (median R$ 71.9) |
| **Tỷ lệ hủy đơn** | **4.6%** |
| Cửa hàng active / tổng | 883 / 951 |
| Median cycle time | 41.8 phút (p90 = 75 phút) |
| Median quãng đường giao | 2.06 km |
| Tỷ lệ chargeback | 0.12% |
| % đơn free-ship | 35.6% |

---

## 5. Insight tiềm năng (đã có số liệu chứng minh)

> Phân biệt rõ: **[Chứng minh]** = tính trực tiếp từ dữ liệu · **[Giả thuyết]** = cần dữ liệu/bối cảnh bổ sung.

1. **FOOD chạy volume, GOOD chạy giá trị giỏ hàng.** [Chứng minh] FOOD = 88.3% số đơn nhưng AOV chỉ R$84; GOOD = 11.7% số đơn, AOV R$220 (gấp 2.6×), đóng góp 25.7% GMV.
2. **Doanh thu tập trung cực mạnh (Pareto).** [Chứng minh] Top 12.2% cửa hàng active (108/883) tạo 80% GMV; top 20% tạo 88.4%.
3. **Phụ thuộc một kênh duy nhất.** [Chứng minh] MARKETPLACE = 79% GMV; riêng kênh "FOOD PLACE" = 279,632 đơn (79% đơn hoàn tất) & R$24.05M (68% GMV). OWN CHANNEL AOV cao hơn (R$218 vs R$88). → **[Giả thuyết]** rủi ro tập trung / chi phí hoa hồng.
4. **GOOD bị hủy gấp ~4× FOOD, và tỷ lệ hủy đang tăng.** [Chứng minh] Cancel rate GOOD 12.7% vs FOOD 3.4%; theo tháng 4.34% (T1) → 5.03% (T4). **[Giả thuyết]** nguyên nhân (tồn kho? thời gian giao?) chưa xác định.
5. **Giao hàng là "loss leader".** [Chứng minh] Phí thu bình quân R$6.22 < chi phí giao R$7.58; 53.4% đơn phí thu < chi phí; 35.6% đơn free-ship.
6. **Cầu theo giờ lưỡng đỉnh (trưa + tối) và dồn cuối tuần.** [Chứng minh] Đỉnh 15h & 22-23h UTC; Thứ 6–CN ≈ 174k đơn > T2–T5. **[Giả thuyết]** đỉnh = 12h/19h giờ địa phương (lệch UTC-3).
7. **Phân bổ đội xe khớp cự ly.** [Chứng minh] MOTOBOY 73% lượt giao, median 2.62 km; BIKER 27%, median 1.03 km (ngắn hơn 2.5×). 71% shipper là FREELANCE.
8. **Tập trung địa lý.** [Chứng minh] São Paulo + Rio = 86.3% GMV (52.7% + 33.6%); SP có AOV cao nhất R$116.9.

---

## 6. Bước tiếp theo
Sau khi anh/chị **duyệt hướng phân tích + chốt 5–8 insight**, tôi sẽ dựng **mockup HTML dashboard** để review trước, rồi mới build dashboard hoàn chỉnh + validation + assets đăng bài.
