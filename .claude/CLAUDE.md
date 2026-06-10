# tidy-animations — project instructions

Animated explainers for data science / ML concepts: Quarto RevealJS + anime.js,
driven by RevealJS fragments.

## Reusable animation recipes

- **`docs/recipe-ggplot2-deconstructed.md`** — the "code-deconstructed" style
  (ggplot2 code on the left; the plot lays down, explodes into one stacked
  semi-transparent card per code block, walks up highlighting each line + its
  slice, then collapses). Follow it when a user supplies a different ggplot2
  snippet and wants this treatment. Canonical impl: `examples/ggplot2-deconstructed.qmd`
  + `js/ggplot2-deconstructed.html`.

## Core convention: ONE `.qmd` PER ANIMATION

Every concept is its own self-contained deck under `examples/`, with a matching
`js/<concept>.html` animation module. Do **not** put multiple unrelated
animations in one deck — it lets fragment ids cross-fire and breaks the
"copy this slide into a real talk" goal.

## Where things live

- `_quarto.yml` — shared format defaults (theme, 1280×720 size), loads anime.js
  and the shared `js/infra.html` for *every* deck. Also has a `pre-render:
  tools/make_bundle.py --all` hook (rebuilds reuse bundles on every render) and
  `resources: [gifs/, bundles/]` (ships the GIFs and zips into `_site/`).
- `examples/<concept>.qmd` — one deck per concept. Its YAML adds the concept's own
  module via `include-after-body: [../js/<concept>.html]`.
- `js/infra.html` — shared helpers under the `TM` namespace: `TM.onReveal`,
  `TM.cssToSlide`, `TM.sectionFor`, `TM.gate`.
- `js/<concept>.html` — the animation: builds DOM, calls `TM.gate(...)`.
- `css/demos.css` — shared styles + per-concept classes.
- `index.qmd` — the landing page, an **HTML website page** (`format: html`, not a
  deck). One `##` section per concept: an `<iframe class="deck-embed">` embedding
  the rendered deck, followed by a `.gif-link` line with four links — *Open full
  deck*, *View as GIF* (`gifs/<concept>.gif`), *View as MP4* (`mp4/<concept>.mp4`),
  and *Download reusable bundle* (`bundles/<concept>.zip`).
- `gifs/<concept>.gif` — committed GIF capture (see capture section).
- `mp4/<concept>.mp4` — committed MP4 capture (same recorder, see capture section).
- `bundles/<concept>.zip` — **generated, but committed** (we push the rendered
  site). Built by `tools/make_bundle.py` from `js/infra.html`, `js/<concept>.html`,
  `css/demos.css`, and `examples/<concept>.qmd`. Don't edit by hand — re-run the
  script (the pre-render hook does this automatically on `quarto render`).

## How an animation module works

Call `TM.gate({ markerClass, fragmentIds, render })`. Write `render(stage)` to be
**idempotent**: `stage` is the count of currently-visible gating fragments, and
`render` sets the target visual state for that stage. Idempotence is what makes
forward nav, back nav, and direct-link/reload arrival all work without special
cases.

Property ownership: CSS owns layout/structure; anime.js owns `transform`,
`opacity`, `background-color`. Never animate the same property from both systems.

**Always drive animations through `TM.anime(...)` (not bare `anime(...)`) and time
gaps with `TM.pause(ms, fn)` (not bare `setTimeout`).** These keep a busy counter
so `TM.idle()` reports when the deck has settled — that's what lets
`tools/capture_recordings.py` pace a GIF/MP4 to the real animation durations instead of
guessing. `anime.set` / `anime.stagger` are instant/static and need no wrapping.

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

## Build segment by segment — don't write the whole animation at once

The best results come from building **one stage (segment) at a time** and
verifying it in the browser before moving to the next. Trying to author every
fragment in one pass produces tangled `render(stage)` logic and bugs that are
hard to localize. Instead, work the loop below for each segment in order:

1. **Agree on the segment list first.** Before writing code, lay out the ordered
   list of stages (stage 0 = slide arrival, stage 1 = first fragment, …) and what
   the visual should look like at each. Confirm this with the user — it's the spec
   the rest of the work follows.
2. **Build stage 0 only**, get the static starting layout right, verify it in the
   browser, *then* move on. Don't scaffold later stages yet.
3. **Add one fragment + its `render(stage)` branch at a time.** Implement the
   transition into the new stage, leave the higher stages unhandled for now.
4. **Verify that segment both ways before continuing:** forward nav into it, and
   back-nav out of it (idempotence). A segment isn't done until back-nav restores
   the previous stage cleanly.
5. **Only then start the next segment.** Re-run `quarto preview` and repeat.

When the user says "let's go segment by segment," treat each segment as a
checkpoint: implement it, show/verify it, and pause for confirmation before
starting the next rather than racing ahead to the final stage.

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

## Adding a new example (keep the site in sync)

When you add `examples/<concept>.qmd` + `js/<concept>.html`, also do these so the
website, GIF, and bundle stay complete — it's easy to forget the last three:

1. Build the deck + module + any `.<concept>-*` CSS in `css/demos.css`.
2. **Capture the GIF and MP4** → `gifs/<concept>.gif` + `mp4/<concept>.mp4` (see
   capture section below; same recorder, just swap the `--out` extension).
3. **Add a `##` section to `index.qmd`** — copy an existing section and swap the
   concept name in the iframe `src` and all four links (deck, gif, mp4, bundle).
4. **No `_quarto.yml` change needed** for the bundle: `make_bundle.py --all`
   auto-discovers any `examples/*.qmd` that has a matching `js/*.html`, and the
   pre-render hook runs it. Just `quarto render` and commit the new
   `bundles/<concept>.zip`.
5. Run `quarto render` and verify the new section renders, the iframe loads, and
   all four links resolve (`_site/gifs/...`, `_site/mp4/...`, `_site/bundles/...`).

## Build / preview

- `quarto preview examples/<concept>.qmd` — single deck, live reload (use for iterating).
- `quarto render` — whole site.

Always verify animations in a real browser — surface checks (HTTP 200, classes
present) won't catch behavioural bugs in shared helpers.

## Capturing a GIF or MP4 (`tools/capture_recordings.py`)

**Don't capture the GIF or MP4 until the user has confirmed they're happy with
the final design.** Iterate on the animation in the browser first; only run the
recorder once the design is signed off.

The output format is chosen from the `--out` extension: `.mp4` encodes H.264
(`libx264`, `yuv420p`, faststart; `--crf` tunes quality, default 18); anything
else produces a GIF. Both share the same frame capture, so commit both per deck.

```bash
quarto render examples/<concept>.qmd   # capture from the rendered _site/ copy
python3 tools/capture_recordings.py \
  --deck _site/examples/<concept>.html --slide 1 \
  --steps <fragments + 1> \
  --selector .<concept>-stage-wrap \
  --out gifs/<concept>.gif
# repeat with --out mp4/<concept>.mp4 for the MP4
```

- **`--steps` must be `(number of gating fragments) + 1`.** The first `ArrowRight`
  lands on the slide (stage 0) rather than advancing a fragment, so a 4-fragment
  deck needs `--steps 5` to reach the final stage. If the last frame stops one
  stage short, this is why.
- `--slide 1` is the content slide (slide 0 is Quarto's title slide).
- `--selector` is the deck's stage wrapper (e.g. `.bs-stage-wrap`); the recording
  is cropped to it.
- Verify the result by extracting frames with ffmpeg (first/mid/last) and reading
  them — don't trust that the run "succeeded".
