---
name: ggplot2-deconstructed
description: Build a "code-deconstructed" ggplot2 animation deck — ggplot2 code on the left, the plot lays down in 3D, explodes into one stacked semi-transparent paper card per code block, walks up highlighting each line and its slice, then collapses back to flat. Use when a user supplies a ggplot2 snippet and wants this treatment in the tidy-animations repo. Canonical impl: examples/ggplot2-deconstructed.qmd + js/ggplot2-deconstructed.html.
---

# Recipe: "code-deconstructed" plot animation

A reusable template for the **ggplot2-deconstructed** style: a ggplot2 code
snippet on the left, the produced plot on the right; the plot lays down in 3D,
explodes into one stacked "paper" card per code block, then each code line is
highlighted in turn while its slice is isolated, before collapsing back to flat.

Use this when the user gives **a different ggplot2 snippet** and wants the same
treatment. `examples/ggplot2-deconstructed.qmd` + `js/ggplot2-deconstructed.html`
are the canonical reference — copy and adapt them.

---

## 0. What you need from the user

- The **ggplot2 code snippet** (verbatim). This drives everything: the left
  listing *and* the set of cards (one card per top-level block).
- Confirm which **dataset** it uses so you can render a faithful plot.

## 1. Decide the card decomposition (the spec — confirm first)

Split the snippet into **one card per visual layer**, mapping each `+`-chained
call to what it draws. The default mapping that worked:

| Code block | Card owns |
|---|---|
| `ggplot(data, aes(...))` | panel background, gridlines, tick marks + tick labels, **legend keys** (the colour/shape scale swatches) |
| `geom_*(...)` (one per geom) | that geom's marks (points, line+ribbon, bars, …) |
| `labs(...)` | **only the text labs sets**: plot title, axis titles, legend *title* |

Rules of thumb:
- Tick *numbers* belong to the coord card; axis *titles* belong to `labs`.
- Legend *swatches* belong to the `aes()` card; the legend *title* to `labs`.
- Each `geom_*` is its own card, stacked in code order.
- Card stack order = **code order, bottom → top**: `ggplot/aes` at the bottom,
  then geoms, `labs` on top. (Index 0 = bottom.)

Lay the ordered card list out and confirm it with the user before coding.

## 2. Get faithful plot data from R

Don't eyeball the plot — extract real values with `Rscript`. For a scatter +
loess smooth (adapt columns/geoms as needed):

```r
suppressMessages(library(ggplot2)); suppressMessages(library(jsonlite))
d <- <dataset>
# discrete colour groups -> ggplot's exact hue palette
grp <- sort(unique(d$<colorvar>))
cols <- scales::hue_pal()(length(grp))
# loess like geom_smooth default (n < 1000)
lo <- loess(<y> ~ <x>, data = d, span = 0.75, degree = 2)
xs <- seq(min(d$<x>), max(d$<x>), length.out = 80)
pr <- predict(lo, newdata = data.frame(<x> = xs), se = TRUE)
# emit points [x, y, groupIndex], smooth [x, fit, lo, hi], ranges, palette
```

Embed the arrays as JS literals in the module (see the `PTS` / `SMOOTH` /
`COLORS` constants). Hardcode them — do not fetch at runtime.

## 3. Plot geometry (SVG, drawn once)

- The plot lives in `#gd-plot`, a fixed local coordinate box (`W` × `H`). Default
  `W = 600`; pick `H` so the **panel** (`H − top − bottom`) reads landscape
  (≈ 386 × 260 worked well). Margins: left for y-title+labels, right for legend,
  top for title, bottom for x-labels+title.
- Scales use ggplot's default **5% additive expansion** on each end:
  `expand(lo, hi) => [lo − .05·range, hi + .05·range]`.
- theme_grey look: panel `#EBEBEB`, **white** major gridlines (width 2) and minor
  (width 1); points `r ≈ 3.4`; smooth ribbon `#999 @ .4`, line black width 2.2.
- Build each card as its own full-size **plane** (`svgPlane`): an outer
  `.gd-plane` div → inner `.gd-tilt` div → [`.gd-card` backing + `<svg>`]. All
  planes are coincident, so at rest they overlay into one flat plot.

## 4. The 3D mechanics (the part that's easy to get wrong)

These are the lessons that took iteration — keep them:

1. **Lay-down = `rotateX` + `rotateZ`.** ~`rotateX(56) rotateZ(20)` lays the
   plot back and tilts it toward the right. (Flip `rotateZ` sign to tilt left.)
2. **Per-card perspective, not a shared one.** Put `perspective` on each
   `.gd-plane` (via CSS), *not* on the stage/parent. A single shared perspective
   has one vanishing point; cards far from it get a skewed projection and their
   edges drift. Per-card perspective centers each card's vanishing point on
   itself → all cards stay edge-aligned.
3. **Tilt the inner `.gd-tilt`; fan the outer `.gd-plane`.** The explode
   separation must be a **screen-space `translateY` on the outer div** (composed
   *outside* the perspective/rotation), so cards move **straight up/down only**
   and keep the same horizontal center. Fan symmetrically about center:
   `translateY = ((N−1)/2 − i) · SPREAD` (≈ 75px gap).
4. **Cards = semi-transparent paper.** `.gd-card` backing
   `rgba(255,255,255,~0.6)`, light border + soft shadow, `opacity 0` until
   explode.

## 5. Fragment sequence (render keyed off stage number)

Drive everything with `TM.gate` and an **idempotent** `render(stage)`. The
fragments, in order (so `N` geoms → `N + 5` fragments):

0. arrival — flat plot, code + plot side by side
1. `lay`     — tilt back (`laid = stage ≥ 1`)
2. `explode` — fan into cards, fade in card backings (`exploded = stage ≥ 2`)
3 … (3+k) `focus-<block>` — walk **up** the stack: highlight code block `k`
   (`focusIdx = stage − 3`) and call out slice `k`. **Highlight the code only —
   never dim the code text** (user preference); the *slice* treatment is where
   the two known variants differ (pick one, or ask):
   - **A — dim others** (`ggplot2-deconstructed`): focused slice stays at
     `opacity 1`, the rest fade to ~0.16. Everything keeps its tilt + fan spot.
   - **B — part & flatten** (`ggplot2-deconstructed-2`): no dimming; the
     non-focused slices slide out of the way (`fan += PART` for `i < focusIdx`,
     `−PART` for `i > focusIdx`, `PART ≈ 280`) and the focused slice **un-rotates
     to head-on** (`rotateX/rotateZ → 0`) so it reads as a clean standalone plot.
4. `collapse`  — merge cards back together, still tilted (`!exploded`, still `laid`)
5. `unrotate`  — flatten to head-on (`!laid`)

Implement collapse/unrotate as two booleans that override the earlier ones:
`flat = stage ≥ LAST; collapsed = stage ≥ LAST−1;`
`laid = … && !flat; exploded = … && !collapsed; focusIdx = … && !collapsed`.

Code highlight: wrap each code block (incl. the `library()` line) in
`<span data-blk="…">`; toggle a `.gd-hot` class (yellow marker) on the focused
block only.

Drive all motion through `TM.anime` / `TM.pause` (never bare `anime`/`setTimeout`)
so the recorder can pace to `TM.idle()`.

## 6. Housekeeping (don't forget — see main CLAUDE.md)

1. Add `.gd-*` (or your prefix) styles to `css/demos.css` (it's SCSS-layered —
   keep them after the `/*-- scss:rules --*/` boundary).
2. `quarto render examples/<concept>.qmd`, then capture **both**:
   ```
   python3 tools/capture_recordings.py --deck docs/examples/<concept>.html \
     --slide 1 --steps <fragments + 1> --selector .<prefix>-stage-wrap \
     --out gifs/<concept>.gif        # repeat with --out mp4/<concept>.mp4
   ```
   `--steps` = (number of gating fragments) + 1.
3. Add a `##` section to `index.qmd` (iframe + 4 links: deck, GIF, MP4, bundle).
4. `quarto render` the whole site — the pre-render hook auto-builds
   `bundles/<concept>.zip`. Verify the iframe + all four links resolve.
