# Telegram Crypto Access & Trading Platform

Telegram bot for crypto portfolio tracking and alerts. Monitors prices, sends notifications, and provides market analysis.

Telegram crypto portfolio and trading bot with subscriptions, perpetual DEX trading, airdrop tracking and risk controls.

**Site:** https://ssrjkk.github.io/b2w-crypto-tg-bot/

## Screenshots

Captured from the published site in a real browser (Chrome, 1440×900 and 390×844).

| Home | Sections |
| --- | --- |
| <img src="docs/screenshots/home.jpg" width="420" alt="B2W Crypto — landing page"> | <img src="docs/screenshots/content.jpg" width="420" alt="B2W Crypto — site sections"> |

<p align="center"><img src="docs/screenshots/mobile.jpg" width="320" alt="B2W Crypto — mobile view"></p>

## Features

- **Telegram Integration**: Bot commands and Mini App interface
- **Telegram Mini App**: Full web interface for trading
- **WebSocket**: Real-time trade/payment notifications
- **JWT Authentication**: Secure API access
- **Wallet Connect**: MetaMask integration
- **Crypto Subscriptions**: Invoice-based payments with on-chain verification
- **Perp DEX Trading**: Adapter-based architecture supporting multiple DEXs
- **Risk Management**: Position limits, slippage controls, kill switch
- **Airdrop Helper**: Eligibility tracking and progress monitoring
- **Activity Dashboard**: Full audit trail of all actions

## Architecture

```
app/
├── bot/               # Telegram bot handlers + Mini App
├── api/               # FastAPI endpoints + middleware + health + WebSocket
├── auth/              # JWT authentication
├── core/              # Enums, exceptions, security
├── services/          # Business logic + Wallet Connect
├── adapters/          # DEX integrations
├── trading/           # Trading orchestrator + price feeds
├── airdrop/           # Airdrop engine
├── payments/          # Invoice & verification
├── dashboard/         # Event logging
├── models/            # SQLAlchemy models
├── config/            # Configuration
├── database/          # SQLAlchemy async manager
├── cache/             # Redis cache manager
├── tasks/             # Celery background tasks
└── celery_config/     # Celery configuration
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file:

```env
# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_MINI_APP_URL=https://your-app.com

# Database
DATABASE__PATH=postgresql://user:pass@localhost/platform
REDIS_URL=redis://localhost:6379/0

# RPC URLs
RPC_URL_ETH=https://your-eth-rpc
RPC_URL_ARBITRUM=https://your-arbitrum-rpc
RPC_URL_OPTIMISM=https://your-optimism-rpc

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Monitoring
SENTRY_DSN=https://xxx@sentry.io/xxx
```

### 3. Run Database Migrations

```bash
# tables are also auto-created at startup via create_all, so this step is
# optional for the sqlite dev flow; for postgres start here:
alembic revision --autogenerate -m "initial"
alembic upgrade head
```

### 4. Run the Application

```bash
# API Server
uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload

# Celery Worker
celery -A app.celery_config worker --loglevel=info

# Celery Beat (scheduler)
celery -A app.celery_config beat --loglevel=info
```

### 5. Run Tests

```bash
pytest tests/ -v --cov=app
```

## API Endpoints

### WebSocket
- `WS /ws` - Real-time updates (auth, subscribe, trade updates)

### Health & Monitoring
- `GET /health` - Basic health check
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe
- `GET /health/metrics` - Prometheus metrics

### Subscription
- `POST /api/subscription/create`
- `GET /api/subscription/status/{user_id}`
- `POST /api/subscription/activate`
- `GET /api/subscription/check-access/{user_id}`

### Payment
- `POST /api/payment/invoice`
- `POST /api/payment/verify`
- `POST /api/payment/confirm/{payment_id}`
- `GET /api/payment/status/{user_id}`

### Trading
- `POST /api/trading/quote`
- `POST /api/trading/execute`
- `GET /api/trading/history/{user_id}`

### Airdrop
- `POST /api/airdrop/check-eligibility`
- `GET /api/airdrop/campaigns/{user_id}`
- `GET /api/airdrop/tasks/{campaign_id}`

### Dashboard
- `POST /api/dashboard/event`
- `GET /api/dashboard/events/{user_id}`
- `GET /api/dashboard/summary/{user_id}`

## Background Tasks (Celery)

| Task | Schedule | Description |
|------|----------|-------------|
| `check_expired_payments` | Every 5 min | Expire pending payments |
| `update_airdrop_progress` | Every 6 hours | Update airdrop progress |
| `check_daily_loss_limits` | Hourly | Check risk limits |
| `cleanup_old_events` | Daily 2 AM | Clean old dashboard events |

## Production Deployment

### Docker Compose

Полный рабочий файл — `docker-compose.yml` в корне репозитория: api, celery-worker, celery-beat, nginx, postgres:15-alpine, redis. Переменные окружения задаются через `.env` (`DATABASE__PATH`, `REDIS_URL`, `TELEGRAM_BOT_TOKEN`, `RPC_URL_*`, `SENTRY_DSN`; значения по умолчанию — внутри compose).

### Security Checklist

- [x] Rate limiting (slowapi)
- [x] Structured logging (structlog)
- [x] Error tracking (Sentry)
- [x] Health checks
- [x] Metrics endpoint
- [ ] SSL/TLS termination
- [ ] API authentication
- [ ] Rate limiting per-user

## Assumptions & Limitations

1. All user actions are explicitly user-initiated via commands
2. No automated trading or bot-like behavior
3. Payments verified on-chain with required confirmations
4. All actions logged with full audit trail
5. PostgreSQL for production, SQLite for development
6. Demo DEX adapters (not connected to real DEXs)
7. No real wallet integration - uses mock addresses

## Development

### Code Quality

```bash
# Lint
ruff check app/

# Format
black app/

# Type check
mypy app/
```

### Pre-commit

```bash
pre-commit install
```

Автор
ssrjkk — QA Engineer 

Telegram: @ssrjkk
Email: ray013lefe@gmail.com
GitHub: https://github.com/ssrjkk

---

**SSRJKK** — [GitHub](https://github.com/ssrjkk) · [Telegram](https://t.me/ssrjkk) · [Projects hub](https://ssrjkk.github.io/) · [Bot catalogue](https://t.me/ssrjkk_bot)

## Documentation

- [API](docs/api_reference.md)
- [Deploy](docs/deployment.md)
- [Showcase](https://ssrjkk.github.io/b2w-crypto-tg-bot/showcase/)
