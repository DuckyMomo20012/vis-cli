import argparse
import json
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

from vis_cli.libs.ocr_engine import OCREngine
from vis_cli.libs.vision_api import VisionAPIEngine, VisionAPIError

# Try to import Tesseract engine
try:
    from vis_cli.libs.tesseract_engine import TesseractEngineError

    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    TesseractEngineError = Exception  # type: ignore[misc]

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}


def setup_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Batch image OCR and label extraction tool supporting multiple OCR engines",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example: %(prog)s ./images ./output --engine tesseract --format json",
    )
    parser.add_argument("input_dir", type=Path, help="Directory containing images")
    parser.add_argument("output_dir", type=Path, help="Directory for output files")

    # OCR Engine selection
    engine_choices = ["vision"]
    if TESSERACT_AVAILABLE:
        engine_choices.append("tesseract")
    parser.add_argument(
        "--engine",
        choices=engine_choices,
        default="vision",
        help="OCR engine to use (default: vision)",
    )

    # Tesseract-specific options
    if TESSERACT_AVAILABLE:
        parser.add_argument(
            "--lang",
            default="eng",
            help="Language code for Tesseract OCR (default: eng)",
        )
        parser.add_argument(
            "--tesseract-config",
            default="",
            help="Additional Tesseract configuration options",
        )

    parser.add_argument(
        "--format",
        choices=["json", "jsonl"],
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")
    return parser


def find_images(input_dir: Path) -> list[Path]:
    images = [
        f for f in input_dir.glob("**/*") if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
    ]
    return sorted(images)


def save_result(result, output_path: Path, format_type: str):
    data = {
        "image": result.image_path,
        "engine": result.engine,
        "success": result.success,
        "text": result.full_text,
        "labels": [{"name": label.description, "score": label.score} for label in result.labels],
        "confidence": result.confidence,
        "error": result.error,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        if format_type == "jsonl":
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
        else:
            json.dump(data, f, indent=2, ensure_ascii=False)


def create_engine(args) -> OCREngine:
    """
    Create an OCR engine based on command-line arguments.

    Args:
        args: Parsed command-line arguments

    Returns:
        OCREngine instance

    Raises:
        VisionAPIError or TesseractEngineError if engine initialization fails
    """
    if args.engine == "vision":
        return VisionAPIEngine()
    elif args.engine == "tesseract":
        if not TESSERACT_AVAILABLE:
            logger.error(
                "Tesseract engine not available. Install with: pip install pytesseract Pillow"
            )
            sys.exit(1)
        # Import here to satisfy type checker (already confirmed available above)
        from vis_cli.libs.tesseract_engine import TesseractEngine as TEngine

        return TEngine(
            lang=getattr(args, "lang", "eng"), config=getattr(args, "tesseract_config", "")
        )
    else:
        logger.error(f"Unknown engine: {args.engine}")
        sys.exit(1)


def main():
    load_dotenv()

    parser = setup_argparser()
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if not args.input_dir.is_dir():
        logger.error(f"Not a directory: {args.input_dir}")
        sys.exit(1)

    images = find_images(args.input_dir)
    if not images:
        logger.warning(f"No images found in {args.input_dir}")
        sys.exit(0)

    logger.info(f"Processing {len(images)} images (recursive)...")

    # Initialize OCR engine
    try:
        engine = create_engine(args)
        logger.info(f"Using OCR engine: {engine.name}")
    except (VisionAPIError, TesseractEngineError) as e:
        logger.error(f"Failed to initialize OCR engine: {e}")
        sys.exit(1)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    success_count = 0
    ext = ".jsonl" if args.format == "jsonl" else ".json"

    try:
        for i, img in enumerate(images, 1):
            if args.verbose:
                logger.info(f"[{i}/{len(images)}] {img.name}")

            try:
                result = engine.analyze_image(img)
                output_file = args.output_dir / f"{img.stem}{ext}"
                save_result(result, output_file, args.format)
                if result.success:
                    success_count += 1
            except (VisionAPIError, TesseractEngineError, FileNotFoundError) as e:
                logger.error(f"{img.name}: {e}")

    except KeyboardInterrupt:
        logger.info("\nInterrupted")
        sys.exit(130)

    logger.info(f"Complete: {success_count}/{len(images)} successful")
    logger.info(f"Output directory: {args.output_dir}")
    sys.exit(0 if success_count == len(images) else 1)


if __name__ == "__main__":
    main()
