"""Upload page with drag-and-drop zone, file browser, and thumbnail preview."""

import os
import logging
from typing import List, Optional

try:
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtGui import QPixmap, QImage
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QFileDialog, QFrame, QScrollArea, QSizePolicy, QMessageBox,
    )
except ImportError:
    pass

import cv2
import numpy as np

from app.ui.widgets import DropZone, SectionHeader, StyledButton
from app.utils.file_handler import FileHandler, LoadedDocument, SUPPORTED_EXTENSIONS

logger = logging.getLogger(__name__)


def _ndarray_to_pixmap(image: np.ndarray, max_w: int = 180,
                       max_h: int = 240) -> QPixmap:
    """Convert a BGR numpy array to a scaled QPixmap thumbnail."""
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    h, w, ch = rgb.shape
    qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
    pix = QPixmap.fromImage(qimg)
    return pix.scaled(max_w, max_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)


class UploadPage(QWidget):
    """Document upload page with drag-and-drop and file browsing."""

    files_loaded = Signal(object)  # LoadedDocument

    def __init__(self, parent=None):
        super().__init__(parent)
        self._file_handler = FileHandler()
        self._loaded_doc: Optional[LoadedDocument] = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)

        layout.addWidget(SectionHeader("Upload Document"))

        self._drop_zone = DropZone()
        self._drop_zone.files_dropped.connect(self._on_files_dropped)
        layout.addWidget(self._drop_zone)

        btn_row = QHBoxLayout()
        self._browse_btn = StyledButton("Browse Files", variant="secondary")
        self._browse_btn.clicked.connect(self._browse_files)
        btn_row.addWidget(self._browse_btn)
        btn_row.addStretch()

        self._file_label = QLabel("No file selected")
        self._file_label.setObjectName("subtitle")
        btn_row.addWidget(self._file_label)
        layout.addLayout(btn_row)

        layout.addWidget(SectionHeader("Preview"))

        preview_scroll = QScrollArea()
        preview_scroll.setWidgetResizable(True)
        preview_scroll.setFrameShape(QFrame.NoFrame)
        preview_scroll.setMinimumHeight(260)

        self._preview_container = QWidget()
        self._preview_layout = QHBoxLayout(self._preview_container)
        self._preview_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self._preview_layout.setSpacing(10)
        preview_scroll.setWidget(self._preview_container)
        layout.addWidget(preview_scroll)

        bottom_row = QHBoxLayout()
        self._process_btn = StyledButton("Process Document")
        self._process_btn.setMinimumHeight(44)
        self._process_btn.setEnabled(False)
        self._process_btn.clicked.connect(self._emit_loaded)
        bottom_row.addStretch()
        bottom_row.addWidget(self._process_btn)
        layout.addLayout(bottom_row)

    def _browse_files(self) -> None:
        ext_filter = "Documents ({})".format(
            " ".join(f"*{e}" for e in sorted(SUPPORTED_EXTENSIONS))
        )
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Document", "", ext_filter,
        )
        if path:
            self._load_file(path)

    def _on_files_dropped(self, paths: List[str]) -> None:
        if paths:
            self._load_file(paths[0])

    def _load_file(self, path: str) -> None:
        loaded = self._file_handler.load(path)
        if loaded.errors:
            QMessageBox.warning(
                self, "Load Error", "\n".join(loaded.errors),
            )
            return

        self._loaded_doc = loaded
        name = os.path.basename(path)
        info = f"{name}  ({loaded.num_pages} page{'s' if loaded.num_pages != 1 else ''}"
        info += f", {loaded.file_size_bytes / 1024:.1f} KB)"
        self._file_label.setText(info)
        self._process_btn.setEnabled(True)
        self._show_thumbnails(loaded)

    def _show_thumbnails(self, loaded: LoadedDocument) -> None:
        while self._preview_layout.count():
            item = self._preview_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        for i, page in enumerate(loaded.pages):
            thumb_widget = self._make_thumbnail(page, i + 1)
            self._preview_layout.addWidget(thumb_widget)

    @staticmethod
    def _make_thumbnail(image: np.ndarray, page_num: int) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        pixmap = _ndarray_to_pixmap(image)
        img_label = QLabel()
        img_label.setPixmap(pixmap)
        img_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(img_label)

        caption = QLabel(f"Page {page_num}")
        caption.setObjectName("subtitle")
        caption.setAlignment(Qt.AlignCenter)
        layout.addWidget(caption)

        return container

    def _emit_loaded(self) -> None:
        if self._loaded_doc:
            self.files_loaded.emit(self._loaded_doc)

    def get_loaded_document(self) -> Optional[LoadedDocument]:
        return self._loaded_doc

    def reset(self) -> None:
        self._loaded_doc = None
        self._file_label.setText("No file selected")
        self._process_btn.setEnabled(False)
        while self._preview_layout.count():
            item = self._preview_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
