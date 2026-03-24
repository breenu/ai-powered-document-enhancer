"""Settings page for API keys, model preferences, and Tesseract path config."""

import logging
from typing import Optional

try:
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
        QComboBox, QGroupBox, QFormLayout, QFileDialog, QMessageBox,
        QCheckBox, QDoubleSpinBox, QSpinBox, QScrollArea, QFrame,
    )
except ImportError:
    pass

from app.ui.widgets import SectionHeader, StyledButton
from app.database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)


class SettingsPage(QWidget):
    """Configuration panel for Tesseract, OCR, models, and preferences."""

    settings_changed = Signal()

    def __init__(self, db_manager: Optional[DatabaseManager] = None,
                 parent=None):
        super().__init__(parent)
        self._db = db_manager
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self) -> None:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        main_layout = QVBoxLayout(content)
        main_layout.setContentsMargins(32, 24, 32, 24)
        main_layout.setSpacing(16)

        main_layout.addWidget(SectionHeader("Settings"))

        main_layout.addWidget(self._build_ocr_group())
        main_layout.addWidget(self._build_pipeline_group())
        main_layout.addWidget(self._build_export_group())
        main_layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        reset_btn = StyledButton("Reset to Defaults", variant="secondary")
        reset_btn.clicked.connect(self._reset_defaults)
        btn_row.addWidget(reset_btn)

        save_btn = StyledButton("Save Settings")
        save_btn.setMinimumHeight(40)
        save_btn.clicked.connect(self._save_settings)
        btn_row.addWidget(save_btn)

        main_layout.addLayout(btn_row)

        scroll.setWidget(content)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _build_ocr_group(self) -> QGroupBox:
        group = QGroupBox("OCR Configuration")
        form = QFormLayout(group)

        path_row = QHBoxLayout()
        self._tesseract_path = QLineEdit()
        self._tesseract_path.setPlaceholderText(
            "Leave empty for system default (tesseract on PATH)"
        )
        path_row.addWidget(self._tesseract_path)

        browse_btn = StyledButton("Browse", variant="secondary")
        browse_btn.clicked.connect(self._browse_tesseract)
        path_row.addWidget(browse_btn)
        form.addRow("Tesseract Path:", path_row)

        self._ocr_language = QComboBox()
        self._ocr_language.addItems([
            "eng", "fra", "deu", "spa", "ita", "por", "hin",
            "chi_sim", "jpn", "kor", "ara",
        ])
        form.addRow("OCR Language:", self._ocr_language)

        self._apply_threshold = QCheckBox("Apply adaptive thresholding")
        form.addRow("Preprocessing:", self._apply_threshold)

        return group

    def _build_pipeline_group(self) -> QGroupBox:
        group = QGroupBox("Pipeline Defaults")
        form = QFormLayout(group)

        self._target_grade = QDoubleSpinBox()
        self._target_grade.setRange(1.0, 20.0)
        self._target_grade.setValue(10.0)
        self._target_grade.setSingleStep(0.5)
        form.addRow("Target Reading Grade:", self._target_grade)

        self._similarity_threshold = QDoubleSpinBox()
        self._similarity_threshold.setRange(0.0, 1.0)
        self._similarity_threshold.setValue(0.7)
        self._similarity_threshold.setSingleStep(0.05)
        self._similarity_threshold.setDecimals(2)
        form.addRow("Plagiarism Threshold:", self._similarity_threshold)

        self._paraphrase_count = QSpinBox()
        self._paraphrase_count.setRange(1, 10)
        self._paraphrase_count.setValue(3)
        form.addRow("Paraphrase Suggestions:", self._paraphrase_count)

        self._summary_method = QComboBox()
        self._summary_method.addItems(["extractive", "abstractive"])
        form.addRow("Default Summary Method:", self._summary_method)

        self._summary_sentences = QSpinBox()
        self._summary_sentences.setRange(1, 20)
        self._summary_sentences.setValue(5)
        form.addRow("Default Summary Length:", self._summary_sentences)

        return group

    def _build_export_group(self) -> QGroupBox:
        group = QGroupBox("Export Preferences")
        form = QFormLayout(group)

        self._pdf_font = QComboBox()
        self._pdf_font.addItems(["Helvetica", "Courier", "Times"])
        form.addRow("PDF Font:", self._pdf_font)

        self._pdf_font_size = QSpinBox()
        self._pdf_font_size.setRange(8, 24)
        self._pdf_font_size.setValue(12)
        form.addRow("PDF Font Size:", self._pdf_font_size)

        return group

    def _browse_tesseract(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Tesseract Executable", "",
            "Executable (*.exe);;All Files (*)",
        )
        if path:
            self._tesseract_path.setText(path)

    def _load_settings(self) -> None:
        if not self._db:
            return
        try:
            settings = self._db.get_settings_by_category("ocr")
            settings.update(self._db.get_settings_by_category("pipeline"))
            settings.update(self._db.get_settings_by_category("export"))

            if "tesseract_path" in settings:
                self._tesseract_path.setText(str(settings["tesseract_path"]))
            if "ocr_language" in settings:
                idx = self._ocr_language.findText(str(settings["ocr_language"]))
                if idx >= 0:
                    self._ocr_language.setCurrentIndex(idx)
            if "apply_threshold" in settings:
                self._apply_threshold.setChecked(bool(settings["apply_threshold"]))
            if "target_grade" in settings:
                self._target_grade.setValue(float(settings["target_grade"]))
            if "similarity_threshold" in settings:
                self._similarity_threshold.setValue(
                    float(settings["similarity_threshold"])
                )
            if "paraphrase_count" in settings:
                self._paraphrase_count.setValue(int(settings["paraphrase_count"]))
            if "summary_method" in settings:
                idx = self._summary_method.findText(str(settings["summary_method"]))
                if idx >= 0:
                    self._summary_method.setCurrentIndex(idx)
            if "summary_sentences" in settings:
                self._summary_sentences.setValue(int(settings["summary_sentences"]))
            if "pdf_font" in settings:
                idx = self._pdf_font.findText(str(settings["pdf_font"]))
                if idx >= 0:
                    self._pdf_font.setCurrentIndex(idx)
            if "pdf_font_size" in settings:
                self._pdf_font_size.setValue(int(settings["pdf_font_size"]))
        except Exception as e:
            logger.warning("Failed to load settings: %s", e)

    def _save_settings(self) -> None:
        if not self._db:
            QMessageBox.information(
                self, "Settings", "Settings saved locally (no database).",
            )
            self.settings_changed.emit()
            return
        try:
            self._db.set_setting(
                "tesseract_path", self._tesseract_path.text(), "ocr",
            )
            self._db.set_setting(
                "ocr_language", self._ocr_language.currentText(), "ocr",
            )
            self._db.set_setting(
                "apply_threshold", self._apply_threshold.isChecked(), "ocr",
            )
            self._db.set_setting(
                "target_grade", self._target_grade.value(), "pipeline",
            )
            self._db.set_setting(
                "similarity_threshold",
                self._similarity_threshold.value(), "pipeline",
            )
            self._db.set_setting(
                "paraphrase_count", self._paraphrase_count.value(), "pipeline",
            )
            self._db.set_setting(
                "summary_method", self._summary_method.currentText(), "pipeline",
            )
            self._db.set_setting(
                "summary_sentences", self._summary_sentences.value(), "pipeline",
            )
            self._db.set_setting(
                "pdf_font", self._pdf_font.currentText(), "export",
            )
            self._db.set_setting(
                "pdf_font_size", self._pdf_font_size.value(), "export",
            )

            QMessageBox.information(self, "Settings", "Settings saved successfully.")
            self.settings_changed.emit()
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to save settings: {e}",
            )

    def _reset_defaults(self) -> None:
        self._tesseract_path.clear()
        self._ocr_language.setCurrentIndex(0)
        self._apply_threshold.setChecked(False)
        self._target_grade.setValue(10.0)
        self._similarity_threshold.setValue(0.7)
        self._paraphrase_count.setValue(3)
        self._summary_method.setCurrentIndex(0)
        self._summary_sentences.setValue(5)
        self._pdf_font.setCurrentIndex(0)
        self._pdf_font_size.setValue(12)

    def get_pipeline_config(self) -> dict:
        """Return current settings as a dict suitable for PipelineConfig."""
        return {
            "tesseract_path": self._tesseract_path.text() or None,
            "ocr_language": self._ocr_language.currentText(),
            "apply_threshold": self._apply_threshold.isChecked(),
            "target_readability_grade": self._target_grade.value(),
            "similarity_threshold": self._similarity_threshold.value(),
            "num_paraphrase_suggestions": self._paraphrase_count.value(),
            "summarization_method": self._summary_method.currentText(),
            "summary_sentences": self._summary_sentences.value(),
        }
