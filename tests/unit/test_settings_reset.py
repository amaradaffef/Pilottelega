"""Test du nettoyage des clés d'accès et de la session (reset_credentials)."""

from __future__ import annotations

from pilottelega.app import paths, settings


def test_reset_credentials_deletes_config_and_session_only(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "app_data_dir", lambda: tmp_path)
    (tmp_path / "config.json").write_text("{}", encoding="utf-8")
    (tmp_path / "pilottelega.session").write_text("x", encoding="utf-8")
    (tmp_path / "pilottelega.session-journal").write_text("x", encoding="utf-8")
    (tmp_path / "prefs.json").write_text("{}", encoding="utf-8")
    (tmp_path / "history.json").write_text("[]", encoding="utf-8")

    settings.reset_credentials()

    # Clés + session (et annexes) effacées…
    assert not (tmp_path / "config.json").exists()
    assert not (tmp_path / "pilottelega.session").exists()
    assert not (tmp_path / "pilottelega.session-journal").exists()
    # …mais les préférences et l'historique sont conservés.
    assert (tmp_path / "prefs.json").exists()
    assert (tmp_path / "history.json").exists()


def test_reset_credentials_no_error_when_absent(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "app_data_dir", lambda: tmp_path)
    settings.reset_credentials()  # ne doit pas lever même si rien à supprimer
