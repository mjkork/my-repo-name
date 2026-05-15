# MyShots — Project Notes

A working summary of design decisions, UX patterns, and useful habits for the MyShots archery training journal. Personal to this project — not generic advice. Update as the project grows.

---

## Project at a glance

A personal Django web app for logging archery training. Runs locally as a single-user app (no auth flow). Multi-user support was refactored out for simplicity and can be added back later if the app is shared.

**Stack**: Django (Python) · SQLite · Server-rendered templates · Vanilla JavaScript · Plain CSS with custom properties.

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

### Adding quick-delete to a new list
1. Add `list-row` to the `<li>` class.
2. Wrap the main label in `<span class="list-row-main">`.
3. Add `.list-row-actions` div with the button (three data attributes as above).
4. The handler in `modals.js` picks it up automatically — no page-specific JS needed.

---

## Form patterns

- **Required fields** — small "Required" pill badge next to the label
- **Helper text** — small gray text under the label
- **Draw weight** — decimal field with `step="0.5"`, so the up/down arrows step in half-pound increments
- **Disabled-until-changed** — the "Accept changes" button in the modify modal is disabled until the user actually changes a field (JavaScript change detection comparing current values to a snapshot of the originals)

---

## Bow model

Currently scoped to **Olympic Recurve only**. The Bow model includes these optional text fields for component brand/model info:

- Riser, Limbs, Arrow rest, Sight, Main stabilizer, Extender, Side stabilizers, V-bar, Clicker, Button (plunger)

### Deletion semantics

Bows with sessions referencing them **cannot be deleted** (`on_delete=PROTECT`). If the user attempts this, `DeleteBowView` catches the `ProtectedError`, adds a Django messages-framework error message ("Cannot delete '{name}' — it's used in N session(s)..."), and redirects back to `/mybows/`. No stack trace is shown.

The error message via Django messages framework appears as a red banner at the top of the page content — the messages framework is wired into `base.html` and is available for use on any page (success, warning, error variants all have CSS).

**User's path forward:** edit the sessions blocking the deletion and set their bow to "— No bow —", then try deleting the bow again.

### Future: other bow types
Planned: barebow, longbow, horsebow. When adding these:
- Some components are bow-type-specific (e.g., counter weight = barebow only; clicker = Olympic only; riser/limbs/button = shared across recurve-style bows)
- Maintain a `NOTES.md` listing which components belong to which bow types
- A small amount of JavaScript will conditionally show/hide fields based on the selected bow type

---

## Testing

**Framework:** pytest + pytest-django (configured in `[tool.pytest.ini_options]` in `pyproject.toml`).

**Run all tests:**
```
uv run pytest
```
**Do NOT use `python manage.py test`** — it reports "Found 0 tests" because tests are written in pytest style (no `TestCase` parent class), not Django's built-in unittest style.

**Test file locations:** `tests/` folder inside each Django app (`equipment/tests/`, `sessions/tests/`), files named `test_*.py`.

**Database tests** must use the `@pytest.mark.django_db` marker.

**Why pytest:** better failure output, modern Django ecosystem standard, cleaner syntax, and a rich plugin ecosystem (pytest-cov, pytest-mock, factory_boy, etc.).

**JavaScript-driven UI flows** (modal interactions, form-state behavior) are verified manually via documented scenarios in each feature prompt — no JS test runner is configured.

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

### v1 form fields

The Add session modal exposes these fields via `SessionForm` (prefix `"session"`):

| Form field | Required | Notes |
|---|---|---|
| `name` | Yes | session name |
| `date` | Yes | HTML5 date input; defaults to today |
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

## What's next (some natural follow-ups)

- **Sessions pagination and quick-delete** — pagination + trash icon on list rows (prompt 4)
- **Sessions tests** — full test suite for the sessions app (prompt 5)
- **Other bow types** — barebow first, with the `NOTES.md` pattern and conditional fields
- **Statistics & graphs** — once there's data to visualize
- **Multi-user / auth** — if you ever decide to share the app
