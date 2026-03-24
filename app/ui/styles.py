"""QSS dark and light theme stylesheets for the application."""

COLORS_DARK = {
    "bg_primary": "#1e1e2e",
    "bg_secondary": "#2a2a3c",
    "bg_tertiary": "#333348",
    "surface": "#3a3a50",
    "border": "#4a4a60",
    "text_primary": "#e0e0e8",
    "text_secondary": "#a0a0b8",
    "text_muted": "#707088",
    "accent": "#7c6ff0",
    "accent_hover": "#9488f5",
    "accent_pressed": "#6558d0",
    "success": "#4caf7a",
    "warning": "#e8a838",
    "error": "#e05555",
    "sidebar_bg": "#181828",
    "sidebar_active": "#7c6ff0",
    "sidebar_hover": "#2a2a40",
    "input_bg": "#2a2a3c",
    "scrollbar_bg": "#2a2a3c",
    "scrollbar_handle": "#4a4a60",
}

COLORS_LIGHT = {
    "bg_primary": "#f5f5fa",
    "bg_secondary": "#ffffff",
    "bg_tertiary": "#eeeef5",
    "surface": "#ffffff",
    "border": "#d0d0dc",
    "text_primary": "#2a2a3c",
    "text_secondary": "#5a5a70",
    "text_muted": "#8888a0",
    "accent": "#6c5ce7",
    "accent_hover": "#8070f0",
    "accent_pressed": "#5a4ad0",
    "success": "#27ae60",
    "warning": "#e67e22",
    "error": "#e74c3c",
    "sidebar_bg": "#e8e8f0",
    "sidebar_active": "#6c5ce7",
    "sidebar_hover": "#d8d8e8",
    "input_bg": "#ffffff",
    "scrollbar_bg": "#eeeef5",
    "scrollbar_handle": "#c0c0d0",
}


def _build_stylesheet(c: dict) -> str:
    """Generate a complete QSS stylesheet from a colour palette dictionary."""
    return f"""
/* ── Global ── */
QWidget {{
    background-color: {c['bg_primary']};
    color: {c['text_primary']};
    font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
}}

/* ── Main Window ── */
QMainWindow {{
    background-color: {c['bg_primary']};
}}

/* ── Sidebar ── */
QWidget#sidebar {{
    background-color: {c['sidebar_bg']};
    border-right: 1px solid {c['border']};
}}

QWidget#sidebar QPushButton {{
    background-color: transparent;
    color: {c['text_secondary']};
    border: none;
    border-radius: 6px;
    padding: 10px 16px;
    text-align: left;
    font-size: 13px;
    font-weight: 500;
}}

QWidget#sidebar QPushButton:hover {{
    background-color: {c['sidebar_hover']};
    color: {c['text_primary']};
}}

QWidget#sidebar QPushButton[active="true"] {{
    background-color: {c['sidebar_active']};
    color: #ffffff;
    font-weight: 600;
}}

/* ── Labels ── */
QLabel {{
    background-color: transparent;
    color: {c['text_primary']};
}}

QLabel#pageTitle {{
    font-size: 22px;
    font-weight: 700;
    padding: 4px 0;
}}

QLabel#subtitle {{
    font-size: 14px;
    color: {c['text_secondary']};
}}

/* ── Push Buttons ── */
QPushButton {{
    background-color: {c['accent']};
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px 20px;
    font-size: 13px;
    font-weight: 600;
    min-height: 28px;
}}

QPushButton:hover {{
    background-color: {c['accent_hover']};
}}

QPushButton:pressed {{
    background-color: {c['accent_pressed']};
}}

QPushButton:disabled {{
    background-color: {c['surface']};
    color: {c['text_muted']};
}}

QPushButton#secondaryButton {{
    background-color: {c['bg_tertiary']};
    color: {c['text_primary']};
    border: 1px solid {c['border']};
}}

QPushButton#secondaryButton:hover {{
    background-color: {c['surface']};
}}

QPushButton#dangerButton {{
    background-color: {c['error']};
}}

QPushButton#dangerButton:hover {{
    background-color: {c['error']};
    opacity: 0.85;
}}

/* ── Line Edits / Text Edits ── */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {c['input_bg']};
    color: {c['text_primary']};
    border: 1px solid {c['border']};
    border-radius: 6px;
    padding: 6px 10px;
    selection-background-color: {c['accent']};
    selection-color: #ffffff;
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border: 1px solid {c['accent']};
}}

/* ── Combo Box ── */
QComboBox {{
    background-color: {c['input_bg']};
    color: {c['text_primary']};
    border: 1px solid {c['border']};
    border-radius: 6px;
    padding: 6px 10px;
    min-height: 24px;
}}

QComboBox:hover {{
    border: 1px solid {c['accent']};
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

QComboBox QAbstractItemView {{
    background-color: {c['bg_secondary']};
    color: {c['text_primary']};
    border: 1px solid {c['border']};
    selection-background-color: {c['accent']};
    selection-color: #ffffff;
}}

/* ── Progress Bar ── */
QProgressBar {{
    background-color: {c['bg_tertiary']};
    border: none;
    border-radius: 4px;
    text-align: center;
    color: {c['text_secondary']};
    min-height: 18px;
    font-size: 11px;
}}

QProgressBar::chunk {{
    background-color: {c['accent']};
    border-radius: 4px;
}}

/* ── Table Widget ── */
QTableWidget {{
    background-color: {c['bg_secondary']};
    alternate-background-color: {c['bg_tertiary']};
    color: {c['text_primary']};
    gridline-color: {c['border']};
    border: 1px solid {c['border']};
    border-radius: 6px;
    selection-background-color: {c['accent']};
    selection-color: #ffffff;
}}

QHeaderView::section {{
    background-color: {c['surface']};
    color: {c['text_primary']};
    border: none;
    border-bottom: 1px solid {c['border']};
    padding: 6px 8px;
    font-weight: 600;
}}

/* ── Scroll Bars ── */
QScrollBar:vertical {{
    background-color: {c['scrollbar_bg']};
    width: 10px;
    border-radius: 5px;
}}

QScrollBar::handle:vertical {{
    background-color: {c['scrollbar_handle']};
    border-radius: 5px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {c['accent']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar:horizontal {{
    background-color: {c['scrollbar_bg']};
    height: 10px;
    border-radius: 5px;
}}

QScrollBar::handle:horizontal {{
    background-color: {c['scrollbar_handle']};
    border-radius: 5px;
    min-width: 30px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {c['accent']};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

/* ── Status Bar ── */
QStatusBar {{
    background-color: {c['bg_secondary']};
    color: {c['text_secondary']};
    border-top: 1px solid {c['border']};
    font-size: 12px;
    padding: 2px 8px;
}}

/* ── Tab Widget ── */
QTabWidget::pane {{
    background-color: {c['bg_secondary']};
    border: 1px solid {c['border']};
    border-radius: 6px;
}}

QTabBar::tab {{
    background-color: {c['bg_tertiary']};
    color: {c['text_secondary']};
    border: none;
    padding: 8px 16px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}}

QTabBar::tab:selected {{
    background-color: {c['accent']};
    color: #ffffff;
    font-weight: 600;
}}

QTabBar::tab:hover:!selected {{
    background-color: {c['surface']};
    color: {c['text_primary']};
}}

/* ── Tooltips ── */
QToolTip {{
    background-color: {c['surface']};
    color: {c['text_primary']};
    border: 1px solid {c['border']};
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 12px;
}}

/* ── Group Box ── */
QGroupBox {{
    background-color: {c['bg_secondary']};
    border: 1px solid {c['border']};
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 20px;
    font-weight: 600;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    padding: 2px 10px;
    color: {c['text_primary']};
}}

/* ── Splitter ── */
QSplitter::handle {{
    background-color: {c['border']};
}}

/* ── Message Box ── */
QMessageBox {{
    background-color: {c['bg_secondary']};
}}
"""


DARK_THEME = _build_stylesheet(COLORS_DARK)
LIGHT_THEME = _build_stylesheet(COLORS_LIGHT)

THEMES = {
    "dark": DARK_THEME,
    "light": LIGHT_THEME,
}


def get_theme(name: str = "dark") -> str:
    """Return the QSS stylesheet for the given theme name."""
    return THEMES.get(name, DARK_THEME)
