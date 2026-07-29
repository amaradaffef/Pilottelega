"""Normalisation des liens de groupes Telegram (logique pure, testable).

Accepte ``@nom``, ``t.me/nom``, ``https://t.me/nom``, liens d'invitation (``t.me/+hash``,
``joinchat/hash``) et identifiants numériques. Les entrées invalides sont signalées sans
interrompre le lot (FR-006/007/015).
"""

from __future__ import annotations

import re

_URL_PREFIXES = (
    "https://t.me/",
    "http://t.me/",
    "https://telegram.me/",
    "http://telegram.me/",
    "t.me/",
    "telegram.me/",
)

_USERNAME_RE = re.compile(r"[A-Za-z0-9_]{3,32}")


def normalize_link(raw: str) -> str | None:
    """Convertit une saisie en identifiant exploitable, ou ``None`` si invalide.

    Retourne ``@nom`` pour un username, l'identifiant numérique tel quel, ou le jeton
    d'invitation (``+hash`` / ``joinchat/hash``).
    """
    s = raw.strip()
    if not s:
        return None

    low = s.lower()
    for prefix in _URL_PREFIXES:
        if low.startswith(prefix):
            s = s[len(prefix) :]
            break
    s = s.strip("/")
    if not s:
        return None

    # Liens d'invitation : conservés tels quels.
    if s.startswith("+") or s.lower().startswith("joinchat/"):
        return s

    if s.startswith("@"):
        s = s[1:]

    # Identifiant numérique (éventuellement négatif pour les supergroupes).
    if s.lstrip("-").isdigit():
        return s

    # Username Telegram (3 à 32 caractères alphanumériques/underscore).
    if _USERNAME_RE.fullmatch(s):
        return f"@{s}"

    return None


def entity_ref(identifier: str) -> str | int:
    """Convertit un identifiant en référence acceptée par Telethon.

    Un identifiant **numérique** doit être passé en ``int`` : sous forme de chaîne, Telethon
    le prendrait pour un numéro de téléphone et échouerait à trouver le groupe. C'est le cas
    des groupes **privés** (sans ``@pseudo``), identifiés uniquement par leur ID.
    """
    s = identifier.strip()
    if s.lstrip("-").isdigit():
        return int(s)
    return s


def invite_hash(identifier: str) -> str | None:
    """Extrait le jeton d'un lien d'invitation privé, ou ``None`` si ce n'en est pas un.

    Accepte ``+hash``, ``joinchat/hash`` et leurs formes complètes (``https://t.me/+hash``).
    """
    s = identifier.strip()
    low = s.lower()
    for prefix in _URL_PREFIXES:
        if low.startswith(prefix):
            s = s[len(prefix) :]
            break
    s = s.strip("/")
    if s.startswith("+"):
        return s[1:] or None
    if s.lower().startswith("joinchat/"):
        return s[len("joinchat/") :] or None
    return None


def parse_links(text: str) -> tuple[list[str], list[str]]:
    """Découpe un bloc multi-lignes (1 lien/ligne).

    Retourne ``(identifiants_valides_dédupliqués, lignes_invalides)``. Les lignes vides
    sont ignorées ; les doublons sont supprimés en préservant l'ordre (FR-015).
    """
    valid: list[str] = []
    invalid: list[str] = []
    seen: set[str] = set()

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        normalized = normalize_link(stripped)
        if normalized is None:
            invalid.append(stripped)
        elif normalized not in seen:
            seen.add(normalized)
            valid.append(normalized)

    return valid, invalid
