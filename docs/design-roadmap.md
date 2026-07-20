# Pilottelega — Roadmap de design UX/UI

> Objectif : transformer l'interface actuelle (un long écran qui défile + onglets)
> en une application **claire, moderne et sûre**, sans toucher à la logique métier
> (`core/`) ni casser le multilingue (FR/EN/RU).

---

## 1. Diagnostic UX (état actuel)

| Problème | Impact |
|---|---|
| Tout sur un seul écran qui défile (config + actions + résultats) | Surcharge, on se perd |
| Aucune hiérarchie visuelle, look Qt par défaut | Paraît « technique », peu rassurant |
| La liste « à ne jamais retirer » occupe l'écran en permanence | Bruit visuel |
| Onglet « Retirer » : 4 modes + lots + options empilés | Confusion, erreurs possibles |
| Pas d'action principale claire par écran | L'utilisateur hésite |
| Retour d'info = petit label en bas | Peu visible, surtout sur actions sensibles |
| Pas de mode sombre, pas d'identité visuelle | Fatigue visuelle, image « brouillon » |

---

## 2. Principes directeurs (les règles qu'on suit)

1. **Divulgation progressive** — n'afficher que ce qui sert à la tâche en cours.
2. **Une action principale par écran** — mise en avant visuelle (bouton primaire).
3. **Sécurité des actions destructives** — confirmation + aperçu + couleur d'alerte.
4. **Cohérence** — un seul système de composants et de couleurs (design tokens).
5. **Feedback immédiat** — progression, succès, erreurs lisibles (toasts).
6. **Accessibilité** — contraste AA, navigation clavier, tailles de clic suffisantes.
7. **i18n préservée** — chaque texte via `tr()`, mises en page qui tolèrent le russe (plus long).

---

## 3. Architecture de l'information (nouvelle navigation)

On sépare **configuration** et **actions**, et on remplace « long scroll + onglets » par
une **barre latérale** (sidebar) + **pages empilées** (`QStackedWidget`).

```
┌───────────────┬─────────────────────────────────────────────┐
│  Pilottelega  │  [Compte connecté @xxx]           [Langue ▾] │  ← en-tête
├───────────────┼─────────────────────────────────────────────┤
│ ● Groupes     │                                             │
│ ○ Analyse     │            CONTENU DE LA PAGE                │
│ ○ Nettoyage   │            (une tâche à la fois)            │
│ ○ Vérifier    │                                             │
│ ○ Historique  │                                             │
│ ─────────     │                                             │
│ ⚙ Paramètres  │                                             │
└───────────────┴─────────────────────────────────────────────┘
```

**On déplace dans « Paramètres »** (hors du flux principal) : liste des comptes protégés,
« exclure les bots », langue, gestion des clés d'accès, groupes enregistrés.

---

## 4. Système de design (design tokens)

Un module `theme.py` centralise les jetons ; on génère la QSS (feuille de style Qt) à partir d'eux.

- **Couleurs** : 1 primaire (bleu distinct), neutres (gris), sémantiques
  succès `#2e7d32` / alerte `#f9a825` / danger `#c62828` / info `#1565c0`.
- **Thèmes** : **clair** + **sombre** (bascule dans l'en-tête). Parité totale.
- **Typographie** : échelle (titre / sous-titre / corps / légende), police avec support **cyrillique**.
- **Espacement** : grille 4/8 px.
- **Composants** : boutons (primaire / secondaire / danger), champs, tableaux zébrés,
  cartes, **pastilles de statut** (badges colorés), onglets, barre de progression, **toasts**.
- **Rayons / élévation** : coins arrondis cohérents, ombres légères.

---

## 5. Refonte écran par écran

- **Onboarding** : assistant en 3 étapes (1 clés → 2 téléphone/code → 3 2FA), lien d'aide,
  validation en direct, messages d'erreur clairs.
- **Groupes** : champ + **puces** des groupes enregistrés, progression, **cartes de groupe**
  avec badge de statut d'accès ; tableau membres avec **recherche/tri**, colonne `join_date`, export.
- **Analyse** : deux panneaux nets (un seul groupe / plusieurs) avec **compteurs** et recherche.
- **Nettoyage (retrait)** : sélecteur de mode en **segmented control** ; chaque mode = un formulaire
  focalisé ; réglages de lot repliables ; **confirmation forte** ; progression avec états flood/lot.
- **Vérification** : saisie + résultats en **pastilles colorées** (trouvé/introuvable), export.
- **Historique** : tableau **filtrable**, vider/exporter.
- **Paramètres** : comptes protégés, bots, langue, clés d'accès.

---

## 6. Interaction & feedback

- **Toasts** (succès/erreur) au lieu du label en bas.
- **États vides** avec conseils (« Aucun groupe — collez un lien pour commencer »).
- **États de chargement** visibles ; l'UI reste réactive (qasync déjà en place).
- **Confirmations** pour tout ce qui est irréversible (déjà partiel — à généraliser).

---

## 7. Approche technique (PySide6, sans casser l'existant)

- `ui/theme.py` : tokens + génération QSS (clair/sombre), 1 point d'application global.
- `ui/widgets/` : composants stylés réutilisables (Button, Card, Badge, Toast).
- `QStackedWidget` + sidebar à la place du scroll+tabs.
- **MVC respecté** : changements **UI uniquement**, `core/` intact → aucun test métier cassé.
- Icônes (SVG/emoji embarqués) + **icône d'application** dédiée.

---

## 8. Roadmap par phases (1 branche + 1 PR par phase)

| Phase | Contenu | Gain | Risque |
|---|---|---|---|
| **0 — Fondations** | `theme.py` + QSS globale + **mode sombre** | Uplift visuel immédiat, peu de refonte | Faible |
| **1 — Navigation/IA** | Sidebar + pages empilées, config → Paramètres | Clarté, moins de scroll | Moyen |
| **2 — Composants** | Boutons, tableaux, pastilles, toasts, états vides | Cohérence, feedback | Faible |
| **3 — Écrans clés** | Onboarding, Nettoyage, Groupes redessinés | Flux plus sûrs et lisibles | Moyen |
| **4 — Finitions** | Icônes, icône d'app, clavier, contraste, docs | Qualité perçue, accessibilité | Faible |

Recommandation : **commencer par la Phase 0** (impact maximal, risque minimal) puis Phase 2,
avant la refonte structurelle (Phase 1/3).

---

## 9. Critères de succès

- Moins de clics/scroll pour les tâches clés.
- Action principale évidente sur chaque écran.
- Composants cohérents ; parité clair/sombre.
- **Aucune régression** fonctionnelle (les 96 tests restent verts).
- Lisibilité maintenue en FR / EN / RU.
