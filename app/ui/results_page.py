"""Results page with final output display and DOCX/PDF export options."""

import logging
import os
from typing import Optional

try:
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
        QFrame, QFileDialog, QMessageBox,
    )
except ImportError:
    pass

from app.ui.widgets import SectionHeader, StatusCard, StyledButton
from app.models.document import Document

logger = logging.getLogger(__name__)


class ResultsPage(QWidget):
    """Final results display with metrics and export actions."""

    export_requested = Signal(str, str)  # format ("docx"/"pdf"), output_path

    def __init__(self, parent=None):
        super().__init__(parent)
        self._document: Optional[Document] = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(12)

        layout.addWidget(SectionHeader("Results"))

        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)
        self._status_card = StatusCard("Status", "--")
        self._confidence_card = StatusCard("OCR Confidence", "--")
        self._readability_card = StatusCard("Readability", "--")
        self._plagiarism_card = StatusCard("Plagiarism", "--")
        self._words_card = StatusCard("Word Count", "--")
        self._type_card = StatusCard("Doc Type", "--")
        stats_row.addWidget(self._status_card)
        stats_row.addWidget(self._confidence_card)
        stats_row.addWidget(self._readability_card)
        stats_row.addWidget(self._plagiarism_card)
        stats_row.addWidget(self._words_card)
        stats_row.addWidget(self._type_card)
        layout.addLayout(stats_row)

        text_label = QLabel("Enhanced Text")
        font = text_label.font()
        font.setBold(True)
        text_label.setFont(font)
        layout.addWidget(text_label)

        self._text_display = QTextEdit()
        self._text_display.setReadOnly(True)
        self._text_display.setPlaceholderText(
            "Enhanced document text will appear here after processing..."
        )
        layout.addWidget(self._text_display, stretch=1)

        summary_label = QLabel("Summary")
        font2 = summary_label.font()
        font2.setBold(True)
        summary_label.setFont(font2)
        layout.addWidget(summary_label)

        self._summary_display = QTextEdit()
        self._summary_display.setReadOnly(True)
        self._summary_display.setMaximumHeight(150)
        self._summary_display.setPlaceholderText("Document summary...")
        layout.addWidget(self._summary_display)

        export_row = QHBoxLayout()
        export_row.addStretch()

        self._docx_btn = StyledButton("Export DOCX")
        self._docx_btn.setMinimumHeight(40)
        self._docx_btn.setEnabled(False)
        self._docx_btn.clicked.connect(lambda: self._export("docx"))
        export_row.addWidget(self._docx_btn)

        self._pdf_btn = StyledButton("Export PDF", variant="secondary")
        self._pdf_btn.setMinimumHeight(40)
        self._pdf_btn.setEnabled(False)
        self._pdf_btn.clicked.connect(lambda: self._export("pdf"))
        export_row.addWidget(self._pdf_btn)

        layout.addLayout(export_row)

    def set_document(self, document: Document) -> None:
        self._document = document

        self._status_card.set_value(document.status.value.replace("_", " ").title())
        self._confidence_card.set_value(f"{document.ocr_confidence:.1f}%")
        self._readability_card.set_value(f"{document.readability_score:.1f}")
        self._plagiarism_card.set_value(f"{document.plagiarism_score:.1f}%")
        self._words_card.set_value(str(document.get_word_count()))
        self._type_card.set_value(
            document.doc_type.value if document.doc_type else "N/A"
        )

        self._text_display.setPlainText(
            document.enhanced_text or document.raw_text
        )
        self._summary_display.setPlainText(
            document.summary_text or "No summary generated."
        )

        has_text = bool(document.enhanced_text or document.raw_text)
        self._docx_btn.setEnabled(has_text)
        self._pdf_btn.setEnabled(has_text)

    def _export(self, fmt: str) -> None:
        if not self._document:
            return

        ext = ".docx" if fmt == "docx" else ".pdf"
        default_name = os.path.splitext(self._document.filename)[0] + f"_enhanced{ext}"

        file_filter = (
            "Word Document (*.docx)" if fmt == "docx" else "PDF Document (*.pdf)"
        )
        path, _ = QFileDialog.getSaveFileName(
            self, f"Export as {fmt.upper()}", default_name, file_filter,
        )
        if path:
            self.export_requested.emit(fmt, path)

    def clear(self) -> None:
        self._document = None
        self._text_display.clear()
        self._summary_display.clear()
        for card in (
            self._status_card, self._confidence_card, self._readability_card,
            self._plagiarism_card, self._words_card, self._type_card,
        ):
            card.set_value("--")
        self._docx_btn.setEnabled(False)
        self._pdf_btn.setEnabled(False)
