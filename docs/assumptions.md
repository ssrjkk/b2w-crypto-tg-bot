# Assumptions & Limitations

## Product Assumptions

1. **User-Initiated Actions Only**
   - All trading and on-chain actions must be explicitly triggered by user commands
   - No background automation, bots, or scheduled tasks
   - Anti-bot protection implemented via explicit confirmations

2. **Subscription Model**
   - Prepaid subscription model with crypto payment
   - Subscription required to access trading features
   - Manual activation after on-chain confirmation

3. **Demo Adapters**
   - DEX adapters are mock implementations for demonstration
   - Real integration would require wallet connection
   - API endpoints exist but don't connect to real DEXs

4. **Database**
   - SQLite for local demonstration
   - In production, would use PostgreSQL or similar
   - Schema designed for easy migration

5. **Security**
   - Telegram user identity for authentication
   - No private keys stored (demo mode)
   - Risk limits enforced on all trades

## Current Limitations

1. **Payment Verification**
   - On-chain verification is mocked
   - Real implementation would poll RPC for confirmations

2. **Trading**
   - Only quote-to-trade flow implemented
   - No real order book or execution
   - Position tracking is basic

3. **Airdrop**
   - Eligibility rules are configurable but basic
   - No real on-chain checking
   - Progress tracking is manual

4. **Telegram Bot**
   - Mini App not fully implemented
   - Basic command handlers only

## Future Enhancements

1. **Real Wallet Integration**
   - Wallet connect for transactions
   - Balance management

2. **Real DEX Integration**
   - Live price feeds
   - Actual trade execution

3. **Payment Providers**
   - Stripe-like crypto payment processors
   - Fiat on-ramps

4. **Analytics**
   - Portfolio tracking
   - PnL analytics
