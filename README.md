# CV Julien Hassan + Générateur de CV

Ce repo a deux usages :

1. **Me présenter.** Mon CV est à jour ici, en deux versions :
   - [`CV - JULIEN HASSAN.pdf`](CV%20-%20JULIEN%20HASSAN.pdf) (version FR/EU)
   - [`CV - JULIEN HASSAN (US:UK).pdf`](CV%20-%20JULIEN%20HASSAN%20(US%3AUK).pdf) (version US/UK, sans photo)

   Applied AI Engineer : je conçois des outils internes et des automatisations IA, de la cartographie des process jusqu'à la mise en production.

2. **Partager le template.** Le CV est généré par un petit outil Python à partir d'un fichier JSON. Si la mise en page vous plaît, vous pouvez la reprendre pour votre propre CV.

## Utiliser le générateur

Prérequis : Python 3, `pymupdf` et `flask`.

```bash
pip install pymupdf flask
```

**En ligne de commande**, à partir de `cv_config.json` :

```bash
python3 cv_editor.py                     # génère "CV JULIEN HASSAN.pdf"
python3 cv_editor.py --preview           # génère CV_preview.pdf
python3 cv_editor.py --output mon_cv.pdf # choisir le fichier de sortie
```

**Avec l'interface web**, pour éditer les sections et voir l'aperçu :

```bash
python3 cv_web.py   # puis ouvrir http://localhost:5001
```

## Reprendre le template pour votre CV

1. Forkez ou clonez le repo.
2. Modifiez `cv_config.json` (ou `cv_config_us.json`) : accroche, expériences, projets, formation, compétences, liens de contact.
3. Photo : indiquez le chemin de votre image dans `"photo"`, ou mettez `false` pour la retirer.
4. Lancez `python3 cv_editor.py`. La mise en page s'ajuste automatiquement pour tenir sur une page.

Le script réécrit le contenu d'un PDF gabarit à partir du JSON. Passez-lui un PDF de base avec `--source mon_gabarit.pdf` (par défaut : `CV JULIEN HASSAN copie.pdf`, non inclus dans le repo).

Libre à vous de le réutiliser. Une étoile ⭐ sur le repo fait toujours plaisir.
