# MyShots — Project Notes

A working summary of design decisions, UX patterns, and useful habits for the MyShots archery training journal. Personal to this project — not generic advice. Update as the project grows.

---

## Project at a glance

A personal Django web app for logging archery training. Runs locally as a single-user app (no auth flow). Multi-user support was refactored out for simplicity and can be added back later if the app is shared.

**Stack**: Django 5.x (Python 3.12+) · SQLite · Server-rendered templates · Vanilla JavaScript · Plain CSS with custom properties.

**Package manager**: `uv`. Key commands:
```
uv run python manage.py runserver   # dev server
uv run pytest                       # run all tests
uv run ruff check . && uv run ruff format --check .   # lint + format check
uv run python manage.py makemigrations && uv run python manage.py migrate
```

### Django apps

| App | Label | Purpose |
|---|---|---|
| `accounts` | `accounts` | Custom `User` model (extends `AbstractUser`, no extra fields yet). `AUTH_USER_MODEL` is set. |
| `sessions` | `practice_sessions` | Training sessions CRUD. Label is **`practice_sessions`**, not `sessions`, to avoid clash with Django's built-in `django.contrib.sessions` middleware. All URL `{% url %}` calls and `reverse()` calls must use the `practice_sessions:` prefix. |
| `equipment` | `equipment` | Bows and type-specific component setups (`OlympicBowSetup`). |
| `plotting` | `plotting` | Arrow-plot photo detection — stub only, models empty, no functionality yet. |

The `sessions` app must be registered in `INSTALLED_APPS` as `"sessions.apps.SessionsConfig"` (not bare `"sessions"`) so Django picks up the custom app label.

---

## Visual identity

The app intentionally blends two aesthetics: a **classical brand** (the header) and **modern UI** (the buttons and modals inside the page).

### Header
- Custom SVG banner at the top of every non-homepage view
- Earthy palette: forest green (`#2d4a2e`) to warm brown (`#4a3826`)
- Aged-gold accents (`#c9a961`, `#b8965a`)
- Serif typography (Georgia)
- Decorative double border, longbow + target ornaments
- Wide aspect ratio (2000×100) so it stays slim across screen sizes

### Body UI
- Sans-serif font throughout (system font stack)
- CSS custom properties for theming — change a variable, retune everything
- Modern, clean look inspired by the reference designs you supplied

---

## Page heading rows

When a page pairs a heading with a primary action button (e.g., "My Bows" + "Add new bow"), use the `.page-heading-row` class on the wrapper div.

**Rule:** The heading and its action button MUST appear close together on the left, using `.page-heading-row`. Do NOT use `justify-content: space-between` or `margin-left: auto` to push the action to the opposite edge. The heading and its primary action should feel paired, not separated — this is a deliberate UX choice.

When adding a new page with this shape, reuse `.page-heading-row` rather than reinventing the layout. The rule is also encoded as a comment directly in the CSS.

---

## Button system

All buttons share the same shape, height, padding, and rounded/pill corners. Only the color differs.

| Variant | When to use | Color |
|---|---|---|
| Primary | Main actions (Add new bow, Accept changes) | Blue → teal gradient |
| Secondary | Cancel, Close | Outlined, neutral |
| Home / Nav | Return to homepage | Medium green gradient |
| Destructive | Delete, Remove | Red gradient |

No icons on buttons currently. New variants (e.g., a warning yellow) can be added the same way.

---

## Modal system

Every modal in the app follows a shared pattern.

### Universal close behavior
All modals can be closed via:
- The X icon
- Clicking the backdrop outside the modal
- Pressing Esc
- Any explicit Cancel/Close button inside

### Modal types
- **View** — read-only display, opens when a bow name is clicked
- **Add** — form for new bow
- **Modify** — pre-populated form for editing
- **Confirmation** — reusable component with a small alert icon next to the title; accepts title, body, primary/secondary button labels and actions

### Form reset on dismiss
When any form-containing modal is dismissed (Cancel/X/outside/Esc), the form resets to its initial state (empty for Add, original DB values for Modify). This is baked into the shared modal infrastructure so every future form modal inherits the behavior automatically.

### Cancel-in-confirmation behavior — intentionally asymmetric
- **Accept changes → Cancel** → modify form *preserves* edits ("still editing, just not ready to save yet")
- **Delete → Cancel** → modify form *resets* to original ("I was about to delete; changing my mind should leave me in a clean state")

---

## List row pattern (.list-row)

Any list in the app can have inline quick-action buttons (e.g., a quick-delete trash icon) using this reusable system.

### HTML structure
```html
<li class="your-list-item list-row" data-...>
    <span class="list-row-main">Item name</span>
    <div class="list-row-actions">
        <button type="button"
                class="list-row-action list-row-action--danger"
                aria-label="Delete session"
                data-delete-url="/sessions/42/delete/"
                data-delete-name="2024-05-12 outdoor session"
                data-delete-label="session">
            <!-- inline SVG trash icon, 16×16, stroke="currentColor" -->
        </button>
    </div>
</li>
```

### How the JS handler works
A single `document`-level click listener in `modals.js` catches all `.list-row-action--danger` clicks anywhere in the app. It reads the three `data-delete-*` attributes, opens the reusable confirmation modal with the correct label and name, and on confirm POSTs to the delete URL via a dynamically created form (CSRF token copied from any existing form on the page).

### Optional secondary context in the confirmation message

The JS handler also reads an optional `data-delete-context` attribute. When present, the confirmation body becomes:

> Are you sure you want to delete "{name}" from {context}? This action cannot be undone.

When absent, the simpler form is used (same as bows). Use this for any list where a second piece of context (e.g., a date) makes the confirmation clearer.

```html
data-delete-context="{{ session.date|date:'j F Y' }}"
```

### Adding quick-delete to a new list
1. Add `list-row` to the `<li>` class.
2. Wrap the main label in `<span class="list-row-main">`.
3. Add `.list-row-actions` div with the button (three or four data attributes as above).
4. The handler in `modals.js` picks it up automatically — no page-specific JS needed.

---

## Form patterns

- **Required fields** — small "Required" pill badge next to the label
- **Helper text** — small gray text under the label
- **Draw weight** — decimal field with `step="0.5"`, so the up/down arrows step in half-pound increments
- **Disabled-until-changed** — the "Accept changes" button in the modify modal is disabled until the user actually changes a field (JavaScript change detection comparing current values to a snapshot of the originals)

---

## Bow model

Currently scoped to **Olympic Recurve only**.

### Base `Bow` fields

| Field | Type | Notes |
|---|---|---|
| `name` | CharField(200) | User's nickname, e.g. "Blue Hoyt" |
| `type` | CharField choices | `olympic_recurve` only for now |
| `length_inches` | PositiveSmallIntegerField, nullable | Optional; validated 40–80 inches (covers horsebow to longbow). Form datalist suggests 68, 70 (Olympic Recurve typical). Datalist suggestions will vary per bow type when other types are added. |
| `draw_weight_lbs` | DecimalField(5,1), nullable | Optional; `step="0.5"` in the form UI |
| `notes` | TextField | blank=True |

Default ordering: by `name` ascending (`Meta.ordering = ["name"]`).

### `OlympicBowSetup` — 1:1 with Bow

All fields are optional free-text strings (user fills brand/model/details however they like):
riser · limbs · arrow_rest · sight · main_stabilizer · extender · side_stabilizers · v_bar · clicker · button

This model is the migration point if components ever become first-class `Equipment` entities (purchase date, retirement tracking, swapping between bows).

### Deletion semantics

Bows with sessions referencing them **cannot be deleted** (`on_delete=PROTECT`). If the user attempts this, `DeleteBowView` catches the `ProtectedError`, adds a Django messages-framework error message ("Cannot delete '{name}' — it's used in N session(s)..."), and redirects back to `/mybows/`. No stack trace is shown.

The error message via Django messages framework appears as a red banner at the top of the page content — the messages framework is wired into `base.html` and is available for use on any page (success, warning, error variants all have CSS).

**User's path forward:** edit the sessions blocking the deletion and set their bow to "— Leave empty —", then try deleting the bow again.

### Future: other bow types
Planned: barebow, longbow, horsebow. When adding these:
- Some components are bow-type-specific (e.g., counter weight = barebow only; clicker = Olympic only; riser/limbs/button = shared across recurve-style bows)
- Maintain a `NOTES.md` listing which components belong to which bow types
- A small amount of JavaScript will conditionally show/hide fields based on the selected bow type
- The `length_inches` datalist suggestions should also vary by type: Olympic 68/70; longbow 60–72; traditional 58–62; horsebow 42–54

---

## Testing

**Framework:** pytest + pytest-django (configured in `[tool.pytest.ini_options]` in `pyproject.toml`).

**Run all tests:**
```
uv run pytest
```
**Do NOT use `python manage.py test`** — it reports "Found 0 tests" because tests are written in pytest style (no `TestCase` parent class), not Django's built-in unittest style.

**Test file locations:** `tests/` folder inside each Django app (`equipment/tests/`, `sessions/tests/`), files named `test_*.py`. Classes do not inherit from `TestCase`. Database tests use `@pytest.mark.django_db`.

**Why pytest:** better failure output, modern Django ecosystem standard, cleaner syntax, and a rich plugin ecosystem (pytest-cov, pytest-mock, factory_boy, etc.).

**JavaScript-driven UI flows** (modal interactions, form-state behavior) are verified manually via documented scenarios in each feature prompt — no JS test runner is configured.

### Three-tier testing strategy

- **Tier 1 — new functionality:** every prompt that adds a feature writes tests for that feature and runs the app's test subset. Token-efficient.
- **Tier 2 — shared infrastructure:** any prompt that touches shared infrastructure (CSS variables, `modals.js`, `base.html`, anything documented in the Patterns sections of this file) runs the **full** `pytest` suite to catch regressions across apps.
- **Tier 3 — milestone:** run `uv run pytest` manually at the end of each feature and before any push to GitHub. Free, catches anything the Claude Code summary glossed over.

---

## Working with Claude Code — habits that have paid off

### Before every risky change
```
git add -A && git commit -m "before <feature>"
```
Cheap rollback safety net.

### Ask for a plan before code
Most feature prompts include "plan first, don't change code yet, ask any clarifying questions." For a non-dev, this catches misunderstandings before they turn into 30 file edits to undo.

### Ask before guessing
Every prompt includes "if anything is ambiguous, stop and ask rather than guessing." Especially important when you can't quickly review code yourself.

### Screenshots beat paragraphs
When something looks wrong, a screenshot tells Claude Code far more than a description.

### Verification scenarios live in the prompt
List the exact manual flows you'll test, in the prompt itself. Claude Code uses them to self-verify, and you get a checklist to walk through.

### Hard refresh after CSS/JS changes
`Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac) bypasses the browser cache.

### Treat reusable patterns as architecture, not features
When something will recur (modal close behavior, form reset, confirmation dialogs, button styles), build it once into shared infrastructure rather than copying it per page. This has saved a lot of churn already.

### Split large features into sequential prompts
For complex features (model → CRUD → pagination → tests), breaking the work into 4–5 sequential prompts — each scoped to a specific layer — keeps token usage manageable and each prompt reviewable before continuing. A good split: (1) model + scaffold, (2) add flow, (3) edit/delete, (4) pagination + polish, (5) tests.

### Event propagation: belt-and-suspenders for parent + child click handlers
When a parent element (e.g., a list row `<li>`) has a direct click listener AND it contains child action buttons (e.g., a delete icon) handled via event delegation on `document`, there is a subtle ordering trap:

- The `<li>` listener fires **during DOM bubbling**, before the event reaches `document`.
- By the time the `document` handler calls `e.stopPropagation()`, the `<li>` handler has already run.
- Result: both the row action AND the row's main handler fire — in this case, both the delete confirmation AND the view modal open.

The fix requires **both** defenses:
1. `e.stopPropagation()` in the document-level handler — hygiene, and works correctly if the parent also uses delegation.
2. `if (e.target.closest('.list-row-action')) return;` at the top of the parent's direct handler — the actual guard.

Neither alone is bulletproof; together they cover all cases and survive future refactors.

---

## Navigation

A site-wide nav bar lives in `base.html` and appears on every page except the homepage (detected via `request.resolver_match.url_name == 'home'`).

- **Contents (left-aligned):** Home (green), My Bows (blue → `equipment:mybows`), My Sessions (blue → `practice_sessions:mysessions`)
- **Active state:** the current page's button gets a colored ring via `.nav-active` class, assigned by checking `request.resolver_match.namespace` in the template
- **Homepage:** suppresses the nav entirely; uses its own in-page entry-point buttons (My Bows, My Sessions)
- **URL namespace:** the `sessions` app has `app_name = "practice_sessions"` (to avoid the Django session middleware clash); all its URL references use the `practice_sessions:` prefix

---

## Session model

Lives in the `sessions` app (`sessions/models.py`), app_label `practice_sessions`.

### v1 fields (objective only — subjective fields deliberately deferred)

| Field | Type | Notes |
|---|---|---|
| `name` | CharField(100) | user-friendly session name |
| `date` | DateField | default today; backdating allowed |
| `bow` | FK → Bow (PROTECT), nullable | optional — can log without a bow; PROTECT still blocks bow deletion when sessions reference it |
| `location` | CharField choices | `indoor` / `outdoor` |
| `session_type` | CharField choices | `free_practice` only for now; structured for future expansion |
| `distance_m` | PositiveSmallIntegerField | nullable |
| `arrow_count` | PositiveIntegerField | nullable |
| `notes` | TextField | blank=True |

### Deferred (CLAUDE.md lists these; skipped in v1 by deliberate choice)
`temperature`, `wind`, `energy_before`, `energy_after` — subjective ordinal fields. Will be added in a future iteration once the scale granularity decision is made.

### Naming reconciliation vs CLAUDE.md
- `distance_m` (not `distance`) — CLAUDE.md naming preferred
- `arrow_count` (not `total_arrows`) — CLAUDE.md naming preferred
- `date` (not `started_at`) — intentional v1 simplification; `started_at` (timezone datetime) may be added later

**CLAUDE.md is the long-term spec.** The v1 Session model is a deliberate subset of it.

### List display and pagination

Sessions are sorted **date descending, pk descending** (most recent first). The list paginates at **8 per page** with `?page=N` URL parameter (bookmarkable). Invalid/out-of-range page values fall back gracefully (string → page 1; number > max → last page). Pagination controls are hidden when there is only one page.

### v1 form fields

The Add session modal exposes these fields via `SessionForm` (prefix `"session"`):

| Form field | Required | Notes |
|---|---|---|
| `name` | Yes | session name |
| `date` | Yes | HTML5 date input; defaults to today; must be ≤ today (future dates rejected by `clean_date()` and capped by `max` attribute in the browser picker) |
| `bow` | No | select with "— Leave empty —" blank option, ordered by name; pre-selects most recently used bow on fresh open |
| `location` | Yes | select: Indoor / Outdoor |
| `distance_m` | No | number input with datalist (see below) |
| `arrow_count` | No | number input |
| `notes` | No | textarea |

`session_type` is excluded from the form and set programmatically to `free_practice` in the view.

**Distance suggestions (datalist):** 10, 18, 30, 50, 70, 90 m. Users can type any custom value; the datalist only provides suggestions.

**Zero-bows case:** if no bows exist, the bow dropdown shows only "— No bow —" and a small italic hint appears below it with a link to My Bows. The form is fully usable; submitting without a bow is allowed.

**Smart default:** on fresh modal open, the bow field is pre-selected to the bow from the user's most recent session (by date). This saves clicks when logging consecutive sessions with the same bow. If no sessions exist yet, nothing is pre-selected.

---

## Session edit and delete flow

Clicking a session row opens the **Modify session modal directly** — there is no intermediate view modal (deliberate departure from the bow flow, which goes row → view modal → modify modal). The bow flow has a view modal because bows have many read-only component fields worth browsing; sessions don't need that layer.

### Modify session modal

Mirrors the bow Modify modal mechanically:
- Pre-populated from `data-*` attributes on the clicked row (JS fills fields, no round-trip).
- **Accept changes** button is disabled on open; enables when any field changes (snapshot-based change detection).
- **Delete session** button (destructive, left footer) — same footer layout as bow modify modal.
- Cancel, X, backdrop click, Esc all close and reset the form (shared modal infrastructure).

### Asymmetric cancel rule (same as bows)
- **Accept changes → Cancel in confirmation** → edit modal stays open with user's edits intact.
- **Delete → Cancel in confirmation** → edit modal stays open with form RESET to original values.

### URLs and views
- `ModifySessionView` at `/mysessions/<pk>/modify/` — GET (re-renders with instance data) and POST (validates and saves; on success adds Django messages success and redirects).
- `DeleteSessionView` at `/mysessions/<pk>/delete/` — POST only (405 for GET); deletes and redirects with a success message.

### Django messages success feedback
`messages.success()` is now used for session updates and deletes, appearing as a green banner via the messages infrastructure wired in `base.html`. The same infrastructure handles bow deletion errors (red banner).

---

## Stat card pattern

The homepage displays two summary stat cards ("Archery sessions" and "Arrows shot") with hover/focus tooltips showing a per-bow breakdown. The `.stat-card` CSS pattern is designed for reuse on other pages (e.g., a future per-bow detail view).

### HTML structure
```html
<div class="stat-card-row">
    <div class="stat-card" tabindex="0">
        <div class="stat-card-label">Card label</div>
        <div class="stat-card-value">42</div>
        <div class="stat-card-tooltip">
            <div class="stat-card-tooltip-header">By bow</div>
            <div class="stat-card-tooltip-row">Bow name: 3 sessions · 120 arrows</div>
            <!-- or when empty: -->
            <div class="stat-card-tooltip-row stat-card-tooltip-empty">No sessions logged yet</div>
        </div>
    </div>
</div>
```

### CSS classes
| Class | Purpose |
|---|---|
| `.stat-card-row` | Flex container for the cards (gap, padding) |
| `.stat-card` | Card with beige background, 3px gold left border, `position: relative` |
| `.stat-card-label` | Small uppercase gray label |
| `.stat-card-value` | Large Georgia serif number in dark forest green (`--color-brand-dark`) |
| `.stat-card-tooltip` | Absolutely-positioned tooltip; hidden by default (`opacity: 0; visibility: hidden`) |
| `.stat-card-tooltip-header` | "By bow" uppercase header with bottom border |
| `.stat-card-tooltip-row` | One row of breakdown text |
| `.stat-card-tooltip-empty` | Italic muted variant for the zero-state message |

### Behavior
- Tooltip appears on `:hover` or `:focus-within` on the `.stat-card` (both covered by CSS).
- Cards have `tabindex="0"` so keyboard users can Tab in and trigger `:focus-within`.
- The fade is a one-liner CSS `transition: opacity 0.15s` — no JavaScript.
- Desktop-only hover design; no mobile tap fallback (deliberate).

### Stat computation (backend)
`HomeView.get_context_data()` in `sessions/views.py` runs **two queries**:
1. `Session.objects.aggregate(Count, Coalesce(Sum))` — overall totals.
2. `Session.objects.values("bow__name").annotate(Count, Coalesce(Sum))` — per-bow breakdown.

The breakdown groups by `bow__name`. Sessions with `bow=None` appear under `"(no bow recorded)"` and are always rendered last (named bows sorted by session count descending).

### Architectural decision: individual bow breakdown (not bow type)
The breakdown is grouped by **individual bow** (e.g., "Blue Hoyt: 12 sessions"). It is deliberately NOT grouped by bow type today. When multiple bow types exist, the breakdown may be refactored to a two-level view (type → bows nested). Until then, individual bow is the most useful grain.

### CSS variables added
- `--color-stat-card-bg: #f7f5ef` — warm beige card background
- `--color-brand-dark: #2d4a2e` — dark forest green (from the SVG header palette); used for stat values and available for other brand-aligned elements

---

## What's next (some natural follow-ups)

- **Sessions comprehensive tests** — full test suite for the sessions app (forms, add flow, modify/delete views, URL routing)
- **Other bow types** — barebow first, with the `NOTES.md` pattern and conditional fields
- **Statistics & graphs** — deeper analysis once 30+ sessions exist
- **Multi-user / auth** — if you ever decide to share the app
