"""Thème global de Pilottelega (Phase 0 du design) : design tokens + feuille QSS.

Style « moderne épuré » : bleu distinct, neutres, coins arrondis, thème clair **et** sombre.
On génère une feuille de style Qt (QSS) à partir des jetons et on l'applique à toute
l'application. Aucune logique métier ici (UI pure).
"""

from __future__ import annotations

from typing import Any

# ----- Design tokens (palette clair / sombre) --------------------------------------------

LIGHT: dict[str, str] = {
    "bg": "#f5f7fa",
    "surface": "#ffffff",
    "surface_alt": "#f0f2f6",
    "border": "#e1e5ea",
    "text": "#1a1d24",
    "text_muted": "#5b6472",
    "primary": "#2f6fed",
    "primary_hover": "#275fd0",
    "primary_text": "#ffffff",
    "danger": "#c62828",
    "danger_hover": "#a91f1f",
    "success": "#2e7d32",
    "selection": "#dbe6ff",
}

DARK: dict[str, str] = {
    "bg": "#16181d",
    "surface": "#1e2128",
    "surface_alt": "#242832",
    "border": "#2c313b",
    "text": "#e7e9ee",
    "text_muted": "#9aa3b2",
    "primary": "#4f9cff",
    "primary_hover": "#3d86e6",
    "primary_text": "#0f1115",
    "danger": "#ef5350",
    "danger_hover": "#e53935",
    "success": "#66bb6a",
    "selection": "#2b3a57",
}

RADIUS = "8px"


def palette(dark: bool) -> dict[str, str]:
    """Retourne la palette de jetons pour le thème demandé."""
    return DARK if dark else LIGHT


def build_qss(dark: bool) -> str:
    """Construit la feuille de style Qt complète à partir des jetons du thème."""
    c = palette(dark)
    return f"""
    * {{
        font-family: "Segoe UI", "Noto Sans", Arial, sans-serif;
        font-size: 13px;
        color: {c["text"]};
    }}
    QMainWindow, QDialog, QScrollArea, QWidget#central {{ background: {c["bg"]}; }}
    QWidget {{ background: transparent; }}
    QLabel {{ background: transparent; color: {c["text"]}; }}

    /* Barre de menu */
    QMenuBar {{ background: {c["surface"]}; border-bottom: 1px solid {c["border"]}; }}
    QMenuBar::item {{ padding: 6px 12px; background: transparent; }}
    QMenuBar::item:selected {{ background: {c["surface_alt"]}; border-radius: 6px; }}
    QMenu {{ background: {c["surface"]}; border: 1px solid {c["border"]}; padding: 4px; }}
    QMenu::item {{ padding: 6px 20px; border-radius: 6px; }}
    QMenu::item:selected {{ background: {c["primary"]}; color: {c["primary_text"]}; }}

    /* Champs de saisie */
    QLineEdit, QPlainTextEdit, QComboBox, QSpinBox {{
        background: {c["surface"]};
        border: 1px solid {c["border"]};
        border-radius: {RADIUS};
        padding: 6px 8px;
        selection-background-color: {c["primary"]};
        selection-color: {c["primary_text"]};
    }}
    QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus, QSpinBox:focus {{
        border: 1px solid {c["primary"]};
    }}
    QComboBox::drop-down {{ border: none; width: 22px; }}
    QComboBox QAbstractItemView {{
        background: {c["surface"]};
        border: 1px solid {c["border"]};
        selection-background-color: {c["primary"]};
        selection-color: {c["primary_text"]};
        outline: none;
    }}

    /* Boutons : neutre par défaut, accent via objectName */
    QPushButton {{
        background: {c["surface"]};
        color: {c["text"]};
        border: 1px solid {c["border"]};
        border-radius: {RADIUS};
        padding: 7px 14px;
    }}
    QPushButton:hover {{ background: {c["surface_alt"]}; }}
    QPushButton:disabled {{ color: {c["text_muted"]}; background: {c["surface_alt"]}; }}
    QPushButton#primary {{ background: {c["primary"]}; color: {c["primary_text"]}; border: none; }}
    QPushButton#primary:hover {{ background: {c["primary_hover"]}; }}
    QPushButton#primary:disabled {{ background: {c["surface_alt"]}; color: {c["text_muted"]}; }}
    QPushButton#danger {{ background: {c["danger"]}; color: #ffffff; border: none; }}
    QPushButton#danger:hover {{ background: {c["danger_hover"]}; }}
    QPushButton#danger:disabled {{ background: {c["surface_alt"]}; color: {c["text_muted"]}; }}

    QCheckBox {{ spacing: 8px; background: transparent; }}
    QCheckBox::indicator {{ width: 16px; height: 16px; }}

    /* Onglets */
    QTabWidget::pane {{ border: 1px solid {c["border"]}; border-radius: {RADIUS}; top: -1px; }}
    QTabBar::tab {{
        background: transparent;
        color: {c["text_muted"]};
        padding: 8px 14px;
        border: none;
        border-bottom: 2px solid transparent;
    }}
    QTabBar::tab:hover {{ color: {c["text"]}; }}
    QTabBar::tab:selected {{ color: {c["primary"]}; border-bottom: 2px solid {c["primary"]}; }}

    /* Listes et tables */
    QListWidget, QTableWidget, QTableView {{
        background: {c["surface"]};
        border: 1px solid {c["border"]};
        border-radius: {RADIUS};
        alternate-background-color: {c["surface_alt"]};
        gridline-color: {c["border"]};
        outline: none;
    }}
    QListWidget::item, QTableView::item {{ padding: 3px; }}
    QListWidget::item:selected, QTableView::item:selected {{
        background: {c["selection"]}; color: {c["text"]};
    }}
    QHeaderView::section {{
        background: {c["surface_alt"]};
        color: {c["text_muted"]};
        padding: 6px 8px;
        border: none;
        border-bottom: 1px solid {c["border"]};
        font-weight: bold;
    }}
    QTableCornerButton::section {{ background: {c["surface_alt"]}; border: none; }}

    /* Progression */
    QProgressBar {{
        background: {c["surface_alt"]};
        border: 1px solid {c["border"]};
        border-radius: {RADIUS};
        height: 18px;
        text-align: center;
        color: {c["text"]};
    }}
    QProgressBar::chunk {{ background: {c["primary"]}; border-radius: {RADIUS}; }}

    /* Barres de défilement discrètes */
    QScrollBar:vertical {{ background: transparent; width: 12px; margin: 2px; }}
    QScrollBar::handle:vertical {{
        background: {c["border"]}; border-radius: 6px; min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{ background: {c["text_muted"]}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollBar:horizontal {{ background: transparent; height: 12px; margin: 2px; }}
    QScrollBar::handle:horizontal {{
        background: {c["border"]}; border-radius: 6px; min-width: 30px;
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
    """


def apply_theme(app: Any, dark: bool) -> None:
    """Applique la feuille de style du thème à toute l'application."""
    app.setStyleSheet(build_qss(dark))
