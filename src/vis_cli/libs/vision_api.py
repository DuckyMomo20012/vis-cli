import base64
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

import requests

logger = logging.getLogger(__name__)


@dataclass
class Label:
    description: str
    score: float


@dataclass
class VisionAnalysisResult:
    image_path: str
    full_text: str | None = None
    labels: list[Label] = field(default_factory=list)
    error: str | None = None

    @property
    def success(self) -> bool:
        return self.error is None


class VisionAPIError(Exception):
    pass


def analyze_image_with_apikey(image_path: str | Path) -> VisionAnalysisResult:
    image_path = Path(image_path)

    base_url = os.environ.get("BASE_URL", "https://vision.googleapis.com/v1/images:annotate")

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
            return VisionAnalysisResult(image_path=str(image_path), error=error_msg)

        result = response.json()
        responses = result.get("responses", [])

        if not responses:
            error_msg = "No response from Vision API"
            logger.error("Empty response for %s", image_path.name)
            return VisionAnalysisResult(image_path=str(image_path), error=error_msg)

        data = responses[0]

        # Extract data even if there's an error (per Vision API docs)
        full_text = data.get("fullTextAnnotation", {}).get("text")
        labels = [
            Label(description=l["description"], score=float(l["score"]))
            for l in data.get("labelAnnotations", [])
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

        return VisionAnalysisResult(
            image_path=str(image_path),
            full_text=full_text,
            labels=labels,
            error=error_msg,
        )

    except (requests.exceptions.RequestException, OSError) as e:
        error_msg = str(e)
        logger.error("Error processing %s: %s", image_path.name, error_msg)
        return VisionAnalysisResult(image_path=str(image_path), error=error_msg)
