# CLAUDE.md

## Règles de rédaction du CV

S'appliquent à toute création ou modification de contenu dans `cv_config*.json`.

1. **Concis.** Une page idéalement, mais la pertinence prime sur une limite arbitraire. Le CV doit montrer qu'on sait écrire clairement et prioriser.
2. **Rien d'hors-sujet.** Rendre la pertinence de chaque élément évidente pour le poste visé et retirer tout ce qui n'apporte pas de signal (ex. réussites du lycée, expériences anciennes sans lien).
3. **L'impact, pas l'action.** Quantifier le résultat au lieu de lister des tâches. « Ré-architecturé un agent » ne dit rien ; « latence réduite de 2 s, satisfaction client en hausse » montre un impact. Pour un rôle commercial, parler chiffre d'affaires.
4. **Facile à survoler.** Mettre en gras l'essentiel et placer la preuve la plus forte en premier sous chaque expérience. Dans une pile de CV, on doit voir en quelques secondes pourquoi celui-ci mérite un entretien. Le gras se déclare dans le champ `bold` du JSON : une liste d'expressions exactes à mettre en gras dans les puces d'expérience, ex. `"bold": ["11 AI tools", "5 clients"]`. Réserver le gras aux métriques et résultats clés, quelques mots par puce au plus.

Fil conducteur : communication claire, pertinence et preuves d'impact.
