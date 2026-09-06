---
name: infra-plan
description: Planned (not yet built) infrastructure for the archery_logger project — CI, error monitoring, email, hosting, backups, rate limiting, and security headers. Load when discussing or setting up deployment, CI/CD, monitoring, backups, or production hardening.
---

# Infrastructure (planned, not all needed for v1)

- **CI:** GitHub Actions running tests + lint on every push, blocking merge on failure.
- **Error monitoring:** Sentry from the first deploy.
- **Email:** transactional provider (Postmark, Resend, or SES) for verification, password reset, notifications.
- **Hosting:** start on Fly.io, Railway, or Render — managed Postgres + Redis, simple deploy. Larger clouds only if/when needed.
- **Backups:** automated daily Postgres backups; periodic restore drills.
- **Rate limiting:** `django-ratelimit` on auth and upload endpoints.
- **Security headers + HTTPS:** `django-csp`, secure cookies, HSTS in prod.
