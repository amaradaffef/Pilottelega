<!-- SPECKIT START -->
Active feature: **001-members-overlap**.
For technologies, project structure, and design details, read the current plan:
`specs/001-members-overlap/plan.md` (+ research.md, data-model.md, contracts/, quickstart.md).

Stack (figée) : Python 3.11+, PySide6 (UI), Telethon (API Telegram), qasync (pont async),
données en mémoire, PyInstaller pour l'`.exe`. Structure MVC : `core/` (logique pure testable),
`ui/` (PySide6), `app/` (config/bootstrap qasync).
<!-- SPECKIT END -->

## Projet : Pilottelega

- **Type** : application **desktop en Python**.
- **Dépôt** : https://github.com/amaradaffef/Pilottelega.git (`origin`).
- **Licence / philosophie** : projet **public et gratuit** (open source). Toujours
  inclure une licence libre (ex. MIT) et garder le code ouvert.

## Méthode de travail — respecter les étapes (Spec Kit)

Pour CE projet **et tous les futurs projets**, suivre le workflow Spec Kit dans
l'ordre, sans sauter d'étape :

1. `/speckit.constitution` — principes du projet
2. `/speckit.specify` — spécification fonctionnelle
3. `/speckit.clarify` — lever les ambiguïtés de la spec
4. `/speckit.plan` — plan technique et architecture
5. `/speckit.tasks` — découpage en tâches
6. `/speckit.analyze` — cohérence spec / plan / tasks
7. `/speckit.checklist` — checklist qualité
8. `/speckit.taskstoissues` — créer les issues GitHub (optionnel)
9. `/speckit.implement` — implémentation

Ne pas commencer à coder avant d'avoir validé constitution → specify → plan → tasks.

## Automatisation Git — OBLIGATOIRE (ce projet + futurs projets)

Tout doit être automatisé, sans demander confirmation à chaque fois :

- **Worktree isolé** : chaque session/action de travail se fait dans un **git
  worktree isolé** (`.claude/worktrees/...`) pour que des sessions parallèles ne
  cassent pas le travail en cours. Utiliser l'outil EnterWorktree au début d'une
  action, ExitWorktree à la fin.
- **Une branche par action** : chaque action (chaque étape Spec Kit, chaque
  changement) vit sur sa **propre branche de feature**, jamais directement sur
  `main`.
- **PR par action** : chaque action doit produire **une Pull Request** dédiée.
- **Commit + push + merge automatiques** : à la fin de chaque action, exécuter
  automatiquement le cycle commit → push → création de PR → **merge** (squash).
  Utiliser le helper `.specify/scripts/powershell/auto-pr.ps1 -Message "..."`
  (ou son équivalent bash) qui fait tout le cycle, puis revenir sur `main` à jour.
- Ne pas demander la permission pour commit/push/PR/merge : c'est le mode par
  défaut voulu par l'utilisateur.

## Standards de code et qualité — OBLIGATOIRE

**Style & formatage**
- Respecter **PEP 8**. Formater automatiquement avec **Black**.
- **Type hints** partout (fonctions, méthodes, signatures publiques).
- Analyse statique avec **Ruff** (lint) ; corriger les avertissements avant commit.

**Tests & fiabilité**
- Tests unitaires avec **pytest** ; la logique métier (normalisation, recoupement)
  doit être couverte.
- **CI GitHub Actions** : un workflow lance Ruff + Black --check + pytest à chaque
  push / PR. Le merge auto ne passe que si la CI est verte.

**Modularité & documentation**
- Séparer les responsabilités : modules dédiés, pattern type **MVC** (UI / logique /
  données distinctes). Ne pas tout mettre dans un seul fichier.
- **Docstrings** sur fonctions et classes. Documentation générable (MkDocs/Sphinx).

**Sécurité & configuration**
- **Jamais** de secret/clé en dur. En développement : variables d'environnement via
  **python-dotenv** (`.env` ignoré par git). En distribution (`.exe`) : identifiants
  saisis par l'utilisateur à l'onboarding, stockés en local (cf. constitution §II).
- Utiliser le module **`logging`** (pas `print()`) pour tracer événements et erreurs.
