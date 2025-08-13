# Telegram Serial Check Bot — V4 (Render + Google Sheets)

Bot kiểm tra mã series lấy dữ liệu trực tiếp từ **Google Sheets** (mọi ô), chạy 24/7 trên **Render** bằng **webhook**.

## Tính năng
- `/start` → “Xin hãy nhập mã sản phẩm.”
- Nhập 1–nhiều mã → trả về:
  - ✅ Chính hãng nếu mã xuất hiện trong **bất kỳ ô** của Google Sheet
  - ❌ Không chính hãng hoặc không phân phối tại đại lý Việt Nam nếu không thấy
  - Ngày kiểm tra gần nhất + Số lần kiểm tra (lưu SQLite — không bền trên free tier)
- `/stats` xem số lượng mã đang index; `/reload` tải lại cache ngay.

---

## A. Chuẩn bị Google Sheets & Service Account (một lần)
1. Tạo **Google Sheet** (ví dụ: `serial_codes`), điền mã ở **bất kỳ ô nào**.
2. Tạo **Google Cloud Project** → bật **Google Sheets API**.
3. Tạo **Service Account** → tạo **JSON key** (tải file JSON).
4. Mở Google Sheet → **Share** cho email của Service Account (quyền Viewer).
5. Lấy **SHEET ID** từ URL: giữa `/d/` và `/edit`.

> Sau này, chỉ cần sửa nội dung Google Sheet là bot tự cập nhật (có cache TTL).

---

## B. Đưa mã lên GitHub
1. Tạo repo mới trên GitHub (Private cũng được).
2. Upload toàn bộ mã nguồn này lên repo (hoặc `render.yaml` nếu muốn auto-setup).

Cấu trúc chính:
```
bot_webhook.py        # entrypoint cho Render (webhook)
bot_polling.py        # chạy local test (polling)
bot_common_gsheets.py # handler logic
codes_gsheets.py      # đọc sheet, cache, index
db.py                 # đếm số lần kiểm tra + ngày gần nhất (SQLite)
requirements.txt
render.yaml           # blueprint cho Render (tuỳ chọn)
.env.example          # mẫu biến môi trường
```

---

## C. Tạo dịch vụ trên Render (Free)
**Cách 1 (tay):**
1. Vào Render → **New → Web Service** → chọn repo GitHub của bạn.
2. Thiết lập:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot_webhook.py`
3. Thêm **Environment Variables**:
   - `BOT_TOKEN` = token từ BotFather
   - `TELEGRAM_WEBHOOK_SECRET` = chuỗi ngẫu nhiên
   - `GOOGLE_SERVICE_JSON` = **copy toàn bộ nội dung JSON key** (giữ nguyên dấu `{}`)
   - `GOOGLE_SHEET_ID` = id của sheet
   - (tuỳ chọn) `GOOGLE_SHEET_NAME` = tên sheet (để trống = sheet đầu)
   - `CACHE_TTL_SECONDS` = 300 (mặc định)
   - `TZ` = `Asia/Ho_Chi_Minh`
4. Deploy. Render sẽ cung cấp `RENDER_EXTERNAL_URL` và `PORT` → bot tự set webhook.

**Cách 2 (render.yaml):**
- Trong Render → **New → Blueprint** → chọn repo có `render.yaml`.
- Điền các env tương tự trên (các key `sync:false` bạn điền thủ công).

---

## D. Test nhanh local (không cần Render)
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Mở .env, điền BOT_TOKEN, GOOGLE_SERVICE_JSON, GOOGLE_SHEET_ID
python bot_polling.py
```

---

## E. Lưu ý quan trọng
- **Render Free**: Web service có thể **ngủ** sau thời gian rảnh → lần gọi đầu có thể chậm (cold start).
- **SQLite trên Free**: dữ liệu đếm số lần kiểm tra **không bền** qua redeploy/restart. Nếu cần bền vững:
  - Dùng **Postgres** (Render cung cấp gói free giới hạn) và đổi `db.py` sang Postgres, hoặc
  - Sử dụng nhà cung cấp DB khác (Neon/ElephantSQL).
- **Bảo mật**: Không commit JSON key lên GitHub. Luôn đặt trong **Environment Variables** trên Render.

---

## F. Biến môi trường phổ biến
```
BOT_TOKEN=...                           # Telegram bot token
ADMIN_IDS=123456789,987654321           # ai được /reload (để trống = ai cũng được)
TZ=Asia/Ho_Chi_Minh

GOOGLE_SERVICE_JSON={...}               # nội dung JSON key
GOOGLE_SHEET_ID=...                     # id của sheet
GOOGLE_SHEET_NAME=                      # để trống lấy sheet đầu
CACHE_TTL_SECONDS=300                   # cache 5 phút

# Webhook
TELEGRAM_WEBHOOK_SECRET=...             # bất kỳ chuỗi ngẫu nhiên
BASE_URL=https://your-app.onrender.com  # Render sẽ tự set RENDER_EXTERNAL_URL, có thể bỏ
PORT=10000                              # Render set tự động
```
