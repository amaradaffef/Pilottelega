"""Tests du thème (génération QSS) et de la préférence de mode sombre."""

from __future__ import annotations

from pilottelega.app import preferences
from pilottelega.ui import theme


def test_build_qss_uses_theme_colors():
    light = theme.build_qss(dark=False)
    dark = theme.build_qss(dark=True)
    # La QSS contient bien la couleur primaire de chaque thème.
    assert theme.LIGHT["primary"] in light
    assert theme.DARK["primary"] in dark
    # Les deux thèmes produisent des feuilles différentes.
    assert light != dark
    # Sélecteurs clés présents (boutons accentués).
    assert "QPushButton#primary" in light
    assert "QPushButton#danger" in light


def test_dark_mode_preference_roundtrip(tmp_path, monkeypatch):
    from pilottelega.app import paths

    monkeypatch.setattr(paths, "app_data_dir", lambda: tmp_path)
    assert preferences.load_dark_mode() is False  # défaut
    preferences.save_dark_mode(True)
    assert preferences.load_dark_mode() is True
