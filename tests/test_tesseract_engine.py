"""Tests for Tesseract OCR engine module."""

from unittest.mock import Mock, patch

import pytest


def test_tesseract_engine_initialization_missing_dependencies():
    """Test that TesseractEngine raises error when dependencies are missing."""
    with patch("vis_cli.libs.tesseract_engine.TESSERACT_AVAILABLE", False):
        from vis_cli.libs.tesseract_engine import TesseractEngine, TesseractEngineError

        with pytest.raises(TesseractEngineError, match="pytesseract and/or Pillow not installed"):
            TesseractEngine()


def test_tesseract_engine_initialization_tesseract_not_installed():
    """Test that TesseractEngine raises error when tesseract is not installed."""
    with (
        patch("vis_cli.libs.tesseract_engine.TESSERACT_AVAILABLE", True),
        patch("vis_cli.libs.tesseract_engine.pytesseract") as mock_pytesseract,
    ):
        mock_pytesseract.get_tesseract_version.side_effect = Exception("Tesseract not found")

        from vis_cli.libs.tesseract_engine import TesseractEngine, TesseractEngineError

        with pytest.raises(TesseractEngineError, match="Tesseract not found"):
            TesseractEngine()


def test_tesseract_engine_initialization_success():
    """Test successful TesseractEngine initialization."""
    with (
        patch("vis_cli.libs.tesseract_engine.TESSERACT_AVAILABLE", True),
        patch("vis_cli.libs.tesseract_engine.pytesseract") as mock_pytesseract,
    ):
        mock_pytesseract.get_tesseract_version.return_value = "5.0.0"

        from vis_cli.libs.tesseract_engine import TesseractEngine

        engine = TesseractEngine(lang="eng", config="--psm 6")
        assert engine.name == "tesseract"
        assert engine.lang == "eng"
        assert engine.config == "--psm 6"


def test_tesseract_analyze_image_file_not_found():
    """Test that analyze_image returns error for non-existent file."""
    with (
        patch("vis_cli.libs.tesseract_engine.TESSERACT_AVAILABLE", True),
        patch("vis_cli.libs.tesseract_engine.pytesseract") as mock_pytesseract,
    ):
        mock_pytesseract.get_tesseract_version.return_value = "5.0.0"

        from vis_cli.libs.tesseract_engine import TesseractEngine

        engine = TesseractEngine()
        result = engine.analyze_image("nonexistent.jpg")

        assert result.success is False
        assert result.error is not None
        assert "Image file not found" in result.error
        assert result.engine == "tesseract"


def test_tesseract_analyze_image_success(tmp_path):
    """Test successful image analysis with Tesseract."""
    img = tmp_path / "test.jpg"
    img.write_bytes(b"fake image")

    with (
        patch("vis_cli.libs.tesseract_engine.TESSERACT_AVAILABLE", True),
        patch("vis_cli.libs.tesseract_engine.pytesseract") as mock_pytesseract,
        patch("vis_cli.libs.tesseract_engine.Image") as mock_image,
    ):
        mock_pytesseract.get_tesseract_version.return_value = "5.0.0"

        # Mock image opening
        mock_img = Mock()
        mock_image.open.return_value = mock_img

        # Mock text extraction
        mock_pytesseract.image_to_string.return_value = "Hello World\nTest Text"

        # Mock detailed data with confidence scores
        mock_pytesseract.image_to_data.return_value = {
            "conf": ["95", "88", "92", "-1", "0"],
            "text": ["Hello", "World", "Test", "", ""],
        }
        mock_pytesseract.Output.DICT = "dict"

        from vis_cli.libs.tesseract_engine import TesseractEngine

        engine = TesseractEngine(lang="eng")
        result = engine.analyze_image(img)

        assert result.success is True
        assert result.full_text == "Hello World\nTest Text"
        assert result.engine == "tesseract"
        assert result.confidence is not None
        # Average of 95, 88, 92 = 91.67, normalized to 0.9167
        assert 0.91 <= result.confidence <= 0.92
        assert len(result.labels) == 1
        assert result.labels[0].description == "text"


def test_tesseract_analyze_image_empty_text(tmp_path):
    """Test image analysis when no text is detected."""
    img = tmp_path / "test.jpg"
    img.write_bytes(b"fake image")

    with (
        patch("vis_cli.libs.tesseract_engine.TESSERACT_AVAILABLE", True),
        patch("vis_cli.libs.tesseract_engine.pytesseract") as mock_pytesseract,
        patch("vis_cli.libs.tesseract_engine.Image") as mock_image,
    ):
        mock_pytesseract.get_tesseract_version.return_value = "5.0.0"

        mock_img = Mock()
        mock_image.open.return_value = mock_img

        # Mock empty text extraction
        mock_pytesseract.image_to_string.return_value = ""
        mock_pytesseract.image_to_data.return_value = {
            "conf": ["-1", "0"],
            "text": ["", ""],
        }
        mock_pytesseract.Output.DICT = "dict"

        from vis_cli.libs.tesseract_engine import TesseractEngine

        engine = TesseractEngine()
        result = engine.analyze_image(img)

        assert result.success is True
        assert result.full_text is None
        assert result.confidence is None
        assert len(result.labels) == 0


def test_tesseract_analyze_image_low_confidence(tmp_path):
    """Test image analysis with low confidence scores."""
    img = tmp_path / "test.jpg"
    img.write_bytes(b"fake image")

    with (
        patch("vis_cli.libs.tesseract_engine.TESSERACT_AVAILABLE", True),
        patch("vis_cli.libs.tesseract_engine.pytesseract") as mock_pytesseract,
        patch("vis_cli.libs.tesseract_engine.Image") as mock_image,
    ):
        mock_pytesseract.get_tesseract_version.return_value = "5.0.0"

        mock_img = Mock()
        mock_image.open.return_value = mock_img

        mock_pytesseract.image_to_string.return_value = "Blurry Text"
        mock_pytesseract.image_to_data.return_value = {
            "conf": ["30", "25", "-1"],
            "text": ["Blurry", "Text", ""],
        }
        mock_pytesseract.Output.DICT = "dict"

        from vis_cli.libs.tesseract_engine import TesseractEngine

        engine = TesseractEngine()
        result = engine.analyze_image(img)

        assert result.success is True
        assert result.full_text == "Blurry Text"
        # Average of 30, 25 = 27.5, normalized to 0.275
        assert result.confidence is not None
        assert 0.27 <= result.confidence <= 0.28


def test_tesseract_analyze_image_processing_error(tmp_path):
    """Test error handling during image processing."""
    img = tmp_path / "test.jpg"
    img.write_bytes(b"fake image")

    with (
        patch("vis_cli.libs.tesseract_engine.TESSERACT_AVAILABLE", True),
        patch("vis_cli.libs.tesseract_engine.pytesseract") as mock_pytesseract,
        patch("vis_cli.libs.tesseract_engine.Image") as mock_image,
    ):
        mock_pytesseract.get_tesseract_version.return_value = "5.0.0"

        # Mock image opening to raise an error
        mock_image.open.side_effect = Exception("Corrupted image file")

        from vis_cli.libs.tesseract_engine import TesseractEngine

        engine = TesseractEngine()
        result = engine.analyze_image(img)

        assert result.success is False
        assert result.error is not None
        assert "Tesseract error" in result.error
        assert "Corrupted image file" in result.error


def test_tesseract_analyze_image_with_custom_config(tmp_path):
    """Test image analysis with custom Tesseract configuration."""
    img = tmp_path / "test.jpg"
    img.write_bytes(b"fake image")

    with (
        patch("vis_cli.libs.tesseract_engine.TESSERACT_AVAILABLE", True),
        patch("vis_cli.libs.tesseract_engine.pytesseract") as mock_pytesseract,
        patch("vis_cli.libs.tesseract_engine.Image") as mock_image,
    ):
        mock_pytesseract.get_tesseract_version.return_value = "5.0.0"

        mock_img = Mock()
        mock_image.open.return_value = mock_img
        mock_pytesseract.image_to_string.return_value = "Custom Config Text"
        mock_pytesseract.image_to_data.return_value = {
            "conf": ["90"],
            "text": ["Custom"],
        }
        mock_pytesseract.Output.DICT = "dict"

        from vis_cli.libs.tesseract_engine import TesseractEngine

        engine = TesseractEngine(lang="eng+fra", config="--psm 6 --oem 1")
        result = engine.analyze_image(img)

        # Verify custom config was used
        mock_pytesseract.image_to_string.assert_called_once()
        call_kwargs = mock_pytesseract.image_to_string.call_args[1]
        assert call_kwargs["lang"] == "eng+fra"
        assert call_kwargs["config"] == "--psm 6 --oem 1"

        assert result.success is True
        assert result.full_text == "Custom Config Text"


def test_tesseract_engine_interface_compliance():
    """Test that TesseractEngine properly implements OCREngine interface."""
    with (
        patch("vis_cli.libs.tesseract_engine.TESSERACT_AVAILABLE", True),
        patch("vis_cli.libs.tesseract_engine.pytesseract") as mock_pytesseract,
    ):
        mock_pytesseract.get_tesseract_version.return_value = "5.0.0"

        from vis_cli.libs.ocr_engine import OCREngine
        from vis_cli.libs.tesseract_engine import TesseractEngine

        engine = TesseractEngine()

        # Verify it's an instance of OCREngine
        assert isinstance(engine, OCREngine)
        assert hasattr(engine, "analyze_image")
        assert hasattr(engine, "name")
        assert callable(engine.analyze_image)
