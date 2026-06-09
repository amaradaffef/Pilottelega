"""Tests unitaires de l'internationalisation (FR/EN/RU)."""

from __future__ import annotations

import pytest

from pilottelega.app import i18n


@pytest.fixture(autouse=True)
def _reset_language():
    """Rétablit la langue par défaut après chaque test."""
    yield
    i18n.set_language(i18n.DEFAULT_LANGUAGE)


def test_default_language_is_french():
    assert i18n.get_language() == "fr"
    assert i18n.tr("main.fetch") == "Récupérer les membres"


def test_switch_to_english():
    i18n.set_language("en")
    assert i18n.tr("main.fetch") == "Fetch members"


def test_switch_to_russian():
    i18n.set_language("ru")
    assert i18n.tr("common.export_excel") == "Экспорт в Excel"


def test_unknown_language_is_ignored():
    i18n.set_language("zz")
    assert i18n.get_language() == "fr"


def test_unknown_key_returns_key():
    assert i18n.tr("does.not.exist") == "does.not.exist"


def test_format_kwargs():
    i18n.set_language("en")
    assert i18n.tr("main.fetching", id="@grp") == "Fetching @grp…"


def test_all_languages_share_the_same_keys():
    fr_keys = set(i18n._TRANSLATIONS["fr"])
    for lang in ("en", "ru"):
        assert set(i18n._TRANSLATIONS[lang]) == fr_keys, f"clés manquantes en {lang}"
