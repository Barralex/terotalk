#!/usr/bin/env python3
"""Render the README screenshot: the home page on a desktop frame and on a phone.

    python design/preview/build.py

Writes assets/brand/preview.jpg (1860x1050). Needs Chrome or Edge (CHROME overrides the
path) and PyMuPDF for the JPEG. Both frames are frozen late in the 11 s hero loop, so the
thread is drawn, the tero has landed and the picker sits at rest.
"""
import pathlib
import subprocess
import sys
import tempfile

import fitz

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "logo"))
from build import shoot  # noqa: E402  the Chrome runner lives with the mark

ROOT = pathlib.Path(__file__).resolve().parents[2]
PAGE = ROOT / "design" / "preview" / "preview.html"
OUT = ROOT / "assets" / "brand" / "preview.jpg"
WIDTH, HEIGHT = 1860, 1050


def main():
    with tempfile.TemporaryDirectory() as tmp:
        png = pathlib.Path(tmp) / "preview.png"
        shoot(PAGE.as_uri(), str(png), WIDTH, HEIGHT)
        pix = fitz.Pixmap(str(png))
        if pix.alpha:
            pix = fitz.Pixmap(pix, 0)
        pix.save(str(OUT), jpg_quality=88)
    print("wrote", OUT.relative_to(ROOT), f"{OUT.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
