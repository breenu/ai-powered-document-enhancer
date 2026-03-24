"""Main Window for AI Document Enhancement System (PySide6 Desktop App).

Provides the QMainWindow shell with left sidebar navigation, a QStackedWidget
for page content, a status bar, and QThreadPool for background AI operations.
Wires all UI pages to the core pipeline via signals/slots (Phase 7).
"""

import logging
import os
import sys
from pathlib import Path
from typing import List, Optional

import numpy as np

try:
    from PySide6.QtWidgets import (
        QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QLabel, QStackedWidget, QLineEdit,
        QTextEdit, QFileDialog, QProgressBar, QMessageBox,
        QTableWidget, QTableWidgetItem, QComboBox, QStatusBar,
        QSizePolicy, QFrame, QSpacerItem,
    )
    from PySide6.QtCore import Qt, QThreadPool, Signal, Slot, QSize
    from PySide6.QtGui import QIcon
except ImportError:
    pass


def _resource_dir() -> Path:
    """Resolve the resources/ directory for both dev and PyInstaller builds."""
    if getattr(sys, "_MEIPASS", None):
        return Path(sys._MEIPASS) / "resources"
    return Path(__file__).resolve().parent.parent.parent / "resources"

from app.ui.styles import get_theme, THEMES
from app.ui.widgets import SidebarButton, PipelineProgressBar

from app.ui.home_page import HomePage
from app.ui.upload_page import UploadPage
from app.ui.preview_page import PreviewPage
from app.ui.editor_page import EditorPage
from app.ui.enhance_page import EnhancePage
from app.ui.results_page import ResultsPage
from app.ui.settings_page import SettingsPage
from app.ui.workers import PipelineWorker, ExportWorker, WorkerSignals
from app.core.pipeline import PipelineConfig
from app.models.document import Document, DocumentStatus, PipelineStage

logger = logging.getLogger(__name__)


# ────────────────────────────────────────────────────────────────────
# Existing page widgets (LoginWidget, DashboardWidget) kept for
# backward compatibility and admin-dashboard features.
# ────────────────────────────────────────────────────────────────────

class LoginWidget(QWidget):
    """Login form widget for admin dashboard."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        self.title_label = QLabel("AI Document Enhancer - Login")
        self.title_label.setObjectName("loginTitle")
        layout.addWidget(self.title_label)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setObjectName("usernameInput")
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setObjectName("passwordInput")
        layout.addWidget(self.password_input)

        self.login_button = QPushButton("Login")
        self.login_button.setObjectName("loginButton")
        self.login_button.clicked.connect(self.handle_login)
        layout.addWidget(self.login_button)

        self.error_label = QLabel("")
        self.error_label.setObjectName("errorLabel")
        self.error_label.setStyleSheet("color: red;")
        layout.addWidget(self.error_label)

    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        if not username or not password:
            self.error_label.setText("Please enter both username and password")
            return False
        if len(password) < 6:
            self.error_label.setText("Password must be at least 6 characters")
            return False
        self.error_label.setText("")
        return True


class DashboardWidget(QWidget):
    """Admin dashboard showing orders, documents, and analytics."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        header = QLabel("Admin Dashboard")
        header.setObjectName("dashboardHeader")
        layout.addWidget(header)

        self.order_table = QTableWidget(0, 5)
        self.order_table.setHorizontalHeaderLabels(
            ["Order ID", "User", "Pages", "Total", "Status"]
        )
        self.order_table.setObjectName("orderTable")
        layout.addWidget(self.order_table)

        btn_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setObjectName("refreshBtn")
        self.export_btn = QPushButton("Export Report")
        self.export_btn.setObjectName("exportBtn")
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All", "Pending", "Processing", "Completed"])
        self.filter_combo.setObjectName("filterCombo")
        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addWidget(self.export_btn)
        btn_layout.addWidget(self.filter_combo)
        layout.addLayout(btn_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("progressBar")
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

    def add_order_row(self, order_id, user, pages, total, status):
        row = self.order_table.rowCount()
        self.order_table.insertRow(row)
        self.order_table.setItem(row, 0, QTableWidgetItem(str(order_id)))
        self.order_table.setItem(row, 1, QTableWidgetItem(str(user)))
        self.order_table.setItem(row, 2, QTableWidgetItem(str(pages)))
        self.order_table.setItem(row, 3, QTableWidgetItem(f"\u20b9{total:.2f}"))
        self.order_table.setItem(row, 4, QTableWidgetItem(status))


# ────────────────────────────────────────────────────────────────────
# Sidebar page definitions: (key, display_label)
# ────────────────────────────────────────────────────────────────────

_NAV_PAGES = [
    ("home", "Home"),
    ("upload", "Upload"),
    ("preview", "Preview"),
    ("editor", "Editor"),
    ("enhance", "Enhance"),
    ("results", "Results"),
    ("settings", "Settings"),
]


_STAGE_INDEX_MAP = {
    "preprocessing": 0,
    "ocr": 1,
    "grammar": 2,
    "readability": 3,
    "summarization": 4,
    "formatting": 5,
    "plagiarism_check": 6,
    "paraphrasing": 7,
}


class MainWindow(QMainWindow):
    """Main application window with sidebar navigation and full pipeline integration.

    Coordinates between UI pages and the background pipeline worker,
    forwarding progress signals to the progress bar and populating
    downstream pages when processing completes.
    """

    page_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Document Enhancement System")
        self.setMinimumSize(1200, 800)

        self.thread_pool = QThreadPool.globalInstance()
        self.thread_pool.setMaxThreadCount(4)
        logger.info("QThreadPool max threads: %d", self.thread_pool.maxThreadCount())

        self._current_theme = "dark"
        self._nav_buttons: dict[str, SidebarButton] = {}
        self._pages: dict[str, QWidget] = {}

        self._current_worker: Optional[PipelineWorker] = None
        self._current_images: List[np.ndarray] = []
        self._current_document: Optional[Document] = None
        self._doc_counter = 0

        self._setup_ui()
        self._wire_signals()
        self.navigate_to("home")

    # ── UI construction ──────────────────────────────────────────────

    def _setup_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._build_sidebar())
        root_layout.addWidget(self._build_content_area(), stretch=1)

        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.setVisible(False)

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(200)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(8, 16, 8, 16)
        layout.setSpacing(2)

        app_label = QLabel("DocEnhance AI")
        app_label.setObjectName("pageTitle")
        app_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(app_label)
        layout.addSpacing(16)

        icons_dir = _resource_dir() / "icons"
        for key, label in _NAV_PAGES:
            icon_path = str(icons_dir / f"{key}.svg")
            btn = SidebarButton(label, icon_path=icon_path)
            btn.setObjectName(f"nav_{key}")
            btn.clicked.connect(lambda checked, k=key: self.navigate_to(k))
            layout.addWidget(btn)
            self._nav_buttons[key] = btn

        layout.addStretch()

        self._cancel_btn = QPushButton("Cancel Processing")
        self._cancel_btn.setObjectName("dangerButton")
        self._cancel_btn.setCursor(Qt.PointingHandCursor)
        self._cancel_btn.setVisible(False)
        self._cancel_btn.clicked.connect(self._cancel_pipeline)
        layout.addWidget(self._cancel_btn)

        self._theme_btn = QPushButton("Toggle Theme")
        self._theme_btn.setObjectName("secondaryButton")
        self._theme_btn.setCursor(Qt.PointingHandCursor)
        self._theme_btn.clicked.connect(self._toggle_theme)
        layout.addWidget(self._theme_btn)

        return sidebar

    def _build_content_area(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.stack = QStackedWidget()
        self.stack.setObjectName("pageStack")
        layout.addWidget(self.stack, stretch=1)

        self._progress_widget = PipelineProgressBar()
        self._progress_widget.setVisible(False)
        self._progress_widget.setFixedHeight(60)
        layout.addWidget(self._progress_widget)

        self._register_pages()
        return container

    def _register_pages(self) -> None:
        """Create real page widgets and add them to the stack."""
        self._home_page = HomePage()
        self._upload_page = UploadPage()
        self._preview_page = PreviewPage()
        self._editor_page = EditorPage()
        self._enhance_page = EnhancePage()
        self._results_page = ResultsPage()
        self._settings_page = SettingsPage()

        page_map = {
            "home": self._home_page,
            "upload": self._upload_page,
            "preview": self._preview_page,
            "editor": self._editor_page,
            "enhance": self._enhance_page,
            "results": self._results_page,
            "settings": self._settings_page,
        }

        for key, _ in _NAV_PAGES:
            widget = page_map[key]
            self._pages[key] = widget
            self.stack.addWidget(widget)

    # ── Signal wiring (Phase 7) ──────────────────────────────────────

    def _wire_signals(self) -> None:
        """Connect page signals to slots for full pipeline integration."""
        self._home_page.navigate_requested.connect(self.navigate_to)
        self._upload_page.files_loaded.connect(self._on_files_loaded)
        self._preview_page.edit_requested.connect(
            lambda: self.navigate_to("editor"),
        )
        self._editor_page.text_accepted.connect(self._on_text_accepted)
        self._results_page.export_requested.connect(self._on_export_requested)
        self._settings_page.settings_changed.connect(self._on_settings_changed)

    # ── Pipeline orchestration ───────────────────────────────────────

    @Slot(object)
    def _on_files_loaded(self, loaded_doc) -> None:
        """User clicked Process on the upload page."""
        from app.utils.file_handler import LoadedDocument

        if not isinstance(loaded_doc, LoadedDocument) or not loaded_doc.pages:
            return

        self._current_images = loaded_doc.pages
        self._doc_counter += 1
        self._current_document = Document(
            doc_id=self._doc_counter,
            user_id=1,
            filename=loaded_doc.filename,
            file_path=loaded_doc.file_path,
            num_pages=loaded_doc.num_pages,
        )

        config = self._build_pipeline_config()
        self._start_pipeline(self._current_images, self._current_document, config)

    def _build_pipeline_config(self) -> PipelineConfig:
        """Merge settings page values with enhance page config."""
        settings = self._settings_page.get_pipeline_config()
        enhance_cfg = self._enhance_page.get_pipeline_config()

        return PipelineConfig(
            enable_grammar=enhance_cfg.enable_grammar,
            enable_readability=enhance_cfg.enable_readability,
            enable_summarization=enhance_cfg.enable_summarization,
            enable_plagiarism=enhance_cfg.enable_plagiarism,
            enable_paraphrasing=enhance_cfg.enable_paraphrasing,
            summarization_method=enhance_cfg.summarization_method,
            summary_sentences=enhance_cfg.summary_sentences,
            target_readability_grade=settings.get("target_readability_grade", 10.0),
            similarity_threshold=settings.get("similarity_threshold", 0.7),
            ocr_language=settings.get("ocr_language", "eng"),
            tesseract_path=settings.get("tesseract_path"),
            num_paraphrase_suggestions=settings.get("num_paraphrase_suggestions", 3),
            apply_threshold=settings.get("apply_threshold", False),
        )

    def _start_pipeline(self, images: List[np.ndarray],
                        document: Document,
                        config: PipelineConfig) -> None:
        """Launch a PipelineWorker on the thread pool."""
        self._current_worker = PipelineWorker(images, document, config)
        self._current_worker.signals.stage_progress.connect(self._on_stage_progress)
        self._current_worker.signals.finished.connect(self._on_pipeline_finished)
        self._current_worker.signals.error.connect(self._on_pipeline_error)
        self._current_worker.signals.cancelled.connect(self._on_pipeline_cancelled)

        self.show_progress()
        self._cancel_btn.setVisible(True)
        self._set_processing_ui(True)
        self.set_status("Processing document...")

        self.thread_pool.start(self._current_worker)
        logger.info("Pipeline started for %s", document.filename)

    @Slot(str, float, str)
    def _on_stage_progress(self, stage_value: str, percent: float,
                           message: str) -> None:
        stage_idx = _STAGE_INDEX_MAP.get(stage_value, -1)
        self._progress_widget.set_stage(stage_idx, message)

        total_stages = len(_STAGE_INDEX_MAP)
        if stage_idx >= 0:
            base = (stage_idx / total_stages) * 100
            stage_contribution = (percent / 100) * (100 / total_stages)
            overall = min(100.0, base + stage_contribution)
            self._progress_widget.set_progress(overall)

        self.set_status(message)

    @Slot(object)
    def _on_pipeline_finished(self, document: Document) -> None:
        self._current_document = document
        self._current_worker = None
        self._cancel_btn.setVisible(False)
        self._set_processing_ui(False)

        self._progress_widget.mark_complete()

        from PySide6.QtCore import QTimer
        QTimer.singleShot(1500, self.hide_progress)

        self._preview_page.set_data(self._current_images, document)
        self._editor_page.set_document(document)
        self._enhance_page.set_document(document)
        self._results_page.set_document(document)

        self.navigate_to("preview")
        self.set_status(f"Processing complete: {document.filename}", timeout=5000)
        logger.info("Pipeline finished for %s", document.filename)

    @Slot(str)
    def _on_pipeline_error(self, error_msg: str) -> None:
        self._current_worker = None
        self._cancel_btn.setVisible(False)
        self._set_processing_ui(False)
        self.hide_progress()

        QMessageBox.critical(
            self, "Processing Error",
            f"An error occurred during document processing:\n\n{error_msg}",
        )
        self.set_status("Processing failed")
        logger.error("Pipeline error: %s", error_msg)

    @Slot()
    def _on_pipeline_cancelled(self) -> None:
        self._current_worker = None
        self._cancel_btn.setVisible(False)
        self._set_processing_ui(False)
        self.hide_progress()

        self.set_status("Processing cancelled")
        logger.info("Pipeline cancelled by user")

    def _cancel_pipeline(self) -> None:
        if self._current_worker is not None:
            self._current_worker.cancel()
            self._cancel_btn.setEnabled(False)
            self.set_status("Cancelling...")

    def _set_processing_ui(self, is_processing: bool) -> None:
        """Disable/enable navigation buttons during processing."""
        for btn in self._nav_buttons.values():
            btn.setEnabled(not is_processing)

    # ── Editor integration ───────────────────────────────────────────

    @Slot(str)
    def _on_text_accepted(self, text: str) -> None:
        """User accepted edited text from the editor page."""
        if self._current_document:
            self._current_document.raw_text = text
            self._preview_page.set_data(
                self._current_images, self._current_document,
            )
        self.set_status("Text changes accepted")
        self.navigate_to("enhance")

    # ── Export integration ───────────────────────────────────────────

    @Slot(str, str)
    def _on_export_requested(self, fmt: str, output_path: str) -> None:
        if not self._current_document:
            return

        doc_type = (
            self._current_document.doc_type.value
            if self._current_document.doc_type else None
        )
        worker = ExportWorker(self._current_document, output_path, doc_type)
        worker.signals.finished.connect(self._on_export_finished)
        worker.signals.error.connect(self._on_export_error)

        self.set_status(f"Exporting to {fmt.upper()}...")
        self.thread_pool.start(worker)

    @Slot(object)
    def _on_export_finished(self, output_path) -> None:
        self.set_status(f"Exported to {output_path}", timeout=5000)
        QMessageBox.information(
            self, "Export Complete",
            f"Document exported successfully to:\n{output_path}",
        )

    @Slot(str)
    def _on_export_error(self, error_msg: str) -> None:
        self.set_status("Export failed")
        QMessageBox.critical(
            self, "Export Error",
            f"Failed to export document:\n\n{error_msg}",
        )

    # ── Settings integration ─────────────────────────────────────────

    @Slot()
    def _on_settings_changed(self) -> None:
        self.set_status("Settings updated", timeout=3000)

    # ── Navigation ───────────────────────────────────────────────────

    def navigate_to(self, page_key: str) -> None:
        """Switch the stacked widget to the page identified by *page_key*."""
        page = self._pages.get(page_key)
        if page is None:
            logger.warning("Unknown page key: %s", page_key)
            return

        self.stack.setCurrentWidget(page)

        for key, btn in self._nav_buttons.items():
            btn.set_active(key == page_key)

        self.page_changed.emit(page_key)
        logger.debug("Navigated to %s", page_key)

    def register_page(self, key: str, widget: QWidget) -> None:
        """Replace a page with a different implementation at runtime."""
        old = self._pages.get(key)
        if old is not None:
            idx = self.stack.indexOf(old)
            self.stack.removeWidget(old)
            old.deleteLater()

        self._pages[key] = widget
        self.stack.addWidget(widget)

    # ── Theme ────────────────────────────────────────────────────────

    def _toggle_theme(self) -> None:
        self._current_theme = "light" if self._current_theme == "dark" else "dark"
        self._apply_theme(self._current_theme)

    def _apply_theme(self, theme_name: str) -> None:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            app.setStyleSheet(get_theme(theme_name))
        logger.info("Theme switched to %s", theme_name)

    @property
    def current_theme(self) -> str:
        return self._current_theme

    # ── Progress / status helpers ────────────────────────────────────

    def show_progress(self) -> None:
        """Show the pipeline progress bar below the content area."""
        self._progress_widget.reset()
        self._progress_widget.setVisible(True)

    def hide_progress(self) -> None:
        self._progress_widget.setVisible(False)

    @property
    def progress_bar(self) -> PipelineProgressBar:
        return self._progress_widget

    def set_status(self, message: str, timeout: int = 0) -> None:
        """Update the status bar message."""
        self._status_bar.showMessage(message, timeout)
