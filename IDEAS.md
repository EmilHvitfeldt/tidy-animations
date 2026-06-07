# Animation ideas: tidymodels concepts

A backlog of tidymodels concepts that animate well in Quarto RevealJS (anime.js +
fragments). Grouped by where they sit in the modeling workflow.

## Data spending
- **Initial train/test split** — a block of rows sliding apart; test set "locked in a vault".
- **Cross-validation / V-fold** — rows partition into V folds; each fold takes a turn as the
  assessment set (the classic rotating-highlight animation). ← **building first**
- **Bootstrap resampling** — rows sampled *with replacement*; some rows duplicated, some left
  out (OOB) bouncing into an out-of-bag pile.
- **Validation set / `initial_validation_split`** — three-way split.
- **Time-based / rolling-origin resampling** — a window sliding forward through time-ordered data.

## Preprocessing (recipes)
- **Recipe pipeline** — data flowing through `step_*()` one fragment at a time.
- **`step_dummy()`** — a categorical column fanning out into multiple 0/1 columns.
- **`step_normalize()`** — a column's values squishing toward mean 0, sd 1.
- **`step_pca()`** — points rotating onto new principal-component axes.
- **Skipping on `bake()`** — showing why `skip = TRUE` steps don't run at prediction time.

## Model / workflow
- **Workflow assembly** — recipe box + model box snapping together, then fitting.
- **`parsnip` engine swap** — same model spec, different engine plugging in underneath.
- **Prediction flow** — new data entering the fitted workflow → predictions out.

## Tuning
- **Grid search** — a grid of hyperparameter combos lighting up one cell at a time, each scored.
- **`tune_grid()` over resamples** — the grid × folds matrix filling in (every combo on every fold).
- **Bayesian / iterative search** — points appearing one at a time, each guided toward better regions.
- **`select_best()`** — the winning grid cell rising to the top.

## "Punchline" / motivational
- **"Just normalize the whole dataset"** → data leakage seeping from test into train (cautionary).
- **`workflow_set`** — a matrix of model × recipe combinations all training at once.

## Distribution / tooling
- **Quarto extension per animation** — bundle each animation (infra + module + CSS)
  as a Quarto extension so end users install with `quarto add` and drop it in via a
  one-line shortcode (e.g. `{{< cv-animation >}}`) instead of hand-copying files.
  Cleaner for reuse than the manual "copy four pieces" recipe in the README.
