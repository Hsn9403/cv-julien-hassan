#!/usr/bin/env python3
"""
CV Editor — génère le PDF à partir de cv_config.json

Usage:
    python3 cv_editor.py                  → génère CV JULIEN HASSAN.pdf
    python3 cv_editor.py --preview        → génère CV_preview.pdf (sans écraser)

Sections éditables via cv_config.json :
    experience  → expériences professionnelles (avec bullets circulaires)
    projects    → projets personnels
    education   → formations
    skills      → compétences techniques et langues
"""

import json, sys, fitz, tempfile, os
from pathlib import Path

# ── Chemins ──────────────────────────────────────────────────
DIR          = Path(__file__).parent
ORIGINAL_PDF = DIR / "CV JULIEN HASSAN copie.pdf"
CONFIG_FILE  = DIR / "cv_config.json"
OUTPUT_PDF   = DIR / "CV JULIEN HASSAN.pdf"

# ── Mise en page (mesurée sur l'original) ────────────────────
PAGE_W       = 612.0
PAGE_H       = 792.0
RIGHT_MARGIN = 576.0
FONT_SIZE    = 10.0
BULLET_SIZE  = 13.0
LINE_H       = 13.5
SECTION_GAP  = 18.0
ENTRY_GAP    = 11.0

X_LEFT     = 36.0
X_DATE     = 36.8
X_INST     = 122.2
X_BULLET   = 34.5
X_TEXT     = 52.5
X_SUB_DASH = 54.8
X_SUB_TEXT = 60.0

X_EXP_CIRCLE_X = 127.125
X_EXP_CIRCLE_R = 1.875
X_EXP_TEXT     = 141.0

GRAY = (0.502, 0.502, 0.502)

CUT_Y_WITH_EXP = 115.0
CUT_Y_NO_EXP   = 395.0


# ── Polices ──────────────────────────────────────────────────
def load_fonts(doc):
    tmp_files = []

    def extract(xref):
        data = doc.extract_font(xref)[3]
        tmp = tempfile.NamedTemporaryFile(suffix=".ttf", delete=False)
        tmp.write(data)
        tmp.close()
        tmp_files.append(tmp.name)
        return tmp.name

    cal_bold_xref = cal_xref = arial_xref = None
    for f in doc[0].get_fonts():
        base = f[3].lower()
        if "calibri" in base and "bold" in base:
            cal_bold_xref = f[0]
        elif "calibri" in base and cal_xref is None:
            cal_xref = f[0]
        elif "arial" in base and "bold" not in base and arial_xref is None:
            arial_xref = f[0]

    fonts = {
        "reg":   fitz.Font(fontfile=extract(cal_xref      or 5)),
        "bold":  fitz.Font(fontfile=extract(cal_bold_xref or 4)),
        "arial": fitz.Font(fontfile=extract(arial_xref    or 6)),
    }
    return fonts, tmp_files


# ── Utilitaires ──────────────────────────────────────────────
def wrap(text, font, x_start, x_end=None):
    if x_end is None:
        x_end = RIGHT_MARGIN
    avail = x_end - x_start
    words = text.split()
    lines, cur = [], ""
    for w in words:
        candidate = (cur + " " + w).strip()
        if font.text_length(candidate, fontsize=FONT_SIZE) <= avail:
            cur = candidate
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [""]


def dashed_line(page, y, x0=35.0, x1=578.0):
    x = x0
    while x < x1:
        page.draw_rect(fitz.Rect(x, y, min(x + 2.25, x1), y + 1), fill=GRAY, color=None)
        x += 4.5


# ── Sections ─────────────────────────────────────────────────
def render_experience(page, tw, fonts, experiences, y):
    tw.append((X_LEFT, y), "PROFESSIONAL EXPERIENCE", font=fonts["bold"], fontsize=FONT_SIZE)
    dashed_line(page, y + 2)
    y += LINE_H + 3

    for i, exp in enumerate(experiences):
        dates     = exp.get("dates", "")
        company   = exp.get("company", "")
        comp_type = exp.get("company_type", "")
        location  = exp.get("location", "")
        role      = exp.get("role", "")
        bullets   = exp.get("bullets", [])

        tw.append((X_DATE, y), dates, font=fonts["reg"], fontsize=FONT_SIZE)
        co_w = fonts["bold"].text_length(company, fontsize=FONT_SIZE)
        tw.append((X_INST, y), company, font=fonts["bold"], fontsize=FONT_SIZE)
        if comp_type:
            tw.append((X_INST + co_w, y), " " + comp_type, font=fonts["reg"], fontsize=FONT_SIZE)
        if location:
            loc_w = fonts["reg"].text_length(location, fontsize=FONT_SIZE)
            tw.append((RIGHT_MARGIN - loc_w, y), location, font=fonts["reg"], fontsize=FONT_SIZE)
        y += LINE_H

        tw.append((X_INST, y), role, font=fonts["bold"], fontsize=FONT_SIZE)
        y += LINE_H + 2

        for bullet_text in bullets:
            blines = wrap(bullet_text, fonts["reg"], X_EXP_TEXT)
            page.draw_circle(
                fitz.Point(X_EXP_CIRCLE_X, y - 1.875),
                X_EXP_CIRCLE_R,
                color=(0, 0, 0), fill=(0, 0, 0)
            )
            tw.append((X_EXP_TEXT, y), blines[0], font=fonts["reg"], fontsize=FONT_SIZE)
            y += LINE_H
            for bl in blines[1:]:
                tw.append((X_EXP_TEXT, y), bl, font=fonts["reg"], fontsize=FONT_SIZE)
                y += LINE_H

        if i < len(experiences) - 1:
            y += 10

    return y


def render_projects(page, tw, fonts, projects, y):
    tw.append((X_LEFT, y), "PROJECTS", font=fonts["bold"], fontsize=FONT_SIZE)
    dashed_line(page, y + 2)
    y += LINE_H + 6

    for proj in projects:
        name  = proj["name"]
        desc  = proj.get("description", "")
        subs  = proj.get("sub_bullets", [])

        tw.append((X_BULLET, y + 2), "•", font=fonts["arial"], fontsize=BULLET_SIZE)
        label   = name + ":"
        label_w = fonts["bold"].text_length(label, fontsize=FONT_SIZE)
        space_w = fonts["reg"].text_length(" ", fontsize=FONT_SIZE)
        x_desc  = X_TEXT + label_w + space_w
        tw.append((X_TEXT, y), label, font=fonts["bold"], fontsize=FONT_SIZE)

        words = desc.split()
        line1, remaining = "", list(words)
        while remaining:
            c = (line1 + " " + remaining[0]).strip()
            if fonts["reg"].text_length(c, fontsize=FONT_SIZE) <= RIGHT_MARGIN - x_desc:
                line1 = c
                remaining.pop(0)
            else:
                break
        if line1:
            tw.append((x_desc, y), line1, font=fonts["reg"], fontsize=FONT_SIZE)
        y += LINE_H

        for line in (wrap(" ".join(remaining), fonts["reg"], X_TEXT) if remaining else []):
            tw.append((X_TEXT, y), line, font=fonts["reg"], fontsize=FONT_SIZE)
            y += LINE_H

        for sub in subs:
            sub_lines = wrap(sub, fonts["reg"], X_SUB_TEXT)
            tw.append((X_SUB_DASH, y), "-", font=fonts["reg"], fontsize=FONT_SIZE)
            tw.append((X_SUB_TEXT, y), sub_lines[0], font=fonts["reg"], fontsize=FONT_SIZE)
            y += LINE_H
            for sl in sub_lines[1:]:
                tw.append((X_SUB_TEXT, y), sl, font=fonts["reg"], fontsize=FONT_SIZE)
                y += LINE_H

        y += ENTRY_GAP / 2

    return y


def render_education(page, tw, fonts, education, y):
    y += SECTION_GAP
    tw.append((X_DATE, y), "EDUCATION", font=fonts["bold"], fontsize=FONT_SIZE)
    dashed_line(page, y + 2)
    y += LINE_H + 8

    for entry in education:
        tw.append((X_DATE, y), entry["dates"], font=fonts["reg"], fontsize=FONT_SIZE)
        tw.append((X_INST, y), entry["institution"], font=fonts["bold"], fontsize=FONT_SIZE)
        if entry.get("location"):
            loc_w = fonts["reg"].text_length(entry["location"], fontsize=FONT_SIZE)
            tw.append((RIGHT_MARGIN - loc_w, y), entry["location"], font=fonts["reg"], fontsize=FONT_SIZE)
        y += LINE_H
        for sl in wrap(entry.get("subtitle", ""), fonts["bold"], X_INST):
            tw.append((X_INST, y), sl, font=fonts["bold"], fontsize=FONT_SIZE)
            y += LINE_H
        for dl in wrap(entry.get("description", ""), fonts["reg"], X_INST):
            tw.append((X_INST, y), dl, font=fonts["reg"], fontsize=FONT_SIZE)
            y += LINE_H
        y += ENTRY_GAP

    return y


def render_skills(page, tw, fonts, skills, y):
    y += SECTION_GAP
    tw.append((X_LEFT, y), "TECHNICAL AND LANGUAGES SKILLS", font=fonts["bold"], fontsize=FONT_SIZE)
    dashed_line(page, y + 2, x0=34.5, x1=577.0)
    y += LINE_H + 8
    tw.append((X_LEFT, y), "Technical:", font=fonts["bold"], fontsize=FONT_SIZE)
    tw.append((79.0,   y), skills.get("technical", ""), font=fonts["reg"], fontsize=FONT_SIZE)
    y += LINE_H
    tw.append((X_LEFT, y), "Languages:", font=fonts["bold"], fontsize=FONT_SIZE)
    tw.append((84.2,   y), skills.get("languages", ""), font=fonts["reg"], fontsize=FONT_SIZE)
    return y


# ── Point d'entrée ───────────────────────────────────────────
def generate(config_path=CONFIG_FILE, original=ORIGINAL_PDF, output=OUTPUT_PDF):
    config_path = Path(config_path)
    original    = Path(original)
    output      = Path(output)

    if not original.exists():
        raise FileNotFoundError(f"PDF source introuvable : {original}")

    with open(config_path, encoding="utf-8") as f:
        cfg = json.load(f)

    experiences = cfg.get("experience", [])
    cut_y = CUT_Y_WITH_EXP if experiences else CUT_Y_NO_EXP

    doc  = fitz.open(str(original))
    page = doc[0]
    fonts, tmp_files = load_fonts(doc)

    try:
        page.add_redact_annot(fitz.Rect(0, cut_y, PAGE_W, PAGE_H), fill=(1, 1, 1))
        page.apply_redactions()

        tw = fitz.TextWriter(page.rect)
        y  = cut_y + 8

        if experiences:
            y = render_experience(page, tw, fonts, experiences, y)
            y += SECTION_GAP

        y = render_projects(page, tw, fonts, cfg.get("projects", []), y)
        y = render_education(page, tw, fonts, cfg.get("education", []), y)
        render_skills(page, tw, fonts, cfg.get("skills", {}), y)

        tw.write_text(page)
        doc.save(str(output), garbage=4, deflate=True)
        print(f"✓  Généré : {output}")

    finally:
        doc.close()
        for p in tmp_files:
            try:
                os.unlink(p)
            except OSError:
                pass


if __name__ == "__main__":
    out = OUTPUT_PDF
    if "--preview" in sys.argv:
        out = DIR / "CV_preview.pdf"
        print("Mode preview →", out)
    generate(output=out)
