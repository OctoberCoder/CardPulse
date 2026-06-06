# CardPulse — Gift Card Trading Platform Design Spec

**Date:** 2026-06-04
**Status:** Approved Design

## Overview

CardPulse is a merchant-model gift card trading platform. Users sell gift cards to CardPulse at a discount, and CardPulse resells them at a markup via its own inventory + the Reloadly API. The platform handles pricing, verification, payments, and dispute resolution.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | **FastAPI** (Python async) |
| Frontend | **Flutter** (cross-platform mobile + web) |
| Admin UI | **Supabase Studio** (initial DB admin) + **SQLAdmin** (FastAPI admin panel) |
| State Management | **Riverpod** (Flutter) |
| Database | PostgreSQL via **Supabase** |
| Async Tasks | Celery or Redis Queue |
| Card Inventory | **Reloadly API** (primary buy side) + own inventory (high-margin/local) |
| Payments | **Paystack** + **Flutterwave** (primary), Bank Transfers + Mobile Money (secondary), Crypto (optional, behind heavy KYC) |
| Notifications | SendGrid/Mailgun (email), Firebase Cloud Messaging (push), WebSocket (in-app) |
| Infra | Docker Compose (dev), Supabase (DB), Railway/Fly.io (FastAPI), TestFlight/App Store (Flutter) |
| Monitoring | Sentry (error tracking), Logtail (logging) |

## Project Structure

```
CardPulse/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry
│   │   ├── config/              # Settings (pydantic-settings)
│   │   ├── models/              # SQLAlchemy models
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── routers/             # API route handlers
│   │   ├── services/            # Business logic
│   │   │   ├── reloadly.py      # Reloadly API client
│   │   │   ├── pricing.py       # Rate engine
│   │   │   ├── payments/        # Paystack, Flutterwave, crypto
│   │   │   └── notifications/   # Email, push, in-app
│   │   ├── admin/               # SQLAdmin panel
│   │   ├── celery/              # Task definitions
│   │   └── utils/               # Encryption, audit, helpers
│   ├── tests/
│   ├── requirements/
│   └── Dockerfile
├── frontend/                     # Flutter app (mobile + web)
│   ├── lib/
│   │   ├── screens/             # All screens
│   │   ├── widgets/             # Shared widgets
│   │   ├── services/            # API client, auth, payments
│   │   ├── providers/           # State management
│   │   └── models/              # Dart models
│   └── pubspec.yaml
├── docker-compose.yml
└── README.md
```

## User Tiers

| Tier | Daily Sell Limit | Daily Buy Limit | Payout Speed | Requirements |
|------|-----------------|-----------------|-------------|----------|
| Unverified | $100 | $200 | 48hr | Email + phone |
| Verified | $1,000 | $2,000 | 24hr | ID + address proof |
| Premium | $10,000 | $10,000 | Instant (wallet) | Full KYC + business docs |

## Core Data Models

### accounts
- `User` — id, email, password_hash, phone, tier, kyc_status, is_active, is_staff, created_at
- `KYCSubmission` — user FK, doc_type (id/address/business), file_url, status (pending/approved/rejected), reviewed_by FK, notes, submitted_at, reviewed_at

### cards — Own Inventory
- `CardBrand` — id, name, slug, description, icon, active
- `Denomination` — id, brand FK, value, currency
- `CardSubmission` — id, user FK, brand FK, denomination FK, card_code_encrypted, card_image_url, quoted_amount, final_amount, status (pending/approved/rejected/paid), reviewed_by FK, admin_notes, submitted_at, reviewed_at
- `OwnListing` — id, brand FK, denomination FK, card_code_encrypted, cost_price, sell_price, status (available/sold/expired), purchased_by FK, purchased_at

### cards — Reloadly Integration
- `ReloadlyProduct` — id, reloadly_id, brand, denomination, currency, sell_price, fee, active, last_synced
- `ReloadlyTransaction` — id, user FK, product FK, order reference, amount, fee, recipient_email, status (pending/success/failed), reloadly_tx_id, created_at

### pricing
- `RateRule` — brand FK, denomination FK, base_buy_rate, sell_markup_pct, min_rate, max_rate, active
- `RateAdjustment` — rule FK, trigger_type (stock_low/stock_high/submission_volume/day_of_week), operator, value, adjustment_pct, priority
- `RateSnapshot` — brand FK, denomination FK, effective_buy_rate, effective_sell_price, logged_at

### orders
- `Order` — id, buyer FK, source (own_inventory/reloadly), listing_id (nullable), reloadly_tx_id (nullable), amount_paid, fee, status (pending/completed/refunded), payment_method, payment_reference, idempotency_key (unique), delivered_at

### wallet
- `Wallet` — user FK, balance, currency, locked_amount
- `WalletTransaction` — wallet FK, type (credit/debit), amount, reference, description
- `Withdrawal` — user FK, amount, method (bank/mobile_money/crypto), status (pending/processing/completed/failed), reference, processed_by FK

### disputes
- `Dispute` — order FK, user FK, reason, evidence_urls, status (open/under_review/resolved), resolution (refund/reject), admin_notes, created_at, resolved_at

### audit
- `AuditLog` — actor FK, action, resource_type, resource_id, details (JSON), ip_address, timestamp

### fraud
- `FraudAlert` — id, triggered_by_rule, user FK, submission_id (nullable), description, severity (low/medium/high), status (open/investigated/resolved), resolved_by FK, created_at

## API Endpoints

### Accounts
```
POST   /api/auth/register            — email + password + phone
POST   /api/auth/login               — returns JWT pair
POST   /api/auth/refresh             — refresh access token
POST   /api/auth/verify-otp          — verify email/phone OTP
POST   /api/auth/resend-otp          — resend OTP
GET    /api/auth/me                  — current user profile
PATCH  /api/auth/me                  — update profile

POST   /api/kyc/upload               — submit KYC document
GET    /api/kyc/status               — current KYC level
GET    /api/admin/kyc/pending        — pending verifications
PATCH  /api/admin/kyc/{id}/review    — approve/reject
```

### Cards — Sell to CardPulse (Own Inventory)
```
GET    /api/brands                   — active brands
GET    /api/brands/{slug}/denominations — denominations for brand
POST   /api/cards/quote              — submit code, get quote
POST   /api/cards/submit             — accept quote, create submission
GET    /api/cards/submissions        — user's submissions
GET    /api/cards/submissions/{id}   — single submission
GET    /api/admin/cards/submissions       — all submissions
PATCH  /api/admin/cards/submissions/{id}/review — approve/reject
POST   /api/admin/cards/submissions/{id}/generate-listing — move to inventory
```

### Cards — Buy from CardPulse (Reloadly + Own Inventory)
```
GET    /api/products                 — browse available cards (merged: Reloadly + own)
GET    /api/products/{id}            — single product detail
GET    /api/products/reloadly/{brand} — browse Reloadly cards by brand
POST   /api/products/reloadly/order  — purchase via Reloadly (email delivery)
```

### Reloadly Integration
```
GET    /api/admin/reloadly/products  — admin: browse all Reloadly products
POST   /api/admin/reloadly/sync      — manual sync products from Reloadly
GET    /api/admin/reloadly/transactions — Reloadly order history
PATCH  /api/admin/reloadly/settings  — update Reloadly API config
```

### Orders
```
POST   /api/orders                   — create order (requires `Idempotency-Key` header)
POST   /api/orders/{id}/pay          — process payment (requires `Idempotency-Key` header)
GET    /api/orders/{id}/code         — reveal code (own inventory only)
POST   /api/orders/{id}/resend-email — resend code
GET    /api/orders                   — user's purchase history
GET    /api/admin/orders             — all orders
POST   /api/admin/orders/{id}/refund — admin refund
```

### Pricing
```
GET    /api/admin/rates              — list rate rules
POST   /api/admin/rates              — create rate rule
PATCH  /api/admin/rates/{id}         — update rule
DELETE /api/admin/rates/{id}         — soft delete
GET    /api/admin/rates/effective    — computed rates for all brands
```

### Wallet
```
GET    /api/wallet                   — balance + locked
GET    /api/wallet/transactions      — history
POST   /api/wallet/withdraw          — request withdrawal
GET    /api/admin/payouts/pending    — pending payouts
PATCH  /api/admin/payouts/{id}/process — mark paid
```

### Disputes
```
POST   /api/orders/{id}/dispute      — open dispute
GET    /api/disputes                 — user's disputes
GET    /api/admin/disputes           — all disputes
PATCH  /api/admin/disputes/{id}/resolve — resolve
```

### Notifications
```
GET    /api/notifications            — list notifications
PATCH  /api/notifications/{id}/read  — mark read
PATCH  /api/notifications/read-all   — mark all read
```

## Key Flows

### Card Buying Flow (User Sells to CardPulse)
1. User selects brand + denomination, enters card code
2. `POST /api/cards/quote` — pricing engine computes rate, returns quote
3. User accepts → `POST /api/cards/submit` — creates CardSubmission (status: pending)
4. Admin reviews code in admin panel — approves or rejects
5. If approved → wallet credited, `OwnListing` created in inventory
6. User notified via email + push

### Card Selling Flow (User Buys from CardPulse)
1. Buyer browses products at `GET /api/products` — merged feed of Reloadly + own inventory
2. Two paths:
   - **Reloadly path**: Buyer selects Reloadly product → enters recipient email → creates order → pays → Reloadly API delivers code to email
   - **Own inventory path**: Buyer selects OwnListing → creates order → pays → code decrypted and displayed + emailed
3. Order status set to completed, listing marked as sold

### Reloadly Integration Flow
1. Cron job syncs available products from Reloadly API every 15 min → `ReloadlyProduct` table
2. Admin sets sell markup on Reloadly products (e.g., +5% on Reloadly's price)
3. When a Reloadly order comes in:
   - `POST /api/products/reloadly/order` → calls Reloadly API to fulfill
   - Reloadly delivers gift card code to buyer's email
   - `ReloadlyTransaction` and `Order` created
4. If Reloadly API fails → automatic retry (3 attempts), then manual admin review

### Payout Flow
1. Card submission approved → `Wallet` credited, `WalletTransaction` created
2. User requests withdrawal → `POST /api/wallet/withdraw`
3. Admin processes payout in admin panel
4. Premium users: instant auto-payout via Paystack/Flutterwave transfer API

### Dispute Flow
1. Buyer opens dispute with evidence → status: open
2. Admin reviews → checks card code validity
3. Resolves: refund (payment returned) or reject (card was valid)
4. Notification sent to buyer

## Reloadly Integration Plan

### API Flow
```
Reloadly API Endpoints Used:
- GET  /o/token                    — OAuth2 client credentials auth
- GET  /gift-cards/products        — list available products (brand, denom, price)
- GET  /gift-cards/products/{id}   — single product detail
- POST /gift-cards/orders          — place order (product_id, quantity, recipient_email)
- GET  /gift-cards/orders/{id}     — check order status
- GET  /gift-cards/transactions    — transaction history
```

### Data Flow
```
Reloadly API → Sync cron (every 15 min) → ReloadlyProduct table
                                            ↓
User browses products ← GET /api/products (merged: ReloadlyProducts + OwnListings)
                                            ↓
User selects product → pays → Order created
                                            ↓
ReloadlyOrder placed → confirm status → code delivered to email
```

### Markup Logic
```
sell_price = reloadly_product.price × (1 + markup_pct / 100)
admin_markup = order.amount_paid - reloadly_product.price
```
Markup is set per brand in the admin panel (default: 5%).

### Error Handling
- Reloadly API timeouts → retry with exponential backoff (3 attempts)
- Product out of stock → hide from product feed, show "Currently unavailable"

### Balance Management
- **Monitoring**: Celery cron checks Reloadly wallet balance every hour via `GET /gift-cards/balance`
- **Alerts**: Balance below threshold ($200 / $100 / $50) → send alerts via email + Slack to admin
- **Auto-disable**: Balance below $20 → automatically disable Reloadly product listings in product feed, show "Top-up required" admin banner
- **Top-up flow**: Admin tops up via Reloadly dashboard (manual). After top-up, balance check passes → products re-enabled automatically

## Inventory Sourcing Strategy

| Source | Use Case | Margin |
|--------|----------|--------|
| **Reloadly API** | Primary source for buy side (selling to users). 200+ brands, instant delivery via email | Low (5-10% markup) |
| **Own Inventory** | High-margin cards (>15%), locally sourced, bulk-purchased cards, regional brands not on Reloadly | High (10-30%) |

**Reloadly is the default.** Own inventory only supplements where margins justify the manual verification overhead. Product feed at `GET /api/products` merges both sources, prioritizing own inventory when prices beat Reloadly.

## Liquidity Management (Working Capital)

This is the critical real-world constraint — CardPulse must have cash available to pay sellers when they sell cards. The platform's liquidity model:

### Capital Sources (Phase 1)
- **Founder capital** — initial float to cover first payouts ($5k-$20k recommended)
- **Revenue reinvestment** — spread from buy/sell margin replenishes the payout pool
- **Payment settlement lag** — Paystack/Flutterwave settlement takes 1-3 days, creating a natural float (buyers pay instantly, funds arrive later)

### Strategies to Reduce Capital Pressure
- **Reloadly as primary buy source**: No capital tied up in pre-purchased inventory. Cards are fulfilled on-demand by Reloadly, and Reloadly bills your account (net terms or prepaid balance).
- **Tiered payout timing**: Unverified (48hr), Verified (24hr), Premium (instant wallet). The delay for lower tiers creates a cash buffer.
- **Platform wallet incentive**: Encourage users to keep funds in their CardPulse wallet (earn rewards or discounts) rather than withdrawing immediately.
- **Payout batching**: Bank transfers are processed in daily batches (reducing per-transfer fees and allowing cash consolidation).
- **Spread-first operations**: In early stages, cap daily submissions to what the current float can cover. Display "submission limit reached" when float is low.

### Monitoring
- `LiquiditySnapshot` model tracks daily: opening_balance, submissions_payable, revenue_in, withdrawals_processed, closing_balance
- Alert admin when float drops below 2x average daily payout volume
- Admin dashboard shows real-time payout liability vs. available balance

## Payments

| Method | Type | Direction | KYC Required |
|--------|------|-----------|-------------|
| Paystack | Primary | Buy + Payouts | Standard |
| Flutterwave | Primary | Buy + Payouts | Standard |
| Bank Transfer | Secondary | Buy (manual) | Yes |
| Mobile Money | Secondary | Payouts | Standard |
| Crypto (USDT) | Optional | Buy + Payouts | Full KYC + source of funds |

**Flow:** Paystack/Flutterwave handle the majority of transactions. Bank transfers and mobile money are fallbacks for users who can't use card payments. Crypto is a premium feature behind enhanced KYC (address proof, source of funds documentation, transaction limits).

**Webhook handling:** Paystack and Flutterwave send webhooks on `charge.success` → order marked as paid → code delivered.

**Webhook signature verification:**
- Paystack: Verify `x-paystack-signature` header — HMAC-SHA256 hash of request body using secret key. Compare against computed hash. Reject mismatches with 401.
- Flutterwave: Verify `verif-hash` header — compare against configured webhook secret. Reject mismatches with 401.
- Both: Webhook handlers are idempotent — check `payment_reference` before processing. Respond with 200 OK within 5 seconds. Failed processing → queue to Celery for retry.
- Crypto: On-chain confirmation required — wait for N confirmations (configurable, default 3) before releasing card code.

## Security

- **Card code encryption**: AES-256-GCM via `cryptography` library. Each code encrypted with a unique IV. Encryption key stored in **Supabase Vault** (column-level encryption) or environment variables managed via **Doppler** (secret rotation, audit trail, rollback). Keys rotated quarterly via Celery cron task that re-encrypts all stored codes with the new key.
- **Card code access**: Decryption happens only at the moment of purchase completion. Decrypted code is never logged, stored in memory only, and discarded after display.
- **Audit logging**: Every card code access attempt (decrypt, view, manual check) logged to `AuditLog` with actor, IP, timestamp. Admin decryption requires 2FA.
- **Rate limiting**: Implemented via **slowapi** (FastAPI middleware with Redis backend). Limits: 5 req/min on auth, 30 req/min on general API, 100 req/min on product browsing. Burst limits allow short spikes (e.g., 10 req/10s on auth). Per-IP + per-user tracking. Exceeded limit returns 429 with `Retry-After` header.
- **Brute force protection**: Login lockout after 5 failed attempts (15 min cooldown). OTP rate limited to 3 attempts per phone/email per hour.
- **JWT tokens**: Access token (15 min), refresh token (7 days) with rotation. Stored in httpOnly cookies on web, secure storage on mobile.
- **File uploads**: Validate type (PDF, JPG, PNG), max 5MB, scan with ClamAV. Store on Supabase Storage with signed URLs (expiring).
- **API security**: CORS restricted to Flutter app domain. All admin routes require staff role + 2FA.

### Fraud Detection Rules

All evaluated server-side before accepting card submissions or processing payouts:

1. **Duplicate card code**: Same card code submitted more than once → flag as fraud, block second submission, notify admin. Comparison done on SHA-256 hash of the code.
2. **Velocity checks**: Same user > 5 submissions in 1 hour → flag for manual review. Same user > 10 submissions in 24hr → temporary submission ban.
3. **New user fraud**: Accounts < 24hr old with submission value > $500 → hold for manual review before payment.
4. **Card reuse across accounts**: Same code hash from different users → flag both accounts, trigger investigation.
5. **Suspicious IP/device**: VPN/proxy detected on high-value submission → flag. Same device on multiple accounts → flag.
6. **Payout fraud**: Withdrawal requested immediately after card approval → hold for 24hr review window for new accounts.

Fraud flags are stored in `FraudAlert` model and surfaced in admin dashboard.

## Error Handling Strategy

- **API errors**: Consistent response format — `{ "detail": "...", "code": "ERROR_CODE", "field": "..." }`
- **FastAPI exception handlers**: Global handlers for 400, 401, 403, 404, 422, 500
- **Retry logic**: External API calls (Reloadly, Paystack, Flutterwave) use tenacity with exponential backoff (max 3 retries)
- **Idempotency**: Payment endpoints require `Idempotency-Key` header (UUID v4). Key stored on `Order.idempotency_key` with unique constraint. Same key within 24hr returns cached response. Keys expire after 24hr.
- **Graceful degradation**: If Reloadly is down, show own inventory only. If Paystack is down, fall back to Flutterwave. If both down, disable buy flow and show maintenance banner.
- **Dead letter queue**: Failed Celery tasks go to a dead letter queue, alerting admin via Slack/email

## Testing Strategy

### Unit Tests (pytest)
- All service functions with mocked dependencies
- Pydantic schema validation
- Pricing engine logic (rate rules, adjustments)
- Encryption/decryption round-trip
- Reloadly API client (mocked HTTP calls)
- Payment webhook signature verification

### Integration Tests
- FastAPI test client against test database
- Full auth flow (register → verify → login → refresh)
- Card submission → approval → listing flow
- Order → payment → delivery flow
- Wallet credit → withdrawal flow
- Reloadly sync → product listing → purchase flow

### End-to-End Tests
- Flutter integration tests (firebase_test_lab or similar)
- Critical user journeys: sign up → sell card → buy card → withdraw

### Coverage Target
- Backend: 85%+
- Critical paths (payments, card code handling): 95%+

## Monitoring (Sentry + Logtail)

- **Sentry**: Capture FastAPI exceptions, log errors with full context. Flutter crash reporting via Sentry SDK.
- **Logtail**: Structured JSON logging for all API requests, Celery tasks, external API calls. Alerts on error rate spikes.
- **Health checks**: `GET /health` — DB connection, Redis, Reloadly API, payment provider status. Monitored via UptimeRobot.
- **Business metrics**: Daily submissions, orders, revenue, payout volume. Logged to a metrics table and visualized in admin dashboard.

## Scalability Notes

- **FastAPI async**: Async handlers for all I/O-bound operations (DB queries, external API calls). No blocking in request handlers.
- **Database**: Supabase PostgreSQL with connection pooling (PgBouncer). Read replicas for product browsing if needed.
- **Caching**: Redis cache for product listings (TTL: 5 min), rate rules (TTL: 1 min), brand list (TTL: 1 hour).
- **Celery/Redis Queue**: Background tasks for Reloadly sync, email delivery, payout processing. Task prioritization (payouts > sync).
- **Flutter**: Lazy-loading product lists, pagination on API responses, local caching for frequently viewed brands.
- **Horizontal scaling**: FastAPI is stateless — scale behind a load balancer. Celery workers scale independently. Redis and PostgreSQL are the bottlenecks.
- **Supabase**: Built-in auto-scaling for PostgreSQL. Row-Level Security (RLS) policies for multi-tenant data isolation if needed.

## Flutter Frontend Screens

### Guest Screens
- `/` — Landing with featured products, brand categories
- `/login` — Email + password, OTP verification
- `/register` — Registration form
- `/browse` — Browse products (filter by brand, price range, source)

### User Screens (Authenticated)
- `/dashboard` — Balance overview, recent activity
- `/sell` — Sell card form + submission status tracker
- `/sell/{id}` — Individual submission detail
- `/buy` — Browse + purchase (merged Reloadly + own inventory)
- `/orders` — Purchase history
- `/wallet` — Balance, transactions, withdrawal form
- `/settings` — Profile, KYC upload, 2FA, payment methods
- `/disputes` — My disputes
- `/notifications` — Notification list

### Admin Screens (Staff role)
- `/admin` — Dashboard with stats (submissions, orders, revenue charts)
- `/admin/submissions` — Review card submissions (approve/reject) [SQLAdmin]
- `/admin/users` — Manage users, set tiers, suspend [SQLAdmin]
- `/admin/kyc` — Verify KYC documents [SQLAdmin]
- `/admin/rates` — Rate management [SQLAdmin]
- `/admin/products` — Manage own listings, view Reloadly products [SQLAdmin]
- `/admin/reloadly` — Sync products, view transactions, configure settings [SQLAdmin]
- `/admin/orders` — All orders, issue refunds [SQLAdmin]
- `/admin/payouts` — Pending payouts, mark as paid [SQLAdmin]
- `/admin/disputes` — Dispute resolution [SQLAdmin]
- `/admin/audit-log` — View audit trail [SQLAdmin]

**Note:** Initial admin panel uses **Supabase Studio** (table-level CRUD on PostgreSQL) + **SQLAdmin** (FastAPI-integrated admin panel) for rapid bootstrapping. However, SQLAdmin is functional but not mobile-friendly and has a dated UI. Custom Flutter admin screens should be prioritized early for the most-used daily operations:

1. **Card review & approval** — highest frequency, needs quick approve/reject with inline card code checking
2. **Payout processing** — needs bulk select, mark-as-paid, payment reference entry
3. **KYC review** — needs document viewer, side-by-side ID comparison, approval/reject

These three custom screens cover ~90% of daily admin work. The rest (rate management, user listing, audit log) can stay on SQLAdmin/Supabase Studio longer.

## Pricing Engine Logic

Rate rules are evaluated per brand+denomination:

```
effective_buy_rate = base_buy_rate

For each active RateAdjustment (ordered by priority):
  if trigger condition met:
    effective_buy_rate += adjustment_pct

effective_buy_rate = clamp(effective_buy_rate, min_rate, max_rate)
sell_price = denomination_value × (sell_markup_pct / 100)
```

Example triggers: stock_high (inventory > 50 → -3%), stock_low (inventory < 10 → +2%), submission_volume_high (> 20/day → -2%), weekend (+1%).

## Future: Hermes AI Agent Integration

### Dev Tool
Hermes Agent (Nous Research) is used alongside opencode as a development tool for building CardPulse. Install via:
```
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```
Point Hermes at `~/CardPulse/` for AI-assisted development.

### Product Feature (Phase 9+)
Embed Hermes as an intelligent assistant within CardPulse:

- **Customer Support Agent** — Deployed via Hermes' messaging gateway (Telegram, WhatsApp) to handle user inquiries about card status, payouts, and disputes
- **Card Recommendation Bot** — Hermes skills system used to build a chatbot that suggests best cards to buy/sell based on user history
- **Automated Admin Assistant** — Hermes cron scheduler for daily reports, fraud flagging, and rate adjustment alerts
- **Integration** — Hermes MCP servers connect to CardPulse's FastAPI for real-time data access
- **Deployment** — Run Hermes gateway on the same Docker Compose stack, connected to Supabase PostgreSQL read-only
