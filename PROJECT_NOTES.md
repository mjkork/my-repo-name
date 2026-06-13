# MyShots — Project Notes

A working summary of design decisions, UX patterns, and useful habits for the MyShots archery training journal. Personal to this project — not generic advice. Update as the project grows.

---

## The intent of this app
The app's job is to make the archer's own thinking better and more visible
to themselves — not to add an external coach or motivator.

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

### Fields

| Field | Type | Notes |
|---|---|---|
| `name` | CharField(100) | user-friendly session name |
| `date` | DateField | default today; backdating allowed |
| `bow` | FK → Bow (PROTECT), nullable | optional — can log without a bow; PROTECT still blocks bow deletion when sessions reference it |
| `location` | CharField choices | `indoor` / `outdoor` |
| `session_type` | CharField choices | `free_practice` only for now; structured for future expansion |
| `distance_m` | PositiveSmallIntegerField | nullable |
| `total_arrows` | PositiveIntegerField | nullable — every arrow shot (warmup + scored + cooldown) |
| `scoring_arrows` | PositiveIntegerField | nullable — subset shot at a target face for scoring; null/0 = blank-bale session |
| `target_face` | CharField choices, max_length=40 | nullable — 40 cm, 40 cm 3-spot, 60 cm, 60 cm 3-spot, 80 cm, 122 cm |
| `total_score` | PositiveIntegerField | nullable — points from the scoring arrows |
| `notes` | TextField | blank=True |

### Deferred (CLAUDE.md lists these; skipped so far by deliberate choice)
`temperature`, `wind`, `energy_before`, `energy_after` — subjective ordinal fields. Will be added in a future iteration once the scale granularity decision is made.

### Naming reconciliation vs CLAUDE.md
- `distance_m` (not `distance`) — CLAUDE.md naming preferred
- `total_arrows` (renamed from initial `arrow_count`) — now matches CLAUDE.md spec
- `date` (not `started_at`) — intentional v1 simplification; `started_at` (timezone datetime) may be added later

**CLAUDE.md is the long-term spec.** The Session model is a deliberate subset of it.

### List display and pagination

Sessions are sorted **date descending, pk descending** (most recent first). The list paginates at **10 per page** with `?page=N` URL parameter (bookmarkable). Invalid/out-of-range page values fall back gracefully (string → page 1; number > max → last page). Pagination controls are hidden when there is only one page.

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

**Zero-bows case:** if no bows exist, the bow dropdown shows only "— Leave empty —" and a small italic hint appears below it: "No bows added yet. You can leave it empty, or add one first in My Bows." (with "My Bows" linking to /mybows/.) The form is fully usable; submitting without a bow is allowed.

**Smart default:** on fresh modal open, the bow field is pre-selected to the bow from the user's most recent session (by date). Saves clicks when logging consecutive sessions with the same bow. If no sessions exist yet, or if the most recent session had no bow, nothing is pre-selected.

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
### Homepage right-side area — deliberately reserved

The right side of the homepage is intentionally empty pending the subjective variables feature. Two ideas parked for future work:

- **Next session focus card** — pulls the "key takeaway" from the most recent session and displays it as the focus/goal for the next training session. Depends on the subjective variables feature shipping first (specifically the `key_takeaway` field).
- **Achievement badges** — milestone recognition (e.g., "100 sessions", "first windy outdoor session"). Deferred until enough usage data exists to know which milestones actually feel meaningful. Requires deliberate design around trigger criteria, visual treatment, and avoiding hollow rewards.

A "recent sessions mini-list" was considered and rejected — the totals + per-bow tooltip already serve the "what have I done lately" need; a recent list would duplicate that less elegantly.

---
### Scored sessions architecture

Reached through deliberate design conversation. Recorded here because the
reasoning matters as much as the decisions — future-you should know *why*
we chose simplicity over more elaborate alternatives.

**Prompt 1 SHIPPED** — scoring fields exist on the Session model and form.
See Session fields table above.

**Core decision: one unified Session model, not multiple session types.**

Rejected alternatives:
- Inheritance (BlankBaleSession / StructuredSession / CompetitionSession) —
  unnecessary complexity for a single-user app at this scale.
- Separate Scoring model in 1:1 relationship with Session — over-engineered;
  optional fields on Session itself are simpler to query, display, and reason
  about.
- Three-phase modeling (warmup_arrows / scored_arrows / cooldown_arrows) —
  most archers don't formally separate phases. Forcing structure creates
  friction for the most common use case.

**The simplification: two arrow counts.**

- `total_arrows` — every arrow shot in the session (target + non-target).
- `scoring_arrows` — the subset shot at a target face (what the score
  is based on).
- The difference (`total_arrows - scoring_arrows`) implicitly captures
  warmup + cooldown + blank-bale arrows, without forcing the archer to
  break it down.
- Pure blank-bale sessions: `scoring_arrows = 0` or null.
- Pure scored sessions: `scoring_arrows = total_arrows`.
- Mixed sessions (warmup + scored + cooldown): the most common case; user
  enters the two numbers naturally.

**No `session_type` field.**

The data shape reveals the session's nature:
- `scoring_arrows > 0` → a scored session.
- `scoring_arrows null or 0` → a blank-bale session.

No need for an enum the user has to pick. Filtering and display logic
queries the data itself. If a casual user-facing tag is wanted later
("competition prep day", "technique session"), it can be added as free-text
metadata — but it's not architecture.

**Target face by distance — static dict, not a model (STILL PENDING — Prompt 2):**
### Target face — deliberate non-constraint by distance

**Decision: target face is fully archer's choice at any distance. No
JavaScript filtering, no validation, no per-distance constraint.**

Reasoning (this came up after Prompt 1 shipped, when a constraint feature
was on the radar for Prompt 2):

- "Official" WA target-face-by-distance pairings (e.g., 60 cm at 30 m,
  122 cm at 70 m) do NOT match how real archers actually train.
- Beginners frequently use larger faces than their distance "should"
  warrant — 80 cm at 30 m is common.
- Age, ability, recovery from injury, kids' training, club-specific
  rules, and personal training goals all drive face choices the app
  cannot anticipate.
- Constraining choice would be patronizing AND wrong for real-world use.

**The mirror handles comparability, not the form:**

The form trusts the archer's choice. The eventual mirror feature MUST
handle face-aware comparisons correctly:

- Group/filter scores by `(distance, target_face)` together — never by
  distance alone.
- Refuse to compare or average scores across different faces at the same
  distance (e.g., 287 on 80 cm at 50 m is NOT comparable to 287 on
  122 cm at 50 m).
- Display the target face prominently in any score view so the user
  always knows what they're looking at.

This is the right division of responsibility: **the form captures
reality, the mirror is careful about apples-to-apples**.

**What was considered and rejected:**

- Per-distance dropdown filtering (JavaScript repopulates target_face
  options when distance changes): rejected — too restrictive.
- "Smart default" (suggest the official face for the chosen distance,
  user can override): rejected as over-engineering for marginal benefit.
  An archer who uses 80 cm at 30 m already knows to pick 80 cm; the
  default saves nothing.

**Status:** No further work needed. The current implementation (free
choice from the full set of target faces, optional field) is correct.
```python
TARGET_FACES_BY_DISTANCE = {
    18: ['40cm', '40cm 3-spot vertical'],
    30: ['60cm', '60cm 3-spot'],
    40: ['80cm', '122cm'],
    50: ['80cm', '122cm'],
    60: ['80cm', '122cm'],
    70: ['122cm'],
}
```

Custom distances get the full list. JavaScript repopulates the target face
dropdown when distance changes. Not yet implemented — all 6 target face
options appear regardless of distance until Prompt 2 ships.

**Scoring granularity: total score only, for now.**

- Total score: easy to enter (one number). Sufficient for most mirror
  correlations.
- Per-end and per-arrow scoring: rejected for v1. Per-end could be added
  later if needed (would enable "fatigue across the round" analysis).
  Per-arrow is probably overkill forever.

**Competition: just a scored session with optional context.**

- Not a separate model.
- Possibly a flag (`is_competition: bool`) + optional `competition_name`
  free-text field on the Session.
- Deliberately deferred until actual competition logging is happening.

**Possible rename: `Session` → `ArcherySession`**

The current model name conflicts conceptually with `django.contrib.sessions`
(the framework that handles login state) and is generic. `ArcherySession`
is more descriptive and accurate. The rename would cascade to:
- Model name, app label, URL namespace, all template references, all tests.
- Should be its own focused prompt, not bundled with the scoring fields
  addition. Cosmetic but real work.

**What's still pending from this architecture:**

- **Prompt 2** — target-face-by-distance JavaScript constraint (filter
  dropdown to valid faces for the selected distance).
- **Prompt 3** — subjective variables (all fields added to Session, form
  restructured with sections and conditional display).
- **Optional** — rename `Session` → `ArcherySession`.
- **Eventually** — the Mirror feature (analysis / correlations). Minimum
  30+ scored sessions before this is meaningful.

Each phase is shippable on its own.

---

### Subjective variables (still in design)

Initial list captured but pending further design work:

- sleep (hours), nutrition, stress, weather, temperature, wind force, wind
  direction, time of day

Open questions:

- **Polarity convention** — need to settle whether scales mean "5 = best
  for archery" or "5 = highest intensity." Currently inconsistent across
  proposed variables (nutrition uses quality direction; wind/stress use
  intensity direction). Suggested: intensity convention (5 = highest)
  because some variables (wind, stress) aren't unambiguously good or bad;
  the mirror is supposed to *discover* their effect.
- **Fatigue and physical sensations** — flagged earlier as diagnostic
  (fatigue can reveal equipment mismatch separate from sleep/nutrition).
  Worth reconsidering for inclusion in v1.
- **Variable overlap** — weather / wind / time of day may partially
  double-count each other; expect weather to be the weakest signal.
- **Session context** — target face, distance, indoor/outdoor matter
  for valid score comparisons (already captured on Session model).

The mirror's most powerful displays will pair **subjective inputs**
(sleep, stress, etc.) with **objective outputs (total_score)** — which is
why scored sessions must come first.
---
### Subjective variables — finalized design (not yet built)

Locked through deliberate design conversation. The "monster form" complexity
is accepted as the price of admission to the eventual mirror — the app is
self-selecting for archers serious enough to provide rich input data.

**The variable list:**

*Environmental (archer-independent, mostly outdoor-only):*
- `weather` — Sunny / Partly cloudy / Overcast / Rainy (choice)
- `temperature_celsius` — number, optional. Localization to Fahrenheit
  possible later.
- `wind_force` — Calm / Light / Medium / Strong / Very Strong (choice)
- `wind_direction` — from Left / Right / Front / Back / Front-Left /
  Front-Right / Back-Left / Back-Right (choice)
- `time_of_day` — Morning / Day / Afternoon / Evening (choice)

*Personal state (archer-dependent, fills in before/at start of session):*
- `nutrition` — Very Poor / Poor / OK / Good / Very Good (choice)
- `sleep_hours` — decimal/integer hours, optional
- `sleep_notes` — optional free text (captures sleep quality when the user
  wants to note it; not forced every session)
- `stress` — Very Low / Low / Medium / High / Very High (choice)

*Session experience (fills in at end of session):*
- `fatigue` — Very Low / Low / Medium / High / Very High (choice).
  Kept because it's diagnostic — high fatigue can indicate lack of sleep,
  poor nutrition, too-heavy bow, intense same-day physical exercise, or
  environmental stress (notably temperature).
- `physical_sensations` — optional free text. Captures the "language between
  archer and body" that later — with a coach or in retrospect — can pinpoint
  technique/form issues (e.g., bow-arm shoulder sensations indicating
  shoulder rises too high due to lack of strength or mobility).

**Why weather stays in (against my earlier instinct to drop it):**

- Weather does NOT reliably correlate with wind (rainy days can be calm;
  sunny days can be windy).
- Sunlight has effects beyond hitting-your-face: string reflection (many
  bowstrings are made of white/light materials, can distract aiming) and
  reflection from clothes. Experienced archers choose darker string
  materials for this reason.
- The mirror could surface non-obvious correlations like "you score lower
  on sunny outdoor days" — and a domain-aware archer can then interpret it.

**Polarity / scale convention (CRITICAL):**

Internally store all 1–5 choice fields as integers (1–5). The UI shows ONLY
the descriptive labels — the user never sees the numbers.

- Wind: 1=Calm, 5=Very Strong (intensity scale)
- Stress: 1=Very Low, 5=Very High (intensity scale)
- Nutrition: 1=Very Poor, 5=Very Good (quality scale)
- Fatigue: 1=Very Low, 5=Very High (intensity scale)

Polarity differs by variable, but that's invisible to the user. The mirror
knows per-variable polarity for correlation logic. Form rendering should
never expose numeric values.

**Conditional display (UX rule):**

Outdoor-only fields (`weather`, `temperature_celsius`, `wind_force`,
`wind_direction`) are HIDDEN when `location = indoor`. JavaScript shows
them when the user selects outdoor. Reduces form clutter for indoor
sessions and signals which variables matter when.

`time_of_day` applies to both indoor and outdoor sessions (some archers
shoot better at certain times regardless of light).

**Form layout (UX rule):**

The session form will be long (~20 fields total). Group into logical
sections:

1. **Session basics** — name, date, bow, location, session type indicators.
2. **Shooting details** — distance, total_arrows, scoring_arrows,
   target_face, total_score.
3. **Conditions** — environmental variables (collapsible, hidden when
   indoor).
4. **How you felt** — personal state + session experience (collapsible).
5. **Reflection** — notes, next_focus.

Use native `<details>`/`<summary>` for collapsible sections (already an
established pattern from the Settings page). Less-common groups default to
COLLAPSED so the form looks manageable on first glance and expands as the
user wants to fill in more.

**Form scope philosophy:**

A 20-field form is friction. That friction is acceptable because:
- Every field is OPTIONAL — users fill in what they care about.
- The eventual mirror requires rich input data to produce meaningful
  correlations. There's no shortcut.
- An archer too casual to engage with the form is also too casual to
  benefit from the mirror's eventual output.

The form's complexity self-selects for the audience the app is actually
for.

**Build sequencing (locked):**

1. **Scored sessions architecture** — ✅ SHIPPED (Prompt 1). Scoring fields
   exist on the Session model and form. `arrow_count` renamed to `total_arrows`.
   Target-face-by-distance constraint still pending (Prompt 2).
2. **Target-face-by-distance JS constraint** — Prompt 2. Filters dropdown to
   valid faces for selected distance.
3. **Subjective variables** — Prompt 3. All fields added to Session model.
   Form restructured with sections and conditional display.
4. **Mirror / analysis** — deferred until 30+ scored sessions exist. Frame
   findings as associations, not causation. Enforce minimum-N thresholds.
5. **Optional cosmetic refactor**: rename Session → ArcherySession. Separate
   focused prompt; cascades to URL namespace, templates, tests.
---
## What's next

### Next prompt (Prompt 2)
- **Target-face-by-distance constraint** — JavaScript filters the target face dropdown to only valid options for the selected distance (using the static `TARGET_FACES_BY_DISTANCE` dict). All 6 options currently show regardless of distance.

### Next major feature (Prompt 3)
- **Subjective session variables** — sleep, nutrition, stress, fatigue, time of day, wind, physical sensations. Design finalized in "Subjective variables — finalized design" section below. Form restructured with sections and conditional indoor/outdoor display.

### Earlier "next major feature" notes (superseded by the sequencing above)
- Standardize on **1–5 integer scales** (5 = best), with labels shown only in the UI.
- Make subjective fields **optional but prompted** — don't require them, don't bury them either.
- Show the user **their own historical distribution** when rating (anchors ratings to their personal scale over time, mitigates drift).
- Wind v2 idea worth revisiting: track **wind direction relative to shooting line** (head/tail/cross), not just strength.

### Polish phase (when nearing feature completion)
- **Language consistency pass** — review wording across all UI strings, modal labels, button text, hints. Avoid confusing phrasing like the earlier "No bow" example.
- **Full pytest sweep** — run `uv run pytest` manually before any significant push or milestone.

### Deferred until enough data exists
- **Analysis feature** — explicitly DO NOT build until ~30+ real sessions are logged. Correlations on <50 sessions are statistical noise. Implementation must:
  - Enforce minimum-N thresholds (refuse to compute statistics on tiny samples).
  - Frame findings as **associations, not causation** ("sessions with high sleep ratings tend to have higher self-rating" — never "sleep causes better performance").
  - Eventually consider showing the user their own historical distribution when rating (see subjective variables above).

### Future model expansion
- **Other bow types** — barebow first, then longbow and horsebow. When adding these:
  - Create/update `NOTES.md` (separate from this file) tracking which components belong to which bow types.
  - Some components are bow-type-specific (counter weight = barebow only; clicker = Olympic only; riser/limbs/button = shared across recurve-style bows).
  - Conditional field display in the form based on selected bow type.
- **Other session types** — Structured Training, Competition. When adding these, refactor `Session` to multi-table inheritance.
- **v2 session fields to consider** — `duration_minutes`, `warmup_minutes`, `equipment_changes` (separate from notes), `physical_condition` / soreness / pain.

### Eventually (no rush)
- **Statistics & visualizations** — once analysis exists and there's enough data.
- **Multi-user / auth** — if you ever share the app. Models that would need an `owner` FK if multi-user is reintroduced should be flagged in code comments.
- **Equipment as first-class entities** — purchase date, retirement tracking, swapping between bows. Migration point: the current `OlympicBowSetup` text fields would become FKs to `Equipment` records.


