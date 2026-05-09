# Single-user mode — breadcrumbs for future multi-user

This app currently runs as a single-user local tool with no login required.
The following areas would need to change to reintroduce multi-user support:

## Models
- `equipment.Bow` — add `owner = ForeignKey(settings.AUTH_USER_MODEL, on_delete=CASCADE, related_name="bows")`
- Any future `sessions.Session`, `plotting.ArrowPlot`, etc. — add `owner` FK on creation
- Every queryset on user-owned data must be filtered by `owner=request.user`; never look up by ID alone

## Views
- `sessions.views.HomeView` — add `LoginRequiredMixin` (and all future views)
- All views: use `get_queryset()` scoped to `request.user`

## URLs
- Restore `path("accounts/", include("allauth.urls"))` in `archery_logger/urls.py`

## Settings (`archery_logger/settings.py`)
- Add back to `INSTALLED_APPS`: `"django.contrib.sites"`, `"allauth"`, `"allauth.account"`, `"allauth.mfa"`
- Add back to `MIDDLEWARE`: `"allauth.account.middleware.AccountMiddleware"`
- Add back `AUTHENTICATION_BACKENDS` with the allauth backend
- Add back `SITE_ID`, `ACCOUNT_LOGIN_METHODS`, `ACCOUNT_SIGNUP_FIELDS`, `ACCOUNT_EMAIL_VERIFICATION`, `LOGIN_REDIRECT_URL`, `ACCOUNT_LOGOUT_REDIRECT_URL`, `EMAIL_BACKEND`

## Dependencies (`pyproject.toml`)
- Re-add `django-allauth[mfa]` and run `uv sync`

## Factories / Tests
- Restore `UserFactory` import and `owner = SubFactory(UserFactory)` in `equipment/tests/factories.py`
- Restore owner-scoped tests in `equipment/tests/test_models.py`
