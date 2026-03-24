"""OCR engine module wrapping pytesseract.

Supports standard printed text, handwriting configuration,
per-word confidence scores, and batch (multi-page) processing.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np
import pytesseract
from PIL import Image

logger = logging.getLogger(__name__)


@dataclass
class OCRResult:
    text: str
    confidence: float
    word_confidences: List[Dict] = field(default_factory=list)
    page_number: int = 1


class OCREngine:
    """Wrapper around pytesseract for text extraction from images."""

    DEFAULT_CONFIG = "--oem 3 --psm 6"
    HANDWRITING_CONFIG = "--oem 3 --psm 6"

    def __init__(self, tesseract_path: Optional[str] = None,
                 language: str = "eng"):
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        self.language = language

    def extract_text(self, image: np.ndarray,
                     config: str = None) -> OCRResult:
        if config is None:
            config = self.DEFAULT_CONFIG

        pil_image = Image.fromarray(image)
        text = pytesseract.image_to_string(
            pil_image, lang=self.language, config=config,
        )
        data = pytesseract.image_to_data(
            pil_image, lang=self.language, config=config,
            output_type=pytesseract.Output.DICT,
        )

        confidences = [int(c) for c in data["conf"] if int(c) >= 0]
        avg_confidence = (
            sum(confidences) / len(confidences) if confidences else 0.0
        )

        word_details = []
        for i, word in enumerate(data["text"]):
            if word.strip() and int(data["conf"][i]) >= 0:
                word_details.append({
                    "word": word,
                    "confidence": int(data["conf"][i]),
                    "left": data["left"][i],
                    "top": data["top"][i],
                    "width": data["width"][i],
                    "height": data["height"][i],
                })

        return OCRResult(
            text=text.strip(),
            confidence=round(avg_confidence, 2),
            word_confidences=word_details,
        )

    def extract_handwriting(self, image: np.ndarray) -> OCRResult:
        return self.extract_text(image, config=self.HANDWRITING_CONFIG)

    def batch_extract(self, images: List[np.ndarray],
                      config: str = None) -> List[OCRResult]:
        results = []
        for i, img in enumerate(images, start=1):
            result = self.extract_text(img, config=config)
            result.page_number = i
            results.append(result)
            logger.info("Page %d: confidence=%.1f%%", i, result.confidence)
        return results

    def get_low_confidence_words(self, result: OCRResult,
                                 threshold: float = 60.0) -> List[Dict]:
        return [
            w for w in result.word_confidences
            if w["confidence"] < threshold
        ]
