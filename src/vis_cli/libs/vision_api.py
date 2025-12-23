import base64
import logging
import os
from pathlib import Path

import requests

from vis_cli.libs.ocr_engine import Label, OCREngine, OCRResult

logger = logging.getLogger(__name__)


class VisionAPIError(Exception):
    pass


class VisionAPIEngine(OCREngine):
    """OCR engine using Google Cloud Vision API."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        """
        Initialize Vision API engine.

        Args:
            api_key: Google Cloud Vision API key (defaults to API_KEY env var)
            base_url: Base URL for the API (defaults to BASE_URL env var or standard endpoint)
        """
        self.api_key = api_key or os.environ.get("API_KEY")
        self.base_url = base_url or os.environ.get(
            "BASE_URL", "https://vision.googleapis.com/v1/images:annotate"
        )

        if not self.api_key:
            raise VisionAPIError("API_KEY must be provided or set as environment variable")

    @property
    def name(self) -> str:
        return "vision_api"

    def analyze_image(self, image_path: str | Path) -> OCRResult:
        """
        Analyze image using Google Cloud Vision API.

        Args:
            image_path: Path to the image file

        Returns:
            OCRResult with extracted text and labels
        """
        return analyze_image_with_apikey(image_path, self.api_key, self.base_url)


def analyze_image_with_apikey(
    image_path: str | Path, api_key: str | None = None, base_url: str | None = None
) -> OCRResult:
    """
    Analyze an image using Google Cloud Vision API.

    Args:
        image_path: Path to the image file
        api_key: Google Cloud Vision API key (defaults to API_KEY env var)
        base_url: Base URL for the API (defaults to BASE_URL env var)

    Returns:
        OCRResult with extracted text and labels
    """
    image_path = Path(image_path)

    if base_url is None:
        base_url = os.environ.get("BASE_URL", "https://vision.googleapis.com/v1/images:annotate")

    if api_key is None:
        api_key = os.environ.get("API_KEY")

    if not api_key:
        raise VisionAPIError("API_KEY environment variable is not set")

    if not image_path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    try:
        with open(image_path, "rb") as f:
            base64_image = base64.b64encode(f.read()).decode("utf-8")

        payload = {
            "requests": [
                {
                    "image": {"content": base64_image},
                    "features": [
                        {"type": "LABEL_DETECTION", "maxResults": 5},
                        {"type": "TEXT_DETECTION"},
                    ],
                }
            ]
        }

        response = requests.post(
            f"{base_url}?key={api_key}",
            json=payload,
            timeout=30,
        )

        if response.status_code != 200:
            error_msg = f"HTTP {response.status_code}: {response.text}"
            logger.error("API error for %s: %s", image_path.name, error_msg)
            return OCRResult(image_path=str(image_path), engine="vision_api", error=error_msg)

        result = response.json()
        responses = result.get("responses", [])

        if not responses:
            error_msg = "No response from Vision API"
            logger.error("Empty response for %s", image_path.name)
            return OCRResult(image_path=str(image_path), engine="vision_api", error=error_msg)

        data = responses[0]

        # Extract data even if there's an error (per Vision API docs)
        full_text = data.get("fullTextAnnotation", {}).get("text")
        labels = [
            Label(description=label["description"], score=float(label["score"]))
            for label in data.get("labelAnnotations", [])
        ]

        # Check for errors but still return partial results
        error_msg = None
        if "error" in data:
            error_info = data["error"]
            error_msg = (
                f"{error_info.get('message', 'Unknown error')} "
                f"(code: {error_info.get('code', 'N/A')})"
            )
            logger.warning("Partial result for %s: %s", image_path.name, error_msg)

        return OCRResult(
            image_path=str(image_path),
            engine="vision_api",
            full_text=full_text,
            labels=labels,
            error=error_msg,
        )

    except (requests.exceptions.RequestException, OSError) as e:
        error_msg = str(e)
        logger.error("Error processing %s: %s", image_path.name, error_msg)
        return OCRResult(image_path=str(image_path), engine="vision_api", error=error_msg)
