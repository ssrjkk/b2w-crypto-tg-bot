# Architecture Documentation

## Overview

The Telegram Crypto Platform follows clean architecture principles with clear separation of concerns.

## Layer Architecture

### 1. Bot Layer (`app/bot/`)
- Telegram bot handlers
- Command handlers
- Callback handlers
- Keyboard definitions

### 2. API Layer (`app/api/`)
- FastAPI routes
- Request/Response DTOs
- Database dependencies

### 3. Core Layer (`app/core/`)
- Custom exceptions
- Enums
- Security utilities

### 4. Services Layer (`app/services/`)
- Subscription service
- Payment service
- Risk service
- Action queue service
- Alerting service

### 5. Adapters Layer (`app/adapters/`)
- Base adapter interface
- DEX-specific implementations
- Easy to add new DEXs

### 6. Trading Layer (`app/trading/`)
- Trading orchestrator
- Quote management
- Execution flow

### 7. Airdrop Layer (`app/airdrop/`)
- Airdrop engine
- Rules engine
- Progress tracking

### 8. Dashboard Layer (`app/dashboard/`)
- Event logging
- Activity tracking
- Audit trail

## Design Patterns

### Adapter Pattern
Used for DEX integrations to abstract different trading protocols behind a common interface.

### Queue-Based Execution
All actions go through an action queue for reliability and auditability.

### Risk-First
Every trading action is validated against risk rules before execution.

### Event Sourcing
All actions logged to dashboard for audit trail.

## Database Schema

- `users` - User accounts
- `subscriptions` - Subscription records
- `payments` - Payment invoices
- `trades` - Trade history
- `action_queue` - Queued actions
- `airdrop_campaigns` - Campaign definitions
- `airdrop_progress` - User progress
- `dashboard_events` - Activity log

## Security Considerations

- All actions user-initiated
- Subscription required for trading
- Risk limits enforced
- Full audit trail
- No automated trading
