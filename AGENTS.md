# CardPulse

Gift card trading platform — merchant model. Users sell gift cards to CardPulse at a discount, CardPulse resells them at a markup via Reloadly API + own inventory.

## Architecture

```
backend/       — FastAPI async Python API
frontend/      — Flutter mobile + web app (future)
docs/          — Design specs + implementation plans
```

### Core flows
- **Buy flow**: User submits card code → rate engine quotes → admin approves → wallet credited → listing created
- **Sell flow**: User browses products (merged Reloadly + own inventory) → pays → code delivered
- **Admin**: SQLAdmin + custom Flutter screens for card review, payouts, KYC

## Tech Stack

| Layer | Tech |
|-------|------|
| Backend | FastAPI, SQLAlchemy 2.0, Alembic |
| Database | PostgreSQL (Supabase) |
| Async | Celery + Redis |
| Auth | JWT (access + refresh tokens) |
| Payments | Paystack + Flutterwave (primary), bank/momo (secondary), crypto (optional) |
| Card inventory | Reloadly API (primary) + own inventory (high-margin) |
| Admin | SQLAdmin + Supabase Studio |
| Frontend | Flutter with Riverpod (not started) |
| Infra | Docker Compose, Railway/Fly.io, Vercel |
| Monitoring | Sentry + Logtail |

## Build Commands

```bash
# Backend
cd backend
pip install -e ".[dev]"          # install deps
uvicorn app.main:app --reload    # dev server (port 8000)
pytest                           # run tests
pytest -v                        # verbose tests
coverage run -m pytest           # coverage
alembic revision --autogenerate  # create migration
alembic upgrade head             # apply migrations

# Docker
docker compose up -d db redis    # start infra
docker compose up api            # start API
docker compose logs -f           # follow logs
```

## Project Status

- **Phase 1** (complete ✅): Backend scaffolding, auth with JWT, card brands/submissions API, admin review flow, wallet with auto-credit on approval, SQLAdmin panel, rate limiting, 18 passing tests
- **Phase 2**: Pricing engine, Reloadly integration | **Phase 3**: Payments (Paystack/Flutterwave)
- **Phase 4**: Flutter frontend | **Phase 5+**: KYC, disputes, admin custom screens, Hermes AI agent
- **Phase 2**: Pricing engine, Reloadly integration
- **Phase 3**: Payments (Paystack/Flutterwave)
- **Phase 4**: Flutter frontend
- **Phase 5+**: KYC, disputes, admin custom screens, Hermes AI agent

## Key Files

| File | Purpose |
|------|---------|
| `backend/app/main.py` | FastAPI app entry |
| `backend/app/config/settings.py` | Pydantic settings |
| `backend/app/database.py` | SQLAlchemy async engine + session |
| `backend/app/models/` | SQLAlchemy models |
| `backend/app/schemas/` | Pydantic request/response schemas |
| `backend/app/routers/` | API route handlers |
| `backend/app/services/` | Business logic |
| `backend/app/admin_setup.py` | SQLAdmin configuration |
| `docs/superpowers/specs/` | Design specifications |
| `docs/superpowers/plans/` | Implementation plans |

## MCP Servers (for Hermes/opencode)

- PostgreSQL introspection (Supabase connection)
- File system access to `backend/` directory

## Design Docs

- [Spec](docs/superpowers/specs/2026-06-04-cardpulse-design.md)
- [Phase 1 Plan](docs/superpowers/plans/2026-06-04-cardpulse-phase1.md)
