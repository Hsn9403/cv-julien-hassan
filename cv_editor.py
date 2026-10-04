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
EXP_GAP      = 10.0

# Auto-fit : réglages typographiques essayés du plus aéré au plus dense,
# jusqu'à ce que le contenu tienne au-dessus de MAX_Y.
MAX_Y = 772.0
FIT_PRESETS = [
    # (font_size, line_h, section_gap, entry_gap, exp_gap)
    (10.0, 13.5, 18.0, 11.0, 10.0),
    (10.0, 12.5, 15.0,  9.0,  9.0),
    ( 9.7, 12.0, 13.0,  8.0,  8.0),
    ( 9.5, 11.6, 12.0,  7.0,  8.0),
    ( 9.2, 11.2, 11.0,  6.0,  7.0),
    ( 9.0, 10.8, 10.0,  6.0,  6.0),
]

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

# Accroche du header : conservée du PDF source, réécrite si "summary" est
# présent dans le config. Mesures relevées sur l'original.
SUMMARY_RECT   = fitz.Rect(34.5, 76.5, 505.0, 112.0)  # zone effacée (hors photo)
SUMMARY_X      = 36.0
SUMMARY_X_END  = 500.0
SUMMARY_Y0     = 87.5    # ~12.8pt sous l'email, comme l'écart tél. → email
SUMMARY_LINE_H = 11.0    # même respiration que le corps du CV
SUMMARY_SIZE   = 9.0
SUMMARY_MAX_LINES = 3

# Photo du header : remplacée si "photo" est présent dans le config,
# supprimée si "photo" vaut false (CV US/UK). L'accroche prend alors toute la largeur.
PHOTO_DPI = 400.0

# Ligne de contact sous le téléphone : réécrite si "contact" est présent
# (liste de {"text", "url"} séparés par « | », chaque élément cliquable).
CONTACT_RECT  = fitz.Rect(34.5, 66.0, 505.0, 78.0)
CONTACT_X     = 36.0
CONTACT_Y     = 75.0
CONTACT_SIZE  = 10.0
CONTACT_COLOR = (0.0, 0.0, 1.0)


# ── Polices ──────────────────────────────────────────────────
# Les polices embarquées dans le PDF source sont sous-ensemblées : elles ne
# contiennent que les glyphes utilisés à l'origine (le « R » et le « M » de
# Calibri regular manquaient, remplacés par un fallback à empattements).
# On préfère donc les fichiers système complets quand ils sont disponibles.
SYSTEM_FONTS = {
    "reg": [
        "/Applications/Microsoft Word.app/Contents/Resources/DFonts/Calibri.ttf",
        "/Applications/Microsoft PowerPoint.app/Contents/Resources/DFonts/Calibri.ttf",
    ],
    "bold": [
        "/Applications/Microsoft Word.app/Contents/Resources/DFonts/Calibrib.ttf",
        "/Applications/Microsoft PowerPoint.app/Contents/Resources/DFonts/Calibrib.ttf",
    ],
    "arial": [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
    ],
}


def _system_font(kind):
    for path in SYSTEM_FONTS.get(kind, []):
        if os.path.exists(path):
            return path
    return None


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

    fallback = {"reg": cal_xref or 5, "bold": cal_bold_xref or 4, "arial": arial_xref or 6}
    fonts = {
        kind: fitz.Font(fontfile=_system_font(kind) or extract(xref))
        for kind, xref in fallback.items()
    }
    return fonts, tmp_files


# ── Utilitaires ──────────────────────────────────────────────
def wrap(text, font, x_start, x_end=None, size=None):
    if x_end is None:
        x_end = RIGHT_MARGIN
    if size is None:
        size = FONT_SIZE
    avail = x_end - x_start
    words = text.split()
    lines, cur = [], ""
    for w in words:
        candidate = (cur + " " + w).strip()
        if font.text_length(candidate, fontsize=size) <= avail:
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


# ── Photo ────────────────────────────────────────────────────
def find_photo(page):
    """Retourne l'info de l'image du header (coin haut droit), ou None."""
    for info in page.get_image_info(xrefs=True):
        x0, y0, x1, y1 = info["bbox"]
        if x0 > 400 and y1 < 130 and (x1 - x0) > 30:
            return info
    return None


def replace_photo(page, photo_path):
    """Remplace la photo du header, recadrée au ratio du cadre (pas de déformation)."""
    from io import BytesIO
    from PIL import Image

    info = find_photo(page)
    if info is None:
        print("⚠  Photo introuvable dans le PDF source — remplacement ignoré")
        return

    frame = fitz.Rect(info["bbox"])
    ratio = frame.width / frame.height

    img = Image.open(photo_path).convert("RGB")
    # Recadrage centré au ratio du cadre
    if img.width / img.height > ratio:
        w = round(img.height * ratio)
        box = ((img.width - w) // 2, 0, (img.width - w) // 2 + w, img.height)
    else:
        h = round(img.width / ratio)
        box = (0, (img.height - h) // 2, img.width, (img.height - h) // 2 + h)
    img = img.crop(box)

    # Rééchantillonnage à PHOTO_DPI (inutile de stocker plus)
    target_w = round(frame.width / 72.0 * PHOTO_DPI)
    if img.width > target_w:
        img = img.resize((target_w, round(target_w / ratio)), Image.LANCZOS)

    buf = BytesIO()
    img.save(buf, format="JPEG", quality=92, optimize=True)
    page.replace_image(info["xref"], stream=buf.getvalue())
    print(f"ℹ  Photo remplacée : {img.width}×{img.height}px "
          f"({img.width / (frame.width / 72.0):.0f} dpi)")


# ── Sections ─────────────────────────────────────────────────
def render_contact(page, fonts, contact):
    tw = fitz.TextWriter(page.rect, color=CONTACT_COLOR)
    sep = fitz.TextWriter(page.rect)
    font, x = fonts["reg"], CONTACT_X
    sep_text = "  |  "
    for i, item in enumerate(contact):
        if i:
            sep.append((x, CONTACT_Y), sep_text, font=font, fontsize=CONTACT_SIZE)
            x += font.text_length(sep_text, fontsize=CONTACT_SIZE)
        text = item["text"]
        w = font.text_length(text, fontsize=CONTACT_SIZE)
        tw.append((x, CONTACT_Y), text, font=font, fontsize=CONTACT_SIZE)
        if item.get("url"):
            page.insert_link({"kind": fitz.LINK_URI, "uri": item["url"],
                              "from": fitz.Rect(x, CONTACT_Y - 8, x + w, CONTACT_Y + 2)})
        x += w
    tw.write_text(page)
    sep.write_text(page)


def render_summary(tw, fonts, summary, x_end=SUMMARY_X_END):
    lines = wrap(summary, fonts["reg"], SUMMARY_X, x_end, size=SUMMARY_SIZE)
    if len(lines) > SUMMARY_MAX_LINES:
        print(f"⚠  Accroche trop longue ({len(lines)} lignes, max {SUMMARY_MAX_LINES}) — elle empiète sur la suite")
    y = SUMMARY_Y0
    for line in lines:
        tw.append((SUMMARY_X, y), line, font=fonts["reg"], fontsize=SUMMARY_SIZE)
        y += SUMMARY_LINE_H



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
            y += EXP_GAP

    return y


def render_projects(page, tw, fonts, projects, y):
    if not projects:
        return y - SECTION_GAP
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


SKILL_LABELS = {"technical": "Technical", "ai": "AI & Automation", "languages": "Languages"}


def render_skills(page, tw, fonts, skills, y):
    y += SECTION_GAP
    tw.append((X_LEFT, y), "TECHNICAL AND LANGUAGES SKILLS", font=fonts["bold"], fontsize=FONT_SIZE)
    dashed_line(page, y + 2, x0=34.5, x1=577.0)
    y += LINE_H + 8
    # Une ligne par clé, dans l'ordre du config ; les valeurs longues sont repliées
    # sous le libellé.
    for i, (key, value) in enumerate((k, v) for k, v in skills.items() if v):
        if i:
            y += LINE_H
        label = SKILL_LABELS.get(key, key.replace("_", " ").title()) + ":"
        tw.append((X_LEFT, y), label, font=fonts["bold"], fontsize=FONT_SIZE)
        x_val = X_LEFT + fonts["bold"].text_length(label + "  ", fontsize=FONT_SIZE)
        lines = wrap(value, fonts["reg"], x_val)
        tw.append((x_val, y), lines[0], font=fonts["reg"], fontsize=FONT_SIZE)
        for line in lines[1:]:
            y += LINE_H
            tw.append((x_val, y), line, font=fonts["reg"], fontsize=FONT_SIZE)
    return y


# ── Rendu complet & auto-fit ─────────────────────────────────
def render_all(page, tw, fonts, cfg, cut_y):
    """Écrit toutes les sections et retourne le y atteint en bas de page."""
    y = cut_y + 8
    if cfg.get("experience"):
        y = render_experience(page, tw, fonts, cfg["experience"], y)
        y += SECTION_GAP
    y = render_projects(page, tw, fonts, cfg.get("projects", []), y)
    y = render_education(page, tw, fonts, cfg.get("education", []), y)
    y = render_skills(page, tw, fonts, cfg.get("skills", {}), y)
    return y


def _apply_metrics(preset):
    global FONT_SIZE, LINE_H, SECTION_GAP, ENTRY_GAP, EXP_GAP, BULLET_SIZE
    FONT_SIZE, LINE_H, SECTION_GAP, ENTRY_GAP, EXP_GAP = preset
    BULLET_SIZE = FONT_SIZE * 1.3


def fit_metrics(fonts, cfg, cut_y):
    """Sélectionne le preset le plus aéré qui tienne sur une page."""
    for preset in FIT_PRESETS:
        _apply_metrics(preset)
        scratch = fitz.open()
        page = scratch.new_page(width=PAGE_W, height=PAGE_H)
        y = render_all(page, fitz.TextWriter(page.rect), fonts, cfg, cut_y)
        scratch.close()
        if y <= MAX_Y:
            return preset, y
    return FIT_PRESETS[-1], y


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
        photo = cfg.get("photo", "")
        photo = photo.strip() if isinstance(photo, str) else photo
        if photo is False:
            info = find_photo(page)
            if info:
                page.add_redact_annot(fitz.Rect(info["bbox"]), fill=(1, 1, 1))
        elif photo:
            photo_path = Path(photo)
            if not photo_path.is_absolute():
                photo_path = DIR / photo_path
            if photo_path.exists():
                replace_photo(page, photo_path)
            else:
                print(f"⚠  Photo introuvable : {photo_path}")

        summary = cfg.get("summary", "").strip()
        page.add_redact_annot(fitz.Rect(0, cut_y, PAGE_W, PAGE_H), fill=(1, 1, 1))
        if summary:
            page.add_redact_annot(SUMMARY_RECT, fill=(1, 1, 1))
        contact = cfg.get("contact")
        if contact:
            for link in page.get_links():
                if link["from"].intersects(CONTACT_RECT):
                    page.delete_link(link)
            page.add_redact_annot(CONTACT_RECT, fill=(1, 1, 1))
        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_REMOVE if photo is False
                              else fitz.PDF_REDACT_IMAGE_NONE)

        preset, y_end = fit_metrics(fonts, cfg, cut_y)
        if y_end > MAX_Y:
            print(f"⚠  Contenu trop long : dépasse de {y_end - MAX_Y:.0f}pt même au réglage le plus dense")
        elif preset is not FIT_PRESETS[0]:
            print(f"ℹ  Auto-fit : corps {preset[0]}pt / interligne {preset[1]}pt")

        tw = fitz.TextWriter(page.rect)
        if contact:
            render_contact(page, fonts, contact)
        if summary:
            render_summary(tw, fonts, summary,
                           RIGHT_MARGIN if photo is False else SUMMARY_X_END)
        render_all(page, tw, fonts, cfg, cut_y)
        tw.write_text(page)
        # Les Calibri système sont complètes (~1,5 Mo chacune) : on ne garde
        # que les glyphes réellement utilisés.
        try:
            doc.subset_fonts()
        except Exception as exc:
            print(f"⚠  Sous-ensemblage des polices impossible ({exc}) — PDF plus lourd")
        doc.save(str(output), garbage=4, deflate=True)
        print(f"✓  Généré : {output}")

    finally:
        doc.close()
        for p in tmp_files:
            try:
                os.unlink(p)
            except OSError:
                pass


def _arg(name, default):
    if name in sys.argv:
        return sys.argv[sys.argv.index(name) + 1]
    return default


if __name__ == "__main__":
    out = _arg("--output", OUTPUT_PDF)
    if "--preview" in sys.argv:
        out = DIR / "CV_preview.pdf"
        print("Mode preview →", out)
    generate(config_path=_arg("--config", CONFIG_FILE),
             original=_arg("--source", ORIGINAL_PDF), output=out)
