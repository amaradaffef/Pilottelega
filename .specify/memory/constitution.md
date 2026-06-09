<!--
SYNC IMPACT REPORT
==================
Version change: (template) → 1.0.0
Bump rationale: Première ratification de la constitution (initialisation depuis le template).

Principes définis (5):
  I.   Open Source & Gratuit (MIT)
  II.  Conformité, accès légitime & confidentialité
  III. UI réactive non bloquante
  IV.  Simplicité MVP-first (YAGNI)
  V.   Qualité & testabilité

Sections ajoutées:
  - Contraintes techniques (stack figée)
  - Workflow de développement (Spec Kit + jalons)
  - Governance

Templates à vérifier:
  ✅ .specify/templates/plan-template.md   (Constitution Check générique, compatible)
  ✅ .specify/templates/spec-template.md   (compatible)
  ✅ .specify/templates/tasks-template.md  (compatible)

Suivi / TODO: aucun. Date de ratification = aujourd'hui (premier projet).
-->

# Pilottelega Constitution

Pilottelega est une application **desktop Windows** qui récupère les membres des
groupes Telegram accessibles à l'utilisateur et analyse leurs recoupements entre
plusieurs groupes. Cette constitution fixe les règles non négociables du projet.

## Core Principles

### I. Open Source & Gratuit (MIT)

Le projet EST et RESTE public et gratuit. Le code est distribué sous licence
**MIT** ; un fichier `LICENSE` MIT MUST être présent à la racine. Aucune
fonctionnalité ne peut être mise derrière un paywall et aucune dépendance à
licence non libre/incompatible MIT ne peut être introduite sans justification
explicite. Rationale : l'utilisateur veut un outil libre, réutilisable et
auditable par tous.

### II. Conformité, accès légitime & confidentialité

L'application n'analyse QUE ce que le compte connecté peut **légitimement** lire
sur Telegram. Elle MUST afficher le **statut d'accès par groupe** (liste
complète / admin requis / membres masqués) plutôt que de tenter de contourner
une restriction. Les identifiants API (`api_id`, `api_hash`), le numéro et la
session sont saisis par l'utilisateur et stockés **uniquement en local** (type
`AppData`) — JAMAIS embarqués dans l'`.exe`, JAMAIS transmis à un tiers. Base
RGPD : gestion et analyse de ses propres communautés, pas de réutilisation pour
de la prospection non sollicitée. Rationale : respecter les CGU de Telegram, le
RGPD et la vie privée des membres est une condition d'existence du projet.

### III. UI réactive non bloquante

Tout appel réseau (connexion, envoi de code, fetch des membres) MUST être
asynchrone et passer par le pont **qasync** : l'interface ne gèle JAMAIS pendant
une attente réseau. Le câblage qasync MUST être en place dès le premier appel
réseau (onboarding). Rationale : c'est le seul point technique non trivial du
MVP et la principale source de bugs d'expérience utilisateur.

### IV. Simplicité MVP-first (YAGNI)

Le MVP traite les données **en mémoire**, sans base de données. Les éléments
hors-périmètre — persistance SQLite, segmentation par activité (`last_seen`),
re-fetch planifié, graphiques, multi-comptes, chiffrement du stockage — MUST
rester hors du MVP tant qu'ils ne sont pas explicitement priorisés. Toute
complexité ajoutée MUST être justifiée par un besoin réel et actuel. Rationale :
livrer vite une application fonctionnelle et testable prime sur l'exhaustivité.

### V. Qualité & testabilité

La logique métier (normalisation des liens, construction de la correspondance
`user_id → groupes`, calcul des uniques vs multi-groupes) MUST être isolée de
l'UI et couverte par des tests automatisés. L'application MUST rester lançable et
testable via `python` directement à chaque jalon, avant tout packaging. Rationale :
la valeur du produit est dans la justesse de l'analyse de recoupement ; elle doit
être vérifiable sans cliquer dans l'interface.

## Contraintes techniques (stack figée)

Les choix suivants sont figés pour le MVP et ne changent pas sans amendement :

| Couche | Choix |
| --- | --- |
| UI | **PySide6** (`QTabWidget`, tables performantes) |
| API Telegram | **Telethon** |
| Pont async | **qasync** (asyncio dans la boucle Qt) |
| Stockage | **En mémoire** (données) + fichiers locaux `AppData` (config/session) |
| Identifiants | **Saisis par l'utilisateur** au premier lancement |
| Packaging | **PyInstaller** → `.exe` autonome Windows |

Cible : **Windows**. Python 3.x.

## Workflow de développement

Le projet suit le workflow **Spec Kit** dans l'ordre, sans sauter d'étape :
`constitution → specify → clarify → plan → tasks → analyze → checklist →
(taskstoissues) → implement`. Aucune implémentation ne démarre avant la
validation de `constitution → specify → plan → tasks`.

Livraison par jalons (la logique d'abord, l'emballage ensuite) :

1. Onboarding API & connexion (code + 2FA, session sauvegardée)
2. Écran principal & saisie des liens (1 par ligne, normalisation)
3. Fetch + un onglet par groupe avec statut d'accès
4. Vue Analyse (uniques vs multi-groupes) — le cœur
5. Packaging Windows (`.exe` via PyInstaller)

Les jalons 1→4 livrent l'app fonctionnelle, testable via `python`. Le jalon 5
n'est que la distribution.

## Governance

Cette constitution prévaut sur toutes les autres pratiques du projet. Tout
amendement MUST être documenté dans ce fichier (Sync Impact Report) et versionné
selon le semantic versioning :

- **MAJOR** : suppression/redéfinition incompatible d'un principe ou d'une règle
  de gouvernance.
- **MINOR** : ajout d'un principe/section ou extension matérielle d'une règle.
- **PATCH** : clarifications, reformulations, corrections non sémantiques.

Toute revue de plan, de tâches et de code MUST vérifier la conformité aux
principes ci-dessus ; toute dérogation (notamment à II. Conformité et III. UI non
bloquante) MUST être justifiée explicitement et, à défaut, refusée.

**Version**: 1.0.0 | **Ratified**: 2026-06-09 | **Last Amended**: 2026-06-09
