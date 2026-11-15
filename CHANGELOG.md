# Changelog

Все заметные изменения проекта. Формат — Keep a Changelog, версии по смыслу правок.

## [1.1.0] — 2026-11-16

### Fixed
- **Критично:** `DatabaseSettings.path` больше не захватывает системную переменную
  `PATH` (pydantic-settings матчил поле без алиаса case-insensitively) — добавлены
  алиасы `DATABASE__PATH` (compose/.env) и `DB_PATH` (README systemd-пример).
- **Критично:** восстановлена инфраструктура alembic — `alembic.ini` был env.py,
  переименованным в `.ini`; теперь настоящие `alembic.ini` + `alembic/env.py` +
  `script.py.mako` + `versions/`, цикл autogenerate → upgrade проверен запуском.
- Global 500-handler больше не падает сам (logger.error без kwargs) — контракт
  JSON-ошибки `{"error", "code": "INTERNAL_ERROR"}` возвращается всегда.
- Mini App: API и WebSocket выводятся из `window.location` (same-origin деплой по
  deploy/nginx.conf), `file://`-дев фолбэкается на localhost:8000.
- SECURITY.md: репорты уязвимостей через GitHub Private Vulnerability Reporting
  (включён на репо) или email владельца — прежний контакт указывал на домен
  другого проекта.
- `docs/api_reference.md`: все эндпоинты приведены к `/api/*`-префиксу.
- Мёртвая ветка в `get_database_url()` схлопнута; obsolete `version:` убран из
  docker-compose.yml.

### Changed
- README: срезан дубль Quick Start из хвоста; шаг миграций теперь честен
  (autogenerate + upgrade, create_all для sqlite-дева); compose-блок заменён
  указателем на реальный файл.

### Added
- tests/unit/test_settings_regression.py — регрессионные тесты PATH-бага и
  контракта 500-ответа.
- og:image/Twitter-карточки шаринга (docs/og-card.png), favicon, canonical,
  robots.txt, sitemap.xml.

## [1.0.0] — до 2026-11
Начальная платформа: подписки с on-chain оплатами, perp-трейдинг через DEX-адаптеры,
airdrop-трекер, Mini App, WebSocket, JWT, celery.
