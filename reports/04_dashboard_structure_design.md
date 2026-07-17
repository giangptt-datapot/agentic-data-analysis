# Dashboard Structure · Design System · Custom Visual Policy (Concept C)

## A. Cấu trúc 6 trang & visual (mỗi visual = 1 câu hỏi)

| Page | Persona | Hero-insight | Visuals |
|---|---|---|---|
| **P1 Executive Overview** | Ban điều hành | 68% GMV từ 1 kênh | 6 KPI card · GMV line+area (peak marker) · Insight callout+drill · Orders&Cancel small-multiples · City risk bubble map · Segment-mix ribbon |
| **P2 Order & Revenue** | Ops/Commercial | Cầu lưỡng đỉnh 12h/19h | Orders line · Top-channels lollipop · Payment donut · Order-value histogram · Peak-hour heatmap (dow×hour) |
| **P3 Delivery Performance** | Delivery Perf. Mgr | Cự ly KHÔNG quyết định thời gian (r=0.25) | 4 KPI · Distance×Time scatter · Cycle boxplot theo modal · Funnel stage bar · Modal split + case drill-through |
| **P4 Hub & Geographic** | Hub Manager | ELIXIR hub hủy 30.8% | Hub bubble map · Hub cancel ranked bar (min-vol) · GMV-by-city bar · GMV waterfall · Daily-load calendar |
| **P5 Store & Partner** | Store/Partner Mgr | Top 12% store = 80% GMV | Pareto · Partner priority matrix 2×2 · Top-store table · AOV×Cancel bubble · Channel→Segment Sankey |
| **P6 Insight Lab** | Deep-dive/all | Bù lỗ giao R$1.36/đơn | Decomposition tree · Key influencers · Free-ship what-if slider · Anomaly register table+drill · Validated bullets |

**Điều hướng & UX (đã dựng trong mockup):** menu cố định trái · Home/Back/Reset/Filters · dynamic title+subtitle theo trang · filter drawer (bookmark open/close) · selected-filter summary chips · tooltip hover trên mọi mark · drill-through modal · what-if slider.

---

## B. Design system — "Neo-Logistics Dark"

- **Chủ đề:** đêm đô thị Brazil / logistics command-center (nền tối, điểm nhấn phát sáng).
- **Màu (đã kiểm CVD):** nền `#0a0d14`/panel `#141a28`; mực `#f3f6ff`/`#aab4ca`/`#6e7892`. Categorical: blue `#3d8bff` · teal `#22b8a6` · violet `#8878ff` · amber `#f2a71b`. **Semantic (tách khỏi accent):** good `#38c172` / warning `#f2a71b` / risk/critical `#df4f67`.
- **Quy tắc màu:** màu theo *thực thể* không theo thứ hạng; semantic chỉ cho trạng thái (hủy/SLA), không tái dùng làm "series"; marketplace=blue, own=violet nhất quán mọi trang.
- **Typography:** Segoe UI (PBI-native) / Inter; số dùng `tabular-nums`.
- **Grid:** canvas 16:9; hàng KPI 6 cột; lưới card 2/3/4 cột; khoảng trắng 10–14px; bo góc 12px.
- **Định dạng số:** tiền R$ (M/k rút gọn ở visual, đầy đủ ở tooltip); thời gian phút `′`; % 1–2 chữ số thập phân.
- **Trạng thái tốt/TB/rủi ro:** chip màu + nhãn chữ (không chỉ dựa màu) — vd hub hủy ≥8% đỏ, 4.6–8% amber, <4.6% teal.

---

## C. Chính sách Custom Visual (AppSource)

Chỉ 2 custom visual, đều có biện minh & fallback:

| Custom visual | Trả lời câu hỏi gì | Vì sao visual mặc định chưa đủ | Hiệu năng/chia sẻ | Fallback mặc định |
|---|---|---|---|---|
| **Sankey** (P5) | Dòng đơn từ loại kênh → segment cửa hàng | Stacked bar khó thể hiện "luồng" 2 tầng trực quan | Nhẹ (4 node); certified visual → chia sẻ OK | 100% stacked bar (channel_type × segment) |
| **Calendar Heatmap** (P4) | Ngày nào hệ thống chịu tải cao | Matrix thường khó đọc theo lịch/tuần | Nhẹ; nếu tổ chức chặn custom visual → rủi ro | Matrix tuần (hàng) × thứ (cột) với color scale |

**KHÔNG dùng custom visual** cho: decomposition tree & key influencers (đã là native PBI), map (Azure Maps/ArcGIS native), boxplot (native mới hỗ trợ, hoặc dùng Deneb/Vega nếu cần). Không thêm visual chỉ để "nhiều màu".

**Deneb/Vega-Lite (tuỳ chọn):** chỉ nếu cần boxplot/scatter tuỳ biến vượt native — cân nhắc chi phí bảo trì.

---

## D. Kế hoạch bàn giao Power BI (sau khi duyệt) — PBIP/TMDL + mockup HTML
1. **Data model:** star schema (report 02) dạng TMDL (`model.tmdl`, các `tables/*.tmdl`).
2. **Power Query (M):** import 7 CSV (đúng encoding), parse timestamp, tạo cột phái sinh (dow/hour/is_weekend), cột cờ outlier, rollup deliveries/payments (hoặc để measure xử lý), `dim_date` calendar.
3. **DAX:** toàn bộ measure trong bảng KPI (mục B report 03) + measure phụ trợ (min-volume filter, % share, cancel by segment).
4. **Pages:** dựng 6 trang theo mockup; cấu hình bookmark (filter open/close, reset), drill-through page (case detail + anomaly), tooltip pages, dynamic title (measure), navigation buttons.
5. **Validate:** đối chiếu mọi KPI DAX vs pandas; kiểm filter-context; kiểm double-count; kiểm % mẫu số.
6. **Export:** ảnh showcase từng trang (từ mockup HTML, vì môi trường không có PBI Desktop để render .pbix).

## Senior DA Review (giai đoạn cấu trúc/design)
- **Giữ:** 6 trang, mỗi trang 1 persona + hero-insight; scatter/boxplot/pareto/matrix (tạo giá trị phân tích thật).
- **Cân nhắc bỏ nếu loãng:** GMV waterfall (gần trùng bar city) — giữ vì minh hoạ "build-up" tốt cho social; calendar (đẹp nhưng thông tin ~ trùng heatmap) → có thể gộp.
- **Rủi ro hình thức > giá trị:** Sankey chỉ 2×2 node → có thể chỉ là stacked bar; đánh dấu "optional".
- **Nhất quán:** marketplace=blue/own=violet, semantic riêng — đã áp toàn bộ.
- **Bước sau kiểm chứng:** min-volume threshold có làm lệch kết luận hub/store không; boxplot native PBI có sẵn không (nếu không → Deneb).
