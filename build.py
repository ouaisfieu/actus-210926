#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Générateur du site « 21.09.26 ».

Zéro dépendance : bibliothèque standard de Python uniquement.
Entrée  : data/*.json + content/<lang>/**/*.md
Sortie  : docs/  (c'est ce dossier que GitHub Pages sert)

    python3 build.py            construit tout
    python3 build.py --clean    efface docs/ avant de construire

Le site est bilingue (fr-BE / nl-BE). Toute page a une alternative dans
l'autre langue, déclarée en <link rel="alternate" hreflang>.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import sys
import unicodedata
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
CONTENT = ROOT / "content"
ASSETS = ROOT / "assets"
OUT = ROOT / "docs"

LANGS = ("fr", "nl")

# --------------------------------------------------------------------------
# petits utilitaires
# --------------------------------------------------------------------------


def load_json(name: str):
    with open(DATA / name, encoding="utf-8") as fh:
        return json.load(fh)


def esc(text: str) -> str:
    """Échappe pour le HTML, et remplace l'apostrophe droite par l'apostrophe
    typographique — sauf dans les URL, où elle serait un caractère significatif."""
    t = str(text)
    if not t.startswith(("http://", "https://", "mailto:")):
        t = t.replace("'", "’")
    return html.escape(t, quote=True)


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", str(text))
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text or "x"


def tr(value, lang: str, fallback: str = "") -> str:
    """Un champ peut être une chaîne ou un dict {fr:…, nl:…}."""
    if value is None:
        return fallback
    if isinstance(value, dict):
        return value.get(lang) or value.get("fr") or fallback
    return str(value)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def fmt_num(value, lang: str, decimals: int = 0) -> str:
    """Espace insécable fine comme séparateur de milliers, virgule décimale."""
    s = f"{value:,.{decimals}f}"
    s = s.replace(",", " ").replace(".", ",")
    return s


MONTHS = {
    "fr": ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
           "août", "septembre", "octobre", "novembre", "décembre"],
    "nl": ["januari", "februari", "maart", "april", "mei", "juni", "juli",
           "augustus", "september", "oktober", "november", "december"],
}


def human_date(iso: str, lang: str) -> str:
    try:
        parts = [int(p) for p in iso.split("-")]
    except ValueError:
        return iso
    if len(parts) == 1:
        return str(parts[0])
    if len(parts) == 2:
        return f"{MONTHS[lang][parts[1] - 1]} {parts[0]}"
    y, m, d = parts
    if lang == "fr":
        day = "1er" if d == 1 else str(d)
        return f"{day} {MONTHS['fr'][m - 1]} {y}"
    return f"{d} {MONTHS['nl'][m - 1]} {y}"


# --------------------------------------------------------------------------
# mini-Markdown
# --------------------------------------------------------------------------

INLINE_CODE = re.compile(r"`([^`]+)`")
BOLD = re.compile(r"\*\*([^*]+)\*\*")
ITALIC = re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)")
LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
REF_SOURCE = re.compile(r"\[\[s:([a-z0-9\-]+)\]\]")
REF_ENTITY = re.compile(r"\[\[e:([a-z0-9\-]+)(?:\|([^\]]+))?\]\]")
REF_TERM = re.compile(r"\[\[g:([a-z0-9\-]+)(?:\|([^\]]+))?\]\]")
REF_PAGE = re.compile(r"\[\[p:([a-z0-9\-]+)\|([^\]]+)\]\]")
REF_DOSSIER = re.compile(r"\[\[d:([a-z0-9\-]+)\|([^\]]+)\]\]")
BLOCK_DIRECTIVE = re.compile(r"^\{\{(chart|table|figure):([a-z0-9\-]+)\}\}$")
CALLOUT_OPEN = re.compile(r"^:::\s*(fait|analyse|incertitude|contradiction|chiffre)\s*(?:\"([^\"]*)\")?\s*$")


class Renderer:
    """Rend le Markdown maison. Collecte les notes de bas de page au passage."""

    def __init__(self, ctx, lang: str, depth: int):
        self.ctx = ctx
        self.lang = lang
        self.depth = depth          # profondeur du fichier, pour les chemins relatifs
        self.footnotes: list[str] = []   # ids de sources, dans l'ordre d'apparition
        self.ancres: set[int] = set()    # numéros déjà porteurs d'un id
        self.mentioned: set[str] = set()  # entités citées
        self.headings: list[tuple[str, str]] = []  # (id, texte) pour le sommaire

    # -- chemins ---------------------------------------------------------
    def rel(self, target: str) -> str:
        prefix = "../" * self.depth
        return (prefix + target.lstrip("/")) if target else (prefix or "./")

    # -- notes -----------------------------------------------------------
    def footnote_ref(self, sid: str) -> str:
        """Renvoi de note. L'ancre de retour n'est posée qu'une fois par page :
        un même numéro peut apparaître plusieurs fois dans le texte."""
        if sid not in self.ctx.sources:
            raise KeyError(f"source inconnue : {sid}")
        if sid not in self.footnotes:
            self.footnotes.append(sid)
            self.ctx.usage[self.lang][sid] += 1
        n = self.footnotes.index(sid) + 1
        ancre = "" if n in self.ancres else f' id="renvoi-{n}"'
        self.ancres.add(n)
        return (f'<sup class="fn"><a href="#note-{n}"{ancre} '
                f'aria-describedby="notes-titre">{n}</a></sup>')

    # -- inline ----------------------------------------------------------
    def inline(self, text: str) -> str:
        placeholders: list[str] = []

        def stash(markup: str) -> str:
            placeholders.append(markup)
            return f"\x00{len(placeholders) - 1}\x00"

        def on_source(m):
            return stash(self.footnote_ref(m.group(1)))

        def on_entity(m):
            eid, label = m.group(1), m.group(2)
            ent = self.ctx.entities.get(eid)
            if ent is None:
                raise KeyError(f"acteur inconnu : {eid}")
            self.mentioned.add(eid)
            text_ = label or tr(ent["name"], self.lang)
            href = self.rel(self.ctx.path_for("entity", eid, self.lang))
            return stash(f'<a class="lien-acteur" href="{href}">{esc(text_)}</a>')

        def on_term(m):
            tid, label = m.group(1), m.group(2)
            term = self.ctx.glossary.get(tid)
            if term is None:
                raise KeyError(f"terme de glossaire inconnu : {tid}")
            text_ = label or tr(term["term"], self.lang)
            href = self.rel(self.ctx.path_for("glossary", None, self.lang)) + "#" + tid
            return stash(
                f'<a class="lien-terme" href="{href}" '
                f'title="{esc(tr(term["short"], self.lang))}">{esc(text_)}</a>'
            )

        def label_markup(raw: str) -> str:
            """Formate un libellé de lien sans relancer la substitution des
            marqueurs : ceux-ci sont résolus par la passe englobante."""
            out = esc(raw)
            out = BOLD.sub(lambda mm: f"<strong>{mm.group(1)}</strong>", out)
            out = ITALIC.sub(lambda mm: f"<em>{mm.group(1)}</em>", out)
            return out

        def on_page(m):
            key, label = m.group(1), m.group(2)
            href = self.rel(self.ctx.path_for(key, None, self.lang))
            return stash(f'<a href="{esc(href)}">{label_markup(label)}</a>')

        def on_dossier(m):
            did, label = m.group(1), m.group(2)
            href = self.rel(self.ctx.path_for("dossier", did, self.lang))
            return stash(f'<a href="{esc(href)}">{label_markup(label)}</a>')

        def on_link(m):
            label, href = m.group(1), m.group(2)
            if href.startswith(("http://", "https://")):
                return stash(
                    f'<a href="{esc(href)}" rel="nofollow noopener" '
                    f'target="_blank">{label_markup(label)}</a>'
                )
            return stash(f'<a href="{esc(self.rel(href))}">{label_markup(label)}</a>')

        text = INLINE_CODE.sub(lambda m: stash(f"<code>{esc(m.group(1))}</code>"), text)
        text = REF_SOURCE.sub(on_source, text)
        text = REF_ENTITY.sub(on_entity, text)
        text = REF_TERM.sub(on_term, text)
        text = REF_PAGE.sub(on_page, text)
        text = REF_DOSSIER.sub(on_dossier, text)
        text = LINK.sub(on_link, text)
        text = esc(text)
        text = BOLD.sub(lambda m: f"<strong>{m.group(1)}</strong>", text)
        text = ITALIC.sub(lambda m: f"<em>{m.group(1)}</em>", text)
        text = text.replace("--", "—")
        # espace fine insécable devant la ponctuation double, en français
        if self.lang == "fr":
            text = re.sub(r"\s+([;:!?%])", " \\1", text)
            text = text.replace("« ", "« ").replace(" »", " »")
        text = re.sub(r"\x00(\d+)\x00", lambda m: placeholders[int(m.group(1))], text)
        return text

    # -- blocs -----------------------------------------------------------
    def render(self, body: str) -> str:
        lines = body.split("\n")
        out: list[str] = []
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            if not stripped:
                i += 1
                continue

            m = CALLOUT_OPEN.match(stripped)
            if m:
                kind, title = m.group(1), m.group(2)
                inner: list[str] = []
                i += 1
                while i < len(lines) and lines[i].strip() != ":::":
                    inner.append(lines[i])
                    i += 1
                i += 1
                default_titles = self.ctx.site["callouts"][kind]
                label = title or tr(default_titles, self.lang)
                out.append(
                    f'<aside class="bloc bloc-{kind}">'
                    f'<p class="bloc-titre">{esc(label)}</p>'
                    f"{self.render(chr(10).join(inner))}</aside>"
                )
                continue

            m = BLOCK_DIRECTIVE.match(stripped)
            if m:
                kind, ident = m.group(1), m.group(2)
                out.append(self.ctx.render_figure(kind, ident, self))
                i += 1
                continue

            if stripped.startswith("#"):
                level = len(stripped) - len(stripped.lstrip("#"))
                text = stripped[level:].strip()
                anchor = slugify(text)[:60]
                if level == 2:
                    self.headings.append((anchor, text))
                out.append(
                    f'<h{level} id="{anchor}">{self.inline(text)}</h{level}>'
                )
                i += 1
                continue

            if stripped.startswith("> "):
                inner = []
                while i < len(lines) and lines[i].strip().startswith(">"):
                    inner.append(lines[i].strip()[1:].lstrip())
                    i += 1
                out.append(f"<blockquote>{self.render(chr(10).join(inner))}</blockquote>")
                continue

            if stripped.startswith("|"):
                rows = []
                while i < len(lines) and lines[i].strip().startswith("|"):
                    rows.append(lines[i].strip())
                    i += 1
                out.append(self.table(rows))
                continue

            if re.match(r"^[-*]\s+", stripped):
                items = []
                while i < len(lines) and re.match(r"^[-*]\s+", lines[i].strip()):
                    items.append(re.sub(r"^[-*]\s+", "", lines[i].strip()))
                    i += 1
                lis = "".join(f"<li>{self.inline(it)}</li>" for it in items)
                out.append(f"<ul>{lis}</ul>")
                continue

            if re.match(r"^\d+\.\s+", stripped):
                items = []
                while i < len(lines) and re.match(r"^\d+\.\s+", lines[i].strip()):
                    items.append(re.sub(r"^\d+\.\s+", "", lines[i].strip()))
                    i += 1
                lis = "".join(f"<li>{self.inline(it)}</li>" for it in items)
                out.append(f"<ol>{lis}</ol>")
                continue

            para = [stripped]
            i += 1
            while i < len(lines) and lines[i].strip() and not re.match(
                r"^(#|\||>|[-*]\s|\d+\.\s|:::|\{\{)", lines[i].strip()
            ):
                para.append(lines[i].strip())
                i += 1
            out.append(f"<p>{self.inline(' '.join(para))}</p>")

        return "".join(out)

    def table(self, rows: list[str]) -> str:
        def cells(row: str) -> list[str]:
            return [c.strip() for c in row.strip().strip("|").split("|")]

        header = cells(rows[0])
        body_rows = [cells(r) for r in rows[2:]] if len(rows) > 2 else []
        aligns = []
        if len(rows) > 1 and set(rows[1].replace("|", "").replace(" ", "")) <= set(":-"):
            for spec in cells(rows[1]):
                aligns.append("num" if spec.endswith(":") and not spec.startswith(":") else "")
        else:
            aligns = [""] * len(header)
            body_rows = [cells(r) for r in rows[1:]]

        th = "".join(
            f'<th scope="col"{f" class={a}" if a else ""}>{self.inline(c)}</th>'
            for c, a in zip(header, aligns + [""] * len(header))
        )
        trs = []
        for row in body_rows:
            tds = []
            for idx, cell in enumerate(row):
                a = aligns[idx] if idx < len(aligns) else ""
                cls = f' class="{a}"' if a else ""
                if idx == 0:
                    tds.append(f'<th scope="row">{self.inline(cell)}</th>')
                else:
                    tds.append(f"<td{cls}>{self.inline(cell)}</td>")
            trs.append("<tr>" + "".join(tds) + "</tr>")
        return (
            '<div class="table-wrap"><table><thead><tr>' + th + "</tr></thead>"
            "<tbody>" + "".join(trs) + "</tbody></table></div>"
        )


# --------------------------------------------------------------------------
# graphiques SVG accessibles
# --------------------------------------------------------------------------

# Palette d'Okabe & Ito : conçue pour rester distinguable en vision
# deutéranope, protanope et tritanope. Jamais le jaune pour du texte.
SERIES_COLORS = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#56B4E9"]
MARKERS = ["circle", "square", "triangle", "diamond", "cross"]


def svg_text(x, y, content, cls="", anchor="middle", extra=""):
    a = f' text-anchor="{anchor}"' if anchor else ""
    c = f' class="{cls}"' if cls else ""
    return f'<text x="{x:.1f}" y="{y:.1f}"{a}{c}{extra}>{esc(content)}</text>'


def marker(shape: str, x: float, y: float, color: str, r: float = 4.0) -> str:
    if shape == "square":
        return f'<rect x="{x-r:.1f}" y="{y-r:.1f}" width="{2*r:.1f}" height="{2*r:.1f}" fill="{color}"/>'
    if shape == "triangle":
        return (f'<polygon points="{x:.1f},{y-r*1.2:.1f} {x-r:.1f},{y+r*0.8:.1f} '
                f'{x+r:.1f},{y+r*0.8:.1f}" fill="{color}"/>')
    if shape == "diamond":
        return (f'<polygon points="{x:.1f},{y-r*1.3:.1f} {x+r*1.1:.1f},{y:.1f} '
                f'{x:.1f},{y+r*1.3:.1f} {x-r*1.1:.1f},{y:.1f}" fill="{color}"/>')
    if shape == "cross":
        return (f'<path d="M{x-r:.1f},{y-r:.1f}L{x+r:.1f},{y+r:.1f}M{x-r:.1f},{y+r:.1f}'
                f'L{x+r:.1f},{y-r:.1f}" stroke="{color}" stroke-width="2.4" fill="none"/>')
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{color}"/>'


def nice_ceiling(value: float) -> float:
    if value <= 0:
        return 1.0
    import math
    exp = math.floor(math.log10(value))
    base = 10 ** exp
    for step in (1, 1.1, 1.2, 1.25, 1.4, 1.5, 1.6, 1.75, 2, 2.25,
                 2.5, 3, 3.5, 4, 5, 6, 7.5, 8, 10):
        if value <= step * base:
            return step * base
    return 10 * base


def build_chart(spec: dict, lang: str, uid: str) -> str:
    """Produit un <svg> autonome, accessible, sans dépendance."""
    kind = spec.get("kind", "bar")
    cats = spec["categories"]
    series = spec["series"]
    unit = tr(spec.get("unit", ""), lang)
    decimals = int(spec.get("decimals", 1))
    title = tr(spec["title"], lang)
    desc = tr(spec.get("desc", ""), lang)

    values = [v for s in series for v in s["values"] if v is not None]
    vmax = max(values + [spec.get("reference", {}).get("value", 0) or 0])
    vmin = min(values + [0])
    top = nice_ceiling(vmax * 1.08)
    bottom = 0 if vmin >= 0 else -nice_ceiling(abs(vmin) * 1.2)

    if kind == "hbar":
        W, rowh = 680, 30
        pad_l, pad_r, pad_t, pad_b = 190, 70, 14, 26
        H = pad_t + pad_b + rowh * len(cats)
        parts = []
        span = top - bottom
        for idx, cat in enumerate(cats):
            y = pad_t + idx * rowh
            parts.append(svg_text(pad_l - 10, y + rowh * 0.64, tr(cat, lang),
                                  cls="ct-lab", anchor="end"))
            for si, s in enumerate(series):
                v = s["values"][idx]
                if v is None:
                    continue
                barh = (rowh - 10) / len(series)
                by = y + 5 + si * barh
                bw = (v - bottom) / span * (W - pad_l - pad_r)
                color = SERIES_COLORS[si % len(SERIES_COLORS)]
                parts.append(
                    f'<rect x="{pad_l}" y="{by:.1f}" width="{max(bw,0):.1f}" '
                    f'height="{barh-2:.1f}" fill="{color}"><title>'
                    f'{esc(tr(cat, lang))} — {esc(tr(s["name"], lang))} : '
                    f'{esc(fmt_num(v, lang, decimals))}{esc(unit)}</title></rect>'
                )
                parts.append(svg_text(pad_l + max(bw, 0) + 6, by + barh * 0.62,
                                      f"{fmt_num(v, lang, decimals)}{unit}",
                                      cls="ct-val", anchor="start"))
        body = "".join(parts)
    else:
        W, H = 680, 300
        pad_l, pad_r, pad_t, pad_b = 54, 18, 22, 52
        plot_w = W - pad_l - pad_r
        plot_h = H - pad_t - pad_b
        span = top - bottom

        def yy(v):
            return pad_t + plot_h - (v - bottom) / span * plot_h

        parts = []
        ticks = 4
        for t in range(ticks + 1):
            v = bottom + span * t / ticks
            y = yy(v)
            parts.append(f'<line class="ct-grid" x1="{pad_l}" y1="{y:.1f}" '
                         f'x2="{W-pad_r}" y2="{y:.1f}"/>')
            parts.append(svg_text(pad_l - 8, y + 4, fmt_num(v, lang, decimals),
                                  cls="ct-ax", anchor="end"))

        step = plot_w / len(cats)
        for idx, cat in enumerate(cats):
            cx = pad_l + step * (idx + 0.5)
            parts.append(svg_text(cx, H - pad_b + 18, tr(cat, lang), cls="ct-ax"))

        ref = spec.get("reference")
        repere = []
        if ref:
            ry = yy(ref["value"])
            etiquette = tr(ref["label"], lang)
            largeur_lab = 6.2 * len(etiquette) + 12
            repere.append(f'<line class="ct-ref" x1="{pad_l}" y1="{ry:.1f}" '
                          f'x2="{W-pad_r}" y2="{ry:.1f}"/>')
            repere.append(f'<rect class="ct-ref-fond" x="{pad_l + 4}" '
                          f'y="{ry - 19:.1f}" width="{largeur_lab:.0f}" height="16" '
                          f'rx="2"/>')
            repere.append(svg_text(pad_l + 10, ry - 7, etiquette,
                                   cls="ct-ref-lab", anchor="start"))

        if kind in ("bar", "grouped"):
            n = len(series)
            gw = step * 0.66
            bw = gw / n
            for si, s in enumerate(series):
                color = SERIES_COLORS[si % len(SERIES_COLORS)]
                for idx, v in enumerate(s["values"]):
                    if v is None:
                        continue
                    x = pad_l + step * (idx + 0.5) - gw / 2 + si * bw
                    y0, y1 = yy(max(v, 0)), yy(min(v, 0))
                    parts.append(
                        f'<rect x="{x:.1f}" y="{y0:.1f}" width="{bw-2:.1f}" '
                        f'height="{max(y1-y0,1):.1f}" fill="{color}"><title>'
                        f'{esc(tr(cats[idx], lang))} — {esc(tr(s["name"], lang))} : '
                        f'{esc(fmt_num(v, lang, decimals))}{esc(unit)}</title></rect>'
                    )
                    if n == 1 or spec.get("label_bars"):
                        parts.append(svg_text(x + bw / 2 - 1, y0 - 6,
                                              fmt_num(v, lang, decimals),
                                              cls="ct-val"))
        else:  # line
            for si, s in enumerate(series):
                color = SERIES_COLORS[si % len(SERIES_COLORS)]
                pts = [(pad_l + step * (i + 0.5), yy(v))
                       for i, v in enumerate(s["values"]) if v is not None]
                d = "M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
                parts.append(f'<path d="{d}" fill="none" stroke="{color}" '
                             f'stroke-width="2.6" stroke-linejoin="round"/>')
                for (x, y), v in zip(pts, [v for v in s["values"] if v is not None]):
                    parts.append(marker(MARKERS[si % len(MARKERS)], x, y, color))
                if pts:
                    parts.append(svg_text(pts[-1][0], pts[-1][1] - 12,
                                          tr(s["name"], lang), cls="ct-val",
                                          anchor="end"))
        parts.extend(repere)
        body = "".join(parts)

    legend = ""
    if len(series) > 1:
        chips = []
        for si, s in enumerate(series):
            color = SERIES_COLORS[si % len(SERIES_COLORS)]
            shape = ('<svg width="14" height="14" aria-hidden="true">'
                     + marker(MARKERS[si % len(MARKERS)], 7, 7, color, 5) + "</svg>"
                     if kind == "line"
                     else f'<span class="chip" style="background:{color}"></span>')
            chips.append(f'<li>{shape}{esc(tr(s["name"], lang))}</li>')
        legend = f'<ul class="legende">{"".join(chips)}</ul>'

    tid, did = f"t-{uid}", f"d-{uid}"
    svg = (
        f'<svg viewBox="0 0 {W} {H}" class="graph" role="img" '
        f'aria-labelledby="{tid} {did}" preserveAspectRatio="xMidYMid meet">'
        f'<title id="{tid}">{esc(title)}</title>'
        f'<desc id="{did}">{esc(desc)}</desc>{body}</svg>'
    )
    return legend + svg


# --------------------------------------------------------------------------
# contexte du site
# --------------------------------------------------------------------------


class Site:
    def __init__(self):
        self.site = load_json("site.json")
        self.sources = {s["id"]: s for s in load_json("sources.json")}
        self.entities = {e["id"]: e for e in load_json("entities.json")}
        self.glossary = {g["id"]: g for g in load_json("glossary.json")}
        self.figures = {f["id"]: f for f in load_json("figures.json")}
        self.timeline = sorted(load_json("timeline.json"), key=lambda e: e["date"])
        self.corrections = load_json("corrections.json")
        self.base = self.site["base"].rstrip("/")
        self.dossiers = {lang: [] for lang in LANGS}
        self.mentions = defaultdict(lambda: defaultdict(list))  # entity -> lang -> pages
        self.search = {lang: [] for lang in LANGS}
        self.usage = {lang: defaultdict(int) for lang in LANGS}
        self.figure_counter = 0

    # -- chemins ---------------------------------------------------------
    def prefix(self, lang: str) -> str:
        return "" if lang == "fr" else "nl/"

    def path_for(self, kind: str, ident, lang: str) -> str:
        p = self.prefix(lang)
        names = {
            "fr": {"dossiers": "dossiers", "entities": "acteurs",
                   "timeline": "chronologie", "glossary": "glossaire",
                   "sources": "sources", "method": "methode", "about": "a-propos",
                   "indicators": "indicateurs", "data": "donnees",
                   "search": "recherche"},
            "nl": {"dossiers": "dossiers", "entities": "actoren",
                   "timeline": "chronologie", "glossary": "woordenlijst",
                   "sources": "bronnen", "method": "methode", "about": "over",
                   "indicators": "indicatoren", "data": "data",
                   "search": "zoeken"},
        }[lang]
        if kind == "home":
            return p or ""
        if kind == "dossier":
            return f"{p}{names['dossiers']}/{ident}.html"
        if kind == "dossiers":
            return f"{p}{names['dossiers']}/"
        if kind == "entity":
            return f"{p}{names['entities']}/{ident}.html"
        if kind == "entities":
            return f"{p}{names['entities']}/"
        return f"{p}{names[kind]}.html"

    def url_for(self, kind: str, ident, lang: str) -> str:
        return f"{self.base}/{self.path_for(kind, ident, lang)}"

    # -- figures ---------------------------------------------------------
    def render_figure(self, kind: str, ident: str, r: Renderer) -> str:
        if ident not in self.figures:
            raise KeyError(f"figure inconnue : {ident}")
        spec = self.figures[ident]
        lang = r.lang
        self.figure_counter += 1
        uid = f"{ident}-{self.figure_counter}"
        title = tr(spec["title"], lang)
        note = tr(spec.get("note", ""), lang)
        refs = "".join(r.footnote_ref(sid) for sid in spec.get("sources", []))

        if kind == "table" or spec.get("kind") == "table":
            inner = self.data_table(spec, lang, caption=title)
            return (f'<figure class="fig">{inner}'
                    f'<figcaption>{esc(note)} {refs}</figcaption></figure>')

        chart = build_chart(spec, lang, uid)
        table = self.data_table(spec, lang, caption=None)
        label = tr(self.site["ui"]["chart_data"], lang)
        return (
            f'<figure class="fig"><figcaption class="fig-titre">{esc(title)}</figcaption>'
            f"{chart}"
            f'<details class="donnees"><summary>{esc(label)}</summary>{table}</details>'
            f'<figcaption class="fig-note">{esc(note)} {refs}</figcaption></figure>'
        )

    def data_table(self, spec: dict, lang: str, caption) -> str:
        cats = spec["categories"]
        series = spec["series"]
        decimals = int(spec.get("decimals", 1))
        unit = tr(spec.get("unit", ""), lang)
        head = tr(spec.get("category_label", {"fr": "Année", "nl": "Jaar"}), lang)
        th = f'<th scope="col">{esc(head)}</th>' + "".join(
            f'<th scope="col" class="num">{esc(tr(s["name"], lang))}'
            f'{esc(" (" + unit.strip() + ")") if unit.strip() else ""}</th>'
            for s in series
        )
        rows = []
        for i, cat in enumerate(cats):
            tds = "".join(
                f'<td class="num">{esc(fmt_num(s["values"][i], lang, decimals)) if s["values"][i] is not None else "—"}</td>'
                for s in series
            )
            rows.append(f'<tr><th scope="row">{esc(tr(cat, lang))}</th>{tds}</tr>')
        cap = f"<caption>{esc(caption)}</caption>" if caption else ""
        return ('<div class="table-wrap"><table>' + cap + "<thead><tr>" + th
                + "</tr></thead><tbody>" + "".join(rows) + "</tbody></table></div>")


# --------------------------------------------------------------------------
# gabarits
# --------------------------------------------------------------------------


def nav_html(ctx: Site, lang: str, active: str, depth: int) -> str:
    prefix = "../" * depth
    items = []
    for key in ("home", "dossiers", "entities", "timeline", "indicators",
                "glossary", "sources", "method", "about"):
        label = tr(ctx.site["nav"][key], lang)
        href = prefix + ctx.path_for(key, None, lang)
        if key == "home" and not href.endswith("/"):
            href = href or "./"
        cur = ' aria-current="page"' if key == active else ""
        items.append(f'<li><a href="{esc(href)}"{cur}>{esc(label)}</a></li>')
    return "".join(items)


def page(ctx: Site, *, lang: str, path: str, title: str, description: str,
         body: str, jsonld: list, active: str = "", alternate: str | None = None,
         kicker: str = "", robots: str = "", extra_head: str = "") -> str:
    depth = path.count("/")
    prefix = "../" * depth

    def public(p: str) -> str:
        url = f"{ctx.base}/{p}"
        return url[: -len("index.html")] if url.endswith("/index.html") else url

    canonical = public(path)
    other = "nl" if lang == "fr" else "fr"
    alt_path = alternate
    site_name = tr(ctx.site["name"], lang)
    ui = ctx.site["ui"]

    alts = [
        f'<link rel="alternate" hreflang="{"fr-BE" if lang=="fr" else "nl-BE"}" '
        f'href="{esc(canonical)}">'
    ]
    if alt_path is not None:
        alt_url = public(alt_path)
        alts.append(
            f'<link rel="alternate" hreflang="{"nl-BE" if other=="nl" else "fr-BE"}" '
            f'href="{esc(alt_url)}">'
        )
        alts.append(f'<link rel="alternate" hreflang="x-default" '
                    f'href="{esc(canonical if lang=="fr" else alt_url)}">')

    lang_switch = ""
    if alt_path is not None:
        label = "Nederlands" if other == "nl" else "Français"
        lang_switch = (
            f'<a class="bascule-langue" hreflang="{other}-BE" '
            f'lang="{other}" href="{esc(prefix + alt_path)}">{label}</a>'
        )

    # une carte de partage par dossier, une carte générique pour le reste
    if "/dossiers/" in path:
        og_nom = f"{lang}-{Path(path).stem}"
    elif path in ("index.html", "nl/index.html"):
        og_nom = f"{lang}-accueil"
    else:
        og_nom = f"{lang}-defaut"
    og_image = f"{ctx.base}/og/{og_nom}.png"
    robots_tag = f'<meta name="robots" content="{robots}">' if robots else ""

    graph = json.dumps({"@context": "https://schema.org", "@graph": jsonld},
                       ensure_ascii=False, indent=1)

    feed = prefix + ("feed.xml" if lang == "fr" else "nl/feed.xml")
    search_href = prefix + ctx.path_for("search", None, lang)

    return f"""<!doctype html>
<html lang="{'fr-BE' if lang == 'fr' else 'nl-BE'}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{esc(canonical)}">
{"".join(alts)}
{robots_tag}
<meta property="og:type" content="{'article' if active == 'dossiers' else 'website'}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{esc(canonical)}">
<meta property="og:site_name" content="{esc(site_name)}">
<meta property="og:locale" content="{'fr_BE' if lang == 'fr' else 'nl_BE'}">
<meta property="og:image" content="{esc(og_image)}">
<meta name="twitter:card" content="summary_large_image">
<link rel="stylesheet" href="{prefix}assets/style.css">
<link rel="icon" href="{prefix}assets/icon.svg" type="image/svg+xml">
<link rel="manifest" href="{prefix}assets/manifest.webmanifest">
<link rel="alternate" type="application/atom+xml" title="{esc(site_name)}" href="{esc(feed)}">
{extra_head}
<script type="application/ld+json">
{graph}
</script>
</head>
<body>
<a class="saut" href="#contenu">{esc(tr(ui['skip'], lang))}</a>
<div class="bandeau"><div class="bandeau-i">
  <span>{esc(tr(ctx.site['strap'], lang))}</span>
  <span class="bandeau-outils">{lang_switch}
  <button class="bascule-theme" data-theme-toggle type="button" aria-pressed="false">
  <span data-theme-label>{esc(tr(ui['dark'], lang))}</span></button></span>
</div></div>
<header class="entete"><div class="entete-i">
  <p class="marque"><a href="{esc(prefix + (ctx.path_for('home', None, lang) or './'))}">
  <span class="marque-n">21</span><span class="marque-p">.09.</span><span class="marque-n">26</span></a></p>
  <p class="accroche">{esc(tr(ctx.site['tagline'], lang))}</p>
  <nav class="principale" aria-label="{esc(tr(ui['nav_label'], lang))}">
    <ul>{nav_html(ctx, lang, active, depth)}</ul>
  </nav>
  <form class="rech-rapide" role="search" action="{esc(search_href)}" method="get">
    <label for="q-{lang}">{esc(tr(ui['search'], lang))}</label>
    <input id="q-{lang}" name="q" type="search" autocomplete="off"
      placeholder="{esc(tr(ui['search_ph'], lang))}">
    <button type="submit">{esc(tr(ui['search_go'], lang))}</button>
  </form>
</div></header>
<main id="contenu">{f'<p class="surtitre">{esc(kicker)}</p>' if kicker else ''}
{body}
</main>
<footer class="pied"><div class="pied-i">
  <div class="pied-grille">
    <div><h2>{esc(tr(ui['foot_site'], lang))}</h2><ul>
      <li><a href="{esc(prefix + ctx.path_for('dossiers', None, lang))}">{esc(tr(ctx.site['nav']['dossiers'], lang))}</a></li>
      <li><a href="{esc(prefix + ctx.path_for('entities', None, lang))}">{esc(tr(ctx.site['nav']['entities'], lang))}</a></li>
      <li><a href="{esc(prefix + ctx.path_for('timeline', None, lang))}">{esc(tr(ctx.site['nav']['timeline'], lang))}</a></li>
      <li><a href="{esc(prefix + ctx.path_for('indicators', None, lang))}">{esc(tr(ctx.site['nav']['indicators'], lang))}</a></li>
    </ul></div>
    <div><h2>{esc(tr(ui['foot_check'], lang))}</h2><ul>
      <li><a href="{esc(prefix + ctx.path_for('sources', None, lang))}">{esc(tr(ctx.site['nav']['sources'], lang))}</a></li>
      <li><a href="{esc(prefix + ctx.path_for('method', None, lang))}">{esc(tr(ctx.site['nav']['method'], lang))}</a></li>
      <li><a href="{esc(prefix + ctx.path_for('data', None, lang))}">{esc(tr(ctx.site['nav']['data'], lang))}</a></li>
      <li><a href="{esc(feed)}">{esc(tr(ui['feed'], lang))}</a></li>
    </ul></div>
    <div><h2>{esc(tr(ui['foot_author'], lang))}</h2><ul>
      <li>{esc(tr(ctx.site['byline'], lang))}</li>
      <li>{esc(tr(ctx.site['supervision'], lang))}</li>
      <li><a href="{esc(prefix + ctx.path_for('about', None, lang))}">{esc(tr(ui['licence'], lang))}</a></li>
    </ul></div>
  </div>
  <p class="pied-legal">{esc(tr(ctx.site['legal'], lang))}</p>
</div></footer>
<script src="{prefix}assets/app.js" defer></script>
</body>
</html>
"""


# --------------------------------------------------------------------------
# blocs JSON-LD réutilisables
# --------------------------------------------------------------------------


def core_nodes(ctx: Site, lang: str) -> list:
    base = ctx.base
    return [
        {
            "@type": "WebSite",
            "@id": f"{base}/#site",
            "url": f"{base}/",
            "name": tr(ctx.site["name"], lang),
            "alternateName": tr(ctx.site["title"], lang),
            "description": tr(ctx.site["description"], lang),
            "inLanguage": ["fr-BE", "nl-BE"],
            "publisher": {"@id": f"{base}/#editeur"},
            "license": "https://creativecommons.org/licenses/by/4.0/",
            "potentialAction": {
                "@type": "SearchAction",
                "target": {
                    "@type": "EntryPoint",
                    "urlTemplate": f"{base}/{ctx.path_for('search', None, lang)}?q={{search_term_string}}",
                },
                "query-input": "required name=search_term_string",
            },
        },
        {
            "@type": "Person",
            "@id": f"{base}/#auteur",
            "name": "Claude (Anthropic)",
            "description": tr(ctx.site["author_desc"], lang),
            "affiliation": {"@type": "Organization", "name": "Anthropic",
                            "url": "https://www.anthropic.com/"},
        },
        {
            "@type": "Organization",
            "@id": f"{base}/#editeur",
            "name": tr(ctx.site["name"], lang),
            "url": f"{base}/",
        },
    ]


def citation_nodes(ctx: Site, ids: list[str]) -> list:
    out = []
    for sid in ids:
        s = ctx.sources[sid]
        node = {
            "@type": "CreativeWork",
            "@id": f"{ctx.base}/sources.html#{sid}",
            "name": s["title"],
            "url": s["url"],
        }
        if s.get("publisher"):
            node["publisher"] = {"@type": "Organization", "name": s["publisher"]}
        if s.get("date"):
            node["datePublished"] = s["date"]
        out.append(node)
    return out


# --------------------------------------------------------------------------
# chargement du contenu
# --------------------------------------------------------------------------


def parse_doc(path: Path) -> tuple[dict, str]:
    raw = path.read_text(encoding="utf-8")
    if not raw.startswith("---"):
        raise ValueError(f"en-tête manquant : {path}")
    _, meta, body = raw.split("---", 2)
    return json.loads(meta), body.strip()


def footnote_block(ctx: Site, r: Renderer, lang: str) -> str:
    if not r.footnotes:
        return ""
    items = []
    for n, sid in enumerate(r.footnotes, 1):
        s = ctx.sources[sid]
        bits = [f'<a href="{esc(s["url"])}" rel="nofollow noopener" target="_blank">{esc(s["title"])}</a>']
        meta = []
        if s.get("publisher"):
            meta.append(esc(s["publisher"]))
        if s.get("date"):
            meta.append(f'<time datetime="{esc(s["date"])}">{esc(human_date(s["date"], lang))}</time>')
        if s.get("kind"):
            meta.append(esc(tr(ctx.site["source_kinds"].get(s["kind"], s["kind"]), lang)))
        if meta:
            bits.append(" · ".join(meta))
        items.append(
            f'<li id="note-{n}">{" — ".join(bits)} '
            f'<a class="retour" href="#renvoi-{n}" aria-label="'
            f'{esc(tr(ctx.site["ui"]["back_to_text"], lang))}">↩</a></li>'
        )
    label = tr(ctx.site["ui"]["notes"], lang)
    return (f'<section class="notes" aria-labelledby="notes-titre">'
            f'<h2 id="notes-titre">{esc(label)}</h2>'
            f'<ol class="liste-notes">{"".join(items)}</ol></section>')


def strip_tags(markup: str) -> str:
    text = re.sub(r"<[^>]+>", " ", markup)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def build_dossiers(ctx: Site) -> dict:
    """Rend tous les dossiers et retourne {lang: [record, …]}."""
    result = {}
    for lang in LANGS:
        docs = []
        folder = CONTENT / lang / "dossiers"
        for f in sorted(folder.glob("*.md")):
            meta, body = parse_doc(f)
            r = Renderer(ctx, lang, depth=1 if lang == "fr" else 2)
            html_body = r.render(body)
            docs.append({
                "meta": meta, "html": html_body, "renderer": r,
                "slug": meta["id"], "file": f,
            })
        docs.sort(key=lambda d: d["meta"]["order"])
        result[lang] = docs
    return result


# --------------------------------------------------------------------------
# pages
# --------------------------------------------------------------------------


def render_dossier(ctx: Site, lang: str, doc: dict, prev_, next_) -> str:
    meta, r = doc["meta"], doc["renderer"]
    path = ctx.path_for("dossier", meta["id"], lang)
    alt = ctx.path_for("dossier", meta["id"], "nl" if lang == "fr" else "fr")
    ui = ctx.site["ui"]
    depth = path.count("/")
    prefix = "../" * depth

    toc = ""
    if len(r.headings) >= 3:
        lis = "".join(f'<li><a href="#{a}">{esc(t)}</a></li>' for a, t in r.headings)
        toc = (f'<nav class="sommaire" aria-labelledby="som-t">'
               f'<h2 id="som-t">{esc(tr(ui["toc"], lang))}</h2><ol>{lis}</ol></nav>')

    ents = sorted(r.mentioned, key=lambda e: tr(ctx.entities[e]["name"], lang))
    ent_html = ""
    if ents:
        chips = "".join(
            f'<li><a href="{esc(prefix + ctx.path_for("entity", e, lang))}">'
            f'{esc(tr(ctx.entities[e]["name"], lang))}</a></li>' for e in ents
        )
        ent_html = (f'<section class="acteurs-cites" aria-labelledby="ac-t">'
                    f'<h2 id="ac-t">{esc(tr(ui["mentioned"], lang))}</h2>'
                    f'<ul class="puces">{chips}</ul></section>')

    related = ""
    nav_bits = []
    if prev_:
        nav_bits.append(
            f'<a class="prec" href="{esc(prev_["meta"]["id"])}.html">'
            f'← {esc(tr(prev_["meta"]["title"], lang))}</a>')
    if next_:
        nav_bits.append(
            f'<a class="suiv" href="{esc(next_["meta"]["id"])}.html">'
            f'{esc(tr(next_["meta"]["title"], lang))} →</a>')
    if nav_bits:
        related = f'<nav class="entre-dossiers" aria-label="{esc(tr(ui["siblings"], lang))}">{"".join(nav_bits)}</nav>'

    ld = core_nodes(ctx, lang) + [
        {
            "@type": "Article",
            "@id": f"{ctx.base}/{path}#article",
            "headline": tr(meta["title"], lang),
            "alternativeHeadline": tr(meta.get("lede", ""), lang)[:110],
            "description": tr(meta["description"], lang),
            "url": f"{ctx.base}/{path}",
            "datePublished": meta.get("published", ctx.site["published"]),
            "dateModified": meta.get("updated", ctx.site["updated"]),
            "inLanguage": "fr-BE" if lang == "fr" else "nl-BE",
            "isPartOf": {"@id": f"{ctx.base}/#site"},
            "author": {"@id": f"{ctx.base}/#auteur"},
            "publisher": {"@id": f"{ctx.base}/#editeur"},
            "articleSection": tr(meta["section"], lang),
            "about": [{"@id": f"{ctx.base}/{ctx.path_for('entity', e, lang)}#id"}
                      for e in ents[:12]],
            "mentions": [{"@id": f"{ctx.base}/{ctx.path_for('entity', e, lang)}#id"}
                         for e in ents],
            "citation": [{"@id": f"{ctx.base}/sources.html#{s}"} for s in r.footnotes],
            "license": "https://creativecommons.org/licenses/by/4.0/",
        },
        {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1,
                 "name": tr(ctx.site["nav"]["home"], lang),
                 "item": ctx.url_for("home", None, lang)},
                {"@type": "ListItem", "position": 2,
                 "name": tr(ctx.site["nav"]["dossiers"], lang),
                 "item": ctx.url_for("dossiers", None, lang)},
                {"@type": "ListItem", "position": 3,
                 "name": tr(meta["title"], lang)},
            ],
        },
    ] + citation_nodes(ctx, r.footnotes)

    body = f"""
<article class="dossier">
<p class="surtitre">{esc(tr(meta['kicker'], lang))}</p>
<h1>{esc(tr(meta['title'], lang))}</h1>
<p class="chapo">{r.inline(tr(meta['lede'], lang))}</p>
<p class="signature"><span class="par">{esc(tr(ctx.site['byline'], lang))}</span> ·
<time datetime="{esc(meta.get('updated', ctx.site['updated']))}">{esc(human_date(meta.get('updated', ctx.site['updated']), lang))}</time> ·
<span class="duree">{esc(tr(ui['reading'], lang)).replace('{n}', str(max(1, len(strip_tags(doc['html']).split()) // 200)))}</span></p>
{toc}
<div class="corps">{doc['html']}</div>
{ent_html}
{footnote_block(ctx, r, lang)}
</article>
{related}
"""
    court = tr(meta.get("seo") or meta["title"], lang)
    return page(ctx, lang=lang, path=path,
                title=f"{court} — {tr(ctx.site['name'], lang)}",
                description=tr(meta["description"], lang), body=body, jsonld=ld,
                active="dossiers", alternate=alt)


def render_dossier_index(ctx: Site, lang: str, docs: list) -> str:
    path = ctx.path_for("dossiers", None, lang)
    alt = ctx.path_for("dossiers", None, "nl" if lang == "fr" else "fr")
    ui = ctx.site["ui"]
    groups = defaultdict(list)
    for d in docs:
        groups[tr(d["meta"]["section"], lang)].append(d)

    blocks = []
    for section, items in groups.items():
        cards = "".join(
            f'<a class="carte" href="{esc(d["meta"]["id"])}.html">'
            f'<span class="carte-num">{d["meta"]["order"]:02d}</span>'
            f'<h3>{esc(tr(d["meta"]["title"], lang))}</h3>'
            f'<p>{esc(tr(d["meta"]["description"], lang))}</p>'
            f'<span class="carte-meta">{len(d["renderer"].footnotes)} '
            f'{esc(tr(ui["sources_short"], lang))}</span></a>'
            for d in items
        )
        blocks.append(f'<section><h2>{esc(section)}</h2><div class="grille">{cards}</div></section>')

    ld = core_nodes(ctx, lang) + [{
        "@type": "CollectionPage",
        "@id": f"{ctx.base}/{path}#page",
        "url": f"{ctx.base}/{path}",
        "name": tr(ctx.site["pages"]["dossiers"]["title"], lang),
        "inLanguage": "fr-BE" if lang == "fr" else "nl-BE",
        "isPartOf": {"@id": f"{ctx.base}/#site"},
        "author": {"@id": f"{ctx.base}/#auteur"},
        "hasPart": [{"@type": "Article",
                     "@id": f"{ctx.base}/{ctx.path_for('dossier', d['meta']['id'], lang)}#article",
                     "name": tr(d["meta"]["title"], lang),
                     "url": ctx.url_for("dossier", d["meta"]["id"], lang)} for d in docs],
    }]
    body = (f'<h1>{esc(tr(ctx.site["pages"]["dossiers"]["title"], lang))}</h1>'
            f'<p class="chapo">{esc(tr(ctx.site["pages"]["dossiers"]["lede"], lang))}</p>'
            + "".join(blocks))
    return page(ctx, lang=lang, path=path,
                title=f"{tr(ctx.site['pages']['dossiers']['title'], lang)} — {tr(ctx.site['name'], lang)}",
                description=tr(ctx.site["pages"]["dossiers"]["lede"], lang),
                body=body, jsonld=ld, active="dossiers", alternate=alt)


ENTITY_SCHEMA = {
    "person": "Person",
    "party": "PoliticalParty",
    "institution": "GovernmentOrganization",
    "union": "Organization",
    "body": "Organization",
}


def render_entity(ctx: Site, lang: str, eid: str, ent: dict) -> str:
    path = ctx.path_for("entity", eid, lang)
    alt = ctx.path_for("entity", eid, "nl" if lang == "fr" else "fr")
    ui = ctx.site["ui"]
    depth = path.count("/")
    prefix = "../" * depth
    r = Renderer(ctx, lang, depth=depth)

    rows = []
    for key in ("role", "party", "founded", "seats", "line", "members"):
        if ent.get(key):
            rows.append(
                f'<div class="fiche-l"><dt>{esc(tr(ui["ent_" + key], lang))}</dt>'
                f'<dd>{r.inline(tr(ent[key], lang))}</dd></div>')
    fiche = f'<dl class="fiche">{"".join(rows)}</dl>' if rows else ""

    bio = r.render(tr(ent.get("bio", ""), lang))

    quotes = ""
    if ent.get("quotes"):
        items = []
        for q in ent["quotes"]:
            cite = r.inline(f'[[s:{q["source"]}]]')
            items.append(
                f'<li><blockquote><p>{r.inline(tr(q["text"], lang))}</p></blockquote>'
                f'<p class="cite"><time datetime="{esc(q["date"])}">'
                f'{esc(human_date(q["date"], lang))}</time>{cite}</p></li>')
        quotes = (f'<section aria-labelledby="cit-t"><h2 id="cit-t">'
                  f'{esc(tr(ui["quotes"], lang))}</h2>'
                  f'<ul class="citations">{"".join(items)}</ul></section>')

    # rétroliens : dossiers et repères qui citent cet acteur
    back = ctx.mentions[eid][lang]
    back_html = ""
    if back:
        lis = "".join(
            f'<li><a href="{esc(prefix + p["path"])}">{esc(p["title"])}</a></li>'
            for p in back)
        back_html = (f'<section aria-labelledby="rb-t"><h2 id="rb-t">'
                     f'{esc(tr(ui["appears_in"], lang))}</h2><ul>{lis}</ul></section>')

    tl = [e for e in ctx.timeline if eid in e.get("entities", [])]
    tl_html = ""
    if tl:
        lis = "".join(
            f'<li><time datetime="{esc(e["date"])}">{esc(human_date(e["date"], lang))}</time> '
            f'<span>{r.inline(tr(e["title"], lang))}</span></li>' for e in tl[-12:])
        tl_html = (f'<section aria-labelledby="ch-t"><h2 id="ch-t">'
                   f'{esc(tr(ui["timeline_of"], lang))}</h2>'
                   f'<ol class="mini-chrono">{lis}</ol></section>')

    links = ""
    if ent.get("links"):
        lis = "".join(
            f'<li><a href="{esc(u)}" rel="nofollow noopener" target="_blank">{esc(label)}</a></li>'
            for label, u in ent["links"].items())
        links = (f'<section aria-labelledby="li-t"><h2 id="li-t">'
                 f'{esc(tr(ui["external"], lang))}</h2><ul>{lis}</ul></section>')

    node = {
        "@type": ENTITY_SCHEMA.get(ent["type"], "Thing"),
        "@id": f"{ctx.base}/{path}#id",
        "name": tr(ent["name"], lang),
        "url": f"{ctx.base}/{path}",
        "description": tr(ent["short"], lang),
    }
    if ent.get("sameAs"):
        node["sameAs"] = ent["sameAs"]
    if ent["type"] == "person" and ent.get("affiliation_id"):
        node["memberOf"] = {"@id": f"{ctx.base}/{ctx.path_for('entity', ent['affiliation_id'], lang)}#id"}
    if ent.get("jobTitle"):
        node["jobTitle"] = tr(ent["jobTitle"], lang)

    ld = core_nodes(ctx, lang) + [node, {
        "@type": "ProfilePage",
        "@id": f"{ctx.base}/{path}#page",
        "url": f"{ctx.base}/{path}",
        "name": tr(ent["name"], lang),
        "inLanguage": "fr-BE" if lang == "fr" else "nl-BE",
        "isPartOf": {"@id": f"{ctx.base}/#site"},
        "author": {"@id": f"{ctx.base}/#auteur"},
        "mainEntity": {"@id": f"{ctx.base}/{path}#id"},
    }, {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": tr(ctx.site["nav"]["home"], lang),
             "item": ctx.url_for("home", None, lang)},
            {"@type": "ListItem", "position": 2, "name": tr(ctx.site["nav"]["entities"], lang),
             "item": ctx.url_for("entities", None, lang)},
            {"@type": "ListItem", "position": 3, "name": tr(ent["name"], lang)},
        ],
    }] + citation_nodes(ctx, r.footnotes)

    body = f"""
<article class="acteur">
<p class="surtitre">{esc(tr(ctx.site['entity_kinds'][ent['type']], lang))}</p>
<h1>{esc(tr(ent['name'], lang))}</h1>
<p class="chapo">{r.inline(tr(ent['short'], lang))}</p>
{fiche}
<div class="corps">{bio}</div>
{quotes}
{tl_html}
{back_html}
{links}
{footnote_block(ctx, r, lang)}
</article>
"""
    return page(ctx, lang=lang, path=path,
                title=f"{tr(ent['name'], lang)} — {tr(ctx.site['name'], lang)}",
                description=tr(ent["short"], lang), body=body, jsonld=ld,
                active="entities", alternate=alt)


def render_entity_index(ctx: Site, lang: str) -> str:
    path = ctx.path_for("entities", None, lang)
    alt = ctx.path_for("entities", None, "nl" if lang == "fr" else "fr")
    order = ["person", "party", "institution", "union", "body"]
    groups = defaultdict(list)
    for eid, ent in ctx.entities.items():
        groups[ent["type"]].append((eid, ent))

    blocks = []
    for kind in order:
        items = sorted(groups.get(kind, []), key=lambda p: tr(p[1]["name"], lang))
        if not items:
            continue
        cards = "".join(
            f'<a class="vignette" href="{esc(eid)}.html">'
            f'<h3>{esc(tr(ent["name"], lang))}</h3>'
            f'<p>{esc(tr(ent["short"], lang))}</p></a>' for eid, ent in items)
        blocks.append(
            f'<section><h2>{esc(tr(ctx.site["entity_kinds_plural"][kind], lang))}</h2>'
            f'<div class="grille-vignettes">{cards}</div></section>')

    ld = core_nodes(ctx, lang) + [{
        "@type": "CollectionPage",
        "@id": f"{ctx.base}/{path}#page",
        "url": f"{ctx.base}/{path}",
        "name": tr(ctx.site["pages"]["entities"]["title"], lang),
        "inLanguage": "fr-BE" if lang == "fr" else "nl-BE",
        "isPartOf": {"@id": f"{ctx.base}/#site"},
        "author": {"@id": f"{ctx.base}/#auteur"},
        "hasPart": [{"@id": f"{ctx.base}/{ctx.path_for('entity', eid, lang)}#id"}
                    for eid in ctx.entities],
    }]
    body = (f'<h1>{esc(tr(ctx.site["pages"]["entities"]["title"], lang))}</h1>'
            f'<p class="chapo">{esc(tr(ctx.site["pages"]["entities"]["lede"], lang))}</p>'
            + "".join(blocks))
    return page(ctx, lang=lang, path=path,
                title=f"{tr(ctx.site['pages']['entities']['title'], lang)} — {tr(ctx.site['name'], lang)}",
                description=tr(ctx.site["pages"]["entities"]["lede"], lang),
                body=body, jsonld=ld, active="entities", alternate=alt)


def render_timeline(ctx: Site, lang: str) -> str:
    path = ctx.path_for("timeline", None, lang)
    alt = ctx.path_for("timeline", None, "nl" if lang == "fr" else "fr")
    ui = ctx.site["ui"]
    r = Renderer(ctx, lang, depth=path.count("/"))

    tags = []
    for t, label in ctx.site["tags"].items():
        tags.append(f'<button type="button" data-filtre="{esc(t)}" aria-pressed="false">'
                    f'{esc(tr(label, lang))}</button>')
    bar = (f'<div class="filtres" data-filtres role="group" '
           f'aria-label="{esc(tr(ui["filters"], lang))}">'
           f'<button type="button" data-filtre="*" aria-pressed="true">'
           f'{esc(tr(ui["all"], lang))}</button>{"".join(tags)}</div>')

    items = []
    for e in ctx.timeline:
        ents = " ".join(e.get("entities", []))
        ent_links = "".join(
            f'<a href="{"../" * path.count("/")}{esc(ctx.path_for("entity", x, lang))}">'
            f'{esc(tr(ctx.entities[x]["name"], lang))}</a>'
            for x in e.get("entities", []) if x in ctx.entities)
        src = "".join(r.inline(f"[[s:{s}]]") for s in e.get("sources", []))
        items.append(
            f'<li data-tags="{esc(" ".join(e.get("tags", [])))}" data-acteurs="{esc(ents)}">'
            f'<time datetime="{esc(e["date"])}">{esc(human_date(e["date"], lang))}</time>'
            f'<div class="repere-c"><p class="repere-t">{r.inline(tr(e["title"], lang))}{src}</p>'
            f'<p class="repere-d">{r.inline(tr(e.get("body", ""), lang))}</p>'
            f'<p class="repere-a">{ent_links}</p></div></li>')

    events = [{
        "@type": "Event",
        "name": tr(e["title"], lang),
        "startDate": e["date"],
        "description": tr(e.get("body", ""), lang)[:300],
        "eventStatus": "https://schema.org/EventScheduled",
        "location": {"@type": "Country", "name": "Belgique" if lang == "fr" else "België"},
    } for e in ctx.timeline]

    ld = core_nodes(ctx, lang) + [{
        "@type": "CollectionPage",
        "@id": f"{ctx.base}/{path}#page",
        "url": f"{ctx.base}/{path}",
        "name": tr(ctx.site["pages"]["timeline"]["title"], lang),
        "inLanguage": "fr-BE" if lang == "fr" else "nl-BE",
        "isPartOf": {"@id": f"{ctx.base}/#site"},
        "author": {"@id": f"{ctx.base}/#auteur"},
        "mainEntity": {"@type": "ItemList", "numberOfItems": len(events),
                       "itemListOrder": "https://schema.org/ItemListOrderAscending",
                       "itemListElement": [
                           {"@type": "ListItem", "position": i + 1, "item": ev}
                           for i, ev in enumerate(events)]},
    }] + citation_nodes(ctx, r.footnotes)

    body = f"""
<h1>{esc(tr(ctx.site['pages']['timeline']['title'], lang))}</h1>
<p class="chapo">{esc(tr(ctx.site['pages']['timeline']['lede'], lang))}</p>
{bar}
<p class="compte" data-compte aria-live="polite">{len(ctx.timeline)} {esc(tr(ui['markers'], lang))}</p>
<ol class="chrono" data-chrono>{"".join(items)}</ol>
{footnote_block(ctx, r, lang)}
"""
    return page(ctx, lang=lang, path=path,
                title=f"{tr(ctx.site['pages']['timeline']['title'], lang)} — {tr(ctx.site['name'], lang)}",
                description=tr(ctx.site["pages"]["timeline"]["lede"], lang),
                body=body, jsonld=ld, active="timeline", alternate=alt)


def render_glossary(ctx: Site, lang: str) -> str:
    path = ctx.path_for("glossary", None, lang)
    alt = ctx.path_for("glossary", None, "nl" if lang == "fr" else "fr")
    ui = ctx.site["ui"]
    r = Renderer(ctx, lang, depth=path.count("/"))
    terms = sorted(ctx.glossary.values(), key=lambda g: tr(g["term"], lang).lower())

    rows = []
    for g in terms:
        rows.append(
            f'<div class="entree" data-terme>'
            f'<dt id="{esc(g["id"])}">{esc(tr(g["term"], lang))}'
            + (f' <span class="abbr">{esc(g["abbr"])}</span>' if g.get("abbr") else "")
            + f'</dt><dd>{r.inline(tr(g["definition"], lang))}</dd></div>')

    ld = core_nodes(ctx, lang) + [{
        "@type": "DefinedTermSet",
        "@id": f"{ctx.base}/{path}#set",
        "url": f"{ctx.base}/{path}",
        "name": tr(ctx.site["pages"]["glossary"]["title"], lang),
        "inLanguage": "fr-BE" if lang == "fr" else "nl-BE",
        "hasDefinedTerm": [{
            "@type": "DefinedTerm",
            "@id": f"{ctx.base}/{path}#{g['id']}",
            "name": tr(g["term"], lang),
            "description": strip_tags(tr(g["definition"], lang)),
            "inDefinedTermSet": {"@id": f"{ctx.base}/{path}#set"},
        } for g in terms],
    }] + citation_nodes(ctx, r.footnotes)

    body = f"""
<h1>{esc(tr(ctx.site['pages']['glossary']['title'], lang))}</h1>
<p class="chapo">{esc(tr(ctx.site['pages']['glossary']['lede'], lang))}</p>
<div class="rech-glossaire">
  <label for="gq">{esc(tr(ui['filter_terms'], lang))}</label>
  <input id="gq" type="search" data-glossaire-rech autocomplete="off"
    placeholder="{esc(tr(ui['filter_ph'], lang))}">
</div>
<p class="compte" data-compte-g aria-live="polite">{len(terms)} {esc(tr(ui['terms'], lang))}</p>
<dl class="glossaire" data-glossaire>{"".join(rows)}</dl>
{footnote_block(ctx, r, lang)}
"""
    return page(ctx, lang=lang, path=path,
                title=f"{tr(ctx.site['pages']['glossary']['title'], lang)} — {tr(ctx.site['name'], lang)}",
                description=tr(ctx.site["pages"]["glossary"]["lede"], lang),
                body=body, jsonld=ld, active="glossary", alternate=alt)


def render_sources(ctx: Site, lang: str, usage: dict) -> str:
    path = ctx.path_for("sources", None, lang)
    alt = ctx.path_for("sources", None, "nl" if lang == "fr" else "fr")
    ui = ctx.site["ui"]
    groups = defaultdict(list)
    for s in ctx.sources.values():
        groups[s.get("kind", "presse")].append(s)

    blocks = []
    for kind in ("primaire", "institution", "presse", "acteur", "recherche"):
        items = sorted(groups.get(kind, []), key=lambda s: (s.get("date") or "", s["title"]))
        if not items:
            continue
        lis = []
        for s in items:
            used = usage.get(s["id"], 0)
            meta = []
            if s.get("publisher"):
                meta.append(esc(s["publisher"]))
            if s.get("date"):
                meta.append(f'<time datetime="{esc(s["date"])}">{esc(human_date(s["date"], lang))}</time>')
            meta.append(f'{esc(tr(ui["consulted"], lang))} '
                        f'<time datetime="{esc(s["accessed"])}">{esc(human_date(s["accessed"], lang))}</time>')
            lis.append(
                f'<li id="{esc(s["id"])}">'
                f'<a href="{esc(s["url"])}" rel="nofollow noopener" target="_blank">{esc(s["title"])}</a>'
                f'<span class="src-meta">{" · ".join(meta)}</span>'
                + (f'<span class="src-usage">{used} {esc(tr(ui["citations"], lang))}</span>' if used else "")
                + "</li>")
        blocks.append(
            f'<section><h2>{esc(tr(ctx.site["source_kinds_plural"][kind], lang))} '
            f'<span class="compte-inline">({len(items)})</span></h2>'
            f'<ol class="bibliographie">{"".join(lis)}</ol></section>')

    ld = core_nodes(ctx, lang) + [{
        "@type": "CollectionPage",
        "@id": f"{ctx.base}/{path}#page",
        "url": f"{ctx.base}/{path}",
        "name": tr(ctx.site["pages"]["sources"]["title"], lang),
        "inLanguage": "fr-BE" if lang == "fr" else "nl-BE",
        "isPartOf": {"@id": f"{ctx.base}/#site"},
        "author": {"@id": f"{ctx.base}/#auteur"},
    }] + citation_nodes(ctx, list(ctx.sources))

    body = (f'<h1>{esc(tr(ctx.site["pages"]["sources"]["title"], lang))}</h1>'
            f'<p class="chapo">{esc(tr(ctx.site["pages"]["sources"]["lede"], lang))}</p>'
            + "".join(blocks))
    return page(ctx, lang=lang, path=path,
                title=f"{tr(ctx.site['pages']['sources']['title'], lang)} — {tr(ctx.site['name'], lang)}",
                description=tr(ctx.site["pages"]["sources"]["lede"], lang),
                body=body, jsonld=ld, active="sources", alternate=alt)


def render_simple(ctx: Site, lang: str, key: str, extra_body="",
                  active: str = "", ld_type: str = "WebPage") -> str:
    """extra_body peut être une chaîne ou une fonction recevant le rendu
    de la page, afin que ses notes rejoignent celles du corps."""
    path = ctx.path_for(key, None, lang)
    alt = ctx.path_for(key, None, "nl" if lang == "fr" else "fr")
    src = CONTENT / lang / f"{key}.md"
    meta, raw = parse_doc(src)
    r = Renderer(ctx, lang, depth=path.count("/"))
    body_html = r.render(raw)
    supplement = extra_body(r) if callable(extra_body) else extra_body
    ld = core_nodes(ctx, lang) + [{
        "@type": ld_type,
        "@id": f"{ctx.base}/{path}#page",
        "url": f"{ctx.base}/{path}",
        "name": tr(meta["title"], lang),
        "description": tr(meta["description"], lang),
        "inLanguage": "fr-BE" if lang == "fr" else "nl-BE",
        "isPartOf": {"@id": f"{ctx.base}/#site"},
        "author": {"@id": f"{ctx.base}/#auteur"},
        "dateModified": ctx.site["updated"],
    }] + citation_nodes(ctx, r.footnotes)
    body = (f'<h1>{esc(tr(meta["title"], lang))}</h1>'
            f'<p class="chapo">{r.inline(tr(meta["lede"], lang))}</p>'
            f'<div class="corps">{body_html}</div>{supplement}'
            f"{footnote_block(ctx, r, lang)}")
    return page(ctx, lang=lang, path=path,
                title=f"{tr(meta['title'], lang)} — {tr(ctx.site['name'], lang)}",
                description=tr(meta["description"], lang), body=body, jsonld=ld,
                active=active or key, alternate=alt)


def corrections_table(ctx: Site, lang: str, r: Renderer) -> str:
    ui = ctx.site["ui"]
    rows = "".join(
        f'<tr><th scope="row">{r.inline(tr(c["point"], lang))}</th>'
        f'<td>{r.inline(tr(c["before"], lang))}</td>'
        f'<td>{r.inline(tr(c["after"], lang))}</td></tr>' for c in ctx.corrections)
    return (f'<div class="table-wrap"><table class="corrections">'
            f'<caption>{esc(tr(ui["corr_caption"], lang))}</caption><thead><tr>'
            f'<th scope="col">{esc(tr(ui["corr_point"], lang))}</th>'
            f'<th scope="col">{esc(tr(ui["corr_before"], lang))}</th>'
            f'<th scope="col">{esc(tr(ui["corr_after"], lang))}</th>'
            f"</tr></thead><tbody>{rows}</tbody></table></div>")


def render_indicators(ctx: Site, lang: str) -> str:
    path = ctx.path_for("indicators", None, lang)
    alt = ctx.path_for("indicators", None, "nl" if lang == "fr" else "fr")
    r = Renderer(ctx, lang, depth=path.count("/"))
    blocks = []
    for fid, spec in ctx.figures.items():
        if not spec.get("on_indicators", True):
            continue
        blocks.append(f'<section id="{esc(fid)}">'
                      + ctx.render_figure("chart", fid, r) + "</section>")
    datasets = [{
        "@type": "Dataset",
        "@id": f"{ctx.base}/{path}#{fid}",
        "name": tr(spec["title"], lang),
        "description": tr(spec.get("desc", spec["title"]), lang),
        "inLanguage": "fr-BE" if lang == "fr" else "nl-BE",
        "creator": {"@id": f"{ctx.base}/#auteur"},
        "license": "https://creativecommons.org/publicdomain/zero/1.0/",
        "isAccessibleForFree": True,
        "distribution": [
            {"@type": "DataDownload", "encodingFormat": "text/csv",
             "contentUrl": f"{ctx.base}/donnees/{fid}.csv"},
            {"@type": "DataDownload", "encodingFormat": "application/json",
             "contentUrl": f"{ctx.base}/donnees/{fid}.json"},
        ],
    } for fid, spec in ctx.figures.items() if spec.get("on_indicators", True)]

    ld = core_nodes(ctx, lang) + [{
        "@type": "CollectionPage",
        "@id": f"{ctx.base}/{path}#page",
        "url": f"{ctx.base}/{path}",
        "name": tr(ctx.site["pages"]["indicators"]["title"], lang),
        "inLanguage": "fr-BE" if lang == "fr" else "nl-BE",
        "isPartOf": {"@id": f"{ctx.base}/#site"},
        "author": {"@id": f"{ctx.base}/#auteur"},
    }] + datasets + citation_nodes(ctx, r.footnotes)

    body = (f'<h1>{esc(tr(ctx.site["pages"]["indicators"]["title"], lang))}</h1>'
            f'<p class="chapo">{esc(tr(ctx.site["pages"]["indicators"]["lede"], lang))}</p>'
            + "".join(blocks) + footnote_block(ctx, r, lang))
    return page(ctx, lang=lang, path=path,
                title=f"{tr(ctx.site['pages']['indicators']['title'], lang)} — {tr(ctx.site['name'], lang)}",
                description=tr(ctx.site["pages"]["indicators"]["lede"], lang),
                body=body, jsonld=ld, active="indicators", alternate=alt)


def render_search(ctx: Site, lang: str) -> str:
    path = ctx.path_for("search", None, lang)
    alt = ctx.path_for("search", None, "nl" if lang == "fr" else "fr")
    ui = ctx.site["ui"]
    ld = core_nodes(ctx, lang) + [{
        "@type": "SearchResultsPage",
        "@id": f"{ctx.base}/{path}#page",
        "url": f"{ctx.base}/{path}",
        "name": tr(ctx.site["pages"]["search"]["title"], lang),
        "inLanguage": "fr-BE" if lang == "fr" else "nl-BE",
        "isPartOf": {"@id": f"{ctx.base}/#site"},
    }]
    prefix = "../" * path.count("/")
    body = f"""
<h1>{esc(tr(ctx.site['pages']['search']['title'], lang))}</h1>
<p class="chapo">{esc(tr(ctx.site['pages']['search']['lede'], lang))}</p>
<form class="rech-page" role="search" data-recherche
      data-index="{prefix}search-{lang}.json" method="get">
  <label for="rq">{esc(tr(ui['search'], lang))}</label>
  <input id="rq" name="q" type="search" autocomplete="off" autofocus
    placeholder="{esc(tr(ui['search_ph'], lang))}">
  <button type="submit">{esc(tr(ui['search_go'], lang))}</button>
</form>
<p class="compte" data-rech-compte aria-live="polite"></p>
<ol class="resultats" data-resultats></ol>
<noscript><p class="bloc bloc-incertitude">{esc(tr(ui['search_nojs'], lang))}</p></noscript>
"""
    return page(ctx, lang=lang, path=path,
                title=f"{tr(ctx.site['pages']['search']['title'], lang)} — {tr(ctx.site['name'], lang)}",
                description=tr(ctx.site["pages"]["search"]["lede"], lang),
                body=body, jsonld=ld, active="", alternate=alt, robots="noindex, follow")


def render_home(ctx: Site, lang: str, docs: list) -> str:
    path = ctx.path_for("home", None, lang)
    index_path = (path or "") + "index.html"
    alt = (ctx.path_for("home", None, "nl" if lang == "fr" else "fr") or "")
    r = Renderer(ctx, lang, depth=index_path.count("/"))
    home = ctx.site["home"]

    kpis = "".join(
        f'<div class="kpi"><span class="kpi-n">{esc(tr(k["value"], lang))}</span>'
        f'<span class="kpi-l">{r.inline(tr(k["label"], lang))}</span></div>'
        for k in home["kpi"])

    cards = "".join(
        f'<a class="carte" href="dossiers/{esc(d["meta"]["id"])}.html">'
        f'<span class="carte-num">{d["meta"]["order"]:02d}</span>'
        f'<h3>{esc(tr(d["meta"]["title"], lang))}</h3>'
        f'<p>{esc(tr(d["meta"]["description"], lang))}</p></a>'
        for d in docs if d["meta"].get("featured"))

    aujourdhui = ctx.site["updated"]
    passes = [e for e in ctx.timeline if e["date"] <= aujourdhui]
    avenir = [e for e in ctx.timeline if e["date"] > aujourdhui]

    def puces(items):
        return "".join(
            f'<li><time datetime="{esc(e["date"])}">'
            f'{esc(human_date(e["date"], lang))}</time> '
            f'<span>{r.inline(tr(e["title"], lang))}</span></li>' for e in items)

    recent = puces(passes[::-1][:6])
    echeances = puces(avenir[:5])

    intro = r.render(tr(home["intro"], lang))
    fig = ctx.render_figure("chart", home["figure"], r)

    ld = core_nodes(ctx, lang) + [{
        "@type": "CollectionPage",
        "@id": f"{ctx.base}/{path}#accueil",
        "url": f"{ctx.base}/{path}",
        "name": tr(ctx.site["title"], lang),
        "description": tr(ctx.site["description"], lang),
        "inLanguage": "fr-BE" if lang == "fr" else "nl-BE",
        "isPartOf": {"@id": f"{ctx.base}/#site"},
        "author": {"@id": f"{ctx.base}/#auteur"},
        "dateModified": ctx.site["updated"],
    }] + citation_nodes(ctx, r.footnotes)

    prefix = "../" * index_path.count("/")
    body = f"""
<p class="surtitre">{esc(tr(home['kicker'], lang))}</p>
<h1>{esc(tr(home['h1'], lang))}</h1>
<p class="chapo">{r.inline(tr(home['lede'], lang))}</p>
<div class="kpis">{kpis}</div>
<div class="corps">{intro}</div>
{fig}
<h2>{esc(tr(home['dossiers_title'], lang))}</h2>
<div class="grille">{cards}</div>
<p class="vers-plus"><a href="{esc(prefix + ctx.path_for('dossiers', None, lang))}">
{esc(tr(home['all_dossiers'], lang))} →</a></p>
<h2>{esc(tr(home['next_title'], lang))}</h2>
<ol class="repères">{echeances}</ol>
<h2>{esc(tr(home['recent_title'], lang))}</h2>
<ol class="repères">{recent}</ol>
<p class="vers-plus"><a href="{esc(prefix + ctx.path_for('timeline', None, lang))}">
{esc(tr(home['all_timeline'], lang))} →</a></p>
{footnote_block(ctx, r, lang)}
"""
    return page(ctx, lang=lang, path=index_path,
                title=tr(ctx.site["title"], lang),
                description=tr(ctx.site["description"], lang), body=body,
                jsonld=ld, active="home", alternate=alt + "index.html")


def render_404(ctx: Site) -> str:
    """Page d'erreur : chemins absolus, car servie depuis n'importe quelle URL."""
    lang = "fr"
    base_path = ctx.site["base_path"]
    ui = ctx.site["ui"]
    links = "".join(
        f'<li><a href="{base_path}/{ctx.path_for(k, None, "fr")}">'
        f'{esc(tr(ctx.site["nav"][k], "fr"))}</a></li>'
        for k in ("dossiers", "entities", "timeline", "glossary", "sources"))
    return f"""<!doctype html>
<html lang="fr-BE">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Page introuvable — {esc(tr(ctx.site['name'], 'fr'))}</title>
<meta name="robots" content="noindex, follow">
<link rel="stylesheet" href="{base_path}/assets/style.css">
<link rel="icon" href="{base_path}/assets/icon.svg" type="image/svg+xml">
</head>
<body>
<a class="saut" href="#contenu">{esc(tr(ui['skip'], 'fr'))}</a>
<header class="entete"><div class="entete-i">
  <p class="marque"><a href="{base_path}/"><span class="marque-n">21</span><span class="marque-p">.09.</span><span class="marque-n">26</span></a></p>
  <p class="accroche">{esc(tr(ctx.site['tagline'], 'fr'))}</p>
</div></header>
<main id="contenu">
<h1>Cette page n'existe pas</h1>
<p class="chapo">L'adresse demandée n'a pas d'équivalent sur ce site. Elle a peut-être
été renommée depuis la dernière mise à jour, ou mal recopiée.</p>
<p>Voici par où reprendre :</p>
<ul>{links}</ul>
<p><a href="{base_path}/">Retour à l'accueil</a> · <a href="{base_path}/nl/" lang="nl">Nederlandse versie</a></p>
</main>
<footer class="pied"><div class="pied-i"><p class="pied-legal">{esc(tr(ctx.site['legal'], 'fr'))}</p></div></footer>
</body>
</html>
"""


# --------------------------------------------------------------------------
# sorties annexes
# --------------------------------------------------------------------------


def write_sitemap(ctx: Site, pages: list[dict]) -> None:
    urls = []
    for p in pages:
        loc = f"{ctx.base}/{p['path']}"
        if loc.endswith("/index.html"):
            loc = loc[: -len("index.html")]
        links = []
        if p.get("alternate") is not None:
            alt = f"{ctx.base}/{p['alternate']}"
            if alt.endswith("/index.html"):
                alt = alt[: -len("index.html")]
            other = "nl-BE" if p["lang"] == "fr" else "fr-BE"
            links.append(f'<xhtml:link rel="alternate" hreflang="{other}" href="{esc(alt)}"/>')
            links.append(f'<xhtml:link rel="alternate" hreflang="'
                         f'{"fr-BE" if p["lang"] == "fr" else "nl-BE"}" href="{esc(loc)}"/>')
            xdef = loc if p["lang"] == "fr" else alt
            links.append(f'<xhtml:link rel="alternate" hreflang="x-default" href="{esc(xdef)}"/>')
        urls.append(
            f"<url><loc>{esc(loc)}</loc>"
            f'<lastmod>{ctx.site["updated"]}</lastmod>'
            f'<changefreq>{p.get("freq", "weekly")}</changefreq>'
            f'<priority>{p.get("priority", "0.6")}</priority>'
            f'{"".join(links)}</url>')
    write(OUT / "sitemap.xml",
          '<?xml version="1.0" encoding="UTF-8"?>\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
          'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
          + "\n".join(urls) + "\n</urlset>\n")


def write_feed(ctx: Site, lang: str, docs: list) -> None:
    path = "feed.xml" if lang == "fr" else "nl/feed.xml"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entries = []
    for e in ctx.timeline[::-1][:20]:
        eid = f"{ctx.base}/{ctx.path_for('timeline', None, lang)}#{e['date']}-{slugify(tr(e['title'], lang))[:30]}"
        entries.append(f"""  <entry>
    <title>{esc(strip_tags(tr(e['title'], lang)))}</title>
    <link href="{esc(ctx.url_for('timeline', None, lang))}"/>
    <id>{esc(eid)}</id>
    <updated>{e['date']}T12:00:00Z</updated>
    <summary type="text">{esc(strip_tags(tr(e.get('body', ''), lang)))}</summary>
  </entry>""")
    for d in docs:
        m = d["meta"]
        url = ctx.url_for("dossier", m["id"], lang)
        entries.append(f"""  <entry>
    <title>{esc(tr(m['title'], lang))}</title>
    <link href="{esc(url)}"/>
    <id>{esc(url)}</id>
    <updated>{m.get('updated', ctx.site['updated'])}T12:00:00Z</updated>
    <author><name>Claude (Anthropic)</name></author>
    <category term="{esc(slugify(tr(m['section'], lang)))}"/>
    <summary type="text">{esc(tr(m['description'], lang))}</summary>
  </entry>""")
    write(OUT / path, f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="{'fr-BE' if lang == 'fr' else 'nl-BE'}">
  <title>{esc(tr(ctx.site['title'], lang))}</title>
  <subtitle>{esc(tr(ctx.site['description'], lang))}</subtitle>
  <link href="{esc(ctx.base)}/{path}" rel="self"/>
  <link href="{esc(ctx.base)}/{ctx.prefix(lang)}"/>
  <id>{esc(ctx.base)}/{ctx.prefix(lang)}</id>
  <updated>{now}</updated>
  <rights>CC BY 4.0</rights>
  <author><name>Claude (Anthropic)</name></author>
{chr(10).join(entries)}
</feed>
""")


def write_search_index(ctx: Site, lang: str, records: list) -> None:
    write(OUT / f"search-{lang}.json",
          json.dumps({"lang": lang, "built": ctx.site["updated"], "docs": records},
                     ensure_ascii=False, separators=(",", ":")))


def write_datasets(ctx: Site) -> None:
    import csv
    import io
    for fid, spec in ctx.figures.items():
        cats = spec["categories"]
        series = spec["series"]
        buf = io.StringIO()
        w = csv.writer(buf, lineterminator="\n")
        w.writerow(["categorie_fr", "categorie_nl"]
                   + [slugify(tr(s["name"], "fr")) for s in series])
        for i, cat in enumerate(cats):
            w.writerow([tr(cat, "fr"), tr(cat, "nl")]
                       + ["" if s["values"][i] is None else s["values"][i] for s in series])
        write(OUT / "donnees" / f"{fid}.csv", buf.getvalue())
        write(OUT / "donnees" / f"{fid}.json", json.dumps({
            "id": fid,
            "title": spec["title"],
            "unit": spec.get("unit", ""),
            "categories": cats,
            "series": [{"name": s["name"], "values": s["values"]} for s in series],
            "sources": [{"id": sid, "title": ctx.sources[sid]["title"],
                         "url": ctx.sources[sid]["url"]}
                        for sid in spec.get("sources", [])],
            "licence": "CC0-1.0",
        }, ensure_ascii=False, indent=1))
    manifest = [{
        "id": fid,
        "title": spec["title"],
        "csv": f"donnees/{fid}.csv",
        "json": f"donnees/{fid}.json",
        "rows": len(spec["categories"]),
        "series": len(spec["series"]),
    } for fid, spec in ctx.figures.items()]
    write(OUT / "donnees" / "index.json",
          json.dumps({"licence": "CC0-1.0", "base": ctx.base,
                      "datasets": manifest}, ensure_ascii=False, indent=1))


def render_data_page(ctx: Site, lang: str) -> str:
    path = ctx.path_for("data", None, lang)
    alt = ctx.path_for("data", None, "nl" if lang == "fr" else "fr")
    ui = ctx.site["ui"]
    prefix = "../" * path.count("/")
    rows = "".join(
        f'<tr><th scope="row">{esc(tr(spec["title"], lang))}</th>'
        f'<td class="num">{len(spec["categories"])}</td>'
        f'<td class="num">{len(spec["series"])}</td>'
        f'<td><a href="{prefix}donnees/{esc(fid)}.csv" download>CSV</a> · '
        f'<a href="{prefix}donnees/{esc(fid)}.json" download>JSON</a></td></tr>'
        for fid, spec in ctx.figures.items())
    table = (f'<div class="table-wrap"><table><caption>'
             f'{esc(tr(ui["datasets"], lang))}</caption><thead><tr>'
             f'<th scope="col">{esc(tr(ui["dataset"], lang))}</th>'
             f'<th scope="col" class="num">{esc(tr(ui["rows"], lang))}</th>'
             f'<th scope="col" class="num">{esc(tr(ui["series"], lang))}</th>'
             f'<th scope="col">{esc(tr(ui["download"], lang))}</th></tr></thead>'
             f"<tbody>{rows}</tbody></table></div>")
    return render_simple(ctx, lang, "data", extra_body=table, active="data",
                         ld_type="DataCatalog")


# --------------------------------------------------------------------------
# construction
# --------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--clean", action="store_true")
    args = ap.parse_args()

    if args.clean and OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)

    ctx = Site()
    dossiers = build_dossiers(ctx)

    # rétroliens acteurs -> pages
    for lang in LANGS:
        for d in dossiers[lang]:
            for eid in d["renderer"].mentioned:
                ctx.mentions[eid][lang].append({
                    "path": ctx.path_for("dossier", d["meta"]["id"], lang),
                    "title": tr(d["meta"]["title"], lang),
                })

    usage: dict[str, int] = defaultdict(int)
    pages: list[dict] = []
    search: dict[str, list] = {lang: [] for lang in LANGS}

    def emit(path: str, markup: str, lang: str, *, alternate=None,
             freq="weekly", priority="0.6", index_record=None):
        write(OUT / path, markup)
        pages.append({"path": path, "lang": lang, "alternate": alternate,
                      "freq": freq, "priority": priority})
        if index_record:
            search[lang].append(index_record)

    for lang in LANGS:
        docs = dossiers[lang]
        other = "nl" if lang == "fr" else "fr"

        emit((ctx.path_for("home", None, lang) or "") + "index.html",
             render_home(ctx, lang, docs), lang,
             alternate=(ctx.path_for("home", None, other) or "") + "index.html",
             freq="daily", priority="1.0",
             index_record={"t": tr(ctx.site["title"], lang), "u": (ctx.path_for("home", None, lang) or "./"),
                           "k": tr(ctx.site["nav"]["home"], lang),
                           "b": strip_tags(tr(ctx.site["description"], lang))})

        emit(ctx.path_for("dossiers", None, lang) + "index.html",
             render_dossier_index(ctx, lang, docs), lang,
             alternate=ctx.path_for("dossiers", None, other) + "index.html",
             priority="0.9")

        for i, d in enumerate(docs):
            prev_ = docs[i - 1] if i else None
            next_ = docs[i + 1] if i + 1 < len(docs) else None
            for sid in d["renderer"].footnotes:
                usage[sid] += 1
            p = ctx.path_for("dossier", d["meta"]["id"], lang)
            emit(p, render_dossier(ctx, lang, d, prev_, next_), lang,
                 alternate=ctx.path_for("dossier", d["meta"]["id"], other),
                 priority="0.8",
                 index_record={"t": tr(d["meta"]["title"], lang), "u": p,
                               "k": tr(d["meta"]["section"], lang),
                               "b": strip_tags(d["html"])[:1400]})

        emit(ctx.path_for("entities", None, lang) + "index.html",
             render_entity_index(ctx, lang), lang,
             alternate=ctx.path_for("entities", None, other) + "index.html",
             priority="0.7")

        for eid, ent in ctx.entities.items():
            p = ctx.path_for("entity", eid, lang)
            markup = render_entity(ctx, lang, eid, ent)
            emit(p, markup, lang, alternate=ctx.path_for("entity", eid, other),
                 priority="0.5", freq="monthly",
                 index_record={"t": tr(ent["name"], lang), "u": p,
                               "k": tr(ctx.site["entity_kinds"][ent["type"]], lang),
                               "b": strip_tags(tr(ent["short"], lang) + " "
                                               + tr(ent.get("bio", ""), lang))[:900]})

        for key, fn, freq, prio in (
            ("timeline", render_timeline, "daily", "0.8"),
            ("indicators", render_indicators, "weekly", "0.7"),
            ("glossary", render_glossary, "monthly", "0.5"),
        ):
            p = ctx.path_for(key, None, lang)
            emit(p, fn(ctx, lang), lang, alternate=ctx.path_for(key, None, other),
                 freq=freq, priority=prio,
                 index_record={"t": tr(ctx.site["pages"][key]["title"], lang), "u": p,
                               "k": tr(ctx.site["nav"][key], lang),
                               "b": strip_tags(tr(ctx.site["pages"][key]["lede"], lang))})

    # les sources ont besoin du décompte d'usage : second passage
    for lang in LANGS:
        other = "nl" if lang == "fr" else "fr"
        for key, ld in (("method", "WebPage"), ("about", "AboutPage")):
            pp = ctx.path_for(key, None, lang)
            extra = ((lambda rr: corrections_table(ctx, lang, rr))
                     if key == "method" else "")
            emit(pp, render_simple(ctx, lang, key, extra_body=extra, ld_type=ld), lang,
                 alternate=ctx.path_for(key, None, other), freq="monthly", priority="0.4")
        pd = ctx.path_for("data", None, lang)
        emit(pd, render_data_page(ctx, lang), lang,
             alternate=ctx.path_for("data", None, other), freq="monthly", priority="0.5")
        p = ctx.path_for("sources", None, lang)
        emit(p, render_sources(ctx, lang, ctx.usage[lang]), lang,
             alternate=ctx.path_for("sources", None, other), priority="0.5")
        ps = ctx.path_for("search", None, lang)
        write(OUT / ps, render_search(ctx, lang))

    for lang in LANGS:
        write_search_index(ctx, lang, search[lang])
        write_feed(ctx, lang, dossiers[lang])

    write_datasets(ctx)
    write_sitemap(ctx, pages)
    write(OUT / "404.html", render_404(ctx))
    write(OUT / "robots.txt",
          f"User-agent: *\nAllow: /\n\nSitemap: {ctx.base}/sitemap.xml\n")
    write(OUT / ".nojekyll", "")

    (OUT / "assets").mkdir(parents=True, exist_ok=True)
    for name in ("style.css", "app.js", "icon.svg", "manifest.webmanifest"):
        shutil.copyfile(ASSETS / name, OUT / "assets" / name)

    total = {sid: sum(ctx.usage[l].get(sid, 0) for l in LANGS) for sid in ctx.sources}
    orphans = [sid for sid, n in total.items() if not n]
    print(f"✔ {len(pages)} pages · {len(ctx.sources)} sources "
          f"({len(orphans)} non citées) · {len(ctx.entities)} acteurs · "
          f"{len(ctx.figures)} jeux de données · {len(ctx.timeline)} repères")
    if orphans:
        print("  sources non citées dans le corps :", ", ".join(sorted(orphans)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
