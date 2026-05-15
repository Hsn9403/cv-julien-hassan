#!/usr/bin/env python3
"""
CV Editor — interface web
Usage : python3 cv_web.py   →  http://localhost:5001
"""

import json, os, sys, tempfile
from pathlib import Path
import re
import fitz
from flask import Flask, request, jsonify, send_file, render_template_string

DIR = Path(__file__).parent
sys.path.insert(0, str(DIR))
from cv_editor import generate as generate_cv, ORIGINAL_PDF, CONFIG_FILE

app = Flask(__name__)

# ─────────────────────────────────────────────────────────────
HTML = r"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CV Editor</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f1f5f9;color:#1e293b;min-height:100vh}
.app{max-width:880px;margin:0 auto;padding:28px 16px}

/* Header */
.header{display:flex;align-items:center;gap:12px;margin-bottom:28px}
.header-icon{width:40px;height:40px;background:#1e293b;border-radius:10px;display:flex;align-items:center;justify-content:center;color:white;font-size:1.2rem}
.header h1{font-size:1.4rem;font-weight:700;color:#1e293b}
.header p{font-size:.85rem;color:#64748b;margin-top:2px}

/* Steps */
.steps{display:flex;gap:6px;margin-bottom:24px}
.step{flex:1;padding:10px 8px;border-radius:8px;background:#e2e8f0;color:#94a3b8;font-size:.8rem;font-weight:600;text-align:center;transition:all .2s;cursor:default}
.step span{display:block;font-size:.65rem;font-weight:500;margin-top:2px;opacity:.8}
.step.active{background:#1e293b;color:#fff}
.step.done{background:#22c55e;color:#fff}

/* Upload */
.dropzone{border:2px dashed #cbd5e1;border-radius:14px;padding:48px 24px;text-align:center;cursor:pointer;transition:all .2s;background:#fff}
.dropzone:hover,.dropzone.over{border-color:#3b82f6;background:#eff6ff}
.dropzone .icon{font-size:2.5rem;margin-bottom:12px}
.dropzone .title{font-size:1rem;font-weight:600;color:#334155;margin-bottom:6px}
.dropzone .sub{font-size:.85rem;color:#64748b}
.dropzone .filename{color:#3b82f6;font-weight:700;font-size:1rem}
#file-input{display:none}
.upload-card{background:#fff;border-radius:14px;padding:24px;box-shadow:0 1px 4px rgba(0,0,0,.08);margin-bottom:16px}
.upload-actions{display:flex;justify-content:flex-end;margin-top:16px}

/* Sections accordéon */
.section-wrap{background:#fff;border-radius:12px;box-shadow:0 1px 3px rgba(0,0,0,.07);margin-bottom:12px;overflow:hidden}
.section-header{display:flex;align-items:center;justify-content:space-between;padding:14px 18px;cursor:pointer;user-select:none;border-bottom:1px solid transparent;transition:background .15s}
.section-header:hover{background:#f8fafc}
.section-header.open{border-bottom-color:#e2e8f0}
.section-title{font-size:.75rem;font-weight:700;letter-spacing:.07em;text-transform:uppercase;color:#475569}
.section-chevron{color:#94a3b8;transition:transform .2s;font-size:.9rem}
.section-header.open .section-chevron{transform:rotate(180deg)}
.section-body{display:none;padding:14px 18px 18px}
.section-body.open{display:block}

/* Entry cards */
.entry-card{background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:14px;margin-bottom:10px;position:relative}
.entry-card:last-child{margin-bottom:0}
.entry-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}
.entry-label{font-size:.75rem;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:.05em}
.remove-entry{background:none;border:none;color:#ef4444;cursor:pointer;font-size:1.1rem;padding:2px 6px;border-radius:4px;line-height:1;transition:background .15s}
.remove-entry:hover{background:#fef2f2}

/* Forms */
.form-row{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:10px}
.form-row-1{margin-bottom:10px}
.form-group label{display:block;font-size:.7rem;font-weight:600;color:#64748b;text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px}
.form-group label .hint{font-weight:400;text-transform:none;letter-spacing:0;color:#94a3b8}
.form-group input,.form-group textarea{width:100%;border:1px solid #e2e8f0;border-radius:7px;padding:8px 10px;font-size:.875rem;font-family:inherit;color:#1e293b;background:#fff;transition:border-color .15s;resize:vertical}
.form-group input:focus,.form-group textarea:focus{outline:none;border-color:#3b82f6;box-shadow:0 0 0 3px rgba(59,130,246,.1)}
.form-group textarea{min-height:58px}

/* Bullets */
.bullets-label{font-size:.7rem;font-weight:600;color:#64748b;text-transform:uppercase;letter-spacing:.05em;margin-bottom:6px}
.bullet-row{display:flex;gap:6px;align-items:flex-start;margin-bottom:6px}
.bullet-row textarea{flex:1;min-height:48px;border:1px solid #e2e8f0;border-radius:7px;padding:7px 9px;font-size:.875rem;font-family:inherit;color:#1e293b;background:#fff;resize:vertical}
.bullet-row textarea:focus{outline:none;border-color:#3b82f6;box-shadow:0 0 0 3px rgba(59,130,246,.1)}
.remove-bullet{flex-shrink:0;background:none;border:1px solid #e2e8f0;border-radius:6px;width:28px;height:28px;color:#ef4444;cursor:pointer;font-size:.95rem;display:flex;align-items:center;justify-content:center;transition:all .15s}
.remove-bullet:hover{background:#fef2f2;border-color:#fca5a5}

/* Buttons */
.btn-add-bullet{display:flex;align-items:center;gap:5px;font-size:.78rem;font-weight:600;color:#3b82f6;background:none;border:1px dashed #bfdbfe;border-radius:6px;padding:5px 10px;cursor:pointer;transition:all .15s;margin-top:4px}
.btn-add-bullet:hover{background:#eff6ff;border-color:#93c5fd}
.btn-add-entry{display:flex;align-items:center;gap:6px;width:100%;justify-content:center;padding:10px;background:#f0fdf4;border:1px dashed #86efac;border-radius:8px;color:#16a34a;font-size:.85rem;font-weight:600;cursor:pointer;margin-top:10px;transition:all .15s}
.btn-add-entry:hover{background:#dcfce7;border-color:#4ade80}

/* Skills section */
.skills-grid{display:grid;grid-template-columns:auto 1fr;gap:6px 12px;align-items:center}
.skills-grid label{font-size:.7rem;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:.05em;white-space:nowrap}
.skills-grid input{border:1px solid #e2e8f0;border-radius:7px;padding:8px 10px;font-size:.875rem;font-family:inherit;color:#1e293b;background:#fff}
.skills-grid input:focus{outline:none;border-color:#3b82f6;box-shadow:0 0 0 3px rgba(59,130,246,.1)}

/* Generate / Actions */
.actions{margin-top:20px}
.btn-generate{width:100%;padding:14px;background:#1e293b;color:white;border:none;border-radius:10px;font-size:.95rem;font-weight:700;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:8px;transition:background .15s}
.btn-generate:hover{background:#0f172a}
.btn-generate:disabled{opacity:.5;cursor:not-allowed}

/* Progress */
.progress-card{background:#fff;border-radius:14px;padding:24px;box-shadow:0 1px 4px rgba(0,0,0,.08);margin-top:12px}
.progress-title{font-size:.9rem;font-weight:600;color:#334155;margin-bottom:14px;display:flex;align-items:center;gap:8px}
.progress-bar{height:8px;background:#e2e8f0;border-radius:999px;overflow:hidden;margin-bottom:8px}
.progress-fill{height:100%;background:linear-gradient(90deg,#3b82f6,#6366f1);border-radius:999px;width:0%;transition:width .25s ease}
.progress-meta{display:flex;justify-content:space-between;font-size:.78rem;color:#64748b}

/* Download */
.download-card{display:none;background:#f0fdf4;border:1px solid #86efac;border-radius:12px;padding:20px;margin-top:12px;text-align:center}
.download-card.visible{display:block}
.download-card .check{font-size:2rem;margin-bottom:8px}
.download-card h3{font-size:1rem;font-weight:700;color:#166534;margin-bottom:4px}
.download-card p{font-size:.85rem;color:#4d7c0f;margin-bottom:16px}
.btn-download{display:inline-flex;align-items:center;gap:8px;padding:12px 24px;background:#16a34a;color:white;border-radius:8px;font-weight:700;font-size:.9rem;cursor:pointer;border:none;text-decoration:none;transition:background .15s}
.btn-download:hover{background:#15803d}

/* Divider */
.divider{height:1px;background:#e2e8f0;margin:20px 0}

/* Spinner */
@keyframes spin{to{transform:rotate(360deg)}}
.spinner{display:inline-block;width:16px;height:16px;border:2px solid rgba(255,255,255,.3);border-top-color:white;border-radius:50%;animation:spin .6s linear infinite}
</style>
</head>
<body>
<div class="app">

  <!-- Header -->
  <div class="header">
    <div class="header-icon">CV</div>
    <div>
      <h1>CV Editor</h1>
      <p>Modifie ton CV, génère le PDF en un clic</p>
    </div>
  </div>

  <!-- Steps -->
  <div class="steps">
    <div class="step active" id="step-1">1. Importer<span>Ton CV PDF</span></div>
    <div class="step" id="step-2">2. Modifier<span>Contenu</span></div>
    <div class="step" id="step-3">3. Télécharger<span>PDF généré</span></div>
  </div>

  <!-- ── Step 1 : Upload ── -->
  <div id="upload-section">
    <div class="upload-card">
      <div class="dropzone" id="dropzone">
        <input type="file" id="file-input" accept=".pdf">
        <div class="icon"></div>
        <div class="title drop-title">Dépose ton CV ici</div>
        <div class="sub drop-sub">ou <u style="cursor:pointer" onclick="document.getElementById('file-input').click()">clique pour parcourir</u></div>
      </div>
      <div class="upload-actions">
        <button class="btn-generate" style="width:auto;padding:10px 24px" id="continue-btn" onclick="startEditing()" disabled>
          Continuer →
        </button>
      </div>
    </div>
  </div>

  <!-- ── Step 2 : Edit ── -->
  <div id="edit-section" style="display:none">

    <!-- Experience -->
    <div class="section-wrap">
      <div class="section-header open" onclick="toggleSection(this)">
        <span class="section-title">Expérience Professionnelle</span>
        <span class="section-chevron">▾</span>
      </div>
      <div class="section-body open">
        <div id="experience-entries"></div>
        <button class="btn-add-entry" onclick="addExpEntry()">+ Ajouter une expérience</button>
      </div>
    </div>

    <!-- Projects -->
    <div class="section-wrap">
      <div class="section-header open" onclick="toggleSection(this)">
        <span class="section-title">Projets</span>
        <span class="section-chevron">▾</span>
      </div>
      <div class="section-body open">
        <div id="project-entries"></div>
        <button class="btn-add-entry" onclick="addProjEntry()">+ Ajouter un projet</button>
      </div>
    </div>

    <!-- Education -->
    <div class="section-wrap">
      <div class="section-header" onclick="toggleSection(this)">
        <span class="section-title">Formation</span>
        <span class="section-chevron">▾</span>
      </div>
      <div class="section-body">
        <div id="education-entries"></div>
        <button class="btn-add-entry" onclick="addEduEntry()">+ Ajouter une formation</button>
      </div>
    </div>

    <!-- Skills -->
    <div class="section-wrap">
      <div class="section-header" onclick="toggleSection(this)">
        <span class="section-title">Compétences</span>
        <span class="section-chevron">▾</span>
      </div>
      <div class="section-body">
        <div class="skills-grid">
          <label>Technique</label>
          <input type="text" id="skills-technical" placeholder="Python, JavaScript...">
          <label>Langues</label>
          <input type="text" id="skills-languages" placeholder="French (native), English (C1)...">
        </div>
      </div>
    </div>

    <div class="actions">
      <button class="btn-generate" id="generate-btn" onclick="generateCV()">
        <span id="gen-label">Générer mon CV</span>
        <span id="gen-spinner" class="spinner" style="display:none"></span>
      </button>
    </div>
  </div>

  <!-- ── Step 3 : Progress + Download ── -->
  <div id="result-section" style="display:none">
    <div class="progress-card">
      <div class="progress-title">
        <span id="progress-icon"></span>
        <span id="progress-label">Génération en cours…</span>
      </div>
      <div class="progress-bar"><div class="progress-fill" id="progress-fill"></div></div>
      <div class="progress-meta">
        <span id="progress-step">Traitement du PDF…</span>
        <span id="progress-pct">0%</span>
      </div>
    </div>
    <div class="download-card" id="download-card">
      <div class="check"></div>
      <h3>Ton CV est prêt !</h3>
      <p>Le PDF a été généré avec succès.</p>
      <a id="download-link" class="btn-download">Télécharger le PDF</a>
      <div class="divider"></div>
      <button class="btn-generate" style="background:#475569" onclick="backToEdit()">← Faire d'autres modifications</button>
    </div>
  </div>

</div><!-- /app -->

<script>
// ── Upload ────────────────────────────────────────────────────
const dropzone  = document.getElementById('dropzone');
const fileInput = document.getElementById('file-input');

dropzone.addEventListener('dragover',  e => { e.preventDefault(); dropzone.classList.add('over'); });
dropzone.addEventListener('dragleave', () => dropzone.classList.remove('over'));
dropzone.addEventListener('drop', e => {
  e.preventDefault(); dropzone.classList.remove('over');
  handleFile(e.dataTransfer.files[0]);
});
dropzone.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', () => handleFile(fileInput.files[0]));

let uploadedFile = null;

function handleFile(file) {
  if (!file || !file.name.toLowerCase().endsWith('.pdf')) return;
  uploadedFile = file;
  dropzone.querySelector('.drop-title').innerHTML = `<span class="filename">${file.name}</span>`;
  dropzone.querySelector('.drop-sub').textContent  = 'Fichier sélectionné — clique sur Continuer';
  document.getElementById('continue-btn').disabled = false;
}

async function startEditing() {
  const btn = document.getElementById('continue-btn');
  btn.disabled = true;
  btn.textContent = 'Analyse du CV…';

  try {
    const formData = new FormData();
    formData.append('file', uploadedFile);
    const res = await fetch('/api/parse-pdf', { method: 'POST', body: formData });
    if (!res.ok) throw new Error(await res.text());
    const cfg = await res.json();
    setStep(2);
    show('edit-section'); hide('upload-section');
    populateForm(cfg);
  } catch(err) {
    alert('Erreur lors de l\'analyse : ' + err.message);
    btn.disabled = false;
    btn.textContent = 'Continuer →';
  }
}

// ── Config ────────────────────────────────────────────────────
function populateForm(cfg) {
  document.getElementById('experience-entries').innerHTML = '';
  (cfg.experience || []).forEach(e => addExpEntry(e));
  document.getElementById('project-entries').innerHTML = '';
  (cfg.projects || []).forEach(p => addProjEntry(p));
  document.getElementById('education-entries').innerHTML = '';
  (cfg.education || []).forEach(e => addEduEntry(e));
  document.getElementById('skills-technical').value = cfg.skills?.technical || '';
  document.getElementById('skills-languages').value = cfg.skills?.languages || '';
}

function loadConfig() {
  fetch('/api/config').then(r => r.json()).then(cfg => populateForm(cfg));
}

// ── Helpers ───────────────────────────────────────────────────
const esc = s => (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
const v   = (card, name) => (card.querySelector(`[name="${name}"]`)?.value || '').trim();

function bulletRow(text = '') {
  const d = document.createElement('div');
  d.className = 'bullet-row';
  d.innerHTML = `<textarea class="bullet-text">${esc(text)}</textarea>
    <button class="remove-bullet" onclick="this.closest('.bullet-row').remove()">×</button>`;
  return d;
}

function addBulletTo(container, text = '') {
  container.appendChild(bulletRow(text));
}

function toggleSection(header) {
  header.classList.toggle('open');
  header.nextElementSibling.classList.toggle('open');
}

// ── Experience entries ────────────────────────────────────────
function addExpEntry(data = {}) {
  const wrap = document.getElementById('experience-entries');
  const card = document.createElement('div');
  card.className = 'entry-card';
  card.innerHTML = `
    <div class="entry-header">
      <span class="entry-label">Expérience</span>
      <button class="remove-entry" onclick="this.closest('.entry-card').remove()">✕</button>
    </div>
    <div class="form-row">
      <div class="form-group"><label>Dates</label><input type="text" name="dates" value="${esc(data.dates)}"></div>
      <div class="form-group"><label>Lieu</label><input type="text" name="location" value="${esc(data.location)}"></div>
    </div>
    <div class="form-row">
      <div class="form-group"><label>Entreprise <span class="hint">(en gras)</span></label><input type="text" name="company" value="${esc(data.company)}"></div>
      <div class="form-group"><label>Type / Description courte</label><input type="text" name="company_type" value="${esc(data.company_type)}"></div>
    </div>
    <div class="form-row-1 form-group"><label>Poste <span class="hint">(en gras)</span></label><input type="text" name="role" value="${esc(data.role)}"></div>
    <div>
      <div class="bullets-label">Bullets</div>
      <div class="bullets-container"></div>
      <button class="btn-add-bullet" onclick="addBulletTo(this.previousElementSibling)">＋ Ajouter un bullet</button>
    </div>`;
  wrap.appendChild(card);
  (data.bullets || []).forEach(b => addBulletTo(card.querySelector('.bullets-container'), b));
}

// ── Project entries ───────────────────────────────────────────
function addProjEntry(data = {}) {
  const wrap = document.getElementById('project-entries');
  const card = document.createElement('div');
  card.className = 'entry-card';
  card.innerHTML = `
    <div class="entry-header">
      <span class="entry-label">Projet</span>
      <button class="remove-entry" onclick="this.closest('.entry-card').remove()">✕</button>
    </div>
    <div class="form-row-1 form-group"><label>Nom <span class="hint">(en gras)</span></label><input type="text" name="name" value="${esc(data.name)}"></div>
    <div class="form-row-1 form-group"><label>Description</label><textarea name="description">${esc(data.description)}</textarea></div>
    <div>
      <div class="bullets-label">Sub-bullets</div>
      <div class="bullets-container"></div>
      <button class="btn-add-bullet" onclick="addBulletTo(this.previousElementSibling)">＋ Ajouter un sub-bullet</button>
    </div>`;
  wrap.appendChild(card);
  (data.sub_bullets || []).forEach(b => addBulletTo(card.querySelector('.bullets-container'), b));
}

// ── Education entries ─────────────────────────────────────────
function addEduEntry(data = {}) {
  const wrap = document.getElementById('education-entries');
  const card = document.createElement('div');
  card.className = 'entry-card';
  card.innerHTML = `
    <div class="entry-header">
      <span class="entry-label">Formation</span>
      <button class="remove-entry" onclick="this.closest('.entry-card').remove()">✕</button>
    </div>
    <div class="form-row">
      <div class="form-group"><label>Dates</label><input type="text" name="dates" value="${esc(data.dates)}"></div>
      <div class="form-group"><label>Lieu</label><input type="text" name="location" value="${esc(data.location)}"></div>
    </div>
    <div class="form-row-1 form-group"><label>Établissement <span class="hint">(en gras)</span></label><input type="text" name="institution" value="${esc(data.institution)}"></div>
    <div class="form-row-1 form-group"><label>Sous-titre <span class="hint">(en gras)</span></label><input type="text" name="subtitle" value="${esc(data.subtitle)}"></div>
    <div class="form-row-1 form-group"><label>Description</label><input type="text" name="description" value="${esc(data.description)}"></div>`;
  wrap.appendChild(card);
}

// ── Collect & Generate ────────────────────────────────────────
function collectConfig() {
  const cfg = { experience: [], projects: [], education: [], skills: {} };

  document.querySelectorAll('#experience-entries .entry-card').forEach(card => {
    const entry = { dates: v(card,'dates'), company: v(card,'company'),
      company_type: v(card,'company_type'), location: v(card,'location'),
      role: v(card,'role'), bullets: [] };
    card.querySelectorAll('.bullet-text').forEach(t => { if(t.value.trim()) entry.bullets.push(t.value.trim()); });
    cfg.experience.push(entry);
  });

  document.querySelectorAll('#project-entries .entry-card').forEach(card => {
    const entry = { name: v(card,'name'), description: v(card,'description'), sub_bullets: [] };
    card.querySelectorAll('.bullet-text').forEach(t => { if(t.value.trim()) entry.sub_bullets.push(t.value.trim()); });
    cfg.projects.push(entry);
  });

  document.querySelectorAll('#education-entries .entry-card').forEach(card => {
    cfg.education.push({ dates: v(card,'dates'), institution: v(card,'institution'),
      subtitle: v(card,'subtitle'), description: v(card,'description'), location: v(card,'location') });
  });

  cfg.skills = {
    technical: document.getElementById('skills-technical').value.trim(),
    languages: document.getElementById('skills-languages').value.trim(),
  };
  return cfg;
}

async function generateCV() {
  const btn = document.getElementById('generate-btn');
  btn.disabled = true;
  document.getElementById('gen-label').style.display = 'none';
  document.getElementById('gen-spinner').style.display = 'inline-block';

  show('result-section');
  document.getElementById('download-card').classList.remove('visible');
  setProgress(0, 'Traitement du PDF…');
  setStep(3);

  const steps = ['Analyse du contenu…','Génération des sections…','Mise en page…','Finalisation…'];
  let p = 0, si = 0;
  const timer = setInterval(() => {
    p = Math.min(p + (Math.random() * 6 + 2), 85);
    si = Math.min(Math.floor(p / 22), steps.length - 1);
    setProgress(p, steps[si]);
  }, 180);

  try {
    const res = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(collectConfig())
    });
    if (!res.ok) { const t = await res.text(); throw new Error(t); }

    clearInterval(timer);
    setProgress(100, 'Terminé !');
    document.getElementById('progress-icon').textContent = '';
    document.getElementById('progress-label').textContent = 'CV généré avec succès';

    const blob = await res.blob();
    const url  = URL.createObjectURL(blob);
    const link = document.getElementById('download-link');
    link.href = url;
    link.download = 'CV.pdf';
    document.getElementById('download-card').classList.add('visible');
    btn.disabled = false;
    document.getElementById('gen-label').style.display = '';
    document.getElementById('gen-spinner').style.display = 'none';

  } catch(err) {
    clearInterval(timer);
    alert('Erreur : ' + err.message);
    btn.disabled = false;
    document.getElementById('gen-label').style.display = '';
    document.getElementById('gen-spinner').style.display = 'none';
    setStep(2);
  }
}

function backToEdit() {
  document.getElementById('result-section').style.display = 'none';
  document.getElementById('generate-btn').disabled = false;
  document.getElementById('gen-label').style.display = '';
  document.getElementById('gen-spinner').style.display = 'none';
  setStep(2);
}

// ── Utils ─────────────────────────────────────────────────────
function setProgress(pct, label) {
  document.getElementById('progress-fill').style.width = pct + '%';
  document.getElementById('progress-pct').textContent  = Math.round(pct) + '%';
  if (label) document.getElementById('progress-step').textContent = label;
}

function setStep(n) {
  document.querySelectorAll('.step').forEach((s,i) => {
    s.classList.remove('active','done');
    if (i+1 < n) s.classList.add('done');
    else if (i+1 === n) s.classList.add('active');
  });
}

function show(id) { document.getElementById(id).style.display = ''; }
function hide(id) { document.getElementById(id).style.display = 'none'; }
</script>
</body>
</html>"""


# ── Routes ────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/api/config")
def get_config():
    with open(CONFIG_FILE, encoding="utf-8") as f:
        return jsonify(json.load(f))


def _parse_cv_pdf(pdf_path):
    """Parse un PDF généré par cv_editor.py en utilisant les positions x connues."""
    doc = fitz.open(pdf_path)
    page = doc[0]

    raw_spans = []
    for block in page.get_text("dict")["blocks"]:
        if block.get("type") != 0:
            continue
        for ln in block["lines"]:
            for span in ln["spans"]:
                t = span["text"]
                if not t.strip():
                    continue
                raw_spans.append({
                    "x": span["origin"][0],
                    "y": span["origin"][1],
                    "text": t,
                    "bold": bool(span["flags"] & 16),
                })
    doc.close()

    # Regrouper par ligne (tolérance 4pt sur y)
    raw_spans.sort(key=lambda s: (s["y"], s["x"]))
    lines, cur_y, cur_line = [], None, []
    for s in raw_spans:
        if cur_y is None or abs(s["y"] - cur_y) <= 4:
            cur_line.append(s)
            if cur_y is None:
                cur_y = s["y"]
        else:
            lines.append(cur_line)
            cur_line, cur_y = [s], s["y"]
    if cur_line:
        lines.append(cur_line)

    SECTIONS = {
        "PROFESSIONAL EXPERIENCE": "experience",
        "PROJECTS":                "projects",
        "EDUCATION":               "education",
        "TECHNICAL AND LANGUAGES SKILLS": "skills",
    }

    cfg = {"experience": [], "projects": [], "education": [],
           "skills": {"technical": "", "languages": ""}}
    section = None
    cur_exp = cur_proj = cur_edu = None

    def flush():
        nonlocal cur_exp, cur_proj, cur_edu
        if cur_exp:  cfg["experience"].append(cur_exp); cur_exp = None
        if cur_proj: cfg["projects"].append(cur_proj);  cur_proj = None
        if cur_edu:  cfg["education"].append(cur_edu);  cur_edu = None

    for line in lines:
        full  = "".join(s["text"] for s in line).strip()
        min_x = min(s["x"] for s in line)

        # Détecter en-têtes de section
        matched = None
        for name, key in SECTIONS.items():
            if name in full:
                matched = key
                break
        if matched:
            flush()
            section = matched
            continue

        if section is None:
            continue

        if section == "experience":
            date_sp = [s for s in line if s["x"] < 110]
            rest_sp = [s for s in line if s["x"] >= 110]
            date_t  = "".join(s["text"] for s in date_sp).strip()

            # Nouvelle entrée : dates à gauche + company à droite
            if date_t and re.search(r'\d{2}', date_t) and rest_sp:
                flush()
                bold_co = "".join(s["text"] for s in rest_sp if s["bold"] and s["x"] < 500).strip()
                reg_co  = "".join(s["text"] for s in rest_sp if not s["bold"] and s["x"] < 500).strip()
                loc_t   = "".join(s["text"] for s in rest_sp if s["x"] >= 500).strip()
                cur_exp = {"dates": date_t, "company": bold_co, "company_type": reg_co,
                           "location": loc_t, "role": "", "bullets": []}
            elif cur_exp:
                role_sp = [s for s in line if s["x"] >= 110]
                if role_sp and all(s["bold"] for s in role_sp) and not cur_exp["role"]:
                    cur_exp["role"] = "".join(s["text"] for s in role_sp).strip()
                elif min_x >= 130:
                    raw_t  = "".join(s["text"] for s in line if s["x"] >= 130)
                    is_new = "​" in raw_t[:3]   # zero-width space = nouveau bullet (cercle graphique)
                    bt     = raw_t.replace("​", "").strip()
                    if bt:
                        if is_new or not cur_exp["bullets"]:
                            cur_exp["bullets"].append(bt)
                        else:
                            cur_exp["bullets"][-1] += " " + bt

        elif section == "projects":
            # Nom projet (bold) à x~52.5 — co-localisé avec le "•" à x~34.5
            name_sp = [s for s in line if s["bold"] and s["x"] >= 48]

            if name_sp:  # nouvelle entrée projet
                flush()
                name = "".join(s["text"] for s in name_sp).strip().rstrip(":")
                # Description inline sur la même ligne, au-delà du nom (x > 48, non bold)
                inline_sp = [s for s in line if not s["bold"] and s["x"] >= 48]
                desc = "".join(s["text"] for s in inline_sp).strip()
                cur_proj = {"name": name, "description": desc, "sub_bullets": []}
            elif cur_proj:
                # Format A : tiret x~54.8 + ​ x~57.8 + texte x~60
                has_subtext = any(s["x"] >= 57 for s in line)
                # Format B : tiret+texte fusionnés dans un seul span à x~54.8
                dash_sp = [s for s in line if 52 <= s["x"] <= 56
                           and s["text"].lstrip().startswith(("‐", "-", "–"))]
                if has_subtext:
                    t = "".join(s["text"] for s in line if s["x"] >= 57).strip().replace("​", "")
                    if t:
                        cur_proj["sub_bullets"].append(t)
                elif dash_sp:
                    for sp in dash_sp:
                        t = sp["text"].lstrip().lstrip("‐-– ").strip()
                        if t:
                            cur_proj["sub_bullets"].append(t)
                else:  # suite de description à x~52.5
                    cont = "".join(s["text"] for s in line if s["x"] >= 45 and not s["bold"]).strip()
                    if cont:
                        cur_proj["description"] += " " + cont

        elif section == "education":
            date_sp = [s for s in line if s["x"] < 110]
            rest_sp = [s for s in line if s["x"] >= 110]
            date_t  = "".join(s["text"] for s in date_sp).strip()

            if date_t and re.search(r'\d{4}', date_t):
                flush()
                inst_t = "".join(s["text"] for s in rest_sp if s["bold"] and s["x"] < 500).strip()
                loc_t  = "".join(s["text"] for s in rest_sp if s["x"] >= 500).strip()
                cur_edu = {"dates": date_t, "institution": inst_t,
                           "subtitle": "", "description": "", "location": loc_t}
            elif cur_edu and rest_sp:
                t       = "".join(s["text"] for s in rest_sp).strip()
                is_bold = any(s["bold"] for s in rest_sp)
                if is_bold and not cur_edu["subtitle"]:
                    cur_edu["subtitle"] = t
                elif t:
                    cur_edu["description"] = t

        elif section == "skills":
            bold_t = "".join(s["text"] for s in line if s["bold"]).strip()
            reg_t  = "".join(s["text"] for s in line if not s["bold"]).strip()
            if "Technical" in bold_t:
                cfg["skills"]["technical"] = reg_t
            elif "Languages" in bold_t:
                cfg["skills"]["languages"] = reg_t

    flush()

    def _clean(obj):
        if isinstance(obj, str):
            s = obj.replace("​", "").replace("\xa0", " ")
            return re.sub(r" {2,}", " ", s).strip()
        if isinstance(obj, list):  return [_clean(v) for v in obj]
        if isinstance(obj, dict):  return {k: _clean(v) for k, v in obj.items()}
        return obj

    return _clean(cfg)


@app.route("/api/parse-pdf", methods=["POST"])
def parse_pdf():
    if 'file' not in request.files:
        return "Fichier manquant", 400

    file = request.files['file']
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    file.save(tmp.name)
    tmp.close()

    try:
        return jsonify(_parse_cv_pdf(tmp.name))
    except Exception as e:
        return str(e), 500
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


@app.route("/api/generate", methods=["POST"])
def api_generate():
    cfg = request.get_json(force=True)

    tmp_cfg = tempfile.NamedTemporaryFile(
        suffix=".json", delete=False, mode="w", encoding="utf-8"
    )
    json.dump(cfg, tmp_cfg, ensure_ascii=False)
    tmp_cfg.close()

    tmp_out = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp_out.close()

    try:
        generate_cv(
            config_path=tmp_cfg.name,
            original=ORIGINAL_PDF,
            output=tmp_out.name,
        )
        return send_file(
            tmp_out.name,
            as_attachment=True,
            download_name="CV.pdf",
            mimetype="application/pdf",
        )
    except Exception as e:
        return str(e), 500
    finally:
        os.unlink(tmp_cfg.name)


# ── Main ──────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5003))
    print(f"\n  CV Editor → http://localhost:{port}\n")
    app.run(debug=False, port=port)
