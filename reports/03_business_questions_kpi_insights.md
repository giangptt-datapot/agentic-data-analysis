# Business Questions · KPI Catalog · Insights (Concept C)

## A. Câu hỏi nghiệp vụ theo nhóm người dùng

**Ban điều hành (P1):** GMV/AOV đang tăng tốc hay chững? Doanh thu phụ thuộc vào đâu (kênh/segment/vùng) và rủi ro tập trung ra sao? Tỷ lệ hoàn tất đơn có xói mòn theo thời gian? Khu vực/đối tác nào cần chú ý trước?

**Operations Manager (P2, P3):** Cầu bùng nổ khung giờ/ngày nào để bố trí shipper? Cycle time trung vị & đuôi (p90/p95)? Nút thắt nằm ở khâu chuẩn bị hay di chuyển? Tỷ lệ giao thành công?

**Hub Manager (P4):** Hub nào khối lượng cao nhưng hiệu suất thấp (hủy cao/cycle chậm)? Benchmark hub cùng thành phố? Tải theo ngày để điều phối?

**Store/Partner Manager (P5):** Cửa hàng nào đóng góp/rủi ro? Đối tác nào cần ưu tiên cải thiện (GMV cao + hủy cao)? Chất lượng thương mại (AOV vs hủy) theo segment?

**Delivery Performance Manager (P3, P6):** Quãng đường có quyết định thời gian giao? Motoboy vs Biker phù hợp tải nào? Yếu tố nào làm tăng hủy? Chính sách free-ship tác động chi phí thế nào?

---

## B. KPI Catalog

| KPI | Ý nghĩa | Công thức (DAX rút gọn) | Nguồn | Điều kiện lọc | Kiểm chứng |
|---|---|---|---|---|---|
| **GMV** | Doanh thu hàng hoá hoàn tất | `SUM(fact_orders[order_amount])` | fact_orders | `order_status="FINISHED"` | Σ=R$35.29M; ≠ Σpayments (R$37.3M) |
| **Total / Finished Orders** | Quy mô đơn | `COUNTROWS` / `CALCULATE(COUNTROWS, FINISHED)` | fact_orders | — / FINISHED | 368,999 / 352,020 |
| **AOV** | Giá trị đơn TB | `[GMV]/[Finished Orders]` | fact_orders | FINISHED | R$100.26 (median R$71.9 → lệch phải) |
| **Cancellation Rate** | Tỷ lệ hủy | `DIVIDE(CALCULATE(COUNT,CANCELED),COUNT)` | fact_orders | all | 4.6% |
| **Fulfillment Rate** | Tỷ lệ hoàn tất | `1-[Cancel Rate]` | fact_orders | all | 95.4% |
| **Median Cycle Time** | Tốc độ end-to-end | `MEDIANX(orders, cycle_time)` | fact_orders | FINISHED, 0<ct≤1440 | 41.8′ (p90 67.5′) |
| **Median Delivery Distance** | Bán kính giao | `MEDIANX(deliveries, distance)` | fact_deliveries | DELIVERED, dist≤50km | 2.06 km |
| **Delivery Success Rate** | Độ tin cậy giao | `DIVIDE(DELIVERED, all deliveries)` | fact_deliveries | all | 98.03% |
| **Delivery Subsidy/Order** | Bù lỗ giao TB | `AVG(cost)-AVG(fee)` | fact_orders | cost NOT BLANK | R$1.36 |
| **Store GMV Concentration** | Mức tập trung | `top-N GMV / total GMV` | fact_orders+dim_store | FINISHED, store≥100 đơn | top 12% = 80% |
| **Chargeback Rate** | Rủi ro thanh toán | `DIVIDE(orders có chargeback, orders)` | payments rollup | all | 0.12% |

> **Quy tắc chống double-count:** payments & deliveries đã rollup về order-grain trong ETL; measure tiền luôn từ `order_amount`. Ranking hub/store áp ngưỡng min-volume (hub ≥500, store ≥100 đơn).

---

## C. Insights nổi bật (đầy đủ cấu trúc)

### Insight 1 — GOOD chạy giá trị, FOOD chạy volume
- **Phát hiện:** FOOD = 88.3% đơn nhưng AOV chỉ R$84; GOOD = 11.7% đơn, AOV R$219.8 (2.6×), đóng góp 25.7% GMV.
- **Số liệu:** FOOD 310,814 đơn / R$26.2M; GOOD 41,206 đơn / R$9.06M.
- **Ý nghĩa:** GOOD là đòn bẩy AOV; mở rộng GOOD tăng GMV nhanh hơn FOOD.
- **Giả thuyết:** GOOD (bán lẻ/hàng hoá) giỏ hàng lớn hơn đồ ăn.
- **Hành động:** cân nhắc đẩy danh mục GOOD ở hub có cầu; nhưng xem Insight 4 trước.
- **Giới hạn:** không có chi tiết sản phẩm để biết GOOD gồm gì; chỉ 4 tháng.

### Insight 2 — Doanh thu tập trung Pareto cực mạnh
- **Phát hiện:** 12% cửa hàng active (108/883) tạo 80% GMV; top 20% = 88.4%.
- **Số liệu:** đường Pareto (P5).
- **Ý nghĩa:** rủi ro phụ thuộc số ít đối tác; churn 1 store top ảnh hưởng lớn.
- **Giả thuyết:** hiệu ứng thương hiệu/địa điểm của một số chuỗi lớn.
- **Hành động:** account management riêng cho nhóm top; theo dõi hủy của họ (P5 matrix).
- **Giới hạn:** tên store bị ẩn danh & trùng lặp → không định danh chuỗi thật.

### Insight 3 — Phụ thuộc một kênh duy nhất
- **Phát hiện:** MARKETPLACE = 79% GMV; riêng "FOOD PLACE" = 79% đơn hoàn tất & 68% GMV (R$24.05M).
- **Ý nghĩa:** rủi ro tập trung kênh; quyền định giá/hoa hồng nghiêng về marketplace.
- **Giả thuyết:** "FOOD PLACE" là marketplace chủ lực (kiểu iFood). Kênh riêng AOV cao hơn (R$218 vs R$88) → giá trị nhưng volume nhỏ.
- **Hành động:** giữ volume marketplace nhưng "kéo" giỏ giá trị cao về kênh riêng.
- **Giới hạn:** **không có dữ liệu hoa hồng** → chưa định lượng thiệt hại phụ thuộc (chỉ là rủi ro tập trung, không phải chi phí đã chứng minh).

### Insight 4 — GOOD bị hủy gấp ~4× FOOD, và hủy đang tăng
- **Phát hiện:** cancel GOOD 12.74% vs FOOD 3.41%; theo tháng 4.35%→5.03% (T1→T4).
- **Ý nghĩa:** mở rộng GOOD (Insight 1) đi kèm rủi ro hủy — tăng trưởng "bẩn".
- **Giả thuyết (chưa chứng minh):** GOOD hết hàng/độ sẵn có kém, hoặc giao lâu hơn. **Tương quan ≠ nhân quả.**
- **Hành động:** điều tra nguyên nhân hủy GOOD trước khi scale; playbook tách theo segment.
- **Giới hạn:** dataset không có lý do hủy (cancel reason) → không thể quy nguyên nhân.

### Insight 5 — Giao hàng là "loss leader"
- **Phát hiện:** phí thu TB R$6.22 < chi phí giao R$7.58 (bù R$1.36/đơn); 53.4% đơn phí < chi phí; 35.6% đơn free-ship.
- **Ý nghĩa:** giao hàng lỗ có chủ đích để giữ đơn — đòn bẩy chi phí lớn.
- **Hành động:** what-if free-ship (P6); tối ưu ngưỡng free-ship theo AOV/khoảng cách.
- **Giới hạn:** "cost" là chi phí giao khai báo, không gồm chi phí nền tảng khác; không rõ phương pháp tính cost.

### Insight 6 — Cầu lưỡng đỉnh (trưa+tối) và dồn cuối tuần
- **Phát hiện:** đỉnh 12h (48,813 đơn) & 19–20h; Thứ 6–CN ~174k đơn > T2–T5. (giờ UTC−3)
- **Ý nghĩa:** nhu cầu shipper không đều → xếp ca theo daypart.
- **Giả thuyết:** hành vi ăn trưa/tối. Diễn giải giờ địa phương phụ thuộc **giả định múi giờ UTC−3**.
- **Hành động:** lịch shipper linh hoạt giờ cao điểm; khuyến mãi giờ thấp điểm.
- **Giới hạn:** timezone là giả định; nếu sai, khung giờ dịch chuyển.

### Insight 7 — Đội xe phân bổ khớp cự ly
- **Phát hiện:** MOTOBOY 73% lượt giao, median 2.62 km; BIKER 27%, median 1.03 km (ngắn 2.5×). 71% shipper FREELANCE.
- **Ý nghĩa:** biker cho đơn gần, motoboy cho đơn xa — phân bổ hợp lý.
- **Hành động:** đảm bảo đủ biker ở hub mật độ cao/cự ly ngắn để giảm chi phí.
- **Giới hạn:** median cycle theo modal gần như nhau (41.5 vs 40′) → modal không phải yếu tố tốc độ chính.

### Insight 8 — Thời gian giao KHÔNG do khoảng cách (nút thắt = chuẩn bị)
- **Phát hiện:** tương quan cự ly ↔ cycle time chỉ **r=0.25** (giải thích <8% biến thiên); production median 15′, transit 16.6′, nhưng cycle tổng 41.1′ → phần lớn là hàng chờ.
- **Ý nghĩa:** rút ngắn giao hàng nên tập trung khâu chuẩn bị/điều phối, không phải tối ưu quãng đường.
- **Giả thuyết:** hàng chờ shipper / thời gian bếp là nút thắt.
- **Hành động:** cải thiện dự báo & gán shipper sớm; SLA theo khâu.
- **Giới hạn:** thiếu một số mốc thời gian (collected/walking bị loại khỏi fact); cycle_time có outlier đã lọc.

### Insight 9 — Có hub "volume cao – chất lượng thấp"
- **Phát hiện:** ELIXIR SHOPPING (SP, ≥500 đơn) hủy 30.82% — gấp ~6.7× TB hệ thống (4.6%); STAR 9.25%, REACT 8.12%.
- **Ý nghĩa:** vấn đề vận hành khu trú theo hub, không phải toàn hệ thống.
- **Giả thuyết:** thiếu shipper/đối tác kém tại hub đó.
- **Hành động:** audit vận hành ELIXIR/STAR/REACT.
- **Giới hạn:** đã áp ngưỡng ≥500 đơn để loại nhiễu mẫu nhỏ; vẫn cần xác minh nguyên nhân.

### Insight 10 — Thanh toán tập trung ONLINE, rủi ro thấp
- **Phát hiện:** ONLINE 87.18% đơn; chargeback chỉ 0.12%.
- **Ý nghĩa:** rủi ro thanh toán thấp; ít đòn bẩy ở đây → **không nên** làm KPI trọng tâm.
- **Hành động:** giữ theo dõi nền; không đầu tư visual lớn.
- **Giới hạn:** không có phí xử lý theo phương thức để so sánh chi phí.

---

## Senior DA Review (giai đoạn insight)
- **Được dữ liệu chứng minh:** Insight 1,2,3,5,6,7,8,9,10 (đều tính trực tiếp). Insight 8 (r=0.25) là phát hiện mạnh & phản trực giác.
- **Chỉ là giả thuyết:** nguyên nhân hủy GOOD (I4), diễn giải giờ địa phương (I6), "thiệt hại phụ thuộc kênh" (I3).
- **Nguy cơ tính sai:** double-count nếu dùng payments; ranking mẫu nhỏ (đã chặn min-volume); % hủy dùng mẫu số = orders (không phải deliveries) — phải nhất quán.
- **Insight yếu/hiển nhiên đã loại:** "GMV tăng theo tháng", "SP nhiều đơn nhất" (không đứng một mình).
- **Visual đẹp nhưng cần biện minh:** Sankey & Calendar (custom) — chỉ giữ nếu flow/load không thể hiện tốt bằng stacked bar/matrix (xem report 04).
- **Cần kiểm chứng bước sau:** cross-check mọi KPI bằng DAX vs pandas; kiểm filter-context khi slicer segment/city; xác nhận ngưỡng min-volume hợp lý.
