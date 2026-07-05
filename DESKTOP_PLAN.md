# Katte — Desktop Adaptation Plan

**Target:** make `katte/index.html` (single self-contained file, no build step — keep it that way) work as a proper desktop site while leaving the mobile experience byte-for-byte identical below the breakpoint.

**Executor notes:** All work happens in `index.html` only. The app is vanilla JS + one `<style>` block. There is a static server config in `.claude/launch.json` (`katte`, port 4173). Verify at 375×812 (must look unchanged) and 1280×800 / 1440×900.

---

## Non-negotiable design rules (owner has explicitly rejected violations)

1. **No gradient/fade masks, ever.** Sticky/fixed bars are solid `var(--paper)` or `var(--card)` with a ~1px hairline divider (`#221c1410`–`#221c141c`) and at most one soft shadow.
2. **No emoji.** Flat line SVG icons only — an `icon(name)` helper + `ICONS` map already exist in the JS. Add new icons to that map in the same 24×24, stroke-only, `currentColor` style (stroke-width 1.7, round caps).
3. **Corner radii match the cards**: 14–18px. Nothing fully-rounded (99px pills rejected), nothing near-black/"loud" as chrome (ink dock rejected).
4. Warm paper/ink palette via existing CSS variables. Fonts: Fraunces (display) + Schibsted Grotesk (body). Don't introduce new colors or fonts.
5. Generative kolams appear whole — **no line-drawing animation**, except the sign-in `signdraw` animation which is intentional and stays.

---

## Phase 1 — Breakpoint scaffolding

- Single breakpoint: `@media (min-width: 900px)` (define once; use everywhere). Below 900px, zero changes.
- `.shell`: on desktop, `max-width: 1080px`, keep centered, keep side hairline borders.
- Add desktop-only hover states behind `@media (hover:hover) and (min-width:900px)`: `.pcard`, `.chanrow`, `.acct`, `.scard`, `.chip`, `.mini`, `.setrow` get a subtle lift — `border-color: var(--ink)` or `background: var(--paper)`; no new shadows beyond what cards already use.

## Phase 2 — Navigation: bottom dock → left rail

- `nav.tabs` at ≥900px becomes a **fixed left sidebar**: `position:fixed; left: calc(50% - 540px + 16px); top: 96px; bottom:auto; width: 190px; flex-direction: column; padding: 8px; border-radius: 16px;` same card bg, hairline border, soft shadow (reuse the exact values already on `nav.tabs`).
- Buttons become horizontal rows: `flex-direction: row; justify-content: flex-start; gap: 10px; padding: 11px 14px; font-size: 13px;` icon `font-size:18px`. Active state: keep ink text; move the terracotta dot to the **left edge** (`::after` repositioned: `left:6px; top:50%; transform:translateY(-50%)`) or use a `background: var(--paper-2)` fill — pick one, not both.
- `main` gets `margin-left: 210px` at ≥900px so content clears the rail. `header.appbar` spans the content column only (it lives inside `#app`; give it the same margin-left or restructure with a desktop grid on `#app`: `grid-template-columns: 210px 1fr`).
- `#app{padding-bottom:112px}` → desktop `padding-bottom: 40px` (no bottom dock to clear).

## Phase 3 — Per-view desktop layouts (all pure CSS where possible)

- **Today (`#v-today`)**: two-column grid at ≥900px: `grid-template-columns: 1fr 1fr; gap: 24px`. Left: `.mystatus` + office hours (`.oh`). Right: "On the katte right now" (`#aroundList` + its `h2.sec`). Wrap sections in two `<div>`s if needed — minimal HTML touch.
- **People (`#v-people`)**: `#peopleList` becomes `display:grid; grid-template-columns: 1fr 1fr; gap: 12px` (`.pcard` has `margin-bottom:10px` — zero it out inside the grid).
- **Work Pie (`#v-pie`)**: `.piewrap` (donut+legend) and `.logform` side by side in a 2-col grid; `.eqv` full width beneath; ledger below. Pie can scale to 190px on desktop (it's SVG).
- **Me (`#v-me`)**: cap content at `max-width: 560px; margin: 0 auto`. The `.mekolam` square stays full width of that column.

## Phase 4 — Adda master-detail (the only structural change)

Goal: on desktop, channel list (left, ~320px) and thread (right) visible **simultaneously**.

- Wrap `#v-adda` and `#v-channel` in a shared parent `<div id="addaWrap">` (they are adjacent siblings already). At ≥900px, when either is `.active`, show both: `#addaWrap{display:grid; grid-template-columns: 320px 1fr; gap: 24px}`.
- JS: add `const isDesktop = () => matchMedia("(min-width:900px)").matches;`
  - In `openChannel()` / `openDM()`: on desktop, do **not** remove `.active` from `#v-adda` — only from other views. Keep the Adda tab highlighted.
  - In `go("adda", …)`: on desktop, if no channel is open yet, auto-open the first channel (`allChannels()[0]`) so the right pane isn't empty; or show a quiet empty state (`"Pick an adda"` in italic ink-faint).
  - `#backToAdda` (`.backbtn`): hide at ≥900px (`display:none`) — the list is always visible.
  - Highlight the open channel's `.chanrow` on desktop (add/remove an `.open` class in `openChannel`/`openDM`; style: `border-color: var(--ink); background: var(--paper)`).
- **Composer & lockedbar**: they are `position:fixed` + centered with `max-width:430px` — wrong for a right-hand pane. At ≥900px switch both to `position:sticky; bottom:0` **inside** `#v-channel` (they're already children of it), full width of the pane, solid paper bg + hairline top (already the style). Remove the 112px spacer's effect at desktop (`#v-channel > div[style*="height"]` → set a class instead of inline style so CSS can zero it at ≥900px).
- On breakpoint cross (resize), state stays consistent because `.active` classes are only additive on desktop; test both directions.

## Phase 5 — Sign-in at desktop width

- `#signin` fills `.shell` (up to 1080px). `renderSigninKolam()` already measures `#signin` live and re-renders on resize — but `cols` is hardcoded to 9. Make cell size roughly constant instead: `const cols = Math.max(9, Math.round(W/46));` so the weave stays fine-grained at 1080px rather than ballooning.
- `.hero` text: keep `max-width` (~340px) but move the block off-center-left with generous left padding at ≥900px (`padding-left: 8vw`) — the kolam fills the rest (blocked-cell reservation handles it automatically since text boxes are measured).
- `.gbtn`: cap width at 380px, keep centered (or align with hero column — executor's judgement, keep it calm).
- Account picker `.sheet`: at ≥900px, render as a centered modal card instead of bottom sheet: `bottom:auto; top:50%; left:50%; transform:translate(-50%,-50%); width: 420px; border-radius: 22px; border-bottom: 1.5px solid var(--ink);` same for `#chanSheetWrap`'s sheet.

## Phase 6 — Fixed-element sweep & QA

- `#toast`: at ≥900px anchor `bottom: 32px` (no dock).
- Grep for every `position:fixed`/`position:sticky` and confirm desktop anchoring: `header.appbar`, `nav.tabs`, `.composer`, `.lockedbar`, `#toast`, `.sheetwrap`.
- **Checklist** (use the preview server, viewport presets):
  1. 375×812: pixel-identical to current mobile (spot-check Today, Adda list, a channel thread, Work Pie, Me, sign-in).
  2. 1280×800 signed out: kolam fills, text zones clear, button sane.
  3. Sign in → rail nav works, all five views lay out per Phase 3.
  4. Adda: list+thread side by side; Dean lock bar and composer sit at the bottom of the thread pane; sending a message keeps scroll inside the pane sensible.
  5. Resize across 900px both ways while a channel is open — no dead/blank states.
  6. No console errors; no gradients anywhere (`grep -n "linear-gradient" `— the only allowed hits are none in chrome; radial in none).

**Out of scope:** PWA/manifest, real auth, backend, localStorage schema changes, any redesign of mobile.
