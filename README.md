# 🤖 Order Bot - Telegram Bot Đặt Hàng

Bot Telegram giúp tạo file Excel đặt hàng thực phẩm từ danh sách nhà cung cấp.

## 🚀 Cách chạy (3 bước)

### Bước 1: Upload file Excel lên cùng thư mục với bot.py
- `DAILY_ORDER_MIN_xlsx.xlsx` (file danh sách mặt hàng của bạn)

### Bước 2: Deploy lên Railway (miễn phí)

1. Tạo tài khoản tại https://railway.app (đăng nhập bằng GitHub)
2. Tạo GitHub repo mới, upload toàn bộ thư mục này lên
3. Vào Railway → New Project → Deploy from GitHub repo
4. Trong Settings → Variables, thêm:
   - `BOT_TOKEN` = token lấy từ [@BotFather](https://t.me/BotFather)
   - `ALLOWED_USER_IDS` = danh sách Telegram User ID được phép dùng bot (phân cách bằng dấu phẩy, VD: `123456789,987654321`)
   - `EXCEL_PATH` = tên file Excel (mặc định: `DAILY_ORDER_MIN_xlsx.xlsx`)
5. Deploy!

> 💡 Lấy Telegram User ID của bạn: nhắn tin cho [@userinfobot](https://t.me/userinfobot)

### Bước 3: Dùng thôi!

Mở Telegram, tìm bot của bạn và gõ `/start`

---

## 📱 Lệnh bot

| Lệnh | Mô tả |
|------|-------|
| `/start` | Bắt đầu |
| `/order` | Tạo đơn đặt hàng mới |
| `/list` | Xem danh sách mặt hàng |
| `/tim <từ khoá>` | Tìm kiếm mặt hàng |
| `/cancel` | Huỷ đơn đang làm |

---

## 🔄 Cách dùng /order

1. Gõ `/order`
2. Chọn nhóm hàng (THỊT / RAU CỦ QUẢ / ...)
3. Chọn mặt hàng muốn đặt
4. Nhập số lượng
5. Tiếp tục chọn mặt hàng khác
6. Bấm **"Xong – Tạo file đặt hàng"**
7. Bot gửi file Excel về!

---

## 🛠️ Chạy local (để test)

```bash
# Tạo file .env từ template
cp .env.example .env
# Điền BOT_TOKEN và các biến khác vào .env

pip install -r requirements.txt
python bot.py
```

## 📝 Cập nhật danh sách mặt hàng

Chỉ cần thay file `DAILY_ORDER_MIN_xlsx.xlsx` bằng file mới và restart bot.

---

## 🔒 Bảo mật

- **Không bao giờ** commit token vào git. Token chỉ được đặt qua biến môi trường.
- Dùng `ALLOWED_USER_IDS` để giới hạn ai được phép sử dụng bot.
