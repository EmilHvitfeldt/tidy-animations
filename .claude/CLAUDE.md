# tidymodels-animated — project instructions

Animated explainers for tidymodels concepts: Quarto RevealJS + anime.js, driven
by RevealJS fragments.

## Core convention: ONE `.qmd` PER ANIMATION

Every concept is its own self-contained deck at the project root, with a matching
`js/<concept>.html` animation module. Do **not** put multiple unrelated
animations in one deck — it lets fragment ids cross-fire and breaks the
"copy this slide into a real talk" goal.

## Where things live

- `_quarto.yml` — shared format defaults (theme, 1280×720 size), loads anime.js
  and the shared `js/infra.html` for *every* deck.
- `<concept>.qmd` — one deck per concept. Its YAML adds the concept's own module
  via `include-after-body: [js/<concept>.html]`.
- `js/infra.html` — shared helpers under the `TM` namespace: `TM.onReveal`,
  `TM.cssToSlide`, `TM.sectionFor`, `TM.gate`.
- `js/<concept>.html` — the animation: builds DOM, calls `TM.gate(...)`.
- `css/demos.css` — shared styles + per-concept classes.
- `index.qmd` — landing page linking each deck.
- `IDEAS.md` — backlog of concepts to animate.

## How an animation module works

Call `TM.gate({ markerClass, fragmentIds, render })`. Write `render(stage)` to be
**idempotent**: `stage` is the count of currently-visible gating fragments, and
`render` sets the target visual state for that stage. Idempotence is what makes
forward nav, back nav, and direct-link/reload arrival all work without special
cases.

Property ownership: CSS owns layout/structure; anime.js owns `transform`,
`opacity`, `background-color`. Never animate the same property from both systems.

## Building a slide — the recipe that worked for cross-validation

1. **Stage = a fixed-size coordinate box.** Give the slide a marker class
   (`{.my-slide}`) and an empty `<div id="my-stage">` sized in CSS (e.g.
   1100×520). Build all elements in JS and position them with
   `translate(xpx, ypx)` in *that* coordinate space — never CSS flow.
2. **One fragment marker per step,** in order, in the `.qmd`:
   `[]{.fragment .cv-frag id="step-name"}`. The `.cv-frag` class makes them
   invisible (`position:absolute; pointer-events:none; opacity:0 !important`).
   `render(stage)` then keys off how many are visible.
3. **Build DOM lazily once** inside `render` (guard with `if (built) ...`), since
   the stage element may not exist when the module's IIFE first runs.
4. **Keep each stage's expensive work stable.** When a stage spawns elements
   (e.g. flying "copies"), track what's currently shown (`placedFold`-style flag)
   so re-rendering the same stage is a no-op and back-nav tears it down.

## Gotchas we actually hit (don't relearn these)

- **Theme CSS must be SCSS-layered.** `css/demos.css` is loaded as a reveal theme,
  so it needs a `/*-- scss:rules --*/` boundary or `quarto render` errors.
- **Fading in a fill flashes grey** if you animate `backgroundColor` from
  `rgba(0,0,0,0)` (transparent *black* → passes through grey). Instead fade from a
  transparent version of the element's *own* colour (see `fade(hex)` in
  `cross-validation.html`).
- **Includes are `.html` files with `<script>` tags,** not bare `.js`. anime.js is
  pinned to **v3** (v4 changed the timeline API).
- **Listeners must register without waiting for `ready`.** `include-after-body`
  scripts often load after Reveal inits, so `Reveal.on('ready', …)` may never
  fire. `TM.onReveal` / `TM.gate` already handle this — use them.
- **"Random but stable" = roll once, hardcode.** For scattered-looking layouts,
  hardcode a balanced array (e.g. `ASSIGN`, 10/10/10) rather than calling
  `Math.random()` at runtime (which differs every reload / breaks idempotence).
- **Stagger + a short `setTimeout` pause** between "old elements fade out" and
  "new elements fly in" reads much better than an instant swap (we used 350ms).

## Configurable knobs from the `.qmd`

Expose per-deck settings via a `window.*` global set in a `` ```{=html} `` block at
the top of the `.qmd`, read with a fallback in the module:

```html
<script>window.CV_COLORS = ['#8ecae6', '#90be6d', '#f9c74f'];</script>
```
```js
const COLORS = window.CV_COLORS || ['#8ecae6', '#90be6d', '#f9c74f'];
```

The body script runs before the after-body module, so the value is ready at init.

## Build / preview

- `quarto preview <concept>.qmd` — single deck, live reload (use for iterating).
- `quarto render` — whole site.

Always verify animations in a real browser — surface checks (HTTP 200, classes
present) won't catch behavioural bugs in shared helpers.
