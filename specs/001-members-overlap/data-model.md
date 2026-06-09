# Phase 1 — Data Model: Pilottelega

Modèle **en mémoire** (aucune persistance des membres — Principe IV). Les entités vivent
dans `core/models.py` sous forme de `dataclass`, sans dépendance Qt (Principe V).

## Enum: AccessStatus

État de lecture d'un groupe (FR-010).

| Valeur | Signification |
|---|---|
| `FULL` | Liste complète des membres lue |
| `PARTIAL_HIDDEN` | Membres masqués → liste partielle (éventuellement vide) |
| `ADMIN_REQUIRED` | Droits administrateur requis pour lister |
| `ERROR` | Échec (réseau, entrée invalide, session expirée…) — message conservé |

## Entity: Member

Une personne appartenant à un ou plusieurs groupes.

| Champ | Type | Règles |
|---|---|---|
| `user_id` | `int` | **Clé stable** d'identité inter-groupes (FR-012). Obligatoire, immuable. |
| `username` | `str \| None` | `@handle` sans le `@`. Optionnel. |
| `display_name` | `str` | Libellé de repli (prénom/nom ou `id`) pour l'affichage. |

- **Égalité / hash** : basés sur `user_id` uniquement (déduplication inter-groupes).
- **Affichage** : `@username` si présent, sinon `display_name`, sinon `str(user_id)`.

## Entity: TargetGroup

Un groupe à analyser (FR-006 à FR-010).

| Champ | Type | Règles |
|---|---|---|
| `raw_input` | `str` | Saisie originale (avant normalisation). |
| `identifier` | `str` | Cible normalisée (`@nom`, id, invite) issue de `link_parser`. |
| `title` | `str \| None` | Nom du groupe résolu après fetch. |
| `handle` | `str \| None` | `@handle` du groupe (pour l'affichage « @groupes » en Analyse). |
| `access_status` | `AccessStatus` | Statut de lecture (défaut `ERROR` tant que non récupéré). |
| `members` | `list[Member]` | Membres récupérés (vide si non lisible). |
| `error_message` | `str \| None` | Détail si `access_status == ERROR`. |

- **Déduplication** : deux `TargetGroup` de même `identifier` sont fusionnés (FR-015).
- **Label d'affichage** : `handle` (`@...`) si présent, sinon `title`, sinon `identifier`.

## Entity: Account / Session

Lien authentifié avec le compte Telegram (FR-001 à FR-005). N'est pas en mémoire seule :
config + session persistées **localement** (`%APPDATA%/Pilottelega/`).

| Champ | Type | Règles |
|---|---|---|
| `api_id` | `int` | Identifiant d'accès personnel. Saisi par l'utilisateur. Local uniquement. |
| `api_hash` | `str` | Hash d'accès personnel. Local uniquement. Jamais embarqué/transmis. |
| `phone` | `str` | Numéro de téléphone (login). |
| `session_path` | `str` | Chemin du fichier session Telethon sous `%APPDATA%`. |
| `is_connected` | `bool` | État de connexion courant (runtime). |

- **Cycle de vie** : voir transitions ci-dessous.
- **Sécurité** : `api_hash` et `.session` ne quittent jamais le poste (FR-004, SC-006).

## Entity: AnalysisResult

Résultat du croisement (FR-013/014). Dérivé, recalculé à la demande.

| Champ | Type | Règles |
|---|---|---|
| `membership` | `dict[int, set[str]]` | `user_id` → ensemble des labels de groupes le contenant. |
| `single_group` | `list[(Member, str)]` | Membres présents dans **un seul** groupe (+ le groupe). |
| `multi_group` | `list[(Member, list[str])]` | Membres présents dans **plusieurs** groupes (+ liste `@groupes`). |

- **Construction** : un seul passage sur tous les `TargetGroup.members` pour bâtir `membership`,
  puis partition selon `len(groupes) == 1` vs `> 1` (research D5, FR-013/014).
- **Cas limites** : 0/1 groupe → `multi_group` vide ; même groupe en double déjà fusionné amont.

## State transitions — Session (FR-005)

```text
[Démarrage]
   │  session locale valide ?
   ├── oui ──► CONNECTED ──► (écran principal)
   └── non ──► ONBOARDING
                 │ saisie api_id/api_hash/phone
                 ▼
              CODE_SENT ── saisie code ──► (2FA activée ?)
                                              ├── oui ► PASSWORD_REQUIRED ─ saisie mdp ─►┐
                                              └── non ─────────────────────────────────►┤
                                                                                         ▼
                                                                                     CONNECTED
                                                                                  (session sauvegardée localement)
   Échec à toute étape ──► ERROR (message clair, retour à la saisie) — FR-017
   Session expirée/révoquée détectée ──► ONBOARDING — edge case
```

## State transitions — TargetGroup (fetch)

```text
PENDING ─ fetch ─► FULL | PARTIAL_HIDDEN | ADMIN_REQUIRED | ERROR
```

Le fetch d'un groupe est indépendant : l'échec de l'un (ERROR) n'interrompt pas les autres
(FR-007/017).
