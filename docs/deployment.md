# Deployment Guide

## Prerequisites

- Python 3.11+
- Telegram Bot Token
- RPC URLs for supported networks

## Environment Variables

Create `.env` file:

```env
# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_MINI_APP_URL=https://your-app.com
TELEGRAM_ADMIN_IDS=123456,789012

# Database
DATABASE__PATH=data/platform.db

# RPC URLs
RPC_URL_ETH=https://mainnet.infura.io/v3/YOUR_KEY
RPC_URL_ARBITRUM=https://arb1.arbitrum.io/rpc
RPC_URL_OPTIMISM=https://mainnet.optimism.io/rpc

# Payment Settings
PAYMENT__INVOICE_EXPIRY_MINUTES=30
PAYMENT__CONFIRMATIONS_REQUIRED=12

# Trading Settings
TRADING__MAX_POSITION_SIZE_PERCENT=10.0
TRADING__MAX_SLIPPAGE_PERCENT=2.0
TRADING__MAX_TRADES_PER_HOUR=10
TRADING__DAILY_LOSS_LIMIT_PERCENT=5.0
TRADING__ACTION_COOLDOWN_SECONDS=5
```

## Running in Production

### 1. Install Production Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run API Server

```bash
uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 3. Run Telegram Bot

```bash
python -m app.bot.app
```

Or use a process manager like supervisor or systemd.

## Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Security Checklist

- [ ] Use strong bot token
- [ ] Configure admin IDs
- [ ] Enable HTTPS
- [ ] Set up rate limiting
- [ ] Configure firewall
- [ ] Use secrets management
- [ ] Enable logging
- [ ] Set up monitoring
