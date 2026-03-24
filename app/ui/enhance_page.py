"""Enhance page with grammar, readability, and summarization controls."""

import logging
from typing import Optional

try:
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
        QTabWidget, QFrame, QComboBox, QSpinBox, QCheckBox,
        QDoubleSpinBox, QGroupBox, QFormLayout, QScrollArea,
    )
except ImportError:
    pass

from app.ui.widgets import SectionHeader, StatusCard, StyledButton
from app.models.document import Document
from app.core.pipeline import PipelineConfig

logger = logging.getLogger(__name__)


class GrammarTab(QWidget):
    """Grammar enhancement controls and results display."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        layout.addWidget(QLabel("Grammar corrections applied during processing:"))

        self._results_text = QTextEdit()
        self._results_text.setReadOnly(True)
        self._results_text.setPlaceholderText(
            "Grammar correction results will appear here after processing..."
        )
        layout.addWidget(self._results_text)

        stats_row = QHBoxLayout()
        self._corrections_card = StatusCard("Corrections", "--")
        stats_row.addWidget(self._corrections_card)
        stats_row.addStretch()
        layout.addLayout(stats_row)

    def set_results(self, document: Document) -> None:
        state = document.processing_state
        grammar_data = state.stage_results.get("grammar", {})
        corrections = grammar_data.get("corrections", 0)
        self._corrections_card.set_value(str(corrections))

        if document.enhanced_text and document.raw_text:
            self._results_text.setHtml(
                f"<b>Original text preview:</b><br>"
                f"<pre style='color:#e05555'>{_truncate(document.raw_text, 500)}</pre>"
                f"<br><b>Enhanced text preview:</b><br>"
                f"<pre style='color:#4caf7a'>{_truncate(document.enhanced_text, 500)}</pre>"
            )
        elif corrections == 0:
            self._results_text.setPlainText("No grammar issues found.")

    def clear(self) -> None:
        self._results_text.clear()
        self._corrections_card.set_value("--")


class ReadabilityTab(QWidget):
    """Readability scoring and optimization display."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        layout.addWidget(QLabel("Readability analysis and optimization results:"))

        stats_row = QHBoxLayout()
        self._flesch_card = StatusCard("Flesch Reading Ease", "--")
        self._grade_card = StatusCard("Grade Level", "--")
        self._changes_card = StatusCard("Simplifications", "--")
        stats_row.addWidget(self._flesch_card)
        stats_row.addWidget(self._grade_card)
        stats_row.addWidget(self._changes_card)
        stats_row.addStretch()
        layout.addLayout(stats_row)

        self._details_text = QTextEdit()
        self._details_text.setReadOnly(True)
        self._details_text.setPlaceholderText(
            "Readability details will appear here..."
        )
        layout.addWidget(self._details_text)

    def set_results(self, document: Document) -> None:
        state = document.processing_state
        readability_data = state.stage_results.get("readability", {})
        grade = readability_data.get("flesch_kincaid_grade", "--")
        changes = readability_data.get("changes", "--")

        self._flesch_card.set_value(f"{document.readability_score:.1f}")
        self._grade_card.set_value(str(grade))
        self._changes_card.set_value(str(changes))

        level = "Easy" if document.readability_score >= 60 else (
            "Moderate" if document.readability_score >= 30 else "Difficult"
        )
        self._details_text.setPlainText(
            f"Readability Level: {level}\n"
            f"Flesch Reading Ease: {document.readability_score:.1f}/100\n"
            f"Flesch-Kincaid Grade: {grade}\n"
            f"Simplifications applied: {changes}"
        )

    def clear(self) -> None:
        self._flesch_card.set_value("--")
        self._grade_card.set_value("--")
        self._changes_card.set_value("--")
        self._details_text.clear()


class SummarizationTab(QWidget):
    """Summary display with method and length info."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        layout.addWidget(QLabel("Document summary:"))

        stats_row = QHBoxLayout()
        self._method_card = StatusCard("Method", "--")
        self._ratio_card = StatusCard("Compression", "--")
        stats_row.addWidget(self._method_card)
        stats_row.addWidget(self._ratio_card)
        stats_row.addStretch()
        layout.addLayout(stats_row)

        self._summary_text = QTextEdit()
        self._summary_text.setReadOnly(True)
        self._summary_text.setPlaceholderText(
            "Summary will appear here after processing..."
        )
        layout.addWidget(self._summary_text)

    def set_results(self, document: Document) -> None:
        state = document.processing_state
        summ_data = state.stage_results.get("summarization", {})
        method = summ_data.get("method", "--")
        ratio = summ_data.get("compression_ratio", 0)

        self._method_card.set_value(str(method).capitalize())
        self._ratio_card.set_value(f"{ratio:.1%}" if isinstance(ratio, float) else "--")

        if document.summary_text:
            self._summary_text.setPlainText(document.summary_text)
        else:
            self._summary_text.setPlainText("No summary available.")

    def clear(self) -> None:
        self._method_card.set_value("--")
        self._ratio_card.set_value("--")
        self._summary_text.clear()


class EnhancePage(QWidget):
    """Tabbed page for grammar, readability, and summarization results."""

    run_enhancement = Signal(object)  # PipelineConfig

    def __init__(self, parent=None):
        super().__init__(parent)
        self._document: Optional[Document] = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(12)

        top_row = QHBoxLayout()
        top_row.addWidget(SectionHeader("Enhancement Results"))
        top_row.addStretch()
        layout.addLayout(top_row)

        config_group = self._build_config_panel()
        layout.addWidget(config_group)

        self._tabs = QTabWidget()
        self._grammar_tab = GrammarTab()
        self._readability_tab = ReadabilityTab()
        self._summarization_tab = SummarizationTab()
        self._tabs.addTab(self._grammar_tab, "Grammar")
        self._tabs.addTab(self._readability_tab, "Readability")
        self._tabs.addTab(self._summarization_tab, "Summarization")
        layout.addWidget(self._tabs, stretch=1)

    def _build_config_panel(self) -> QGroupBox:
        group = QGroupBox("Pipeline Configuration")
        form = QFormLayout(group)

        self._chk_grammar = QCheckBox()
        self._chk_grammar.setChecked(True)
        form.addRow("Enable Grammar:", self._chk_grammar)

        self._chk_readability = QCheckBox()
        self._chk_readability.setChecked(True)
        form.addRow("Enable Readability:", self._chk_readability)

        self._chk_summarization = QCheckBox()
        self._chk_summarization.setChecked(True)
        form.addRow("Enable Summarization:", self._chk_summarization)

        self._summary_method = QComboBox()
        self._summary_method.addItems(["extractive", "abstractive"])
        form.addRow("Summary Method:", self._summary_method)

        self._summary_sentences = QSpinBox()
        self._summary_sentences.setRange(1, 20)
        self._summary_sentences.setValue(5)
        form.addRow("Summary Sentences:", self._summary_sentences)

        self._chk_plagiarism = QCheckBox()
        self._chk_plagiarism.setChecked(True)
        form.addRow("Enable Plagiarism Check:", self._chk_plagiarism)

        self._chk_paraphrasing = QCheckBox()
        self._chk_paraphrasing.setChecked(True)
        form.addRow("Enable Paraphrasing:", self._chk_paraphrasing)

        return group

    def get_pipeline_config(self) -> PipelineConfig:
        return PipelineConfig(
            enable_grammar=self._chk_grammar.isChecked(),
            enable_readability=self._chk_readability.isChecked(),
            enable_summarization=self._chk_summarization.isChecked(),
            enable_plagiarism=self._chk_plagiarism.isChecked(),
            enable_paraphrasing=self._chk_paraphrasing.isChecked(),
            summarization_method=self._summary_method.currentText(),
            summary_sentences=self._summary_sentences.value(),
        )

    def set_document(self, document: Document) -> None:
        self._document = document
        self._grammar_tab.set_results(document)
        self._readability_tab.set_results(document)
        self._summarization_tab.set_results(document)

    def clear(self) -> None:
        self._document = None
        self._grammar_tab.clear()
        self._readability_tab.clear()
        self._summarization_tab.clear()


def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."
