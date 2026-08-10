#!/usr/bin/env python3
"""Re-aligne les dates/lieux de la colonne droite d'un CV sur une marge droite propre.

Usage : python3 fix_dates.py <source.pdf> [sortie.pdf]
"""
import fitz, tempfile, os, sys
from pathlib import Path

if len(sys.argv) < 2:
    sys.exit(__doc__)

SRC = sys.argv[1]
OUT = sys.argv[2] if len(sys.argv) > 2 else str(Path(SRC).with_suffix("")) + " - aligned.pdf"
TARGET_RIGHT = 561.0          # bord droit du contenu (= fin des lignes pointillées)

doc = fitz.open(SRC)
page = doc[0]

# Police Calibri régulière embarquée (xref 162)
font_data = doc.extract_font(162)[3]
tmp = tempfile.NamedTemporaryFile(suffix=".ttf", delete=False); tmp.write(font_data); tmp.close()
cal = fitz.Font(fontfile=tmp.name)

# Repérer les spans de la colonne droite (dates + lieux) : tout ce qui est right-aligné
# loin à droite (x0 > 490 et bord droit > 580).
targets = []
for b in page.get_text("dict")["blocks"]:
    if b.get("type") != 0:
        continue
    for ln in b["lines"]:
        for s in ln["spans"]:
            t = s["text"]
            if not t.strip():
                continue
            x0, x1 = s["bbox"][0], s["bbox"][2]
            if x0 > 490 and x1 > 580:
                targets.append({
                    "text": t.rstrip(),
                    "bbox": s["bbox"],
                    "oy": s["origin"][1],
                    "size": s["size"],
                })

print(f"{len(targets)} spans à réaligner")

# 1) Effacer les anciens (redaction blanche), bbox élargi d'1pt pour bien nettoyer
for tg in targets:
    x0, y0, x1, y1 = tg["bbox"]
    page.add_redact_annot(fitz.Rect(x0 - 1, y0 - 1, x1 + 2, y1 + 1), fill=(1, 1, 1))
page.apply_redactions()

# 2) Réécrire right-aligned sur TARGET_RIGHT
tw = fitz.TextWriter(page.rect, color=(0, 0, 0))
for tg in targets:
    txt = tg["text"].strip()
    w = cal.text_length(txt, fontsize=tg["size"])
    new_x = TARGET_RIGHT - w
    tw.append((new_x, tg["oy"]), txt, font=cal, fontsize=tg["size"])
tw.write_text(page)

doc.save(OUT, garbage=4, deflate=True)
doc.close()
os.unlink(tmp.name)
print("✓ écrit :", OUT)
