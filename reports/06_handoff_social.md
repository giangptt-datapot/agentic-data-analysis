# Handoff & Social-post Assets — Brazilian Delivery Center

## Ảnh showcase (light theme, bản chính)
- Contact sheet 7 trang: `outputs/figures/showcase_contact_sheet.png`
- Từng trang: `outputs/figures/show_p1..p7.png` (light) · `pbi_p1..p7.png` (dark, bản social)
- Mockup tương tác: `dashboard/mockup_light.html` (chính) · `dashboard/mockup.html` (dark)

## 5–7 điểm nổi bật (caption đăng bài)
1. **GMV R$35.3M / 369k đơn / 4 tháng**, 4 đô thị Brazil — hủy đơn 4.6%, giao median 42′.
2. **68% GMV đến từ 1 kênh** (FOOD PLACE) → rủi ro phụ thuộc; kênh riêng AOV cao gấp 2.5× (R$218 vs R$88).
3. **Pareto khắc nghiệt:** 12% cửa hàng tạo 80% doanh thu.
4. **GOOD hủy 12.7% vs FOOD 3.4%** → ~R$1.32M GMV bị hủy; kéo về mức FOOD cứu ~R$0.97M.
5. **Giao hàng lỗ có chủ đích:** bù R$1.36/đơn (~R$480k/4 tháng), 35.6% đơn free-ship.
6. **Phản trực giác:** thời gian giao KHÔNG do quãng đường (r=0.25) — nút thắt là khâu chuẩn bị.
7. **Hub ELIXIR hủy 30.8%** (gấp 6.7× TB) — vấn đề khu trú, không phải toàn hệ thống.

## Agent đã TỰ ĐỀ XUẤT những gì
- Star schema 3-fact + quy tắc **doanh thu = order_amount** (không dùng payments) sau khi phát hiện bẫy double-count.
- Giả định **timezone UTC-3** (làm đỉnh giờ trở nên hợp lý: trưa 12h/tối 19h) — nêu rõ là giả định.
- Ngưỡng **min-volume** khi ranking hub/store (tự phát hiện "HUBLESS 60% hủy" là nhiễu 2 đơn).
- Concept "Marketplace 360" 6 trang → **+ trang 7 Khuyến nghị** (theo yêu cầu) với phân loại proven/giả thuyết.
- 10 insight → 5 khuyến nghị có ước tính tác động (R$); phát hiện r=0.25 (cự ly↔thời gian).
- Tự tinh chỉnh visual: bỏ Sankey (2×2 yếu) → stacked bar; waterfall trùng → hub quadrant.

## Agent làm TỐT phần nào
- Audit dữ liệu đầy đủ (grain, FK, missing, outlier) — **gắn cờ, không xóa** bất thường.
- ETL/anti-fan-out chuẩn; **17/17 KPI validate khớp** (pandas ⇄ DAX logic).
- Mockup 7 trang 2 theme, tương tác thật (nav/filter/tooltip/drill/what-if), palette CVD-safe.
- TMDL + M + DAX + theme viết theo spec; tài liệu 6 report + README bàn giao.

## Phần CẦN CON NGƯỜI kiểm tra / hoàn thiện
- **Mở PBIP bằng Power BI Desktop** để round-trip xác nhận TMDL/M/PBIR (không kiểm được trên Linux).
- **Dựng visual 7 trang** theo mockup + cấu hình bookmark/drill-through/tooltip page/nav trong Desktop.
- **Xác nhận timezone** thực của dataset (đang giả định UTC-3).
- **Nguyên nhân hủy GOOD** & **thiệt hại phụ thuộc kênh** — cần dữ liệu ngoài (cancel reason, hoa hồng).
- Ước tính tác động (R$0.97M cứu được) là **có điều kiện** — cần kiểm chứng nghiệp vụ trước khi cam kết.

## Giới hạn dataset (không thể khắc phục bằng phân tích)
Không có `customer_id` (❌ retention/LTV/RFM) · không chi tiết sản phẩm/giỏ hàng · chỉ 4 tháng/2021 (❌ YoY/mùa vụ) · `delivered` thiếu 94.7% (dùng `finished`) · không có route/GPS thực.
