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

## Form patterns

- **Required fields** — small "Required" pill badge next to the label
- **Helper text** — small gray text under the label
- **Draw weight** — decimal field with `step="0.5"`, so the up/down arrows step in half-pound increments
- **Disabled-until-changed** — the "Accept changes" button in the modify modal is disabled until the user actually changes a field (JavaScript change detection comparing current values to a snapshot of the originals)

---

## Bow model

Currently scoped to **Olympic Recurve only**. The Bow model includes these optional text fields for component brand/model info:

- Riser, Limbs, Arrow rest, Sight, Main stabilizer, Extender, Side stabilizers, V-bar, Clicker, Button (plunger)

### Future: other bow types
Planned: barebow, longbow, horsebow. When adding these:
- Some components are bow-type-specific (e.g., counter weight = barebow only; clicker = Olympic only; riser/limbs/button = shared across recurve-style bows)
- Maintain a `NOTES.md` listing which components belong to which bow types
- A small amount of JavaScript will conditionally show/hide fields based on the selected bow type

---

## Testing

Current tests cover models, views, form validation, and URL routing. JavaScript-driven UI flows (modal interactions, form-state behavior) are verified manually via documented scenarios in each feature prompt.

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

---

## What's next (some natural follow-ups)

- **Training sessions** — the actual "training journal" core feature: log shots, scores, notes
- **Quick-delete from the bow list** — a small icon next to each row so you don't have to open Modify just to delete
- **Other bow types** — barebow first, with the `NOTES.md` pattern and conditional fields
- **Statistics & graphs** — once there's data to visualize
- **Multi-user / auth** — if you ever decide to share the app
