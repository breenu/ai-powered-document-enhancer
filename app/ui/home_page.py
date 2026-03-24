"""Home / dashboard page for the AI Document Enhancement System."""

try:
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QFrame, QSizePolicy, QScrollArea, QGridLayout,
    )
except ImportError:
    pass

from app.ui.widgets import StyledButton

_FEATURES = [
    ("\U0001F50D", "OCR Engine",
     "Extract text from images and scanned documents with high accuracy",
     "#7c6ff0"),
    ("\u2713", "Grammar Check",
     "Automatic grammar and spelling correction powered by AI",
     "#4caf7a"),
    ("Aa", "Readability",
     "Flesch\u2013Kincaid scoring and text simplification tools",
     "#e8a838"),
    ("\u03A3", "Summarization",
     "Extractive and abstractive text summaries at any length",
     "#5bc0de"),
    ("\u229E", "Plagiarism",
     "Local TF-IDF similarity checking across documents",
     "#e05555"),
    ("\u2197", "Export",
     "DOCX and PDF export with professional formatting",
     "#9b59b6"),
]


class HomePage(QWidget):
    """Welcome dashboard with quick-start actions and feature overview."""

    navigate_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(40, 32, 40, 32)
        layout.setSpacing(28)

        layout.addWidget(self._build_hero())
        layout.addWidget(self._build_features())
        layout.addStretch()

        scroll.setWidget(content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _build_hero(self) -> QWidget:
        card = QFrame()
        card.setObjectName("heroCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(40, 36, 40, 36)
        layout.setSpacing(12)

        badge = QLabel("\u2726  DocEnhance AI")
        badge.setObjectName("heroBadge")
        badge_row = QHBoxLayout()
        badge_row.addWidget(badge)
        badge_row.addStretch()
        layout.addLayout(badge_row)

        title = QLabel("AI Document Enhancement System")
        title.setObjectName("heroTitle")
        layout.addWidget(title)

        subtitle = QLabel(
            "Upload scanned documents or images, extract text with OCR, "
            "and enhance them with grammar correction, readability "
            "optimization, summarization, and more."
        )
        subtitle.setObjectName("heroSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        layout.addSpacing(8)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        upload_btn = StyledButton("Upload Document")
        upload_btn.setMinimumHeight(44)
        upload_btn.setMinimumWidth(180)
        upload_btn.clicked.connect(
            lambda: self.navigate_requested.emit("upload"),
        )
        btn_row.addWidget(upload_btn)

        settings_btn = StyledButton("Settings", variant="secondary")
        settings_btn.setMinimumHeight(44)
        settings_btn.setMinimumWidth(120)
        settings_btn.clicked.connect(
            lambda: self.navigate_requested.emit("settings"),
        )
        btn_row.addWidget(settings_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        return card

    def _build_features(self) -> QWidget:
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        v_layout = QVBoxLayout(container)
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(16)

        header = QLabel("Features")
        header.setObjectName("sectionTitle")
        v_layout.addWidget(header)

        grid = QGridLayout()
        grid.setSpacing(16)

        for idx, (icon, title, desc, color) in enumerate(_FEATURES):
            card = self._feature_card(icon, title, desc, color)
            row, col = divmod(idx, 3)
            grid.addWidget(card, row, col)

        v_layout.addLayout(grid)
        return container

    @staticmethod
    def _feature_card(icon_text: str, title: str, description: str,
                      accent: str) -> QFrame:
        card = QFrame()
        card.setObjectName("featureCard")
        card.setMinimumHeight(150)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)

        icon_label = QLabel(icon_text)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setFixedSize(42, 42)
        icon_label.setStyleSheet(
            f"background-color: {accent}; color: #ffffff; "
            f"border-radius: 21px; font-size: 18px; font-weight: 700;"
        )

        icon_row = QHBoxLayout()
        icon_row.addWidget(icon_label)
        icon_row.addStretch()
        layout.addLayout(icon_row)

        lbl_title = QLabel(title)
        lbl_title.setObjectName("featureTitle")
        layout.addWidget(lbl_title)

        lbl_desc = QLabel(description)
        lbl_desc.setObjectName("featureDesc")
        lbl_desc.setWordWrap(True)
        layout.addWidget(lbl_desc)

        layout.addStretch()
        return card
