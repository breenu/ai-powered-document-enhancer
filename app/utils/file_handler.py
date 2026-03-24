"""File I/O and PDF page extraction utilities.

Handles loading images (PNG, JPG, TIFF, BMP) and PDFs, converting
PDF pages to images via pdf2image, and providing a unified interface
for the pipeline to consume document pages as numpy arrays.
"""

import logging
import os
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp"}
SUPPORTED_PDF_EXTENSIONS = {".pdf"}
SUPPORTED_EXTENSIONS = SUPPORTED_IMAGE_EXTENSIONS | SUPPORTED_PDF_EXTENSIONS


@dataclass
class LoadedDocument:
    """Result of loading a document file."""
    file_path: str
    filename: str
    pages: List[np.ndarray] = field(default_factory=list)
    num_pages: int = 0
    file_size_bytes: int = 0
    is_pdf: bool = False
    errors: List[str] = field(default_factory=list)


class FileHandler:
    """Loads images and PDFs, converting them to numpy arrays for processing."""

    def __init__(self, poppler_path: Optional[str] = None,
                 temp_dir: Optional[str] = None):
        self._poppler_path = poppler_path
        self._temp_dir = temp_dir or tempfile.gettempdir()

    @staticmethod
    def get_file_extension(file_path: str) -> str:
        return Path(file_path).suffix.lower()

    @staticmethod
    def is_supported(file_path: str) -> bool:
        ext = Path(file_path).suffix.lower()
        return ext in SUPPORTED_EXTENSIONS

    @staticmethod
    def is_image_file(file_path: str) -> bool:
        ext = Path(file_path).suffix.lower()
        return ext in SUPPORTED_IMAGE_EXTENSIONS

    @staticmethod
    def is_pdf_file(file_path: str) -> bool:
        ext = Path(file_path).suffix.lower()
        return ext in SUPPORTED_PDF_EXTENSIONS

    def validate_file(self, file_path: str) -> Tuple[bool, str]:
        """Return (is_valid, message) for the given path."""
        if not os.path.exists(file_path):
            return False, f"File not found: {file_path}"
        if not os.path.isfile(file_path):
            return False, f"Path is not a file: {file_path}"
        if os.path.getsize(file_path) == 0:
            return False, f"File is empty: {file_path}"
        if not self.is_supported(file_path):
            ext = self.get_file_extension(file_path)
            supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
            return False, f"Unsupported format '{ext}'. Supported: {supported}"
        return True, "OK"

    def load_image(self, file_path: str) -> np.ndarray:
        """Load a single image file as a BGR numpy array."""
        image = cv2.imread(file_path, cv2.IMREAD_COLOR)
        if image is None:
            raise IOError(f"Failed to read image: {file_path}")
        logger.debug("Loaded image %s (%dx%d)", file_path, image.shape[1], image.shape[0])
        return image

    def load_pdf_pages(self, file_path: str,
                       dpi: int = 300,
                       first_page: Optional[int] = None,
                       last_page: Optional[int] = None) -> List[np.ndarray]:
        """Convert PDF pages to BGR numpy arrays via pdf2image.

        Args:
            file_path: Path to the PDF file.
            dpi: Resolution for rendering. Higher = better OCR, slower.
            first_page: 1-based first page to extract (None = from start).
            last_page: 1-based last page to extract (None = to end).

        Returns:
            List of numpy arrays, one per page.
        """
        from pdf2image import convert_from_path

        kwargs = {"pdf_path": file_path, "dpi": dpi}
        if self._poppler_path:
            kwargs["poppler_path"] = self._poppler_path
        if first_page is not None:
            kwargs["first_page"] = first_page
        if last_page is not None:
            kwargs["last_page"] = last_page

        pil_images: List[Image.Image] = convert_from_path(**kwargs)
        pages: List[np.ndarray] = []
        for i, pil_img in enumerate(pil_images):
            rgb_array = np.array(pil_img)
            bgr_array = cv2.cvtColor(rgb_array, cv2.COLOR_RGB2BGR)
            pages.append(bgr_array)
            logger.debug("PDF page %d: %dx%d", i + 1, bgr_array.shape[1], bgr_array.shape[0])

        return pages

    def load(self, file_path: str, dpi: int = 300) -> LoadedDocument:
        """Unified loader: returns a LoadedDocument with page images.

        Works for both single images and multi-page PDFs.
        """
        result = LoadedDocument(
            file_path=file_path,
            filename=os.path.basename(file_path),
        )

        valid, msg = self.validate_file(file_path)
        if not valid:
            result.errors.append(msg)
            return result

        result.file_size_bytes = os.path.getsize(file_path)

        try:
            if self.is_pdf_file(file_path):
                result.is_pdf = True
                result.pages = self.load_pdf_pages(file_path, dpi=dpi)
            else:
                image = self.load_image(file_path)
                result.pages = [image]

            result.num_pages = len(result.pages)
            logger.info("Loaded %s: %d page(s), %.1f KB",
                        result.filename, result.num_pages,
                        result.file_size_bytes / 1024)

        except Exception as e:
            error_msg = f"Error loading {file_path}: {e}"
            logger.error(error_msg)
            result.errors.append(error_msg)

        return result

    def save_temp_image(self, image: np.ndarray, prefix: str = "page") -> str:
        """Save a numpy image to a temporary file. Returns the path."""
        fd, path = tempfile.mkstemp(suffix=".png", prefix=f"{prefix}_", dir=self._temp_dir)
        os.close(fd)
        cv2.imwrite(path, image)
        return path

    @staticmethod
    def copy_file(src: str, dst: str) -> str:
        """Copy a file, creating parent directories as needed."""
        os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
        shutil.copy2(src, dst)
        return dst

    @staticmethod
    def ensure_directory(path: str) -> str:
        """Create directory (and parents) if it doesn't exist."""
        os.makedirs(path, exist_ok=True)
        return path
