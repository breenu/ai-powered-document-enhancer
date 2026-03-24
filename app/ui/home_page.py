"""Home / dashboard page for the AI Document Enhancement System."""

try:
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QFrame, QSizePolicy, QScrollArea,
    )
except ImportError:
    pass

from app.ui.widgets import StatusCard, SectionHeader, StyledButton


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
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(20)

        layout.addWidget(self._build_hero())
        layout.addWidget(self._build_quick_actions())
        layout.addWidget(self._build_features())
        layout.addStretch()

        scroll.setWidget(content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _build_hero(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(8)

        title = QLabel("AI Document Enhancement System")
        title.setObjectName("pageTitle")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel(
            "Upload scanned documents or images, extract text with OCR, "
            "and enhance them with grammar correction, readability "
            "optimization, summarization, and more."
        )
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        return container

    def _build_quick_actions(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(12)

        layout.addWidget(SectionHeader("Quick Actions"))

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        upload_btn = StyledButton("Upload Document")
        upload_btn.setMinimumHeight(44)
        upload_btn.clicked.connect(lambda: self.navigate_requested.emit("upload"))
        btn_row.addWidget(upload_btn)

        settings_btn = StyledButton("Settings", variant="secondary")
        settings_btn.setMinimumHeight(44)
        settings_btn.clicked.connect(lambda: self.navigate_requested.emit("settings"))
        btn_row.addWidget(settings_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        return container

    def _build_features(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(12)

        layout.addWidget(SectionHeader("Features"))

        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)

        features = [
            ("OCR Engine", "Extract text from images\nand scanned documents"),
            ("Grammar Check", "Automatic grammar and\nspelling correction"),
            ("Readability", "Flesch-Kincaid scoring\nand simplification"),
            ("Summarization", "Extractive & abstractive\ntext summaries"),
            ("Plagiarism", "Local TF-IDF similarity\nchecking"),
            ("Export", "DOCX and PDF export\nwith formatting"),
        ]

        for title, desc in features:
            card = self._feature_card(title, desc)
            cards_row.addWidget(card)

        layout.addLayout(cards_row)
        return container

    @staticmethod
    def _feature_card(title: str, description: str) -> QFrame:
        card = QFrame()
        card.setFrameShape(QFrame.StyledPanel)
        card.setObjectName("statusCard")
        card.setStyleSheet("""
            QFrame#statusCard {
                border: 1px solid palette(mid);
                border-radius: 8px;
                padding: 12px;
            }
        """)
        card.setMinimumWidth(150)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        lbl_title = QLabel(title)
        font = lbl_title.font()
        font.setBold(True)
        font.setPointSize(12)
        lbl_title.setFont(font)
        layout.addWidget(lbl_title)

        lbl_desc = QLabel(description)
        lbl_desc.setObjectName("subtitle")
        lbl_desc.setWordWrap(True)
        layout.addWidget(lbl_desc)

        return card
