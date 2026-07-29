"""Tests unitaires de la normalisation des liens (T016 / US2). Aucune dépendance externe."""

from __future__ import annotations

import pytest

from pilottelega.core.link_parser import entity_ref, invite_hash, normalize_link, parse_links


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("@groupe_test", "@groupe_test"),
        ("groupe_test", "@groupe_test"),
        ("t.me/groupe_test", "@groupe_test"),
        ("https://t.me/groupe_test", "@groupe_test"),
        ("HTTPS://T.ME/groupe_test", "@groupe_test"),
        ("  @groupe_test  ", "@groupe_test"),
        ("-1001234567890", "-1001234567890"),
        ("t.me/+AbCdEf123", "+AbCdEf123"),
        ("https://t.me/joinchat/AbCdEf", "joinchat/AbCdEf"),
    ],
)
def test_normalize_link_valid(raw, expected):
    assert normalize_link(raw) == expected


@pytest.mark.parametrize("raw", ["", "   ", "ab", "@@@", "espace interdit", "no!chars"])
def test_normalize_link_invalid(raw):
    assert normalize_link(raw) is None


def test_parse_links_dedup_and_invalid():
    text = "\n".join(
        [
            "@alpha",
            "t.me/alpha",  # doublon de @alpha
            "",  # ignoré
            "  ",  # ignoré
            "bravo",
            "ligne invalide !!!",
        ]
    )
    valid, invalid = parse_links(text)
    assert valid == ["@alpha", "@bravo"]
    assert invalid == ["ligne invalide !!!"]


@pytest.mark.parametrize(
    "identifier,expected",
    [
        # Les groupes privés sont désignés par leur ID : il doit rester un entier, sinon
        # Telethon le prendrait pour un numéro de téléphone.
        ("-1001234567890", -1001234567890),
        ("1234567890", 1234567890),
        ("  -100123  ", -100123),
        ("@public", "@public"),
        ("+AbCdEf", "+AbCdEf"),
    ],
)
def test_entity_ref(identifier, expected):
    assert entity_ref(identifier) == expected


@pytest.mark.parametrize(
    "identifier,expected",
    [
        ("+AbCdEf123", "AbCdEf123"),
        ("joinchat/AbCdEf", "AbCdEf"),
        ("https://t.me/+AbCdEf123", "AbCdEf123"),
        ("t.me/joinchat/AbCdEf", "AbCdEf"),
        ("@public", None),
        ("-1001234567890", None),
        ("+", None),
    ],
)
def test_invite_hash(identifier, expected):
    assert invite_hash(identifier) == expected


def test_parse_links_preserves_order():
    valid, invalid = parse_links("charlie\nbravo\nalpha")
    assert valid == ["@charlie", "@bravo", "@alpha"]
    assert invalid == []
