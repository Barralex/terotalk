"""Exports the canvas boards to formats anyone can open.

    python design/canvas/export.py

Writes design/canvas/export/:
    terotalk-canvas.pdf   Every board, one page each, vector, in canvas order
    NN-<board>.svg        One per board, for Figma, Penpot or Illustrator (File > Import)
    NN-<board>.png        One per board at 2x, for the README and quick review

Each board is printed by headless Chrome at its exact canvas size, animations frozen on the
frame the site's own preview uses, then split and converted with PyMuPDF. Text in the SVGs
is outlined so it renders the same without the fonts installed; shapes stay as vectors.
Needs PyMuPDF (pip install pymupdf) and Chrome or Edge (set CHROME to override).
"""
import json
import os
import pathlib
import re
import subprocess
import tempfile

import pymupdf

HERE = pathlib.Path(__file__).resolve().parent
PROJECT = HERE / "project"
OUT = HERE / "export"

# Board files keep the names the canvas gave them; exports get English, descriptive ones.
NAMES = {"Main.dc.html": "brand-sheet", "Mezcla.dc.html": "hero-thread", "About.dc.html": "who-teaches"}

# 6.6 s into the 11 s clock: the thread is untangled, "Deal." is up and the tero has landed.
FREEZE_AT = "-6.6s"

CHROMES = [os.environ.get("CHROME", ""),
           r"C:\Program Files\Google\Chrome\Application\chrome.exe",
           r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
           "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]


def chrome():
    return next(c for c in CHROMES if c and os.path.exists(c))


def printable(html, w, h):
    """The board as a plain page: exact paper size, no editor runtime, motion frozen."""
    html = html.replace('<script src="./support.js"></script>', "")
    style = (f"<style>@page{{size:{w}px {h}px;margin:0}}html,body{{margin:0}}"
             f"*,*::before,*::after{{print-color-adjust:exact;-webkit-print-color-adjust:exact;"
             f"animation-delay:{FREEZE_AT}!important;animation-play-state:paused!important}}</style>")
    return html.replace("</head>", style + "</head>", 1)


def main():
    index = json.loads((PROJECT / "canvas.json").read_text(encoding="utf-8"))
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("*"):
        old.unlink()
    book = pymupdf.open()
    with tempfile.TemporaryDirectory() as tmp:
        for n, board in enumerate(index["order"], 1):
            frame = index["boards"][board]
            w, h = frame["w"], frame["h"]
            page = pathlib.Path(tmp) / f"{n}.html"
            page.write_text(printable((PROJECT / board).read_text(encoding="utf-8"), w, h), encoding="utf-8")
            pdf = pathlib.Path(tmp) / f"{n}.pdf"
            subprocess.run([chrome(), "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                            "--virtual-time-budget=5000", f"--print-to-pdf={pdf}", page.as_uri()],
                           check=True, capture_output=True)
            stem = f"{n:02d}-{NAMES.get(board, re.sub(r'[^a-z0-9]+', '-', board.lower()).strip('-'))}"
            with pymupdf.open(pdf) as single:
                book.insert_pdf(single, from_page=0, to_page=0)
                first = single[0]
                (OUT / f"{stem}.svg").write_text(first.get_svg_image(text_as_path=True), encoding="utf-8")
                # 1 CSS px is .75 pt, so 192 dpi renders the board at 2x.
                first.get_pixmap(dpi=192).save(OUT / f"{stem}.png")
            print(f"{stem}  {w}x{h}  {frame.get('title', board)}")
    book.set_metadata({"title": index.get("title", "Canvas"), "author": "Luis Barral"})
    book.save(OUT / "terotalk-canvas.pdf", garbage=4, deflate=True)
    print("terotalk-canvas.pdf ", len(book), "pages")


if __name__ == "__main__":
    main()
