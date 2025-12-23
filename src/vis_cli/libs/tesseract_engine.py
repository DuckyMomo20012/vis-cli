"""
Tesseract OCR engine implementation.
"""

import logging
from pathlib import Path

try:
    import pytesseract  # type: ignore[import-untyped]
    from PIL import Image

    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    pytesseract = None  # type: ignore[assignment]
    Image = None  # type: ignore[assignment]

from vis_cli.libs.ocr_engine import Label, OCREngine, OCRResult

logger = logging.getLogger(__name__)


class TesseractEngineError(Exception):
    """Exception raised for Tesseract engine errors."""

    pass


class TesseractEngine(OCREngine):
    """OCR engine using Tesseract via pytesseract."""

    def __init__(self, lang: str = "eng", config: str = ""):
        """
        Initialize Tesseract engine.

        Args:
            lang: Language code(s) for OCR (default: "eng")
            config: Additional Tesseract configuration options
        """
        if not TESSERACT_AVAILABLE:
            raise TesseractEngineError(
                "pytesseract and/or Pillow not installed. "
                "Install with: pip install pytesseract Pillow"
            )

        self.lang = lang
        self.config = config

        # Verify tesseract is installed
        try:
            pytesseract.get_tesseract_version()  # type: ignore[union-attr]
        except Exception as e:
            raise TesseractEngineError(f"Tesseract not found or not properly installed: {e}") from e

    @property
    def name(self) -> str:
        return "tesseract"

    def analyze_image(self, image_path: str | Path) -> OCRResult:
        """
        Analyze image using Tesseract OCR.

        Args:
            image_path: Path to the image file

        Returns:
            OCRResult with extracted text and confidence information
        """
        image_path = Path(image_path)

        if not image_path.exists():
            return OCRResult(
                image_path=str(image_path),
                engine=self.name,
                error=f"Image file not found: {image_path}",
            )

        try:
            # Open image with PIL
            image = Image.open(image_path)  # type: ignore[union-attr]

            # Extract text
            text = pytesseract.image_to_string(image, lang=self.lang, config=self.config).strip()  # type: ignore[union-attr]

            # Get detailed data with confidence scores
            data = pytesseract.image_to_data(  # type: ignore[union-attr]
                image,
                lang=self.lang,
                config=self.config,
                output_type=pytesseract.Output.DICT,  # type: ignore[union-attr]
            )

            # Calculate average confidence for words with confidence > 0
            confidences = [
                float(conf)
                for conf in data.get("conf", [])
                if str(conf).replace(".", "").replace("-", "").isdigit() and float(conf) > 0
            ]
            avg_confidence = sum(confidences) / len(confidences) if confidences else None

            # Convert average confidence to 0-1 scale (Tesseract uses 0-100)
            normalized_confidence = avg_confidence / 100.0 if avg_confidence is not None else None

            # Tesseract doesn't do label detection, so we create basic labels
            # based on the presence of text
            labels = []
            if text:
                # Create a generic "text" label
                labels.append(
                    Label(
                        description="text",
                        score=normalized_confidence if normalized_confidence else 0.5,
                    )
                )

            logger.debug(
                "Processed %s with Tesseract: %d chars, confidence: %s",
                image_path.name,
                len(text),
                f"{normalized_confidence:.2f}" if normalized_confidence else "N/A",
            )

            return OCRResult(
                image_path=str(image_path),
                engine=self.name,
                full_text=text if text else None,
                labels=labels,
                confidence=normalized_confidence,
                error=None,
            )

        except Exception as e:
            error_msg = f"Tesseract error: {str(e)}"
            logger.error("Error processing %s: %s", image_path.name, error_msg)
            return OCRResult(image_path=str(image_path), engine=self.name, error=error_msg)
