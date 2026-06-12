# tidymodels, animated

Self-contained animated explainers for data science and machine learning concepts, built with [Quarto RevealJS](https://quarto.org/docs/presentations/revealjs/) and [anime.js](https://animejs.com/).

**▶ Watch them live: <https://emilhvitfeldt.github.io/tidy-animations/>**

Each animation is a single, self-contained slide you can drop straight into your own talk. Browse them on the site above — every concept has a live embed plus links to open the full deck, view it as a GIF or MP4, and download a reusable bundle.

## What's in here

| Concept | Deck |
|---|---|
| Cross-validation | `examples/cross-validation.qmd` |
| Bootstrap resampling | `examples/bootstrap.qmd` |
| Train/test split | `examples/train-test-split.qmd` |
| Train/validation/test split | `examples/train-val-test.qmd` |
| Time-based validation split | `examples/time-val-split.qmd` |
| Sliding window | `examples/sliding-window.qmd` |
| Recipe pipeline | `examples/recipe-pipeline.qmd` |
| `filter()` (one & two conditions) | `examples/filter-one.qmd`, `examples/filter-two.qmd` |
| ggplot2 deconstructed | `examples/ggplot2-deconstructed.qmd` |

The convention is **one `.qmd` deck per concept** (under `examples/`) with a matching animation module (`js/<concept>.html`). Keeping them separate means any slide copies cleanly into a real presentation without animations interfering with each other.

## Using an animation in your own talk

The easiest path: on the [landing page](https://emilhvitfeldt.github.io/tidy-animations/), find the concept you want and click **Download reusable bundle**. The zip contains the slide, its JavaScript, its CSS, and a short README showing how to wire it into your own Quarto RevealJS deck.

## Viewing locally

You'll need [Quarto](https://quarto.org/docs/get-started/) installed.

```bash
quarto preview examples/cross-validation.qmd   # one deck, with live reload
quarto render                                  # build the whole site into docs/
```

## Creating a new animation

This repo is built with [Claude Code](https://claude.com/claude-code) — the conventions, build process, and hard-won gotchas all live in `.claude/CLAUDE.md`, which Claude reads automatically. So the best way to make a new animation is to **open Claude Code in this repo and describe the concept you want to animate.** A few tips for getting good results:

- **Describe the steps, not the code.** Say what should appear and move at each click ("the data splits into 5 folds, then one lights up as the test set…"). Claude turns that into the fragments and animation.
- **Build it segment by segment.** Start with just the first frame — the static starting layout, before anything animates — and get it looking right. Then add one segment at a time, confirming each in the browser before moving on (`say "let's go segment by segment"`). Trying to author the whole animation in one shot produces tangled, buggy code; this is the single biggest lever on quality.
- **Iterate in the browser.** Keep `quarto preview examples/<concept>.qmd` running and check forward *and* backward navigation at each step.
- **Reuse a recipe.** For a ggplot2 walkthrough, just hand Claude a code snippet — the `ggplot2-deconstructed` skill kicks in automatically. Pointing Claude at an existing deck ("make it like cross-validation") is a great starting point for anything else.
- **Capture last.** Only once you're happy with the design, ask Claude to capture the GIF/MP4 and wire the deck into the landing page.
