"""Enhance page with grammar, readability, and summarization controls."""

import logging
from typing import Optional

try:
    from PySide6.QtCore import Qt, Signal, QObject, QRunnable, QThreadPool
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
        QTabWidget, QFrame, QComboBox, QSpinBox, QCheckBox,
        QDoubleSpinBox, QGroupBox, QFormLayout, QScrollArea,
        QSizePolicy,
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

        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)
        self._corrections_card = StatusCard("Corrections", "--")
        self._categories_card = StatusCard("Categories", "--")
        stats_row.addWidget(self._corrections_card)
        stats_row.addWidget(self._categories_card)
        stats_row.addStretch()
        layout.addLayout(stats_row)

        layout.addWidget(QLabel("Individual corrections:"))

        self._details_text = QTextEdit()
        self._details_text.setReadOnly(True)
        self._details_text.setPlaceholderText(
            "Grammar correction details will appear here after processing..."
        )
        layout.addWidget(self._details_text, stretch=1)

    def set_results(self, document: Document) -> None:
        state = document.processing_state
        grammar_data = state.stage_results.get("grammar", {})
        count = grammar_data.get("corrections", 0)
        categories = grammar_data.get("categories", {})
        details = grammar_data.get("correction_details", [])

        self._corrections_card.set_value(str(count))
        self._categories_card.set_value(str(len(categories)))

        if not details and count == 0:
            self._details_text.setPlainText("No grammar issues found.")
            return

        html_parts = []
        for i, d in enumerate(details, 1):
            orig = _escape_html(d.get("original", ""))
            fixed = _escape_html(d.get("corrected", ""))
            msg = _escape_html(d.get("message", ""))
            cat = _escape_html(d.get("category", "Other"))
            ctx = _escape_html(d.get("context", ""))

            html_parts.append(
                f"<div style='margin-bottom:12px; padding:8px; "
                f"border-left:3px solid #7c6ff0; background:rgba(124,111,240,0.06); "
                f"border-radius:4px;'>"
                f"<b style='color:#a0a0b8;'>#{i}</b> "
                f"<span style='color:#a0a0b8; font-size:11px;'>[{cat}]</span><br>"
                f"<span style='color:#e05555; text-decoration:line-through;'>{orig}</span>"
                f" &rarr; "
                f"<span style='color:#4caf7a; font-weight:bold;'>{fixed}</span><br>"
                f"<span style='color:#b0b0c0; font-size:11px;'>{msg}</span>"
                f"</div>"
            )

        if categories:
            cat_summary = " &nbsp;|&nbsp; ".join(
                f"<b>{_escape_html(k)}</b>: {v}" for k, v in categories.items()
            )
            html_parts.insert(
                0,
                f"<div style='margin-bottom:14px; padding:6px; "
                f"color:#b0b0c0; font-size:11px;'>"
                f"Category breakdown: {cat_summary}</div>",
            )

        self._details_text.setHtml("".join(html_parts))

    def clear(self) -> None:
        self._details_text.clear()
        self._corrections_card.set_value("--")
        self._categories_card.set_value("--")


class ReadabilityTab(QWidget):
    """Readability scoring and optimization display."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        layout.addWidget(QLabel("Readability analysis and optimization results:"))

        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)
        self._flesch_card = StatusCard("Flesch Score", "--")
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
        stats_row.setSpacing(12)
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
            summ_errors = [
                e for e in state.errors if e.get("stage") == "summarization"
            ]
            if summ_errors:
                self._summary_text.setPlainText(
                    f"Summarization failed: {summ_errors[-1].get('error', 'Unknown error')}"
                )
            else:
                self._summary_text.setPlainText("No summary available.")

    def clear(self) -> None:
        self._method_card.set_value("--")
        self._ratio_card.set_value("--")
        self._summary_text.clear()


class _ResummarizeSignals(QObject):
    finished = Signal(object)
    error = Signal(str)


class _ResummarizeWorker(QRunnable):
    """Lightweight worker that re-runs only the summarization stage."""

    def __init__(self, text: str, method: str, sentence_count: int):
        super().__init__()
        self.signals = _ResummarizeSignals()
        self.text = text
        self.method = method
        self.sentence_count = sentence_count
        self.setAutoDelete(True)

    def run(self) -> None:
        try:
            from app.core.summarizer import Summarizer
            summarizer = Summarizer()
            result = summarizer.summarize(
                self.text,
                method=self.method,
                sentence_count=self.sentence_count,
            )
            self.signals.finished.emit(result)
        except Exception as exc:
            self.signals.error.emit(str(exc))


class EnhancePage(QWidget):
    """Tabbed page for grammar, readability, and summarization results."""

    run_enhancement = Signal(object)  # PipelineConfig

    def __init__(self, parent=None):
        super().__init__(parent)
        self._document: Optional[Document] = None
        self._resummarize_worker: Optional[_ResummarizeWorker] = None
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
        group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        form = QFormLayout(group)
        form.setContentsMargins(16, 10, 16, 12)
        form.setHorizontalSpacing(20)
        form.setVerticalSpacing(12)
        form.setFieldGrowthPolicy(QFormLayout.FieldsStayAtSizeHint)

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
        self._summary_method.setMinimumWidth(180)
        self._summary_method.setMaximumWidth(250)
        self._summary_method.setFixedHeight(36)
        form.addRow("Summary Method:", self._summary_method)

        self._summary_sentences = QSpinBox()
        self._summary_sentences.setRange(1, 20)
        self._summary_sentences.setValue(5)
        self._summary_sentences.setMinimumWidth(80)
        self._summary_sentences.setMaximumWidth(120)
        self._summary_sentences.setFixedHeight(36)
        form.addRow("Summary Sentences:", self._summary_sentences)

        self._chk_plagiarism = QCheckBox()
        self._chk_plagiarism.setChecked(True)
        form.addRow("Enable Plagiarism Check:", self._chk_plagiarism)

        self._chk_paraphrasing = QCheckBox()
        self._chk_paraphrasing.setChecked(True)
        form.addRow("Enable Paraphrasing:", self._chk_paraphrasing)

        self._summary_method.currentTextChanged.connect(
            self._on_summary_config_changed,
        )
        self._summary_sentences.valueChanged.connect(
            self._on_summary_config_changed,
        )

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

    # ── Live re-summarization ─────────────────────────────────────────

    def _on_summary_config_changed(self) -> None:
        """Re-run summarization when the user changes method or sentence count."""
        if not self._document:
            return
        text = self._document.enhanced_text or self._document.raw_text
        if not text:
            return
        self._re_summarize(text)

    def _re_summarize(self, text: str) -> None:
        method = self._summary_method.currentText()
        sentence_count = self._summary_sentences.value()

        self._summarization_tab._method_card.set_value("...")
        self._summarization_tab._ratio_card.set_value("...")
        self._summarization_tab._summary_text.setPlainText(
            "Re-summarizing with method: " + method + "..."
        )

        worker = _ResummarizeWorker(text, method, sentence_count)
        worker.signals.finished.connect(self._on_resummarize_finished)
        worker.signals.error.connect(self._on_resummarize_error)
        self._resummarize_worker = worker
        QThreadPool.globalInstance().start(worker)

    def _on_resummarize_finished(self, result) -> None:
        if not self._document:
            return
        self._document.set_summary(result.summary)
        self._document.processing_state.stage_results["summarization"] = {
            "method": result.method,
            "compression_ratio": result.compression_ratio,
        }
        self._summarization_tab.set_results(self._document)

    def _on_resummarize_error(self, error_msg: str) -> None:
        self._summarization_tab._method_card.set_value("--")
        self._summarization_tab._ratio_card.set_value("--")
        self._summarization_tab._summary_text.setPlainText(
            f"Summarization failed: {error_msg}"
        )


def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."


def _escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
