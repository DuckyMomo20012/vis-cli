"""Tests for CLI main module."""

import json

from vis_cli.libs.vision_api import Label, VisionAnalysisResult
from vis_cli.main import find_images, save_result


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
    result = VisionAnalysisResult(
        image_path="test.jpg",
        full_text="Hello",
        labels=[Label("Text", 0.9)],
    )

    save_result(result, output, "json")

    data = json.loads(output.read_text())
    assert data["image"] == "test.jpg"
    assert data["success"] is True
    assert data["text"] == "Hello"
    assert len(data["labels"]) == 1
    assert data["labels"][0]["name"] == "Text"


def test_save_result_jsonl(tmp_path):
    output = tmp_path / "result.jsonl"
    result = VisionAnalysisResult(
        image_path="test.jpg",
        error="Some error",
    )

    save_result(result, output, "jsonl")

    content = output.read_text().strip()
    data = json.loads(content)
    assert data["success"] is False
    assert data["error"] == "Some error"
    assert "\n" not in content  # Single line
