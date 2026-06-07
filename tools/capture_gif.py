#!/usr/bin/env python3
"""Capture a tidymodels-animated deck as a (small, crisp) GIF.

Drives a rendered RevealJS deck headlessly with Playwright, advancing through the
fragments. Instead of guessing delays, it waits for `window.TM.idle()` — the
animation modules report busy/idle via TM.anime / TM.pause — so it samples
densely *while* something is animating and lets static holds collapse to a single
long-duration frame.

Frames are captured as **lossless PNG screenshots** (not lossy video), so the flat
background is pixel-identical between frames. ffmpeg assembles them with real
per-frame durations (accurate pacing), then `gifsicle -O3` losslessly
diff-compresses and dedups the hold frames — which is only effective because the
source frames are lossless. The result is crisp (no compression speckle) and
small.

Prereqs: `pip install playwright`, `playwright install chromium`, ffmpeg, and
(optional, for the lossless pass) gifsicle.

Example:
  python tools/capture_gif.py \
      --deck _site/cross-validation.html --slide 2 --steps 5 \
      --out gifs/cross-validation.gif
"""
import argparse
import os
import subprocess
import sys
import tempfile
import time

from playwright.sync_api import sync_playwright

IDLE = "() => window.TM && typeof window.TM.idle === 'function' && window.TM.idle()"


def capture_frames(args, frames_dir):
    """Play the deck, screenshotting the crop region. Returns a list of
    (png_path, timestamp_seconds) sampled across the animation."""
    url = args.deck
    if "://" not in url:
        url = "file://" + os.path.abspath(url)
    if args.slide:
        url += f"#/{args.slide}"

    interval = max(int(1000 / args.fps), 20)  # ms between samples during motion
    frames = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": args.width, "height": args.height},
            device_scale_factor=2,  # crisp 2x screenshots
        )
        page = ctx.new_page()
        page.goto(url)
        page.wait_for_load_state("networkidle")

        def wait_idle():
            page.wait_for_timeout(80)  # let the fragment handler kick off render()
            try:
                page.wait_for_function(IDLE, timeout=args.idle_timeout)
            except Exception:
                pass

        wait_idle()
        box = page.evaluate(
            "(sel) => { const r = document.querySelector(sel).getBoundingClientRect();"
            "return {x: r.x, y: r.y, w: r.width, h: r.height}; }",
            args.selector,
        )
        pad = args.pad
        clip = {
            "x": max(box["x"] - pad, 0),
            "y": max(box["y"] - pad, 0),
            "width": int(box["w"]) + 2 * pad,
            "height": int(box["h"]) + 2 * pad,
        }

        def grab():
            path = os.path.join(frames_dir, f"f{len(frames):05d}.png")
            page.screenshot(path=path, clip=clip)
            frames.append((path, time.monotonic()))

        def sample_until_idle():
            deadline = time.monotonic() + args.idle_timeout / 1000
            while time.monotonic() < deadline:
                grab()
                page.wait_for_timeout(interval)
                if page.evaluate(IDLE):
                    break
            grab()  # final settled frame of this segment

        grab()                              # stage 0
        page.wait_for_timeout(args.start_hold)   # becomes the first frame's duration

        for _ in range(args.steps):
            page.keyboard.press(args.key)
            page.wait_for_timeout(80)
            sample_until_idle()
            page.wait_for_timeout(args.dwell)    # hold -> duration of last frame

        grab()                              # capture the final state
        page.wait_for_timeout(args.end_hold)
        grab()                              # close out the end hold

        ctx.close()
        browser.close()

    return frames, clip


def assemble_gif(frames, args):
    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        # concat demuxer with real per-frame durations -> accurate pacing
        listfile = os.path.join(td, "frames.txt")
        with open(listfile, "w") as fh:
            for i, (path, t) in enumerate(frames):
                if i + 1 < len(frames):
                    dur = max(frames[i + 1][1] - t, 0.02)
                else:
                    dur = 0.1
                fh.write(f"file '{path}'\nduration {dur:.3f}\n")
            fh.write(f"file '{frames[-1][0]}'\n")  # concat needs the last file repeated

        vf = f"fps={args.fps},scale={args.scale}:-1:flags=lanczos"
        palette = os.path.join(td, "palette.png")
        run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", listfile,
             "-vf", f"{vf},palettegen=stats_mode=full", palette])
        run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", listfile, "-i", palette,
             "-lavfi", f"{vf}[x];[x][1:v]paletteuse=dither=none", "-loop", "0", args.out])

    raw = os.path.getsize(args.out)
    if not args.no_optimize and have("gifsicle"):
        run(["gifsicle", "-O3", "--no-warnings", "-b", args.out])
        print(f"wrote {args.out} ({raw // 1024} KB -> {os.path.getsize(args.out) // 1024} KB, lossless)")
    else:
        if not args.no_optimize:
            print("(gifsicle not found — skipping lossless optimisation)")
        print(f"wrote {args.out} ({raw // 1024} KB)")


def run(cmd):
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        sys.exit(f"command failed: {' '.join(cmd)}\n{res.stderr[-2000:]}")


def have(cmd):
    return subprocess.run(["which", cmd], capture_output=True).returncode == 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--deck", required=True, help="rendered .html (e.g. _site/cross-validation.html) or URL")
    ap.add_argument("--out", required=True, help="output .gif path")
    ap.add_argument("--slide", type=int, default=0, help="slide index to start on (Reveal #/N)")
    ap.add_argument("--steps", type=int, required=True, help="number of fragment advances to record")
    ap.add_argument("--selector", default=".cv-stage-wrap", help="element to crop the GIF to")
    ap.add_argument("--key", default="ArrowRight", help="key to advance fragments")
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=720)
    ap.add_argument("--dwell", type=int, default=700, help="ms to hold after each step settles")
    ap.add_argument("--start-hold", type=int, default=900, help="ms to hold on the first frame")
    ap.add_argument("--end-hold", type=int, default=1600, help="ms to hold on the last frame")
    ap.add_argument("--idle-timeout", type=int, default=12000, help="ms cap waiting for TM.idle per step")
    ap.add_argument("--fps", type=int, default=20)
    ap.add_argument("--scale", type=int, default=900, help="output width in px (height auto)")
    ap.add_argument("--pad", type=int, default=8, help="px of padding around the cropped region")
    ap.add_argument("--no-optimize", action="store_true", help="skip the lossless gifsicle -O3 pass")
    args = ap.parse_args()

    with tempfile.TemporaryDirectory() as frames_dir:
        frames, _clip = capture_frames(args, frames_dir)
        if not frames:
            sys.exit("No frames captured.")
        assemble_gif(frames, args)


if __name__ == "__main__":
    main()
