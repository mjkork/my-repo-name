# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Archery Practice Logger

## Project Overview

A web-based application for logging and analyzing personal archery practice sessions. Each session captures contextual variables (location, distance, equipment, weather, subjective energy, etc.) so users can later analyze how these factors correlate with performance and progress.

**Status:** Concept stage — requirements and schema are actively being drafted and will evolve.

**Scaling ambition:** The project starts as a solo tool but is designed from day one to support multiple users safely and to be deployable as a small SaaS later without architectural rewrites. Decisions favor patterns that scale; complexity that isn't needed yet is deferred, but **never in a way that locks out multi-user, async work, or remote storage.**

## Tech Stack

**Currently installed** (see `pyproject.toml`):
- **Language:** Python 3.12+
- **Framework:** Django 5.x
- **Auth:** `django-allauth[mfa]` — email-only login (`ACCOUNT_LOGIN_METHODS = {"email"}`), mandatory email verification
- **Config:** `django-environ` — all settings from env vars; reads `.env` at startup
- **Database:** SQLite in dev (via `DATABASE_URL` env var defaulting to `sqlite:///db.sqlite3`); PostgreSQL 16+ in production
- **Testing:** pytest + pytest-django + factory_boy
- **Lint & format:** ruff

**Planned (not yet installed — discuss before adding):**
- **Frontend interactivity:** HTMX; JS framework (React or Alpine) only on specific surfaces like the arrow-plot UI
- **Async / background jobs:** Celery + Redis
- **Cache & sessions:** Redis
- **Object storage:** S3-compatible via `django-storages` (MinIO or filesystem in dev; S3/R2 in prod)
- **Image processing:** Pillow + OpenCV

If a change to this stack is proposed, discuss trade-offs first before implementing.

## Project Structure

```
archery_logger/
├── archery_logger/        # Django project (settings, urls, wsgi, celery)
├── accounts/              # App: user accounts and profile
├── sessions/              # App: practice sessions (CRUD + analysis)
├── equipment/             # App: bows and other gear
├── plotting/              # App: photo-based arrow plot detection
├── templates/             # Django templates (HTMX partials in templates/partials/)
├── static/                # CSS, JS, images
├── manage.py
├── pyproject.toml
└── README.md
```

App-specific tests live in `<app>/tests/`. Cross-cutting tests live in a top-level `tests/`.

## Domain Model (current concept)

Every user-owned model has an `owner` FK to the `User` model and is filtered by the authenticated user in every queryset. **Never trust a client-supplied user or owner ID.**

### Session
All sessions are currently **free practice**. Structured rounds and competitions (WA Standard, etc.) are a planned future addition (see `Future: Round` below), and will be modeled as a separate concept rather than as additional enum values.

- `owner` — FK to User
- `location` — enum: `indoor`, `outdoor`
- `distance_m` — positive integer (meters)
- `temperature` — subjective ordinal scale; **outdoor only**
- `wind` — subjective ordinal scale (`none` → `heavy`); **outdoor only**
- `energy_before` — subjective ordinal scale (`low` → `high`)
- `energy_after` — same scale as `energy_before`
- `started_at` — timezone-aware datetime
- `arrow_count` — positive integer
- `bow` — FK to Bow (must be owned by the same user)
- `notes` — free-form text, optional

### Bow (base — fields shared by all bow types)
- `owner` — FK to User
- `name` — string (user's nickname for the bow, e.g. "Blue Hoyt")
- `type` — enum: `olympic_recurve` (additional types planned: barebow, compound, traditional)
- `draw_weight_lbs` — decimal, nullable (in pounds; universal across bow types)
- `notes` — free-form text, optional

The base `Bow` model **never** holds type-specific fields. Variant-specific equipment lives in a dedicated `<Type>BowSetup` model.

### OlympicBowSetup (1:1 with Bow when `type == olympic_recurve`)
All component fields are free-text strings, all optional — a bow may or may not have any given component, and the user fills the brand/model/details themselves.

- `bow` — OneToOne to Bow
- `riser`
- `limbs`
- `arrow_rest`
- `sight`
- `main_stabilizer`
- `extender`
- `side_stabilizers`
- `v_bar`
- `clicker`
- `button`

An archer can own multiple Olympic bows; each is a separate `Bow` row with its own `OlympicBowSetup`. Future bow types (barebow, compound, traditional) will get their own `<Type>BowSetup` model with type-appropriate fields.

**Possible future evolution:** components could become first-class `Equipment` entities (so a riser can be tracked across bows with purchase date, retirement, etc.). For now they are simple strings on the Setup. The Setup model is the migration point if/when this evolution happens.

### Future: ArrowPlot
- Linked to a Session and an uploaded photo (stored in object storage, not local disk)
- Stores detected arrow positions on a target face for analysis
- Photo processing runs in a Celery task, never inline in the request

### Future: Round (structured practice / competition)
A standalone model representing defined rounds such as WA Standard, WA 720, indoor 18m, etc. A Round defines structure (arrow count, distance(s), target face, ends, scoring rules). When introduced:

- `Session` gains an optional FK to `Round`. A null `round` means free practice (the only mode today).
- Fields like `arrow_count` and `distance_m` may become derived from the round when one is attached, rather than user-entered. This will be decided when the feature lands.
- Scoring (per-arrow or per-end) is a separate concern from the round itself — see the open question on scoring granularity.

## Dev Environment Bootstrap

```bash
cp .env.example .env   # then edit SECRET_KEY at minimum
```

The `.env.example` defaults to SQLite — no Postgres needed to start developing locally.

## Build, Run, Test

```bash
# Install all dependencies (creates .venv automatically)
uv sync

# Run dev server
uv run python manage.py runserver

# Migrations
uv run python manage.py makemigrations
uv run python manage.py migrate

# Run all tests
uv run pytest

# Run a single test file
uv run pytest accounts/tests/test_models.py

# Run a single test by name
uv run pytest -k test_name

# Lint
uv run ruff check .

# Format
uv run ruff format .

# Lint + format check (pre-commit gate)
uv run ruff check . && uv run ruff format --check .

# Background worker (needs Redis — not configured yet)
uv run celery -A archery_logger worker -l info
```

## Coding Conventions

- Follow PEP 8; ruff enforces this.
- Type hints on all function signatures.
- Docstrings on public functions, classes, and Django models.
- Prefer explicit over clever; readability over brevity.
- All datetimes are timezone-aware; store in UTC, convert at the edges.
- Use `models.TextChoices` for enums.
- Keep views thin; put business logic in `<app>/services.py`.
- HTMX partial templates go in `templates/partials/<app>/`.

## Current Implementation State

The scaffold is in place but most models are empty stubs. What exists today:

- `accounts.User` — thin `AbstractUser` extension (no extra fields yet); `AUTH_USER_MODEL` is set
- `sessions`, `equipment`, `plotting` apps — created but models are empty; no migrations beyond the `accounts` initial migration
- `archery_logger/urls.py` — only `admin/` and `accounts/` (allauth) routes wired up
- `templates/base.html` — bare HTML shell with `title`, `content`, `extra_head`, `extra_scripts` blocks

The domain models described below are the **design target**, not the current DB schema.

## Architecture & Design Principles

- **`sessions` app naming:** Django has a built-in `django.contrib.sessions` app. Our `sessions` app must be registered in `INSTALLED_APPS` as `"sessions.apps.SessionsConfig"` (not just `"sessions"`) to avoid the name collision. This is already done in `settings.py`.
- **Twelve-factor**: config via env vars (`django-environ`); no secrets in code or repo.
- **Single source of truth**: schema lives in Django models; derived state is computed, not stored, where reasonable.
- **Test-driven where it matters**: every model method, service function, and view has at least one test before it's considered done.
- **Type-specific fields go in per-type models.** When an entity has variants (bow types being the canonical example), shared fields live on the base model and variant-specific fields live in dedicated `<Variant>Setup` models linked OneToOne. **Never add nullable type-specific fields to a base table** — that's the path to spaghetti as new variants are introduced.
- **Progressive enhancement**: features work without JS where feasible; HTMX and selective JS layer interactivity on top.
- **YAGNI** — except for the multi-user readiness rules below, which are cheap now and expensive later.

## Multi-User & Scalability Rules

These habits keep the door open to a public service without slowing solo development:

- **Authenticated by default.** Every view requires login (`LoginRequiredMixin` / `login_required`). Public pages are explicit exceptions.
- **Owner-scoped queries.** Every queryset on user data is filtered by `owner=request.user` (or via a manager that enforces this). Never look up records by ID alone.
- **No filesystem assumptions.** All user uploads go through `django-storages`. Code never reads or writes user files via `open()` or absolute local paths. Local dev uses MinIO or the local filesystem backend, but the same API.
- **Async for anything slow.** Photo processing, exports, bulk analysis, email — all queued to Celery. Request handlers stay fast.
- **Stateless web tier.** No in-memory state between requests. Sessions live in Redis or the DB so the app can run multiple processes.
- **No hardcoded URLs or secrets.** Everything sensitive or environment-specific comes from env vars.
- **GDPR-aware data model.** A user must be able to export and delete all their data. Design FKs and cascades with this in mind.

## Workflow Rules

- Branch per change: `feat/<short-name>`, `fix/<short-name>`, `chore/<short-name>`.
- Before committing: run `pytest`, `ruff check .`, and `ruff format --check .`.
- Commit messages: imperative mood, short subject (e.g. "Add wind field to Session model").
- Push to GitHub regularly; open a PR even for solo work — diff review is useful.
- Never commit secrets, `.env` files, local databases, virtualenvs, or media uploads.
- Schema changes: generate and check in the migration alongside the model change in the same commit.
- Don't add new dependencies without discussing first; the dep list should stay small.

## Infrastructure (planned, not all needed for v1)

- **CI:** GitHub Actions running tests + lint on every push, blocking merge on failure.
- **Error monitoring:** Sentry from the first deploy.
- **Email:** transactional provider (Postmark, Resend, or SES) for verification, password reset, notifications.
- **Hosting:** start on Fly.io, Railway, or Render — managed Postgres + Redis, simple deploy. Larger clouds only if/when needed.
- **Backups:** automated daily Postgres backups; periodic restore drills.
- **Rate limiting:** `django-ratelimit` on auth and upload endpoints.
- **Security headers + HTTPS:** `django-csp`, secure cookies, HSTS in prod.

## Open Questions / Decisions Pending

- Subjective scale granularity (3-point vs. 5-point) and storage type (ordinal integer vs. enum string).
- Photo-based arrow plot detection: pure CV, user-assisted clicking, or hybrid.
- Whether to track per-arrow scores, per-end scores, or just session aggregates.
- Whether the arrow-plot UI warrants pulling in React early or whether HTMX + a small JS library suffices.
- Whether to evolve bow components into first-class `Equipment` entities (tracking purchase date, retirement, swapping between bows) — currently kept as free-text strings on the Setup model.

## Notes for Claude

- This is a personal project that may evolve into a small public service. Code should be solo-friendly but never preclude that path.
- When adding fields to existing models, generate the migration in the same change.
- When schema or domain changes, update the Domain Model section of this file.
- Ask before introducing new third-party dependencies.
- If a request is ambiguous, ask before guessing — the concept is still in flux.