<div align="center">

  <h1>vis-cli</h1>

  <p>
    Batch image OCR and label extraction tool with multiple OCR engine support
  </p>

</div>

<!-- Table of Contents -->

# :notebook_with_decorative_cover: Table of Contents

- [About the Project](#star2-about-the-project)
  - [OCR Engines](#ocr-engines)
  - [Environment Variables](#key-environment-variables)
- [Getting Started](#toolbox-getting-started)
  - [Prerequisites](#bangbang-prerequisites)
  - [Installation](#gear-installation)
  - [Usage](#eyes-usage)
  - [Engine Comparison](#engine-comparison)
  - [Programmatic Usage](#programmatic-usage)
- [Development](#hammer_and_wrench-development)
  - [Scripts](#rocket-scripts)
- [Contributing](#wave-contributing)
  - [Code of Conduct](#scroll-code-of-conduct)
- [License](#warning-license)
- [Contact](#handshake-contact)

<!-- About the Project -->

## :star2: About the Project

A command-line tool for batch extracting text (OCR) and labels from images using
multiple OCR engines. It recursively scans directories, processes all images,
and outputs structured JSON or JSONL files for easy analysis and integration.

**Supported OCR Engines:**

- **Google Cloud Vision API** - High-accuracy commercial OCR with semantic label
  detection
- **Tesseract OCR** - Free, open-source OCR that works offline

**Features:**

- **Text Detection (OCR)** - Extract text from images
- **Label Detection** - Identify objects, concepts, and categories in images
- **Multiple Engines** - Choose between Vision API or Tesseract
- **Batch Processing** - Process entire directories recursively
- **Structured Output** - JSON/JSONL format for easy parsing
- **Partial Results** - Returns available data even if some features fail
- **Unified Interface** - Same result structure across all engines

### OCR Engines

#### 1. Google Cloud Vision API (`vision`)

- ✅ High accuracy commercial OCR service
- ✅ Semantic label detection (objects, concepts, categories)
- ✅ 50+ languages supported
- ⚠️ Requires API key and internet connection
- ⚠️ Paid service (API calls)

#### 2. Tesseract OCR (`tesseract`)

- ✅ Free and open-source
- ✅ Works completely offline
- ✅ 100+ languages supported
- ✅ No API key required
- ⚠️ Requires system installation
- ⚠️ Basic label detection only

Both engines return the same `OCRResult` structure with:

- `image_path`: Path to the processed image
- `engine`: Which engine was used ("vision_api" or "tesseract")
- `full_text`: Extracted text content
- `labels`: List of labels/tags with confidence scores
- `confidence`: Overall confidence score (0-1 scale)
- `error`: Error message if processing failed

<!-- Env Variables -->

### :key: Environment Variables

**For Google Cloud Vision API:**

To use the Vision API engine, you will need to add the following environment
variables to your `.env` file:

- `API_KEY`: Your Google Cloud Vision API key.
- `BASE_URL` (optional): Base URL for the Vision API (default is
  `https://vision.googleapis.com/v1/images:annotate`).

**For Tesseract OCR:**

No environment variables required. Just install Tesseract on your system:

- Ubuntu/Debian: `sudo apt-get install tesseract-ocr`
- macOS: `brew install tesseract`
- Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki

#### How to Get Google Vision API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **Cloud Vision API**:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Cloud Vision API"
   - Click "Enable"
4. Create an API key:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "API Key"
   - Copy your API key
5. (Optional) Restrict your API key:
   - Click on your API key to edit
   - Under "API restrictions", select "Cloud Vision API"
   - Save changes

Create a `.env` file in the project root:

```env
# .env
API_KEY=your_google_vision_api_key_here
BASE_URL=https://vision.googleapis.com/v1/images:annotate
```

You can also check out the file `.env.example` to see all required environment
variables.

<!-- Getting Started -->

## :toolbox: Getting Started

<!-- Prerequisites -->

### :bangbang: Prerequisites

- **Python**: Version 3.12 or later
- **uv**: Modern Python package manager (recommended) or pip

**Install uv:**

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or via pip
pip install uv
```

<!-- Installation -->

### :gear: Installation

Clone the project:

```bash
git clone https://github.com/DuckyMomo20012/vis-cli.git
```

Go to the project directory:

```bash
cd vis-cli
```

Install dependencies:

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -e ".[dev]"
```

<!-- Usage -->

### :eyes: Usage

#### Command-Line Interface

Process images in a directory:

```bash
# Using Google Vision API (default)
vis-cli ./images ./output --engine vision

# Using Tesseract OCR
vis-cli ./images ./output --engine tesseract

# Tesseract with specific language(s)
vis-cli ./images ./output --engine tesseract --lang eng+fra

# Tesseract with custom configuration
vis-cli ./images ./output --engine tesseract --tesseract-config "--psm 6"

# JSONL output (single line per file)
vis-cli ./images ./output --engine tesseract --format jsonl

# With verbose logging
vis-cli ./images ./output --engine vision --verbose
```

**Note:** The tool always scans recursively through all subdirectories.

**Output structure:**

```
input/
  ├── photo1.jpg
  └── subdir/
      └── photo2.png

output/
  ├── photo1.json      # Results for photo1.jpg
  └── photo2.json      # Results for photo2.png
```

**Output format (unified across all engines):**

```json
{
  "image": "/path/to/photo.jpg",
  "engine": "tesseract",
  "success": true,
  "text": "Detected text content",
  "labels": [{ "name": "text", "score": 0.88 }],
  "confidence": 0.88,
  "error": null
}
```

### Engine Comparison

| Feature           | Vision API        | Tesseract             |
| ----------------- | ----------------- | --------------------- |
| Cost              | Paid (API calls)  | Free                  |
| Internet          | Required          | Not required          |
| Setup             | API key only      | System installation   |
| Accuracy          | Very high         | Good                  |
| Label Detection   | Yes (semantic)    | Basic (text presence) |
| Languages         | 50+ languages     | 100+ languages        |
| Speed             | Network dependent | Fast (local)          |
| Confidence Scores | Per label         | Per word, averaged    |

**Notes:**

- **Label Detection**: Vision API provides semantic labels (e.g., "car",
  "building"), while Tesseract only provides a basic "text" label indicating
  text was found.
- **Confidence Scores**: Both engines normalize confidence to 0-1 scale for
  consistency.
- **Error Handling**: Both engines return partial results when possible, with
  error details in the `error` field.

### Programmatic Usage

You can use the engines directly in your Python code:

```python
from vis_cli.libs.vision_api import VisionAPIEngine
from vis_cli.libs.tesseract_engine import TesseractEngine

# Vision API
vision_engine = VisionAPIEngine(api_key="your-key")
result = vision_engine.analyze_image("image.jpg")

# Tesseract
tesseract_engine = TesseractEngine(lang="eng")
result = tesseract_engine.analyze_image("image.jpg")

# Both return OCRResult with same structure
print(f"Engine: {result.engine}")
print(f"Text: {result.full_text}")
print(f"Confidence: {result.confidence}")
print(f"Labels: {result.labels}")
print(f"Success: {result.success}")
```

**Quick Demo:**

Test both engines on the same image:

```bash
python demo.py path/to/image.jpg
```

#### Architecture

The project uses an abstract base class pattern for extensibility:

```
OCREngine (Abstract Base Class)
├── VisionAPIEngine (Google Cloud Vision)
└── TesseractEngine (Tesseract OCR)
```

All engines implement the same interface and return a unified `OCRResult`. This
design makes it easy to add new OCR engines (AWS Textract, Azure Computer
Vision, EasyOCR, etc.) by simply implementing the `OCREngine` interface.

<!-- Development -->

## :hammer_and_wrench: Development

### :test_tube: Mock API for Testing

The project includes a Mockoon mock server for testing without consuming Google
Cloud Vision API quota:

```bash
# Start mock API server
docker compose up -d

# The mock API will be available at http://localhost:3000
```

Update your `.env` to use the mock server:

```env
API_KEY=mock_api_key
BASE_URL=http://localhost:3000/v1/images:annotate
```

Stop the mock server:

```bash
docker compose down
```

### :rocket: Scripts

The project uses `make` commands for common development tasks:

```bash
# Install dependencies (including dev)
make install

# Format code with ruff
make format

# Lint code
make lint

# Check formatting and linting (CI-friendly)
make check

# Auto-fix issues and format
make fix

# Run tests
make test

# Clean cache files
make clean
```

**Alternative without make:**

```bash
# Install
uv sync

# Format
ruff format .

# Lint
ruff check .

# Fix
ruff check --fix .

# Test
pytest -v
```

<!-- Contributing -->

## :wave: Contributing

Contributions are always welcome!

Please read the [contribution guidelines](./CONTRIBUTING.md).

<!-- Code of Conduct -->

### :scroll: Code of Conduct

Please read the [Code of Conduct](./CODE_OF_CONDUCT.md).

<!-- License -->

## :warning: License

This project is licensed under the **Creative Commons
Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)**
License.

[![License: CC BY-NC-SA 4.0](https://licensebuttons.net/l/by-nc-sa/4.0/88x31.png)](https://creativecommons.org/licenses/by-nc-sa/4.0/).

See the **[LICENSE.md](./LICENSE.md)** file for full details.

<!-- Contact -->

## :handshake: Contact

Duong Vinh - [@duckymomo20012](https://twitter.com/duckymomo20012) -
tienvinh.duong4@gmail.com

Project Link:
[https://github.com/DuckyMomo20012/vis-cli](https://github.com/DuckyMomo20012/vis-cli).
