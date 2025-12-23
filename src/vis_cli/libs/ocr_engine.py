"""
Unified OCR engine interface supporting multiple OCR backends.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class Label:
    """Represents a label/tag with a confidence score."""

    description: str
    score: float


@dataclass
class OCRResult:
    """Unified result structure for all OCR engines."""

    image_path: str
    engine: str  # Which engine was used (e.g., "vision_api", "tesseract")
    full_text: str | None = None
    labels: list[Label] = field(default_factory=list)
    confidence: float | None = None  # Overall confidence score if available
    error: str | None = None

    @property
    def success(self) -> bool:
        return self.error is None


class OCREngine(ABC):
    """Abstract base class for OCR engines."""

    @abstractmethod
    def analyze_image(self, image_path: str | Path) -> OCRResult:
        """
        Analyze an image and return OCR results.

        Args:
            image_path: Path to the image file

        Returns:
            OCRResult with extracted text and labels
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of this OCR engine."""
        pass
