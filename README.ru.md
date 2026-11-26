# B2W Crypto

> **Языки:** [English](README.md) · [Русский](README.ru.md)

Telegram-бот и Mini App для отслеживания криптовалютного портфеля, ценовых алертов,
подписок, торговли на perpetual DEX и учёта airdrop-кампаний.

**Сайт:** https://ssrjkk.github.io/b2w-crypto-tg-bot/

## Возможности

- Команды Telegram и веб-интерфейс Mini App.
- Мониторинг цен и уведомления через WebSocket.
- JWT-авторизация и подключение кошелька MetaMask.
- Подписки с Invoice и проверкой оплаты в сети.
- Адаптеры perpetual DEX, лимиты позиций, slippage и kill switch.
- Отслеживание airdrop и журнал действий.

## Стек

Python, FastAPI, SQLAlchemy, Redis, Celery, aiogram, JavaScript и Web3 SDK.

## Быстрый старт

```bash
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head

uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload
celery -A app.celery_config worker --loglevel=info
celery -A app.celery_config beat --loglevel=info
```

Заполните `.env` значениями Telegram, базы данных, Redis, RPC и Celery. Пример
переменных и production-порядок запуска описаны в [docs/deployment.md](docs/deployment.md).
Секреты не коммитьятся.

## Проверки

```bash
pytest tests/ -v --cov=app
ruff check app/
mypy app/
```

## Документация

- [API](docs/api_reference.md)
- [Деплой](docs/deployment.md)
- [Showcase](https://ssrjkk.github.io/b2w-crypto-tg-bot/showcase/)
- [Безопасность](SECURITY.md)

## Лицензия

MIT — см. [LICENSE](LICENSE).
