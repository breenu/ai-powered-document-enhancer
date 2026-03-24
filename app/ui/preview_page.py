"""Preview page showing side-by-side original image and extracted OCR text."""

from typing import List, Optional

try:
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtGui import QPixmap, QImage
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
        QSplitter, QFrame, QScrollArea, QSizePolicy, QSpinBox,
    )
except ImportError:
    pass

import cv2
import numpy as np

from app.ui.widgets import SectionHeader, StatusCard, StyledButton
from app.models.document import Document


def _ndarray_to_pixmap(image: np.ndarray) -> QPixmap:
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    h, w, ch = rgb.shape
    qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
    return QPixmap.fromImage(qimg)


class PreviewPage(QWidget):
    """Side-by-side original image vs. extracted text with page navigation."""

    edit_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._images: List[np.ndarray] = []
        self._current_page = 0
        self._document: Optional[Document] = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        top_row = QHBoxLayout()
        top_row.addWidget(SectionHeader("Preview"))
        top_row.addStretch()

        self._page_label = QLabel("Page 1 / 1")
        self._page_label.setObjectName("subtitle")
        top_row.addWidget(self._page_label)

        self._prev_btn = StyledButton("<", variant="secondary")
        self._prev_btn.setFixedWidth(36)
        self._prev_btn.clicked.connect(self._prev_page)
        top_row.addWidget(self._prev_btn)

        self._next_btn = StyledButton(">", variant="secondary")
        self._next_btn.setFixedWidth(36)
        self._next_btn.clicked.connect(self._next_page)
        top_row.addWidget(self._next_btn)

        layout.addLayout(top_row)

        splitter = QSplitter(Qt.Horizontal)

        img_frame = QFrame()
        img_frame.setFrameShape(QFrame.StyledPanel)
        img_layout = QVBoxLayout(img_frame)
        img_layout.setContentsMargins(8, 8, 8, 8)

        img_title = QLabel("Original Image")
        img_title.setAlignment(Qt.AlignCenter)
        font = img_title.font()
        font.setBold(True)
        img_title.setFont(font)
        img_layout.addWidget(img_title)

        self._image_scroll = QScrollArea()
        self._image_scroll.setWidgetResizable(True)
        self._image_scroll.setFrameShape(QFrame.NoFrame)
        self._image_label = QLabel("No image loaded")
        self._image_label.setAlignment(Qt.AlignCenter)
        self._image_scroll.setWidget(self._image_label)
        img_layout.addWidget(self._image_scroll)

        splitter.addWidget(img_frame)

        text_frame = QFrame()
        text_frame.setFrameShape(QFrame.StyledPanel)
        text_layout = QVBoxLayout(text_frame)
        text_layout.setContentsMargins(8, 8, 8, 8)

        text_title = QLabel("Extracted Text (OCR)")
        text_title.setAlignment(Qt.AlignCenter)
        font2 = text_title.font()
        font2.setBold(True)
        text_title.setFont(font2)
        text_layout.addWidget(text_title)

        self._text_edit = QTextEdit()
        self._text_edit.setReadOnly(True)
        self._text_edit.setPlaceholderText("OCR text will appear here...")
        text_layout.addWidget(self._text_edit)

        splitter.addWidget(text_frame)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter, stretch=1)

        stats_row = QHBoxLayout()
        self._confidence_card = StatusCard("OCR Confidence", "--")
        self._word_count_card = StatusCard("Word Count", "--")
        self._pages_card = StatusCard("Pages", "--")
        stats_row.addWidget(self._confidence_card)
        stats_row.addWidget(self._word_count_card)
        stats_row.addWidget(self._pages_card)
        stats_row.addStretch()

        edit_btn = StyledButton("Edit Text")
        edit_btn.clicked.connect(self.edit_requested.emit)
        stats_row.addWidget(edit_btn)
        layout.addLayout(stats_row)

    def set_data(self, images: List[np.ndarray], document: Document) -> None:
        self._images = images
        self._document = document
        self._current_page = 0
        self._update_view()

    def _update_view(self) -> None:
        total = len(self._images)
        self._page_label.setText(f"Page {self._current_page + 1} / {max(1, total)}")
        self._prev_btn.setEnabled(self._current_page > 0)
        self._next_btn.setEnabled(self._current_page < total - 1)

        if self._images:
            img = self._images[self._current_page]
            pixmap = _ndarray_to_pixmap(img)
            max_w = self._image_scroll.viewport().width() - 20
            if pixmap.width() > max_w > 0:
                pixmap = pixmap.scaledToWidth(max_w, Qt.SmoothTransformation)
            self._image_label.setPixmap(pixmap)
        else:
            self._image_label.setText("No image loaded")

        if self._document:
            self._text_edit.setPlainText(self._document.raw_text)
            self._confidence_card.set_value(
                f"{self._document.ocr_confidence:.1f}%"
            )
            self._word_count_card.set_value(
                str(self._document.get_word_count())
            )
            self._pages_card.set_value(str(self._document.num_pages))

    def _prev_page(self) -> None:
        if self._current_page > 0:
            self._current_page -= 1
            self._update_view()

    def _next_page(self) -> None:
        if self._current_page < len(self._images) - 1:
            self._current_page += 1
            self._update_view()

    def clear(self) -> None:
        self._images = []
        self._document = None
        self._current_page = 0
        self._image_label.setText("No image loaded")
        self._text_edit.clear()
        self._confidence_card.set_value("--")
        self._word_count_card.set_value("--")
        self._pages_card.set_value("--")
