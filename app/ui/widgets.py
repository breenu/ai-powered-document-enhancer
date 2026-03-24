"""Reusable custom widgets for the AI Document Enhancement System UI."""

try:
    from PySide6.QtCore import Qt, Signal, QMimeData, QSize, QTimer, Property
    from PySide6.QtGui import (
        QDragEnterEvent, QDropEvent, QFont, QIcon, QPainter,
        QColor, QPen, QPixmap,
    )
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QProgressBar, QFrame, QSizePolicy, QGraphicsDropShadowEffect,
    )
except ImportError:
    pass


class SidebarButton(QPushButton):
    """Navigation button for the sidebar with active-state styling."""

    def __init__(self, text: str, icon_path: str = "", parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(40)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        if icon_path:
            self.setIcon(QIcon(icon_path))
            self.setIconSize(QSize(20, 20))

    def set_active(self, active: bool) -> None:
        self.setChecked(active)
        self.setProperty("active", active)
        self.style().unpolish(self)
        self.style().polish(self)


class StyledButton(QPushButton):
    """Pre-styled button with variant support (primary, secondary, danger)."""

    def __init__(self, text: str, variant: str = "primary", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(34)
        if variant == "secondary":
            self.setObjectName("secondaryButton")
        elif variant == "danger":
            self.setObjectName("dangerButton")


class PipelineProgressBar(QWidget):
    """Multi-stage progress indicator showing pipeline stage labels."""

    def __init__(self, stages: list[str] = None, parent=None):
        super().__init__(parent)
        self._stages = stages or [
            "Preprocessing", "OCR", "Grammar", "Readability",
            "Summarization", "Formatting", "Plagiarism", "Paraphrasing",
        ]
        self._current_stage = -1
        self._progress = 0.0
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._stage_label = QLabel("Ready")
        self._stage_label.setObjectName("subtitle")
        layout.addWidget(self._stage_label)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(True)
        layout.addWidget(self._progress_bar)

        self._detail_label = QLabel("")
        self._detail_label.setObjectName("subtitle")
        layout.addWidget(self._detail_label)

    def set_stage(self, stage_index: int, message: str = "") -> None:
        self._current_stage = stage_index
        if 0 <= stage_index < len(self._stages):
            stage_name = self._stages[stage_index]
            self._stage_label.setText(
                f"Stage {stage_index + 1}/{len(self._stages)}: {stage_name}"
            )
        if message:
            self._detail_label.setText(message)

    def set_progress(self, percent: float) -> None:
        self._progress = max(0.0, min(100.0, percent))
        self._progress_bar.setValue(int(self._progress))

    def set_message(self, message: str) -> None:
        self._detail_label.setText(message)

    def reset(self) -> None:
        self._current_stage = -1
        self._progress = 0.0
        self._progress_bar.setValue(0)
        self._stage_label.setText("Ready")
        self._detail_label.setText("")

    def mark_complete(self) -> None:
        self._progress_bar.setValue(100)
        self._stage_label.setText("Processing Complete")
        self._detail_label.setText("")


class DropZone(QFrame):
    """Drag-and-drop file target area with visual feedback."""

    files_dropped = Signal(list)

    SUPPORTED_EXTENSIONS = {
        ".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp", ".pdf",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMinimumHeight(180)
        self.setFrameShape(QFrame.StyledPanel)
        self.setObjectName("dropZone")
        self.setStyleSheet("""
            QFrame#dropZone {
                border: 2px dashed #7c6ff0;
                border-radius: 12px;
                background-color: rgba(124, 111, 240, 0.04);
            }
            QFrame#dropZone[drag_active="true"] {
                border-color: #9488f5;
                background-color: rgba(124, 111, 240, 0.12);
            }
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        icon_label = QLabel("Drop files here")
        icon_label.setAlignment(Qt.AlignCenter)
        font = icon_label.font()
        font.setPointSize(16)
        icon_label.setFont(font)
        layout.addWidget(icon_label)

        hint = QLabel("or click Browse to select files")
        hint.setAlignment(Qt.AlignCenter)
        hint.setObjectName("subtitle")
        layout.addWidget(hint)

        formats = QLabel("Supported: PNG, JPG, TIFF, BMP, WebP, PDF")
        formats.setAlignment(Qt.AlignCenter)
        formats.setObjectName("subtitle")
        layout.addWidget(formats)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setProperty("drag_active", True)
            self.style().unpolish(self)
            self.style().polish(self)

    def dragLeaveEvent(self, event):
        self.setProperty("drag_active", False)
        self.style().unpolish(self)
        self.style().polish(self)

    def dropEvent(self, event: QDropEvent):
        self.setProperty("drag_active", False)
        self.style().unpolish(self)
        self.style().polish(self)

        paths = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path:
                ext = "." + path.rsplit(".", 1)[-1].lower() if "." in path else ""
                if ext in self.SUPPORTED_EXTENSIONS:
                    paths.append(path)
        if paths:
            self.files_dropped.emit(paths)


class StatusCard(QFrame):
    """Small card widget showing a label and a value (e.g. for metrics)."""

    def __init__(self, title: str, value: str = "--", parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setObjectName("statusCard")
        self.setStyleSheet("""
            QFrame#statusCard {
                border: 1px solid palette(mid);
                border-radius: 8px;
                padding: 12px;
            }
        """)
        self.setMinimumWidth(140)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        self._title = QLabel(title)
        self._title.setObjectName("subtitle")
        layout.addWidget(self._title)

        self._value = QLabel(value)
        font = self._value.font()
        font.setPointSize(18)
        font.setBold(True)
        self._value.setFont(font)
        layout.addWidget(self._value)

    def set_value(self, value: str) -> None:
        self._value.setText(value)

    def set_title(self, title: str) -> None:
        self._title.setText(title)


class LoadingSpinner(QWidget):
    """Animated circular loading indicator (paint-based)."""

    def __init__(self, size: int = 40, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotate)
        self._running = False
        self._color = QColor("#7c6ff0")

    def start(self):
        self._running = True
        self._timer.start(30)
        self.show()

    def stop(self):
        self._running = False
        self._timer.stop()
        self.hide()

    def _rotate(self):
        self._angle = (self._angle + 8) % 360
        self.update()

    def paintEvent(self, event):
        if not self._running:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        pen = QPen(self._color)
        pen.setWidth(3)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

        margin = 4
        rect = self.rect().adjusted(margin, margin, -margin, -margin)
        painter.drawArc(rect, self._angle * 16, 270 * 16)
        painter.end()


class SectionHeader(QWidget):
    """Horizontal section divider with a label."""

    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)

        label = QLabel(text)
        label.setObjectName("pageTitle")
        layout.addWidget(label)
        layout.addStretch()
