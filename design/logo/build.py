"""Builds the TeroTalk mark from one source of truth.

The mark is the chibi mascot nesting in the TT speech bubble. This script writes the
three standalone SVGs in assets/brand/ (light, dark, favicon), the <symbol> the pages
carry in their sprite (colours from the --color-logo-* tokens, never hex) and every mark
on the canvas brand board in design/canvas/. Run it after touching any shape below:

    python design/logo/build.py            # rewrite the SVGs and the page sprites
    python design/logo/build.py --export   # also render the PNG exports and the banner
    python design/logo/build.py --symbol   # print the page sprite symbol

--export needs Chrome or Edge; set CHROME to its path if it is not in the default place.
"""
import os
import pathlib
import re
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
BRAND = ROOT / "assets" / "brand"
PAGES = ["index.html", "kids/index.html", "professionals/index.html"]
CANVAS_BOARD = ROOT / "design" / "canvas" / "project" / "Main.dc.html"
CANVAS_HERO = ROOT / "design" / "canvas" / "project" / "Mezcla.dc.html"
CANVAS_ABOUT = ROOT / "design" / "canvas" / "project" / "About.dc.html"

VIEWBOX = "4 22 232 232"

# The chibi is drawn in its own 0-120 space (the same drawing as .chibi-tero on the home
# page) and placed so its body sinks into the top of the bubble.
BIRD = "translate(28 10) scale(1.62)"

# (role, element) — role is the logo token the shape takes.
BIRD_SHAPES = [
    ("wing", '<ellipse cx="58" cy="80" rx="31" ry="25"/>'),
    ("ink", '<ellipse cx="64" cy="88" rx="20" ry="15"/>'),
    ("belly", '<path d="M44 66 C54 74 76 74 86 64 C86 72 80 78 70 80 C58 81 48 76 44 66 Z"/>'),
    ("arm", '<path d="M30 76 C36 64 52 64 58 74 C52 86 38 88 30 76 Z"/>'),
    ("ink", '<path d="M52 26 C44 12 30 8 18 12 C30 14 42 20 48 30 Z"/>'),
    ("ink", '<path d="M54 30 C48 22 38 20 30 22 C38 24 46 28 50 34 Z"/>'),
    ("wing", '<circle cx="62" cy="44" r="24"/>'),
    ("ink", '<path d="M84 40 C82 30 74 24 66 25 C72 32 74 42 73 52 C72 60 68 66 64 70 L78 70 C82 62 86 50 84 40 Z"/>'),
    ("beak", '<path d="M84 42 L98 46 L84 50 Z"/>'),
    ("cheek", '<ellipse cx="58" cy="54" rx="5" ry="3"/>'),
    ("eye", '<circle cx="66" cy="40" r="8"/>'),
    ("belly", '<circle cx="68" cy="41" r="4.5"/>'),
    ("ink", '<circle cx="70" cy="39" r="1.6"/>'),
]

# The legs only show where the whole mascot stands on its own, as on the quality seal.
LEGS = '<path d="M50 98 L48 112 M48 112 H42 M48 112 H55"/><path d="M66 98 L68 112 M68 112 H62 M68 112 H75"/>'
SEALS = {"quality-seal.svg": "dark", "quality-seal-dark.svg": "light"}
SEAL_BIRD = "translate(80.4 54.2) scale(.72)"  # above the TeroTalk line at y 157

# The stamp that signs a line of text: a teacher's rubber stamp, our version. No ring at all, the
# lettering itself draws the circle, the mascot stands in the middle and three sparks fill the
# gaps. English, like the stamps a teacher actually owns, and pressed on at an angle.
HEAD_SHAPES = BIRD_SHAPES[4:]
STAMP_VIEWBOX = "0 0 200 200"
STAMP_FACE = "translate(33 57) scale(1.15)"
STAMP_TOP = "M22 100 A78 78 0 0 1 178 100"
STAMP_BOT = "M12 100 A88 88 0 0 0 188 100"


# The bubble is a stadium: radius 44 on an 88-tall box, so it has no corners to look square.
BUBBLE = "M66 138 H174 A44 44 0 0 1 174 226 H128 L80 254 L98 226 H66 A44 44 0 0 1 66 138 Z"

# The monogram is the wordmark's own letter: Fraunces italic 500, opsz 144, SOFT 100, WONK 1,
# outlined from the font so no SVG depends on it. Font units, 2000 per em, baseline at y 0 and
# y up, so LETTER_AT flips it and scales the 1511-unit cap to the 70 units the bubble gives it.
LETTER = "M490 1418Q551 1418 616 1408Q682 1398 748 1383Q814 1368 875 1353Q936 1338 987 1328Q1038 1318 1073 1318Q1108 1318 1127 1332Q1146 1346 1155 1372Q1162 1390 1164 1402Q1165 1414 1168 1426Q1178 1466 1200 1488Q1222 1511 1266 1511Q1308 1511 1333 1481Q1358 1451 1356 1389Q1355 1296 1296 1240Q1237 1184 1134 1184Q1091 1184 1028 1196Q966 1207 894 1224Q823 1242 751 1258Q679 1275 616 1287Q552 1299 506 1299Q437 1299 408 1269Q379 1239 378 1187Q378 1175 380 1163Q383 1151 386 1138Q389 1124 389 1107Q388 1067 366 1040Q344 1012 297 1012Q246 1012 214 1046Q183 1081 184 1146Q186 1224 222 1286Q257 1347 324 1382Q392 1418 490 1418ZM611 203Q603 169 609 156Q615 143 634 135L693 120Q737 102 737 64Q737 32 716 16Q696 0 664 0H263Q231 0 217 16Q203 31 203 55Q204 81 218 98Q233 114 257 123L307 137Q339 146 354 166Q369 185 381 231Q392 267 411 336Q430 404 455 493Q480 582 508 682Q535 782 562 882Q590 983 615 1074Q640 1164 660 1235Q679 1306 690 1346L913 1304Q898 1251 876 1174Q855 1096 829 1003Q803 910 776 812Q749 713 723 618Q697 522 674 439Q652 356 636 294Q619 233 611 203Z"
LETTER_SCALE = 70 / 1511
LETTER_X = (61, 112)  # the pair centred on the bubble, at the font's own advance


def letter_at(x):
    return f'transform="translate({x} 218) scale({LETTER_SCALE:.5f} -{LETTER_SCALE:.5f})"'


# Hex values per standalone file. The pages never see these: they use the tokens.
PALETTES = {
    "light": {"ink": "#262940", "wing": "#4A4E6D", "belly": "#FBF8F2", "beak": "#B8323A",
              "bubble": "#262940", "letters": "#F3ECE0", "gap": "#F3ECE0"},
    "dark": {"ink": "#F3ECE0", "wing": "#A9C4DE", "belly": "#262940", "beak": "#E0666D",
             "bubble": "#F3ECE0", "letters": "#262940", "gap": "#262940"},
    "favicon": {"ink": "#F3ECE0", "wing": "#A9C4DE", "belly": "#262940", "beak": "#E0666D",
                "bubble": "#F3ECE0", "letters": "#262940", "gap": "#2D3049"},
    # The seal: the chibi's own colours on a sunken disc, so the eye stays light on a dark pupil.
    "medal": {"ink": "#F3ECE0", "wing": "#A9C4DE", "belly": "#262940", "beak": "#E0666D",
              "bubble": "#F3ECE0", "letters": "#262940", "gap": "#262940"},
}


def paint(role, p):
    """Presentation attributes for a role in a standalone file."""
    if role == "arm":
        return f'fill="{p["belly"]}" stroke="{p["ink"]}" stroke-width="1.5"'
    if role == "eye":
        return f'fill="{p["ink"]}" stroke="{p["beak"]}" stroke-width="1.5"'
    if role == "cheek":
        return f'fill="{p["beak"]}" fill-opacity=".5"'
    return f'fill="{p[role]}"'


def with_attrs(element, attrs):
    return element.replace(" ", f" {attrs} ", 1)


def mark(p=None):
    """The mark's inner markup: classes when p is None, hex attributes otherwise."""
    def attrs(role):
        return f'class="logo__{role}"' if p is None else paint(role, p)

    bird = "".join(with_attrs(el, attrs(role)) for role, el in BIRD_SHAPES)
    if p is None:
        bubble = f'<path class="logo__bubble" stroke-width="7" stroke-linejoin="round" d="{BUBBLE}"/>'
        letters = "".join(
            f'<path class="logo__letters" {letter_at(x)} d="{LETTER}"/>' for x in LETTER_X)
    else:
        bubble = (f'<path fill="{p["bubble"]}" stroke="{p["gap"]}" stroke-width="7" '
                  f'stroke-linejoin="round" d="{BUBBLE}"/>')
        letters = "".join(
            f'<path fill="{p["letters"]}" {letter_at(x)} d="{LETTER}"/>' for x in LETTER_X)
    return f'<g transform="{BIRD}">{bird}</g>{bubble}{letters}'


def bird(p=None):
    """The mascot without legs: classes when p is None, hex attributes otherwise."""
    def attrs(role):
        return f'class="logo__{role}"' if p is None else paint(role, p)

    return "".join(with_attrs(el, attrs(role)) for role, el in BIRD_SHAPES)


def standing(p=None):
    """The whole mascot on its feet, legs behind the body."""
    if p is None:
        legs = f'<g class="logo__legs">{LEGS}</g>'
    else:
        legs = (f'<g fill="none" stroke="{p["beak"]}" stroke-width="3" stroke-linecap="round" '
                f'stroke-linejoin="round">{LEGS}</g>')
    return legs + bird(p)


def symbol():
    return f'<symbol id="logo" viewBox="{VIEWBOX}">{mark()}</symbol>'


# The stamp draws the head hollow, the way a rubber stamp prints: every shape a line and the
# pupil the only fill. The hood, the cheek and the glint drop out: they are
# markings that only read as fills.
OUTLINE_SKIP = (3, 5, 8)
OUTLINE_FILL = (7,)


def outline(attrs, fill_attrs, width=5.5):
    """The mascot's head as line art, in one ink."""
    parts = []
    for i, (role, el) in enumerate(HEAD_SHAPES):
        if i in OUTLINE_SKIP:
            continue
        if i in OUTLINE_FILL:
            parts.append(with_attrs(el, fill_attrs))
        else:
            parts.append(with_attrs(el, f'{attrs} stroke-width="{width}"'))
    return "".join(parts)


def seal(p=None, ids=("stamp-top", "stamp-bot")):
    """The stamp: ring, curved lettering, the mascot standing, sparks. Classes or hex."""
    top, bot = ids
    if p is None:
        ring = ""
        text = 'class="logo__stamp-text"'
    else:
        ring = ""
        text = (f'fill="{p["ink"]}" style="font-family:Figtree,system-ui,sans-serif;font-size:23px;'
                f'font-weight:600;letter-spacing:1.4px"')
    if p is None:
        line = 'class="logo__stamp-line"'
        solid = 'class="logo__stamp-solid"'
    else:
        line = f'fill="none" stroke="{p["ink"]}" stroke-linecap="round" stroke-linejoin="round"'
        solid = f'fill="{p["ink"]}"'
    defs = f'<defs><path id="{top}" d="{STAMP_TOP}"/><path id="{bot}" d="{STAMP_BOT}"/></defs>'
    lettering = (f'<text {text}><textPath href="#{top}" startOffset="50%" style="text-anchor:middle">'
                 f'TEROTALK SAYS</textPath></text>'
                 f'<text {text}><textPath href="#{bot}" startOffset="50%" style="text-anchor:middle">'
                 f'KEEP PUSHING!</textPath></text>')
    return f'{defs}{ring}{lettering}<g transform="{STAMP_FACE}">{outline(line, solid)}</g>'


def seal_symbol():
    return f'<symbol id="tero-seal" viewBox="{STAMP_VIEWBOX}">{seal()}</symbol>'


def write_files():
    ns = 'xmlns="http://www.w3.org/2000/svg"'
    for name, key in (("logo.svg", "light"), ("logo-dark.svg", "dark")):
        (BRAND / name).write_text(f'<svg {ns} viewBox="{VIEWBOX}">{mark(PALETTES[key])}</svg>\n', encoding="utf-8")
    fav = PALETTES["favicon"]
    (BRAND / "favicon.svg").write_text(
        f'<svg {ns} viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="{fav["gap"]}"/>'
        f'<g transform="translate(3 -3.5) scale(.25)">{mark(fav)}</g></svg>\n', encoding="utf-8")
    for page in PAGES:
        path = ROOT / page
        html = path.read_text(encoding="utf-8")
        html, n = re.subn(r'<symbol id="logo".*?</symbol>', lambda _: symbol(), html, flags=re.S)
        assert n == 1, page
        # The inline seal rides beside the logo in every sprite that already carries it.
        html, n = re.subn(r'<symbol id="tero-seal".*?</symbol>', lambda _: seal_symbol(), html, flags=re.S)
        assert n <= 1, page
        path.write_text(html, encoding="utf-8", newline="")
    sync_seals()
    sync_canvas()


def sync_seals():
    """Stand the mascot inside the dashed ring of both quality seals."""
    for name, key in SEALS.items():
        path = BRAND / name
        svg = path.read_text(encoding="utf-8")
        svg, n = re.subn(r'<g transform="[^"]*"( data-mascot="")?>.*</g>(\s*<text x="120" y="157")',
                         lambda m: f'<g transform="{SEAL_BIRD}" data-mascot="">{standing(PALETTES[key])}</g>{m.group(2)}',
                         svg, flags=re.S)
        assert n == 1, name
        path.write_text(svg, encoding="utf-8", newline="")


def sync_canvas():
    """Redraw every mark on the canvas brand board with the palette of the tile it sits on."""
    board = CANVAS_BOARD.read_text(encoding="utf-8")

    def redraw(m):
        on_sand = "#F3ECE0" in board[max(0, m.start() - 200):m.start()]
        return m.group(1) + mark(PALETTES["light" if on_sand else "favicon"]) + "</svg>"

    board, n = re.subn(r'(<svg viewBox="4 22 232 232"[^>]*>).*?</svg>', redraw, board, flags=re.S)
    assert n, "no marks found on the canvas board"
    CANVAS_BOARD.write_text(board, encoding="utf-8", newline="")

    # The hero board lands the mark at the end of the thread, on navy.
    hero = CANVAS_HERO.read_text(encoding="utf-8")
    hero, n = re.subn(r'(<g transform="translate\(1238 128\) scale\(\.56\)">).*?(</g></g>)',
                      lambda m: m.group(1) + mark(PALETTES["favicon"]) + m.group(2), hero, flags=re.S)
    assert n == 1, "no mark found on the hero board"
    CANVAS_HERO.write_text(hero, encoding="utf-8", newline="")

    # The statement on the section board signs with the mascot in the seal ring, on navy.
    about = CANVAS_ABOUT.read_text(encoding="utf-8")
    stamps = [0]

    def restamp(m):
        stamps[0] += 1
        ids = (f"board-top-{stamps[0]}", f"board-bot-{stamps[0]}")
        return m.group(1) + seal(PALETTES["medal"], ids) + "</svg>"

    about, n = re.subn(r'(<svg viewBox="0 0 200 200"[^>]*>).*?</svg>', restamp, about, flags=re.S)
    assert n, "no stamp found on the section board"
    CANVAS_ABOUT.write_text(about, encoding="utf-8", newline="")


CHROMES = [os.environ.get("CHROME", ""),
           r"C:\Program Files\Google\Chrome\Application\chrome.exe",
           r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
           "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
           "google-chrome", "chromium"]


def shoot(url, out, width, height, transparent=False):
    chrome = next(c for c in CHROMES if c and (os.path.exists(c) or "/" not in c and "\\" not in c))
    args = [chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
            f"--window-size={width},{height}", "--virtual-time-budget=3000", f"--screenshot={out}", url]
    if transparent:
        args.insert(-1, "--default-background-color=00000000")
    subprocess.run(args, check=True, capture_output=True)


def export():
    """1024 px PNGs of both logos and both seals on transparent, and the README banner."""
    with tempfile.TemporaryDirectory() as tmp:
        for svg in ("logo", "logo-dark"):
            page = pathlib.Path(tmp) / f"{svg}.html"
            page.write_text(f'<style>html,body{{margin:0;background:transparent}}img{{display:block;width:1024px;'
                            f'height:1024px}}</style><img src="{(BRAND / (svg + ".svg")).as_uri()}">', encoding="utf-8")
            shoot(page.as_uri(), str(BRAND / f"{svg}.png"), 1024, 1024, transparent=True)
    with tempfile.TemporaryDirectory() as tmp:
        for svg in ("quality-seal", "quality-seal-dark"):
            page = pathlib.Path(tmp) / f"{svg}.html"
            page.write_text(f'<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Figtree:wght@600'
                            f'&display=swap"><style>html,body{{margin:0;background:transparent}}svg{{display:block;'
                            f'width:1024px;height:1024px}}</style>{(BRAND / (svg + ".svg")).read_text(encoding="utf-8")}',
                            encoding="utf-8")
            shoot(page.as_uri(), str(BRAND / f"{svg}.png"), 1024, 1024, transparent=True)
    shoot((ROOT / "design" / "logo" / "banner.html").as_uri(), str(BRAND / "banner.png"), 1800, 450)


if __name__ == "__main__":
    if "--symbol" in sys.argv:
        print(symbol())
        print(seal_symbol())
    else:
        write_files()
        if "--export" in sys.argv:
            export()
        print("wrote the brand SVGs and the sprite in", len(PAGES), "pages" + (", plus PNGs" if "--export" in sys.argv else ""))
