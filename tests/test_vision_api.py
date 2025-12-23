"""Tests for Vision API module."""

from unittest.mock import Mock, patch

import pytest

from vis_cli.libs.ocr_engine import Label, OCRResult
from vis_cli.libs.vision_api import (
    VisionAPIError,
    analyze_image_with_apikey,
)


def test_label_creation():
    label = Label(description="Nature", score=0.95)
    assert label.description == "Nature"
    assert label.score == 0.95


def test_ocr_result_success():
    result = OCRResult(
        image_path="test.jpg",
        engine="vision_api",
        full_text="Hello World",
        labels=[Label("Text", 0.9)],
    )
    assert result.success is True
    assert result.error is None


def test_ocr_result_error():
    result = OCRResult(image_path="test.jpg", engine="vision_api", error="API Error")
    assert result.success is False
    assert result.error == "API Error"


def test_analyze_image_missing_api_key(tmp_path):
    img = tmp_path / "test.jpg"
    img.write_bytes(b"fake image")

    with (
        patch.dict("os.environ", {}, clear=True),
        pytest.raises(VisionAPIError, match="API_KEY environment variable"),
    ):
        analyze_image_with_apikey(img)


def test_analyze_image_file_not_found():
    with patch.dict("os.environ", {"API_KEY": "test_key"}), pytest.raises(FileNotFoundError):
        analyze_image_with_apikey("nonexistent.jpg")


@patch("vis_cli.libs.vision_api.requests.post")
def test_analyze_image_success(mock_post, tmp_path):
    img = tmp_path / "test.jpg"
    img.write_bytes(b"fake image")

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "responses": [
            {
                "fullTextAnnotation": {"text": "Hello"},
                "labelAnnotations": [
                    {"description": "Text", "score": 0.95},
                    {"description": "Document", "score": 0.88},
                ],
            }
        ]
    }
    mock_post.return_value = mock_response

    with patch.dict("os.environ", {"API_KEY": "test_key"}):
        result = analyze_image_with_apikey(img)

    assert result.success is True
    assert result.full_text == "Hello"
    assert len(result.labels) == 2
    assert result.labels[0].description == "Text"
    assert result.labels[0].score == 0.95


@patch("vis_cli.libs.vision_api.requests.post")
def test_analyze_image_api_error(mock_post, tmp_path):
    img = tmp_path / "test.jpg"
    img.write_bytes(b"fake image")

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"responses": [{"error": {"message": "Invalid API key"}}]}
    mock_post.return_value = mock_response

    with patch.dict("os.environ", {"API_KEY": "test_key"}):
        result = analyze_image_with_apikey(img)

    assert result.success is False
    assert result.error is not None
    assert "Invalid API key" in result.error


@patch("vis_cli.libs.vision_api.requests.post")
def test_analyze_image_http_error(mock_post, tmp_path):
    img = tmp_path / "test.jpg"
    img.write_bytes(b"fake image")

    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.text = "Bad Request"
    mock_post.return_value = mock_response

    with patch.dict("os.environ", {"API_KEY": "test_key"}):
        result = analyze_image_with_apikey(img)

    assert result.success is False
    assert result.error is not None
    assert "HTTP 400" in result.error
