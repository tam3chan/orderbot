# Order Bot - Telegram Bot Dat Hang

Telegram bot giup tao file Excel dat hang thuc pham tu danh sach nha cung cap.

## Project Structure

```
order_bot/
├── bot.py              # Main bot (ConversationHandler, 12 states)
├── db.py               # MongoDB data access layer
├── r2.py               # Cloudflare R2 storage client
├── requirements.txt     # Python dependencies
├── Dockerfile          # Container configuration
├── .env.example        # Environment template
├── docs/               # Documentation
└── tests/              # Test directory
```

## Tech Stack

- **Language**: Python 3.11
- **Bot Framework**: python-telegram-bot >=21.0
- **Database**: MongoDB Atlas (orders, templates collections)
- **Storage**: Cloudflare R2 (Excel template storage)
- **Excel Processing**: openpyxl 3.1.2
- **Deployment**: Railway, Docker

## Quick Start

### 1. Prepare Excel File

Upload file `DAILY_ORDER_MIN_xlsx.xlsx` cung thu muc voi bot.py. File can co sheet "Food T01" voi cac cot:
- Code (A), Name (E), Category (B), Unit (U), NCC (J)

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your values:
BOT_TOKEN=<from @BotFather>
ALLOWED_USER_IDS=<Telegram user IDs, comma-separated>
MONGODB_URI=<MongoDB Atlas connection string>
R2_ENDPOINT=<Cloudflare R2 endpoint>
R2_ACCESS_KEY=<R2 access key>
R2_SECRET_KEY=<R2 secret key>
```

### 3. Run Local

```bash
pip install -r requirements.txt
python bot.py
```

### 4. Deploy to Railway

1. Create GitHub repo, push code
2. Connect repo to Railway
3. Add environment variables in Railway dashboard
4. Deploy

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Khoi dong bot, hien thi trang thai ket noi |
| `/order` | Tao don dat hang moi |
| `/list` | Xem danh sach mat hang |
| `/tim <tu khoa>` | Tim kiem mat hang |
| `/cancel` | Huy don dang lam |

## Order Flow

1. Goi `/order`
2. Chon nhom hang (THIT / RAU CỦ QUẢ / ...)
3. Chon mat hang
4. Nhap so luong
5. Tiep tuc hoac bam "Xong - Xac nhan"
6. Chon ngay dat hang
7. Nhan file Excel

## Key Features

- **Multi-step Conversation**: 12-state ConversationHandler for complex ordering flow
- **Recent Orders**: Tai don gan nhat tu MongoDB
- **Saved Templates**: Luu va tai mau don thuong dung
- **History Search**: Tim kiem don theo ngay
- **R2 Integration**: Tai Excel template vao RAM luc khoi dong
- **User Whitelist**: Gioi han truy cap qua ALLOWED_USER_IDS

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `BOT_TOKEN` | Yes | Telegram bot token from @BotFather |
| `ALLOWED_USER_IDS` | No | Comma-separated Telegram user IDs |
| `MONGODB_URI` | Yes | MongoDB Atlas connection string |
| `R2_ENDPOINT` | No | Cloudflare R2 endpoint URL |
| `R2_ACCESS_KEY` | No | R2 access key |
| `R2_SECRET_KEY` | No | R2 secret key |
| `R2_BUCKET` | No | R2 bucket name (default: orderbot) |
| `R2_OBJECT_KEY` | No | Excel file key in R2 |
| `EXCEL_PATH` | No | Local Excel path (default: DAILY_ORDER_MIN_xlsx.xlsx) |

## Security

- **Never commit tokens**: All tokens via environment variables
- **User whitelist**: ALLOWED_USER_IDS restricts bot access
- **No sensitive logging**: Credentials not logged

## License

MIT
