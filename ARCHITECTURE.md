# Architecture

Карта системы и причины ключевых решений. Код: `app/`, данные: PostgreSQL или
sqlite (дев), кэш и брокер: Redis.

## Слои и потоки

```
Telegram ──► bot/ (handlers, FSM, keyboards)
                │ mini_app/index.html (SPA без сборки)
                ▼
Telegram Mini App ──HTTPS──► nginx (same-origin) ──► api/ (FastAPI)
                                                       │
                        ┌──────────────────────────────┼───────────────────┐
                        ▼                              ▼                   ▼
              routes/ (5 доменных роутеров)      websocket /ws        auth/ (JWT)
                        │                              │
        services/ ──► models/ (SQLAlchemy) ──► database/ (postgres|sqlite)
                        │                              │
              adapters/ (DEX) ── trading/ ── payments/ (on-chain verify)
                        │
              dashboard/ (event-лог) ──► cache/ + tasks/ + celery_config/
```

## Ключевые решения и их причины

1. **Same-origin за nginx** (`deploy/nginx.conf`): Mini App, API и `/ws` живут на
   одном https-хосте. Следствие: Mini App берёт `location.origin + '/api'` —
   CORS сводится к минимуму, wss/https переключаются автоматически.
2. **Вложенные префиксы API** (`/api/<домен>/*`): роутеры несут внутренние
   префиксы (`subscription`, `payment`, …) и монтируются под общим `/api`.
   Mini App и README завязаны на эти пути — контракт: 21 путь в openapi.
3. **create_all на старте + alembic для postgres**: дев-флоу (sqlite) стартует
   без миграций; prod-путь через `alembic revision --autogenerate` и
   `upgrade head`. `env.py` берёт URL из `settings.database.path`.
4. **Адаптеры DEX** (`adapters/`): каждая биржа — свой адаптер за единым
   интерфейсом orchestrator'а; риск-лимиты (позиция, slippage, kill switch)
   проверяются до исполнения, а не в адаптерах.
5. **Payments через on-chain verify**: invoice → подтверждение по RPC
   (`RPC_URL_*`) → доступ. Никаких ручных «зачислений».
6. **dashboard/event-лог**: каждое действие пользователя пишется — audit-trail
   является частью продукта, не опцией.
7. **Конфиг**: pydantic-settings с явными алиасами (`DATABASE__PATH|DB_PATH`,
   `TELEGRAM_*`, `RPC_URL_*`, `CELERY_*`, `SENTRY_DSN`). Голые поля-имена без
   алиасов запрещены: иначе pydantic-settings захватывает системные env
   (см. CHANGELOG 1.1.0).
8. **Мини-апп одним HTML-файлом**: ноль тулчейна, деплой копированием; цена —
   всё в одном файле, приемлемо для текущего размера (~700 строк).

## Инварианты
- Контракт `/api/<домен>/*` не меняется без обновления Mini App и README.
- Риск-лимиты не обходятся ни одним путём исполнения.
- Оплаты только с on-chain верификацией.
- Каждое действие фиксируется в dashboard-логе.
