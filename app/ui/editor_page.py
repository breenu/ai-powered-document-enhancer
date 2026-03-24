"""Editor page for manual text correction with low-confidence highlighting."""

import logging
from typing import Optional

try:
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtGui import QTextCharFormat, QColor, QFont, QSyntaxHighlighter, QTextDocument
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
        QFrame, QSizePolicy, QPlainTextEdit,
    )
except ImportError:
    pass

from app.ui.widgets import SectionHeader, StatusCard, StyledButton
from app.models.document import Document

logger = logging.getLogger(__name__)


class EditorPage(QWidget):
    """Full-text editor allowing manual correction of OCR output."""

    text_accepted = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._document: Optional[Document] = None
        self._original_text: str = ""
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(12)

        top_row = QHBoxLayout()
        top_row.addWidget(SectionHeader("Text Editor"))
        top_row.addStretch()

        self._conf_label = QLabel("")
        self._conf_label.setObjectName("subtitle")
        top_row.addWidget(self._conf_label)
        layout.addLayout(top_row)

        hint = QLabel(
            "Review the OCR-extracted text below. Words with low confidence "
            "may need manual correction. Edit as needed, then accept."
        )
        hint.setObjectName("subtitle")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self._editor = QPlainTextEdit()
        self._editor.setPlaceholderText("OCR text will appear here for editing...")
        self._editor.setTabStopDistance(32)
        self._editor.textChanged.connect(self._on_text_changed)

        editor_font = QFont("Consolas", 11)
        editor_font.setStyleHint(QFont.Monospace)
        self._editor.setFont(editor_font)
        layout.addWidget(self._editor, stretch=1)

        stats_row = QHBoxLayout()
        self._word_card = StatusCard("Words", "0")
        self._char_card = StatusCard("Characters", "0")
        self._changes_card = StatusCard("Changes", "None")
        stats_row.addWidget(self._word_card)
        stats_row.addWidget(self._char_card)
        stats_row.addWidget(self._changes_card)
        stats_row.addStretch()
        layout.addLayout(stats_row)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        revert_btn = StyledButton("Revert to Original", variant="secondary")
        revert_btn.clicked.connect(self._revert)
        btn_row.addWidget(revert_btn)

        accept_btn = StyledButton("Accept Changes")
        accept_btn.setMinimumHeight(40)
        accept_btn.clicked.connect(self._accept)
        btn_row.addWidget(accept_btn)

        layout.addLayout(btn_row)

    def set_document(self, document: Document) -> None:
        self._document = document
        text = document.raw_text or ""
        self._original_text = text
        self._editor.setPlainText(text)

        if document.ocr_confidence > 0:
            self._conf_label.setText(
                f"OCR Confidence: {document.ocr_confidence:.1f}%"
            )
        self._update_stats()

    def _on_text_changed(self) -> None:
        self._update_stats()

    def _update_stats(self) -> None:
        text = self._editor.toPlainText()
        words = len(text.split()) if text.strip() else 0
        chars = len(text)
        self._word_card.set_value(str(words))
        self._char_card.set_value(str(chars))

        if text != self._original_text:
            orig_words = set(self._original_text.split())
            new_words = set(text.split())
            diff_count = len(orig_words.symmetric_difference(new_words))
            self._changes_card.set_value(f"~{diff_count} words")
        else:
            self._changes_card.set_value("None")

    def _revert(self) -> None:
        self._editor.setPlainText(self._original_text)

    def _accept(self) -> None:
        text = self._editor.toPlainText()
        if self._document:
            self._document.raw_text = text
        self.text_accepted.emit(text)

    def get_text(self) -> str:
        return self._editor.toPlainText()

    def clear(self) -> None:
        self._document = None
        self._original_text = ""
        self._editor.clear()
        self._conf_label.setText("")
        self._word_card.set_value("0")
        self._char_card.set_value("0")
        self._changes_card.set_value("None")
