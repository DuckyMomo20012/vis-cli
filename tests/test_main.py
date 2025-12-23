"""Tests for CLI main module."""

import json
from argparse import Namespace
from unittest.mock import patch

import pytest

from vis_cli.libs.ocr_engine import Label, OCRResult
from vis_cli.main import create_engine, find_images, save_result


def test_find_images_empty_dir(tmp_path):
    images = find_images(tmp_path)
    assert images == []


def test_find_images_with_images(tmp_path):
    (tmp_path / "photo1.jpg").write_bytes(b"fake")
    (tmp_path / "photo2.png").write_bytes(b"fake")
    (tmp_path / "doc.txt").write_bytes(b"fake")

    images = find_images(tmp_path)
    assert len(images) == 2
    assert all(img.suffix.lower() in {".jpg", ".png"} for img in images)


def test_find_images_recursive(tmp_path):
    (tmp_path / "photo1.jpg").write_bytes(b"fake")
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    (subdir / "photo2.png").write_bytes(b"fake")

    images = find_images(tmp_path)
    assert len(images) == 2


def test_save_result_json(tmp_path):
    output = tmp_path / "result.json"
    result = OCRResult(
        image_path="test.jpg",
        engine="tesseract",
        full_text="Hello",
        labels=[Label("Text", 0.9)],
    )

    save_result(result, output, "json")

    data = json.loads(output.read_text())
    assert data["image"] == "test.jpg"
    assert data["engine"] == "tesseract"
    assert data["success"] is True
    assert data["text"] == "Hello"
    assert len(data["labels"]) == 1
    assert data["labels"][0]["name"] == "Text"


def test_save_result_jsonl(tmp_path):
    output = tmp_path / "result.jsonl"
    result = OCRResult(
        image_path="test.jpg",
        engine="vision_api",
        error="Some error",
    )

    save_result(result, output, "jsonl")

    content = output.read_text().strip()
    data = json.loads(content)
    assert data["success"] is False
    assert data["error"] == "Some error"
    assert "\n" not in content  # Single line


def test_create_engine_vision():
    """Test creating Vision API engine."""
    args = Namespace(engine="vision")

    with patch.dict("os.environ", {"API_KEY": "test_key"}):
        engine = create_engine(args)

    from vis_cli.libs.vision_api import VisionAPIEngine

    assert isinstance(engine, VisionAPIEngine)
    assert engine.name == "vision_api"


def test_create_engine_tesseract():
    """Test creating Tesseract engine."""
    args = Namespace(engine="tesseract", lang="eng", tesseract_config="--psm 6")

    with (
        patch("vis_cli.main.TESSERACT_AVAILABLE", True),
        patch("vis_cli.libs.tesseract_engine.TESSERACT_AVAILABLE", True),
        patch("vis_cli.libs.tesseract_engine.pytesseract") as mock_pytesseract,
    ):
        mock_pytesseract.get_tesseract_version.return_value = "5.0.0"
        engine = create_engine(args)

    from vis_cli.libs.tesseract_engine import TesseractEngine

    assert isinstance(engine, TesseractEngine)
    assert engine.name == "tesseract"
    assert engine.lang == "eng"
    assert engine.config == "--psm 6"


def test_create_engine_tesseract_unavailable():
    """Test that creating Tesseract engine exits when unavailable."""
    args = Namespace(engine="tesseract")

    with patch("vis_cli.main.TESSERACT_AVAILABLE", False), pytest.raises(SystemExit):
        create_engine(args)


def test_create_engine_unknown():
    """Test that unknown engine exits."""
    args = Namespace(engine="unknown_engine")

    with pytest.raises(SystemExit):
        create_engine(args)
