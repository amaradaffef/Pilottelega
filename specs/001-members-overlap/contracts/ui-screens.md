# Contract: Écrans UI (ui/, PySide6)

La couche UI (View+Controller) consomme `core/` via qasync. Elle ne contient **aucune** logique
de recoupement ni d'accès réseau direct.

## Onboarding (ui/onboarding.py) — affiché si `is_authorized()` est faux (FR-001/005)

- **Affiche** : explication « identifiant d'accès personnel gratuit requis » + **lien cliquable**
  vers la page officielle de génération.
- **Saisie** : `api_id`, `api_hash`, `phone` → enchaîne `start_login` → champ `code` →
  (si `PASSWORD_REQUIRED`) champ mot de passe 2FA.
- **Succès** : session sauvegardée localement, bascule vers la fenêtre principale.
- **Erreur** : message clair, saisie corrigeable, pas de plantage (FR-017).
- **Contrat de réactivité** : chaque appel réseau est `await`-é via qasync ; indicateur de
  progression pendant l'attente (Principe III).

## Fenêtre principale (ui/main_window.py) — FR-006

- **Saisie** : zone de texte multi-lignes (1 lien/ligne) + bouton « Récupérer ».
- **Action** : `parse_links` → pour chaque identifiant valide, `await fetch_group` → crée un
  onglet de groupe. Les lignes invalides sont signalées sans bloquer.
- **Contient** : un `QTabWidget` regroupant les onglets de groupe + l'onglet Analyse.
- **Réactivité** : barre/indicateur de progression pendant les fetch (SC-005).

## Onglet de groupe (ui/group_tab.py) — FR-009/010

- **Affiche** : table des membres (`@username` ou repli) + **badge de statut d'accès**
  (FULL / PARTIAL_HIDDEN / ADMIN_REQUIRED / ERROR avec message).
- **Source** : un `TargetGroup` renvoyé par `fetch_group`.

## Onglet Analyse (ui/analysis_tab.py) — FR-013/014

- **Recalcule** : appelle `compute_overlap(groups)` sur les groupes récupérés.
- **Vue 1** : table « membres présents dans un seul groupe » (+ nom du groupe).
- **Vue 2** : table « membres présents dans plusieurs groupes » avec, pour chacun, la liste
  des `@groupes` où il apparaît aussi.
- **Mise à jour** : se rafraîchit quand de nouveaux groupes sont récupérés.

## Garanties transverses

- Aucune opération réseau ne gèle l'UI (qasync, Principe III).
- L'UI n'accède jamais directement à Telethon : tout passe par `core/`.
- Aucun secret affiché/loggé ; `logging` (pas `print`) pour les événements/erreurs.
