# tidymodels, animated

Self-contained animated explainers for tidymodels concepts, built with
[Quarto RevealJS](https://quarto.org/docs/presentations/revealjs/) +
[anime.js](https://animejs.com/) and driven by RevealJS **fragments**.

## Convention: one `.qmd` per animation

Each concept lives in **its own `.qmd` deck** under `examples/` (plus a matching
animation module in `js/`). This keeps every animation copy-pasteable into a real
talk and avoids fragment ids cross-firing between concepts.

```
tidymodels-animated/
├── _quarto.yml                    # shared format defaults + anime.js + js/infra.html (loaded everywhere)
├── index.qmd                      # landing page linking to each deck
├── IDEAS.md                       # backlog of concepts to animate
├── examples/
│   └── cross-validation.qmd       # one concept = one deck
├── css/
│   └── demos.css                  # shared styles + per-animation classes
└── js/
    ├── infra.html                 # shared helpers: TM.onReveal, TM.cssToSlide, TM.sectionFor, TM.gate
    └── cross-validation.html      # the CV animation module (one per deck)
```

### Adding a new animation

1. Add a row to `IDEAS.md` (or pick one from the backlog).
2. Create `js/<concept>.html` — a `<script>` that builds its DOM and calls
   `TM.gate({ markerClass, fragmentIds, render })`. Write `render(stage)` to be
   **idempotent**: given the number of visible fragments, it sets the target
   state. That makes forward nav, back nav, and direct-link arrival all work.
3. Create `examples/<concept>.qmd` whose YAML pulls the module in via its own
   `include-after-body: [../js/<concept>.html]`. (Shared `infra.html` is already
   loaded globally from `_quarto.yml`.)
4. Mark the animated slide with a unique class (e.g. `{.cv-slide}`) and add
   invisible `.fragment` markers with ids the module gates on.
5. Add any concept-specific CSS to `css/demos.css`.
6. Link the new deck from `index.qmd`.

## Build / preview

```bash
quarto preview examples/cross-validation.qmd   # single deck with live reload
quarto render                          # build the whole site
```

## Capturing a deck as a GIF

`tools/capture_gif.py` drives a rendered deck headlessly with Playwright,
advancing through the fragments, then assembles a looping GIF. It does **not**
guess delays: each animation module reports busy/idle through `TM.anime` /
`TM.pause`, and the recorder waits for `window.TM.idle()` — so it samples densely
*while* something is animating and lets static holds collapse to a single
long-duration frame, paced to the real animation durations.

Frames are captured as **lossless PNG screenshots** (not lossy video), so the flat
background is pixel-identical between frames. That means no compression speckle,
*and* it lets the final `gifsicle -O3` pass losslessly diff-compress and dedup the
hold frames — shrinking the file dramatically (the cross-validation GIF is ~0.8 MB
this way vs ~6 MB from a video capture).

```bash
pip install playwright && playwright install chromium   # one-time
# also requires ffmpeg, and gifsicle for the lossless pass (brew install gifsicle)
quarto render examples/cross-validation.qmd              # GIF records the rendered _site/ output

python tools/capture_gif.py \
    --deck _site/examples/cross-validation.html \
    --slide 2 --steps 5 \
    --out gifs/cross-validation.gif
```

- `--slide` is the Reveal slide index the animation lives on; `--steps` is the
  number of fragment advances to record.
- `--selector` (default `.cv-stage-wrap`) is the element the GIF is cropped to.
- Pacing knobs: `--dwell` (hold after each step), `--start-hold`, `--end-hold`.
- Output knobs: `--fps`, `--scale` (output width), `--pad`. Lower `--fps`/`--scale`
  to shrink further; `--no-optimize` skips the gifsicle pass.

## Reusing an animation in your own deck

Each animation is self-contained. To drop the cross-validation slide into another
Quarto RevealJS presentation, you need four things: **anime.js**, the shared
**`js/infra.html`**, the animation's **`js/<concept>.html`**, and its **CSS**.

The quickest route is the **reusable bundle**: each concept on the landing page has
a *Download reusable bundle* link (a zip with those files, the example `.qmd`, and a
wiring README). Regenerate the bundles with:

```bash
python tools/make_bundle.py --all      # or name a concept, e.g. cross-validation
```

To assemble it by hand instead:

**1. Copy the files** into your project:

- `js/infra.html` — shared `TM` helpers (needed by every animation)
- `js/cross-validation.html` — the animation module
- the `.cv-*` rules and `:root` colour variables from `css/demos.css`
  (paste them into your own theme, or copy `demos.css` wholesale)

**2. Wire them up in your deck's YAML** (or `_quarto.yml`):

```yaml
format:
  revealjs:
    theme: [default, css/demos.css]   # or merge the .cv-* rules into your theme
    width: 1280
    height: 720
    include-in-header:
      text: |
        <script src="https://cdnjs.cloudflare.com/ajax/libs/animejs/3.2.2/anime.min.js"></script>
    include-after-body:
      - js/infra.html
      - js/cross-validation.html
```

**3. Add the slide** wherever you want it in your deck:

````markdown
```{=html}
<script>window.CV_COLORS = ['#8ecae6', '#90be6d', '#f9c74f'];</script>
```

## {.cv-slide}

::: {.cv-stage-wrap}
<div id="cv-title" class="cv-title"></div>
<div id="cv-stage"></div>
:::

[]{.fragment .cv-frag id="cv-color"}
[]{.fragment .cv-frag id="cv-split"}
[]{.fragment .cv-frag id="cv-fold1"}
[]{.fragment .cv-frag id="cv-fold2"}
[]{.fragment .cv-frag id="cv-fold3"}
````

That's the whole dependency set: **`infra.html` + `cross-validation.html` + the
`.cv-*` CSS + that slide block.**

### Things to watch

- **Keep `width: 1280, height: 720`.** The module lays elements out in absolute
  coordinates against a fixed-size stage (`#cv-stage`, sized in CSS). Reveal
  scales the whole slide to fit, so it survives different displays, but a very
  different aspect ratio could crop the edges.
- **If you load the CSS as a reveal theme,** it must keep the
  `/*-- scss:rules --*/` boundary. Pasting the `.cv-*` rules into your existing
  theme avoids that requirement.
- **Fragment ids must be unique within your deck** — don't reuse the `cv-*` ids on
  another slide.
- **Position-independent.** `TM.gate` keys off the `.cv-slide` marker class and the
  count of visible fragments, so the slide works at any position and survives
  back-navigation and reloads.
- **Recolour** by editing the `window.CV_COLORS` array (one colour per fold).

## Key implementation lessons

Drawn from building anime.js animations on top of RevealJS:

- **Coordinate spaces** — RevealJS scales the slide with a CSS transform; child
  `translateX/Y` are in the slide's internal units (here 1280×720), which is what
  you want. Convert screen measurements with `TM.cssToSlide`.
- **Idempotent `render(stage)`** — never script "play forward" transitions
  imperatively; compute the target state from how many fragments are visible.
  Back-navigation and reloads then need no special handling.
- **Clean ownership of properties** — let CSS own structural/layout properties
  and let anime.js own `transform`, `opacity`, `background-color`. Never animate
  the same property from both.
- **Register listeners without waiting for `ready`** — `include-after-body`
  scripts often load after Reveal initialises, so `Reveal.on('ready', …)` may
  never fire. `TM.onReveal` registers nav listeners immediately and polls for the
  current slide on boot.
