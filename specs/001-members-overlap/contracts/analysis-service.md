# Contract: Analyse & parsing (core/analysis.py, core/link_parser.py)

Logique métier **pure** (aucun réseau, aucun Qt) — cœur testable du produit (Principe V).

## link_parser.py

```text
def normalize_link(raw: str) -> str | None
    # Convertit une saisie en identifiant normalisé.
    # Accepte: "@nom", "https://t.me/nom", "t.me/nom", "t.me/+invite", id numérique.
    # Retourne None si l'entrée est invalide (FR-007).

def parse_links(text: str) -> tuple[list[str], list[str]]
    # Découpe un bloc multi-lignes (1 lien/ligne).
    # Retourne (identifiants_valides_dédupliqués, lignes_invalides).
    # Ignore les lignes vides, strip les espaces, déduplique (FR-006/015).
```

**Règles**
- Déduplication des identifiants identiques (FR-015).
- Les entrées invalides sont **collectées**, pas levées en exception (le lot continue).

## analysis.py

```text
def compute_overlap(groups: list[TargetGroup]) -> AnalysisResult
    # Construit membership: user_id -> set(labels de groupes) en un seul passage.
    # single_group  = membres dont len(groupes) == 1   (FR-013)
    # multi_group   = membres dont len(groupes) > 1, avec la liste des @groupes (FR-014)
```

**Règles**
- Le « label de groupe » affiché est le `@handle` si présent, sinon le titre, sinon l'identifiant.
- Un membre est identifié par `user_id` (research D5) ; un même `user_id` présent dans deux
  groupes compte comme un recoupement.
- Cas limites : 0 ou 1 groupe → `multi_group` vide, tous les membres en `single_group`
  (edge cases spec). Groupes en double déjà fusionnés en amont.

## Tests (unit, sans réseau ni Qt)

- `normalize_link` : chaque forme acceptée → identifiant attendu ; formes invalides → None.
- `parse_links` : déduplication, lignes vides ignorées, invalides collectées.
- `compute_overlap` :
  - membre commun à 2 groupes → présent dans `multi_group` avec la bonne liste de groupes ;
  - membre exclusif → `single_group` ;
  - aucun commun → `multi_group` vide ;
  - 1 seul groupe → tous en `single_group`.
