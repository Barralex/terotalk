# Design

Source of the TeroTalk brand. Every file in `assets/brand/` that carries the mark is generated
from here; edit the source, not the output.

## Contents

| Path | What it is |
|---|---|
| [`logo/build.py`](logo/build.py) | The mark, drawn once; writes the logo SVGs, favicon, seals, page sprites and canvas marks |
| [`logo/banner.html`](logo/banner.html) | Layout of the README banner |
| [`canvas/project/`](canvas/project/) | Source of the design canvas, one `.dc.html` per board |
| [`canvas/export.py`](canvas/export.py) | Renders the boards to PDF, SVG and PNG |
| [`canvas/export/`](canvas/export/) | The rendered boards: [PDF](canvas/export/terotalk-canvas.pdf), SVG for Figma or Penpot, PNG |
| [`preview/preview.html`](preview/preview.html) | Desktop and phone frames of the README screenshot |
| [`preview/build.py`](preview/build.py) | Shoots that layout into `assets/brand/preview.jpg` |

## Build

```bash
python design/logo/build.py --export   # mark, sprites, seals, PNGs, banner
python design/canvas/export.py         # canvas boards to PDF, SVG, PNG
python design/preview/build.py         # README screenshot of the live home page
```

Requires Python 3 with PyMuPDF, and Chrome or Edge (`CHROME` overrides the path).

The monogram in `build.py` is Fraunces italic 500 (`opsz 144`, `SOFT 100`, `WONK 1`) already
outlined, so nothing at build time needs the font. To change the cut, pull the instance from
Google Fonts and re-extract the glyph with fontTools, then paste it back into `LETTER`.
