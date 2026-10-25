"""Generate the README cards and README.md from profile.json.

Usage: python3 scripts/build_cards.py

Standard library only. Every card is written twice, for GitHub's dark and
light themes, and README.md picks the right one with <picture>. Fonts are
embedded into each SVG because GitHub shows README images as <img>, which
can't load web fonts.
"""

import base64
import json
import pathlib
from html import escape

ROOT = pathlib.Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
CARDS = ASSETS / "cards"

THEMES = {
    "dark": {
        "bg": "#331D23", "raised": "#4A2A32", "accent": "#8B0725", "on_accent": "#F7EEEC",
        "prompt": "#F59AAB", "text": "#F7EEEC", "muted": "#CDB7BC", "dim": "#A68A91", "stroke": None,
    },
    "light": {
        "bg": "#FBF5F5", "raised": "#F1E3E6", "accent": "#8B0725", "on_accent": "#FBF5F5",
        "prompt": "#9E1030", "text": "#331D23", "muted": "#6B4E55", "dim": "#8C7177", "stroke": "#E8D6DA",
    },
}

# streak-stats.demolab.com colors per theme
STREAK = {
    "dark": {"background": "331D23", "border": "4A2A32", "stroke": "4A2A32", "ring": "8B0725", "fire": "F59AAB",
             "currStreakNum": "F7EEEC", "sideNums": "F7EEEC", "currStreakLabel": "F59AAB",
             "sideLabels": "CDB7BC", "dates": "A68A91", "hide_border": "true"},
    "light": {"background": "FBF5F5", "border": "E8D6DA", "stroke": "E8D6DA", "ring": "8B0725", "fire": "C0234A",
              "currStreakNum": "331D23", "sideNums": "331D23", "currStreakLabel": "9E1030",
              "sideLabels": "6B4E55", "dates": "8C7177", "hide_border": "false"},
}

WIDTH = 840
MONO_ADVANCE = 0.6  # Roboto Mono glyph width in em

FONTS = {
    "s": ("Geist", "100 900", "geist-subset.woff2",
          "font-family:Geist,system-ui,-apple-system,sans-serif"),
    "m4": ("Roboto Mono", "400", "roboto-mono-400-subset.woff2",
           "font-family:'Roboto Mono',ui-monospace,Menlo,monospace;font-weight:400"),
    "m5": ("Roboto Mono", "500", "roboto-mono-500-subset.woff2",
           "font-family:'Roboto Mono',ui-monospace,Menlo,monospace;font-weight:500"),
}

TICK_CSS = (
    ".tick{opacity:0;animation:tick 18s infinite}.tick.first{opacity:1}"
    "@keyframes tick{0%{opacity:0;transform:translateY(6px)}1.6%{opacity:1;transform:none}"
    "9.6%{opacity:1;transform:none}11.1%{opacity:0;transform:translateY(-6px)}100%{opacity:0}}"
    "@media (prefers-reduced-motion:reduce){.tick{animation:none}}"
)


def b64(path, mime):
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()


def img(name):
    path = ASSETS / "img" / name
    return b64(path, "image/svg+xml" if path.suffix == ".svg" else "image/png" if path.suffix == ".png" else "image/jpeg")


def svg(t, width, height, label, body, fill=None, radius=16, extra_css=""):
    """Wrap a card body, embedding only the font faces it uses."""
    css = []
    for cls, (family, weight, file, rule) in FONTS.items():
        if f'class="{cls}' in body or f' {cls}"' in body or f' {cls} ' in body:
            css.append(f"@font-face{{font-family:'{family}';font-weight:{weight};"
                       f"src:url({b64(ASSETS / 'fonts' / file, 'font/woff2')}) format('woff2')}}.{cls}{{{rule}}}")
    stroke = f' stroke="{t["stroke"]}"' if t["stroke"] else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" aria-label="{escape(label)}">\n'
            f"<title>{escape(label)}</title>\n<style>{''.join(css)}{extra_css}</style>\n"
            f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="{radius}" '
            f'fill="{fill or t["bg"]}"{stroke}/>\n{body}\n</svg>\n')


def text(x, y, value, cls, size, fill, weight=None, anchor=None, extra=""):
    attrs = f'x="{x}" y="{y}" class="{cls}" font-size="{size}" fill="{fill}"'
    if weight:
        attrs += f' font-weight="{weight}"'
    if anchor:
        attrs += f' text-anchor="{anchor}"'
    return f"<text {attrs}{extra}>{value}</text>"


def tile(t, clip_id, href, x, y, size, radius):
    """A rounded image tile, outlined in the light theme so pale logos keep an edge."""
    out = (f'<clipPath id="{clip_id}"><rect x="{x}" y="{y}" width="{size}" height="{size}" rx="{radius}"/></clipPath>'
           f'<image href="{href}" x="{x}" y="{y}" width="{size}" height="{size}" clip-path="url(#{clip_id})"/>')
    if t["stroke"]:
        out += (f'<rect x="{x + 0.5}" y="{y + 0.5}" width="{size - 1}" height="{size - 1}" rx="{radius}" '
                f'fill="none" stroke="{t["stroke"]}"/>')
    return out


# ── cards ────────────────────────────────────────────────────────────────

def hero(p, t):
    step = 18 / len(p["taglines"])
    ticks = [
        f'<text class="tick s{" first" if i == 0 else ""}" x="40" y="164" font-size="26" font-weight="500" '
        f'style="animation-delay:{i * step:g}s"><tspan fill-opacity="0">and I\'m</tspan> '
        f'<tspan fill="{t["text"]}">{escape(line)}</tspan></text>'
        for i, line in enumerate(p["taglines"])
    ]
    chips, x = [], 40
    for chip in p["chips"]:
        w = round(len(chip["label"]) * 12 * MONO_ADVANCE + 28)
        accent = chip.get("accent")
        chips.append(f'<rect x="{x}" y="190" width="{w}" height="28" rx="14" '
                     f'fill="{t["accent"] if accent else t["raised"]}"/>')
        chips.append(text(x + w / 2, 208, escape(chip["label"]), "m5", 12,
                          t["on_accent"] if accent else t["text"], anchor="middle"))
        x += w + 8
    body = "\n".join([
        text(40, 62, "&gt; my name is", "m5", 15, t["prompt"]),
        text(40, 120, f'{escape(p["name"])}<tspan fill="{t["prompt"]}">.</tspan>', "s", 52, t["text"], 600,
             extra=' letter-spacing="-1.2"'),
        text(40, 164, "and I'm", "s", 26, t["muted"], 500),
        *ticks,
        *chips,
    ])
    alt = f'{p["name"]}, and I\'m {p["taglines"][0]} ' + " · ".join(c["label"] for c in p["chips"])
    return svg(t, WIDTH, 250, alt, body, extra_css=TICK_CSS)


def pill(link, t):
    external = link.get("external")
    w = round(len(link["label"]) * 13 * MONO_ADVANCE + 32 + (18 if external else 0))
    accent = link.get("accent")
    arrow = '<tspan class="s" dx="6">↗</tspan>' if external else ""
    body = text(16, 23, f'{escape(link["label"])}{arrow}', "m5", 13, t["on_accent"] if accent else t["text"])
    fill = t["accent"] if accent else t["raised"]
    return svg({**t, "stroke": None}, w, 36, link["label"], body, fill=fill, radius=18)


def strip(section, t, right, label):
    """Slim card: logo, eyebrow, title, two lines, artwork on the right."""
    body = "\n".join([
        tile(t, "logo", img(section["logo"]), 28, 28, 64, 16),
        text(112, 50, escape(section["eyebrow"]), "m5", 13, t["prompt"]),
        text(112, 80, escape(section["title"]), "s", 22, t["text"], 600, extra=' letter-spacing="-0.3"'),
        f'<text class="s" font-size="14" fill="{t["muted"]}">'
        + "".join(f'<tspan x="112" y="{108 + i * 20}">{escape(l)}</tspan>' for i, l in enumerate(section["lines"]))
        + "</text>",
        *right,
    ])
    return svg(t, WIDTH, 156, label, body)


def school(p, t):
    s = p["school"]
    right = []
    for i, (badge, rot) in enumerate(zip(s["badges"], [-6, 4, -3])):
        x = 580 + i * 70
        right.append(f'<image href="{img(badge)}" x="{x}" y="32" width="92" height="92" '
                     f'transform="rotate({rot} {x + 46} 78)"/>')
    return strip(s, t, right, f'{s["eyebrow"]}: {s["title"]} ' + " ".join(s["lines"]))


def studio(p, t):
    s = p["studio"]
    right = []
    for i, app in enumerate(s["apps"]):
        x = 576 + i * 82
        right.append(tile(t, f"app{i}", img(app["icon"]), x, 34, 64, 15))
        right.append(text(x + 32, 120, escape(app["label"]), "m4", 11, t["dim"], anchor="middle"))
    names = ", ".join(a["name"] for a in s["apps"])
    return strip(s, t, right, f'{s["eyebrow"]}: {s["title"]} {names}')


# ── README ───────────────────────────────────────────────────────────────

def picture(dark, light, alt, size='width="100%"'):
    return (f'<picture><source media="(prefers-color-scheme: dark)" srcset="{dark}">'
            f'<img src="{light}" {size} alt="{escape(alt)}"></picture>')


def readme(p):
    user = p["user"]
    cards = f"https://raw.githubusercontent.com/{user}/{user}/main/assets/cards"
    snake = f"https://raw.githubusercontent.com/{user}/{user}/output"

    def card(name, alt, size='width="100%"'):
        return picture(f"{cards}/{name}.svg", f"{cards}/{name}-light.svg", alt, size)

    def streak(theme):
        query = "&".join(f"{k}={v}" for k, v in STREAK[theme].items())
        return f"https://streak-stats.demolab.com?user={user}&{query}&border_radius=16&card_width=840"

    pill_size = 'height="36"'
    pills = "\n".join(f'  <a href="{l["url"]}">{card("link-" + l["id"], l["label"], pill_size)}</a>'
                      for l in p["links"])
    rows = "\n".join(f"- **{label}** · {value}" for label, value in p["about"]["rows"])
    s, st = p["school"], p["studio"]
    return f"""<!-- Generated by scripts/build_cards.py from profile.json. Edit those, not this file. -->

<p align="center">
  {card("hero", f'{p["name"]}, ' + " · ".join(c["label"] for c in p["chips"]))}
</p>

<p align="center">
{pills}
</p>

{rows}

<a href="{st["url"]}">{card("studio", f'{st["eyebrow"]}: {st["title"]} ' + ", ".join(a["name"] for a in st["apps"]))}</a>

<a href="{s["url"]}">{card("42", f'{s["eyebrow"]}: {s["title"]} ' + " ".join(s["lines"]))}</a>

<p align="center">
  {picture(f"{snake}/github-contribution-grid-snake-dark.svg", f"{snake}/github-contribution-grid-snake.svg",
           "Snake eating my contribution graph")}
</p>

<p align="center">
  {picture(streak("dark"), streak("light"), "GitHub streak stats")}
</p>
"""


def main():
    p = json.loads((ROOT / "profile.json").read_text())
    CARDS.mkdir(parents=True, exist_ok=True)
    for old in CARDS.glob("*.svg"):
        old.unlink()
    count = 0
    for theme, t in THEMES.items():
        suffix = "" if theme == "dark" else "-light"
        cards = {"hero": hero(p, t), "42": school(p, t), "studio": studio(p, t)}
        cards.update({f"link-{l['id']}": pill(l, t) for l in p["links"]})
        for name, content in cards.items():
            (CARDS / f"{name}{suffix}.svg").write_text(content)
            count += 1
    (ROOT / "README.md").write_text(readme(p))
    print(f"wrote {count} cards and README.md")


if __name__ == "__main__":
    main()
