# API Reference

## Subscription Endpoints

### Create Subscription
```
POST /subscription/create
```

Request:
```json
{
  "user_id": 123456,
  "plan_name": "premium",
  "duration_days": 30
}
```

Response:
```json
{
  "id": 1,
  "status": "pending",
  "start_date": "2024-01-01T00:00:00",
  "expiry_date": "2024-01-31T00:00:00",
  "days_remaining": 30
}
```

### Check Access
```
GET /subscription/check-access/{user_id}
```

Response:
```json
{
  "has_access": true
}
```

## Payment Endpoints

### Create Invoice
```
POST /payment/invoice
```

Request:
```json
{
  "user_id": 123456,
  "amount": "0.01",
  "token": "ETH",
  "network": "arbitrum"
}
```

Response:
```json
{
  "id": 1,
  "amount": "0.01",
  "token": "ETH",
  "network": "arbitrum",
  "address": "0xabc123...",
  "expires_at": "2024-01-01T00:30:00"
}
```

### Verify Payment
```
POST /payment/verify
```

Request:
```json
{
  "transaction_hash": "0x123...",
  "user_id": 123456,
  "expected_amount": "0.01",
  "token": "ETH",
  "network": "arbitrum"
}
```

## Trading Endpoints

### Get Quote
```
POST /trading/quote
```

Request:
```json
{
  "user_id": 123456,
  "dex": "gmx",
  "network": "arbitrum",
  "from_token": "ETH",
  "to_token": "USDC",
  "amount": "1.0",
  "side": "buy",
  "order_type": "market"
}
```

### Execute Trade
```
POST /trading/execute
```

Request:
```json
{
  "user_id": 123456,
  "dex": "gmx",
  "network": "arbitrum",
  "from_token": "ETH",
  "to_token": "USDC",
  "amount": "1.0",
  "side": "buy",
  "order_type": "market",
  "max_slippage": 2.0
}
```

## Airdrop Endpoints

### Check Eligibility
```
POST /airdrop/check-eligibility
```

Request:
```json
{
  "user_id": 123456,
  "campaign_id": 1,
  "total_volume": 10000,
  "total_trades": 50,
  "activity_arbitrum": 20,
  "holding_days_eth": 30
}
```

## Dashboard Endpoints

### Get Events
```
GET /dashboard/events/{user_id}?limit=50
```

### Get Summary
```
GET /dashboard/summary/{user_id}
```
