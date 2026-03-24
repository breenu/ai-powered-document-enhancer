"""Image preprocessing module for scanned document enhancement.

Provides grayscale conversion, adaptive thresholding, skew correction
via Hough transform, and CLAHE contrast enhancement.
"""

import logging
import math

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class ImagePreprocessor:
    """Preprocesses scanned document images to improve OCR accuracy."""

    def __init__(self, clahe_clip_limit: float = 2.0, clahe_tile_size: int = 8):
        self.clahe_clip_limit = clahe_clip_limit
        self.clahe_tile_size = clahe_tile_size

    def to_grayscale(self, image: np.ndarray) -> np.ndarray:
        if len(image.shape) == 2:
            return image
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    def adaptive_threshold(self, image: np.ndarray, block_size: int = 11,
                           constant: int = 2) -> np.ndarray:
        gray = self.to_grayscale(image)
        return cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, block_size, constant,
        )

    def apply_clahe(self, image: np.ndarray) -> np.ndarray:
        gray = self.to_grayscale(image)
        clahe = cv2.createCLAHE(
            clipLimit=self.clahe_clip_limit,
            tileGridSize=(self.clahe_tile_size, self.clahe_tile_size),
        )
        return clahe.apply(gray)

    def detect_skew_angle(self, image: np.ndarray) -> float:
        """Detect document skew angle using the Hough Line Transform."""
        gray = self.to_grayscale(image)
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        lines = cv2.HoughLinesP(
            edges, 1, np.pi / 180, threshold=100,
            minLineLength=gray.shape[1] // 4, maxLineGap=10,
        )
        if lines is None or len(lines) == 0:
            return 0.0

        angles = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
            if abs(angle) < 45:
                angles.append(angle)

        if not angles:
            return 0.0
        return float(np.median(angles))

    def correct_skew(self, image: np.ndarray) -> np.ndarray:
        angle = self.detect_skew_angle(image)
        if abs(angle) < 0.5:
            return image

        h, w = image.shape[:2]
        center = (w // 2, h // 2)
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(
            image, matrix, (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE,
        )
        logger.info("Corrected skew by %.2f degrees", angle)
        return rotated

    def denoise(self, image: np.ndarray, strength: int = 10) -> np.ndarray:
        if len(image.shape) == 2:
            return cv2.fastNlMeansDenoising(image, None, strength, 7, 21)
        return cv2.fastNlMeansDenoisingColored(image, None, strength, strength, 7, 21)

    def preprocess(self, image: np.ndarray,
                   apply_threshold: bool = False) -> np.ndarray:
        """Full preprocessing pipeline: skew correction -> CLAHE -> denoise."""
        result = self.correct_skew(image)
        result = self.apply_clahe(result)
        result = self.denoise(result)
        if apply_threshold:
            result = self.adaptive_threshold(result)
        return result

    def load_image(self, path: str) -> np.ndarray:
        image = cv2.imread(path)
        if image is None:
            raise FileNotFoundError(f"Could not load image: {path}")
        return image
