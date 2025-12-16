import argparse
import json
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

from vis_cli.libs.vision_api import VisionAPIError, analyze_image_with_apikey

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}


def setup_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Batch image OCR and label extraction tool using Google Cloud Vision API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example: %(prog)s ./images ./output --format json",
    )
    parser.add_argument("input_dir", type=Path, help="Directory containing images")
    parser.add_argument("output_dir", type=Path, help="Directory for output files")
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
        "success": result.success,
        "text": result.full_text,
        "labels": [{"name": l.description, "score": l.score} for l in result.labels],
        "error": result.error,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        if format_type == "jsonl":
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
        else:
            json.dump(data, f, indent=2, ensure_ascii=False)


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

    args.output_dir.mkdir(parents=True, exist_ok=True)
    success_count = 0
    ext = ".jsonl" if args.format == "jsonl" else ".json"

    try:
        for i, img in enumerate(images, 1):
            if args.verbose:
                logger.info(f"[{i}/{len(images)}] {img.name}")

            try:
                result = analyze_image_with_apikey(img)
                output_file = args.output_dir / f"{img.stem}{ext}"
                save_result(result, output_file, args.format)
                if result.success:
                    success_count += 1
            except (VisionAPIError, FileNotFoundError) as e:
                logger.error(f"{img.name}: {e}")

    except KeyboardInterrupt:
        logger.info("\nInterrupted")
        sys.exit(130)

    logger.info(f"Complete: {success_count}/{len(images)} successful")
    logger.info(f"Output directory: {args.output_dir}")
    sys.exit(0 if success_count == len(images) else 1)


if __name__ == "__main__":
    main()
