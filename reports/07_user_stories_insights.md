# User Stories · Insights · Dashboard Rebuild (Brazilian Delivery Center)

**Nguồn số:** `outputs/userstory_insights.json` (script `scripts/12_userstory_insights.py`, tính lại trực tiếp từ `data/processed/fact_orders.csv` 368,999 đơn + `dim_deliveries.csv` 378,843 lượt giao).
**Kỳ dữ liệu:** 01/01/2021 → 30/04/2021 (4 tháng). Giờ = **UTC−3 (giả định)**.
**Tiền:** GMV = `SUM(order_amount)` trên đơn `FINISHED` = **R$35,293,230** (KHÔNG dùng payments — fan-out 48,818 đơn tách thanh toán).

> Báo cáo này **thay thế** phần insight của `03_business_questions_kpi_insights.md` ở 4 điểm bị sai/thiếu (đánh dấu 🔁 bên dưới) và là spec cho bản dashboard Power BI dựng lại (8 trang, `powerbi/`).

---

## 0. Tóm tắt — 12 insight, xếp theo giá trị hành động

| # | Insight | Bằng chứng | Loại |
|---|---|---|---|
| 1 | **1 thương hiệu = 34.5% GMV** (IUMPICA, 14 chi nhánh) | R$12.17M/R$35.29M | 🔁 mới, mạnh nhất |
| 2 | Hủy đơn là **bài toán GOOD × MARKETPLACE**, không phải "GOOD" | 22.5% vs GOOD-own 4.8% | 🔁 sửa insight cũ |
| 3 | **Free-ship là toàn bộ khoản lỗ giao hàng**; đơn có thu phí thì có lãi | −R$920k vs +R$466k | 🔁 định lượng mới |
| 4 | KPI cycle-time gộp FOOD+GOOD là **vô nghĩa** (2 quy trình khác nhau) | P90 FOOD 64.6′ vs GOOD 947′ | 🔁 lỗi thiết kế KPI |
| 5 | Tăng trưởng là **same-store**, không phải mở rộng đối tác | +50.2% M1→M4, same-store = 86% GMV | mới |
| 6 | **Cự ly không quyết định thời gian** (r=0.23) nhưng **pha transit thì có** (r=0.66) | R² 5% vs 44% | tinh chỉnh insight 8 cũ |
| 7 | Gói thuê (`store_plan_price`) **ngược** với giá trị: 56 store gói R$0 = 34% GMV | cancel 2.3% vs gói R$29.9 = 12.9% | mới (trục chưa ai dùng) |
| 8 | Đơn **ngoài giờ mở cửa (0–9h)** hủy 18.9% vs 4.4% | 4,391 đơn = 4.9% tổng số hủy | mới |
| 9 | Rủi ro tập trung kênh: FOOD PLACE **68.2% GMV** | own-channel AOV R$229 vs marketplace R$86 | xác nhận |
| 10 | Hub **ELIXIR SHOPPING** hủy 30.8% & median cycle 26 giờ | ≥500 đơn; hub GOOD-heavy | xác nhận + giải thích |
| 11 | **10% shipper làm 55.6% lượt giao**; 23.6% shipper <5 lượt | 4,583 shipper active | 🔁 sửa số cũ ("top10 = 7.3%") |
| 12 | **1 đơn hủy R$1.79M chiếm 51%** "GMV at risk" → KPI tiền-rủi ro phải loại outlier | GRIME CRU @ SAMPA hub | 🔁 lỗi đo lường |

---

## US-1 · Ban điều hành (CEO/COO) — "Sức khỏe & rủi ro tập trung"

> **As a** thành viên ban điều hành, **I want** thấy GMV/đơn/hủy đang đi đâu và doanh thu phụ thuộc vào ai, **so that** tôi biết rủi ro nào có thể đánh sập P&L trong 1 quý.

**KPI:** GMV R$35.29M · 368,999 đơn (352,020 hoàn tất) · AOV R$100.26 (median R$71.9) · hủy 4.6% · 883 store · 32 hub · 4 thành phố.

### Insight 1 — Một thương hiệu chiếm 34.5% GMV (rủi ro lớn hơn mọi con số Pareto đã báo cáo)
- **Phát hiện:** `store_name` **không phải khóa** — 137 tên trùng, tối đa 15 `store_id`/tên. Gộp theo thương hiệu: **IUMPICA = 14 chi nhánh, 93,759 đơn, R$12.17M = 34.49% GMV**. Top 3 thương hiệu = **46.3%**, top 10 = **61.8%**. Ở grain `store_id` con số này bị chia nhỏ thành 14 dòng nên **dashboard cũ không nhìn thấy**.
- **Ý nghĩa:** mất 1 hợp đồng thương hiệu = mất 1/3 doanh thu. Đây là rủi ro tập trung nghiêm trọng hơn cả phụ thuộc kênh (68%).
- **Hành động:** thêm grain **Brand** (`store_name`) vào model; đặt KPI "Top-1 brand GMV %"; account plan riêng + điều khoản hợp đồng cho IUMPICA/SALITO/IPUPIEMAI.
- **Giới hạn:** tên store đã ẩn danh → "cùng tên = cùng chuỗi" là **giả định** (được củng cố bởi: cùng segment, nhiều city, pattern chi nhánh). Cần xác nhận với business.

### Insight 5 — Tăng trưởng đến từ same-store, không phải mở rộng đối tác
- **Phát hiện:** 411 store hoạt động cả 4 tháng = **86.1% GMV**, GMV tháng 1 → tháng 4 **+50.2%**. Đóng góp của store mới chỉ **2.4–9.1%**/tháng. Bước nhảy T2→T3 (+84.6% GMV) là do đối tác **hiện hữu**.
- **Ý nghĩa:** cỗ máy hiện tại đang tăng năng suất — ưu tiên giữ & nâng đối tác cũ hơn là săn đối tác mới.
- **Giới hạn dữ liệu:** tuần cuối (26–30/04) chỉ có **5 ngày** → biểu đồ tuần "giảm cuối kỳ" một phần là **cắt cụt (truncation)**, phải đánh dấu trên dashboard. Xu hướng giảm 3 tuần đầy đủ cuối (2.58M → 2.38M → 2.26M) thì là thật.

### Insight 9 — Phụ thuộc 1 kênh: FOOD PLACE 68.2% GMV
- FOOD PLACE 279,632 đơn / R$24.05M / AOV R$86 · MARKETPLACE tổng 79% GMV · OWN CHANNEL AOV **R$217.8** (2.5×) nhưng chỉ 34,042 đơn.
- **Hành động:** kéo giỏ giá trị cao về own channel (CHOCO/LISBON/WHATS PLACE, AOV R$225–231).
- **Giới hạn:** **không có dữ liệu hoa hồng** → "thiệt hại do phụ thuộc" chưa định lượng được; chỉ nói rủi ro.

---

## US-2 · Commercial / Ops planning — "Cầu bùng nổ khi nào?"

> **As a** ops planner, **I want** biết cầu theo giờ × ngày và chất lượng đơn ở từng khung, **so that** tôi xếp ca shipper & khuyến mãi đúng chỗ.

### Insight 6a — Cầu lưỡng đỉnh cực nhọn: 73.5% đơn nằm trong 7 giờ
- **Phát hiện:** đỉnh **12h (50,471 đơn)** và **19h (49,000)**; trưa 11–13h = 32.7% đơn, tối 18–21h = 40.8% → **73.5% cầu dồn vào 7/24 giờ**. Đáy 6h chỉ 151 đơn (**tỷ lệ đỉnh/đáy 334×**). Cuối tuần: T6 61,416 · T7 60,355 · CN 60,258 đơn > T2 44,031.
- **Hành động:** ca shipper theo daypart (2 ca nhọn), không phân bổ đều; khuyến mãi giờ thấp điểm 15–17h (chỉ 20,410–17,000 đơn/giờ).
- **Giới hạn:** giờ = UTC−3 **giả định**; nếu sai múi giờ mọi khung dịch chuyển.

### Insight 8 — Đơn ngoài giờ mở cửa: hủy 18.9% (gấp 4.3× ban ngày)
- **Phát hiện:** 0–9h giờ địa phương có **4,391 đơn, hủy 18.88%** (ban ngày 4.43%) — chiếm **4.9% toàn bộ số đơn hủy**. GOOD ban đêm hủy 20.5%, FOOD 12.9%. Cancel theo giờ đạt **31.4% lúc 4h sáng**.
- **Giả thuyết:** store đóng cửa nhưng listing vẫn nhận đơn (không có `cancel_reason` để xác nhận).
- **Hành động:** ép giờ mở cửa vào listing / auto-reject ngoài giờ — quick win, không cần đầu tư.

### Insight 2b — Cancel theo dải giá trị hình chữ U
- ≤R$30: 7.74% hủy · R$100–200: 3.46% (thấp nhất) · >R$500: 8.37%. Đơn rẻ (rủi ro rác) và đơn đắt (rủi ro tồn kho/thanh toán) đều nguy hiểm hơn khúc giữa.

---

## US-3 · Delivery Performance Manager — "Thời gian nằm ở đâu?"

> **As a** delivery performance manager, **I want** biết SLA thực và pha nào ăn thời gian, **so that** tôi đầu tư đúng khâu.

### Insight 4 — KPI cycle-time gộp FOOD+GOOD là sai thiết kế 🔁
- **Phát hiện:** FOOD (309,080 đơn): p50 **40.8′**, p90 **64.6′**, prep 15.6′, transit 16.0′, chỉ 0.5% vượt 180′.
  GOOD (35,108 đơn): p50 **81.4′**, p90 **947′ (~16 giờ)**, prep **1.2′**, transit 27.3′, **29.9% vượt 180′**.
  **87.3%** đơn có cycle >180′ là GOOD.
- **Ý nghĩa:** GOOD là bán lẻ **giao theo hẹn**, không phải đồ ăn nóng → gộp vào một KPI làm median nhích lên và P90 nổ. Mọi card SLA phải **tách segment** hoặc lọc FOOD.
- **Kèm theo — bất nhất trong bản giao hiện tại:** mockup card ghi **P90 = 67.5′** (lọc cycle ≤180′) còn measure DAX `P90 Cycle (min)` (lọc ≤1440′) trả **75.1′**. Cùng một nhãn, hai con số → đã chuẩn hoá ở bản dựng lại (cap 1440′, nêu rõ trong tooltip, và có card P90 riêng cho FOOD).

### Insight 6 — Cự ly không quyết định thời gian, nhưng *pha transit* thì có
- **Phát hiện (cùng một frame: cycle ≤150′, 0<dist ≤15km, n=316,560):** r(distance, cycle) = **0.23** (R² 5.3%) · r(prep, cycle) = **0.48** (R² 23%) · r(transit, cycle) = **0.66** (R² 43.6%) · r(amount, cycle) = 0.08.
- **Đọc đúng:** thêm **km** gần như không làm chậm đơn (từ <1km đến 5–10km median cycle chỉ 37.4′ → 52.8′), nhưng **thời gian nằm trong pha transit** giải thích ~44% biến thiên → nút thắt là **chờ gán/đón shipper & tốc độ di chuyển thực tế**, không phải chiều dài tuyến. Prep vẫn là khâu lớn thứ hai (23%).
- **Hành động:** đo & rút ngắn "ready → collected" (chờ shipper); SLA theo pha thay vì tổng; tối ưu tuyến là ưu tiên thấp.
- **Giới hạn:** `collected/walking` không có trong fact → phần dư median 6.8′ không bóc tách được. Tương quan ≠ nhân quả.

### Insight 11 — Cung shipper tập trung mỏng 🔁
- 4,583 shipper active · median **20 lượt/shipper** · p90 222 · **top 10% shipper = 55.6% lượt giao** · **23.6% shipper <5 lượt**. MOTOBOY 71.4% lượt (median 2.62km) · BIKER 26.3% (1.03km) · **69.8% FREELANCE**.
- Số cũ "top 10 = 7.3%" trong `page_data.json` là *top 10 shipper*, không phải *top 10%* — dễ gây hiểu sai là cung phân tán.
- **Hành động:** giữ chân nhóm nòng cốt (~458 shipper) — họ là điểm gãy vận hành; đo tỷ lệ rơi của freelancer.
- Delivery success 98.03% (lượt giao) / 95.4% (đơn) — hai mẫu số khác nhau, phải ghi rõ.

---

## US-4 · Hub Manager — "Hub nào cần can thiệp?"

> **As a** hub manager, **I want** benchmark hub cùng thành phố theo hủy & cycle, **so that** tôi audit đúng hub.

### Insight 10 — ELIXIR SHOPPING: hủy 30.8% và median cycle 26 giờ
- Áp min-volume ≥500 đơn (26/32 hub đạt, 6 hub loại): **ELIXIR SHOPPING (SP) 10,249 đơn — hủy 30.82%, median cycle 1,565′, median prep 944′**; kế tiếp STAR SHOPPING (RJ) 9.25%, REACT SHOPPING (SP) 8.12%, RUBY 7.76%, PURPLE 6.55%.
- **Giải thích (mới):** ELIXIR là hub **GOOD-heavy** — nên 26 giờ "cycle" là bán lẻ giao hẹn, còn 30.8% hủy khớp với bài toán GOOD×MARKETPLACE (Insight 2). Không phải "hub vận hành tệ toàn diện" như suy luận cũ.
- **Hành động:** audit ELIXIR theo góc **tồn kho/độ sẵn có GOOD**, không theo góc điều phối shipper.
- Nhóm cycle nhanh nhất/chậm nhất trong FOOD hub: SAMPA 46.8′, PURPLE 46.4′, WOLF 45.9′ vs median hệ thống 41.8′ → dư địa hẹp; ưu tiên thấp hơn.

---

## US-5 · Account / Partner Manager — "Đối tác nào ưu tiên?"

> **As an** account manager, **I want** xếp đối tác theo đóng góp × rủi ro, **so that** tôi biết chăm ai và siết ai.

### Insight 2 — Ma trận 4 ô (294 store ≥100 đơn hoàn tất; ngưỡng median GMV R$34,211 · median hủy 3.44%)
| Ô | Store | GMV | % GMV | Hủy TB |
|---|---|---|---|---|
| ⭐ Star (GMV cao · hủy thấp) | 94 | R$24.00M | **74.5%** | 1.63% |
| 🔧 Fix-first (GMV cao · hủy cao) | 53 | R$5.72M | **17.8%** | 9.77% |
| 🌱 Nurture (GMV thấp · hủy thấp) | 53 | R$0.98M | 3.0% | 1.95% |
| 👀 Review (GMV thấp · hủy cao) | 94 | R$1.52M | 4.7% | 11.44% |
- **Fix-first là danh sách công việc thật:** 53 đối tác giữ **17.8% GMV** với hủy ~9.8% — top: ZUPULAR MUC (GOOD, SP, 20.4%), UVURUSM (GOOD, 25.8%), SR SIGIRIMI (FOOD, 14.8%).
- Pareto vẫn đúng: **108/883 store (12.2%) = 80% GMV**, top 20% = 88.3%.

### Insight 7 — Gói thuê ngược chiều với giá trị (trục `store_plan_price` chưa từng phân tích)
| Gói | Store | Đơn/store | GMV | % GMV | AOV | Hủy | % đơn GOOD |
|---|---|---|---|---|---|---|---|
| **R$0** | 56 | **1,596** | R$8.81M | **34.1%** | R$98.6 | **2.33%** | 0.8% |
| R$49.9 | 145 | 660 | R$5.69M | 22.0% | R$59.4 | 4.00% | 1.2% |
| R$29.9 | 172 | 117 | R$4.02M | 15.6% | R$199.8 | **12.87%** | **99.0%** |
| R$29.0 | 234 | 70 | R$3.83M | 14.8% | R$232.2 | 5.57% | 85.8% |
| R$49.0 | 156 | 267 | R$3.01M | 11.7% | R$72.4 | 7.89% | 5.4% |
- **Phát hiện:** 56 store gói **R$0** tạo 1/3 doanh thu với hủy thấp nhất; các gói trả phí thấp lại là nhóm GOOD hủy cao. Gói **không** phân tầng theo giá trị mang lại.
- **Giả thuyết:** gói R$0 là hợp đồng enterprise thương lượng riêng (chuỗi lớn), gói R$29–29.9 là self-serve retail.
- **Hành động:** xem lại pricing/packaging (giá theo GMV/đơn thay vì phí phẳng); dùng bảng này làm đầu vào cho revenue-model.
- **Giới hạn:** không có ngày ký/điều khoản hợp đồng → không kiểm chứng được giả thuyết enterprise.

---

## US-6 · Root-cause hủy đơn (Ops + Commercial)

> **As an** ops/commercial lead, **I want** biết hủy đơn tập trung ở tổ hợp nào, **so that** tôi sửa đúng nguyên nhân thay vì siết toàn hệ thống.

### Insight 2 (chính) — Hủy là bài toán **GOOD × MARKETPLACE** 🔁
| Segment × Kênh | Đơn | Hủy |
|---|---|---|
| FOOD × MARKETPLACE | 311,965 | 3.34% |
| FOOD × OWN | 9,810 | 5.63% |
| **GOOD × MARKETPLACE** | **21,200** | **22.54%** |
| GOOD × OWN | 26,024 | **4.76%** |
- **Ý nghĩa:** báo cáo cũ kết luận "GOOD hủy 12.7% = 3.7× FOOD" → **đúng nhưng lệch trọng tâm**. Cùng hàng hoá GOOD, bán qua own channel chỉ hủy 4.76%; qua marketplace hủy **22.5%** (4.7×). Vấn đề nằm ở **luồng marketplace cho hàng bán lẻ** (đồng bộ tồn kho / độ sẵn có / thời gian phản hồi), không phải bản chất GOOD.
- **Counterfactual:** kéo GOOD về mức FOOD (3.41%) ⇒ ~**4,409 đơn** cứu được ⇒ ~**R$969k** GMV (giả định chuyển đổi tại AOV GOOD). Nếu chỉ nhắm ô GOOD×MARKETPLACE thì phạm vi hẹp hơn nhưng tỷ lệ thắng cao hơn.
- **Xu hướng:** hủy toàn hệ thống 4.35% → 5.03% (T1→T4) — tăng trưởng "bẩn" dần.
- **Giới hạn:** **không có `cancel_reason`** → nguyên nhân vẫn là giả thuyết; chỉ khẳng định được vị trí tập trung.
- Theo thứ: T5 5.13% · T3 4.90% · T6 4.92% cao hơn CN 3.75%.

### Insight 12 — "Tiền rủi ro" bị 1 bản ghi bóp méo 🔁 (lỗi đo lường)
- **Phát hiện:** tổng `order_amount` của đơn hủy = R$3.51M, nhưng **1 đơn duy nhất R$1,788,306** (store GRIME CRU, hub SAMPA SHOPPING) chiếm **51%**. 28 đơn hủy >R$1,500. Sau khi loại flag `order_amount > 1500`: **R$1.62M = 4.58% GMV** — con số dùng được.
- **Hành động:** mọi measure tiền-rủi ro phải kèm `flag_extreme_amount = FALSE`; đưa bản ghi này vào Anomaly register để business xác nhận (đơn test? nhập sai?).
- Vì vậy ranking "hub mất nhiều tiền do hủy" nếu không lọc sẽ đọc sai: SAMPA hiện lên #1 (53% tiền hủy) chỉ vì 1 đơn, dù cancel rate SAMPA chỉ 4.92%.

---

## US-7 · Finance / Pricing — "Chính sách free-ship đang lỗ bao nhiêu?"

> **As a** finance/pricing lead, **I want** biết giao hàng lỗ ở đâu theo giá trị đơn × cự ly, **so that** tôi đặt ngưỡng free-ship có cơ sở.

### Insight 3 — Free-ship là **toàn bộ** khoản lỗ; đơn có thu phí đang có lãi 🔁
- **Phát hiện (346,020 đơn hoàn tất có `order_delivery_cost`):** phí TB **R$6.27** < chi phí TB **R$7.58** ⇒ bù **R$1.31/đơn**, tổng **−R$454,555**/4 tháng.
  Bóc tách: **đơn free-ship (35.05%) lỗ R$920,272**; **đơn có thu phí lãi +R$465,717 (+R$2.07/đơn)**.
- **Theo cự ly:** <1km **+R$10.6k lãi** · 1–2km +R$2.6k lãi · 2–3km −R$110k · 3–5km **−R$164k** · 5–10km −R$99k · 10–50km −R$77k (chỉ 8,631 đơn, **−R$9/đơn**).
- **Theo giá trị đơn:** ≤R$30 −R$172k (56% free-ship) · R$30–60 **−R$275k** (42% free-ship) · R$60–100 −R$73k · **R$100–200 +R$98k lãi** · >R$500 −R$14k (63% free-ship!).
- **Theo segment:** GOOD free-ship **61.8%**, chi phí R$9.37 vs phí R$4.42 → lỗ R$197k trên chỉ 12% đơn; FOOD lỗ R$258k.
- **Khuyến nghị định lượng:** free-ship chỉ khi **giá trị đơn ≥ R$60** *và* **cự ly ≤ 2km**; đơn >R$500 và đơn 10–50km phải thu phí thực chi. Ước tính thu hồi phần lớn R$447k lỗ ở hai dải ≤R$60 (cần A/B vì có rủi ro giảm đơn).
- **Giới hạn:** `order_delivery_cost` là chi phí giao khai báo (không rõ phương pháp tính, thiếu 1.7% bản ghi); **không có elasticity** → tác động lên volume phải test, không suy ra từ dữ liệu.

---

## US-8 · Data/BI Analyst — "Tôi có tin được dashboard này?"

> **As a** BI analyst, **I want** biết mọi bẫy đo lường trước khi đưa lên C-level, **so that** không ai bị hỏi ngược mà không trả lời được.

| Vấn đề | Số | Xử lý trên dashboard |
|---|---|---|
| 1 đơn hủy R$1.79M | 51% "tiền rủi ro" | Measure at-risk loại `flag_extreme_amount` |
| `store_name` không phải khóa | 137 tên → tối đa 15 store_id | Thêm grain **Brand**; bảng store hiển thị cả `store_id` |
| Cycle FOOD vs GOOD khác quy trình | P90 64.6′ vs 947′ | Card SLA tách segment + slicer segment |
| Filter cycle không nhất quán | P90 67.5′ (cap 180′) vs 75.1′ (cap 1440′) | Chuẩn hoá cap 1440′ + ghi rõ nhãn |
| Tuần cuối 5 ngày | 26–30/04 | Đánh dấu "kỳ chưa đủ" trên line chart |
| Đơn không có bản ghi giao | 10,345 (2.8%); trong đó FINISHED 2,677 (0.76%) | Ghi chú mẫu số; success rate 98.03% (lượt) ≠ 95.4% (đơn) |
| Đơn không có bản ghi thanh toán | 18,665 (5.1%) | `any_chargeback` NULL ≠ FALSE — chargeback thật = 426 đơn (**0.12%**) |
| Đơn tách thanh toán | 48,818 | Không bao giờ SUM(payment_amount) làm doanh thu |
| Thiếu `order_delivery_cost` | 6,000 (1.7%) | Measure margin dùng AVERAGEX có lọc NOT ISBLANK |
| Cycle >1440′ | 7,469 | Loại khỏi measure SLA, giữ dòng trong Anomaly |
| Đơn amount = 0 (FINISHED) | 30 | Cờ `flag_zero_amount` |
| Min-volume ranking | hub ≥500 (6/32 hub bị loại) · store ≥100 | Measure guard, không lọc visual |

**Không trả lời được với dữ liệu này:** lý do hủy (không có `cancel_reason`) · giữ chân/LTV/tần suất mua (không có `customer_id`) · YoY & mùa vụ (chỉ 4 tháng) · hoa hồng marketplace → thiệt hại phụ thuộc kênh · elasticity của free-ship · giờ mở cửa store (để chứng minh giả thuyết đơn ban đêm).

---

## Ánh xạ User Story → trang Power BI (bản dựng lại, 8 trang)

| Trang | User story | Hero insight | Visual chính |
|---|---|---|---|
| **P1 Executive** | US-1 | 1 brand = 34.5% GMV | 6 card · GMV line (đánh dấu tuần cụt) · Top brand bar (Top-12 guard) · donut kênh · cột hủy theo tháng |
| **P2 Demand** | US-2 | 73.5% cầu trong 7 giờ | Cột đơn × giờ + line cancel rate theo giờ · cột theo thứ · matrix giờ×thứ · histogram dải giá trị · donut payment |
| **P3 Fulfilment SLA** | US-3 | P90 FOOD 64.6′ vs GOOD 947′ | Card SLA tách segment · cột prep/transit theo segment · scatter hub (distance × cycle) · cột theo dải cự ly · modal split |
| **P4 Hub Ops** | US-4 | ELIXIR 30.8% (≥500 đơn) | Bar hủy (min-vol guard) · scatter quadrant volume×hủy · bảng hub · GMV theo city |
| **P5 Partner & Brand** | US-5 | Fix-first 53 store = 17.8% GMV | Bar Top brand · scatter quadrant GMV×hủy (min 100) · bảng store (kèm store_id) · bảng gói thuê |
| **P6 Cancellation root-cause** | US-6 | GOOD×MARKETPLACE 22.5% | Matrix segment×kênh · cột cancel theo giờ · cột cancel theo dải giá trị · line cancel theo tháng · card counterfactual |
| **P7 Delivery economics** | US-7 | Free-ship lỗ R$920k / paid-ship lãi R$466k | Card fee/cost/subsidy · cột margin theo dải cự ly · cột margin theo dải giá trị · cột free-ship % theo segment · bảng ma trận đề xuất ngưỡng |
| **P8 Data trust & Actions** | US-8 | 1 bản ghi = 51% tiền rủi ro | Card at-risk (clean vs raw) · bảng anomaly · textbox 12 bẫy đo lường + 6 khuyến nghị ưu tiên |

Chi tiết measure/DAX mới xem `powerbi/README.md` mục *v2 — dựng lại theo user story*.

**Đã dựng xong (artifact):**
- `powerbi/` — PBIP v2: model mở rộng (grain brand, distance ở order-grain, 28 measure mới) + report 8 trang, 138 visual. Zip: `powerbi/BrazilianDeliveryCenter_PBIP.zip`.
- `dashboard/pbi_v2_preview.html` + `outputs/figures/v2_p1..p8.png` — preview render **trực tiếp từ PBIR definition** (cùng toạ độ/loại visual, số liệu thật) để xem không cần Power BI Desktop.
- `outputs/userstory_insights.json` — toàn bộ số liệu trong báo cáo này; script `scripts/12_userstory_insights.py`.
- Pipeline: `12_userstory_insights.py` → `13_extend_model.py` → `14_gen_visuals_v2.py` → `15_gen_preview_data.py` → `16_gen_pbi_preview.py`.

**Chưa làm (cần Power BI Desktop, không có trên Linux):** round-trip xác nhận TMDL/PBIR, bật *Sync slicers*, drill-through page, tooltip page, bookmark filter-panel.
