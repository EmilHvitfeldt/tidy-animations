#!/usr/bin/env python3
"""Bundle everything needed to reuse one animation in another Quarto RevealJS deck.

For a given concept, produces `bundles/<concept>.zip` containing the four things
the README's "Reusing an animation" section calls for — anime.js loader notes,
the shared `infra.html`, the concept's own module, and `demos.css` — plus the
example `.qmd` (so the slide block + colour config travel along) and a generated
README with the copy-paste wiring.

Usage:
    python tools/make_bundle.py cross-validation bootstrap
    python tools/make_bundle.py --all
"""
import argparse
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUNDLES = ROOT / "bundles"

ANIME_SRC = "https://cdnjs.cloudflare.com/ajax/libs/animejs/3.2.2/anime.min.js"

README_TMPL = """\
# {concept} — reusable animation bundle

Everything needed to drop the **{concept}** animation into your own Quarto
RevealJS deck. Extracted from https://github.com/EmilHvitfeldt/tidymodels-animated

## Contents

- `js/infra.html` — shared `TM` helpers (needed by every animation)
- `js/{concept}.html` — the animation module
- `css/demos.css` — shared styles + the per-animation classes
- `{concept}.qmd` — the original example deck: copy its `{{=html}}` colour-config
  block and the slide block straight into your presentation

## Wiring it up

1. Copy `js/` and `css/` into your project.

2. In your deck's YAML (or `_quarto.yml`):

   ```yaml
   format:
     revealjs:
       theme: [default, css/demos.css]
       width: 1280
       height: 720
       include-in-header:
         text: |
           <script src="{anime}"></script>
       include-after-body:
         - js/infra.html
         - js/{concept}.html
   ```

3. Paste the colour-config `{{=html}}` block and the slide block from
   `{concept}.qmd` wherever you want the slide.

Keep `width: 1280, height: 720` — the module lays elements out in absolute
coordinates against a fixed-size stage. Fragment ids must stay unique within
your deck.
"""

# Files every bundle ships, relative to repo root.
SHARED = ["js/infra.html", "css/demos.css"]


def build(concept: str) -> Path:
    module = ROOT / "js" / f"{concept}.html"
    example = ROOT / "examples" / f"{concept}.qmd"
    missing = [p for p in (module, example) if not p.exists()]
    if missing:
        sys.exit(f"error: {concept}: missing {', '.join(str(p) for p in missing)}")

    BUNDLES.mkdir(exist_ok=True)
    out = BUNDLES / f"{concept}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for rel in SHARED:
            z.write(ROOT / rel, rel)
        z.write(module, f"js/{concept}.html")
        z.write(example, f"{concept}.qmd")
        z.writestr(
            "README.md",
            README_TMPL.format(concept=concept, anime=ANIME_SRC),
        )
    print(f"wrote {out.relative_to(ROOT)}")
    return out


def discover() -> list[str]:
    return sorted(
        p.stem
        for p in (ROOT / "examples").glob("*.qmd")
        if (ROOT / "js" / f"{p.stem}.html").exists()
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("concepts", nargs="*", help="concept name(s), e.g. bootstrap")
    ap.add_argument("--all", action="store_true", help="bundle every concept")
    args = ap.parse_args()

    concepts = discover() if args.all else args.concepts
    if not concepts:
        ap.error("name at least one concept, or pass --all")
    for c in concepts:
        build(c)


if __name__ == "__main__":
    main()
