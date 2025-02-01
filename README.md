# Kreuzberg

Kreuzberg is a library for simplified text extraction from PDF files. It's meant to offer simple, hassle free text
extraction.

Why?

I am building, like many do now, a RAG focused service. I have text extraction needs.
There are quite a lot of commercial options out there, and several open-source + paid options.
But I wanted something simple, which does not require expansive round-trips to an external API.
Furthermore, I wanted something that is easy to run locally and isn't very heavy / requires a GPU.

Hence, this library.

## Features

- Extract text from PDFs, images, office documents and more (see supported formats below)
- Use modern Python with async (via `anyio`) and proper type hints
- Extensive error handling for easy debugging

## Installation

1. Begin by installing the python package:

   ```shell

   pip install kreuzberg

   ```

2. Install the system dependencies:

- [pandoc](https://pandoc.org/installing.html) (non-pdf text extraction, GPL v2.0 licensed but used via CLI only)
- [tesseract-ocr](https://tesseract-ocr.github.io/) (for image/PDF OCR, Apache License)

## Supported File Types

Kreuzberg supports a wide range of file formats:

### Document Formats

- PDF (`.pdf`) - both searchable and scanned documents
- Word Documents (`.docx`)
- OpenDocument Text (`.odt`)
- Rich Text Format (`.rtf`)

### Image Formats

- JPEG, JPG (`.jpg`, `.jpeg`, `.pjpeg`)
- PNG (`.png`)
- TIFF (`.tiff`, `.tif`)
- BMP (`.bmp`)
- GIF (`.gif`)
- WebP (`.webp`)
- JPEG 2000 (`.jp2`, `.jpx`, `.jpm`, `.mj2`)
- Portable Anymap (`.pnm`)
- Portable Bitmap (`.pbm`)
- Portable Graymap (`.pgm`)
- Portable Pixmap (`.ppm`)

#### Text and Markup Formats

- Plain Text (`.txt`)
- Markdown (`.md`)
- reStructuredText (`.rst`)
- LaTeX (`.tex`)

#### Data Formats

- Comma-Separated Values (`.csv`)
- Tab-Separated Values (`.tsv`)

All formats support text extraction, with different processing methods:

- PDFs are processed using pdfium2 for searchable PDFs and Tesseract OCR for scanned documents
- Images are processed using Tesseract OCR
- Office documents and other formats are processed using Pandoc
- Plain text files are read directly with appropriate encoding detection

## Usage

Kreuzberg exports two async functions:

- Extract text from a file (string path or `pathlib.Path`) using `extract_file()`
- Extract text from a byte-string using `extract_bytes()`

Note - both of these functions are async and therefore should be used in an async context.

### Extract from File

```python
from pathlib import Path
from kreuzberg import extract_file


# Extract text from a PDF file
async def extract_pdf():
    result = await extract_file("document.pdf")
    print(f"Extracted text: {result.content}")
    print(f"Output mime type: {result.mime_type}")


# Extract text from an image
async def extract_image():
    result = await extract_file("scan.png")
    print(f"Extracted text: {result.content}")


# or use Path

async def extract_pdf():
    result = await extract_file(Path("document.pdf"))
    print(f"Extracted text: {result.content}")
    print(f"Output mime type: {result.mime_type}")
```

### Extract from Bytes

```python
from kreuzberg import extract_bytes


# Extract text from PDF bytes
async def process_uploaded_pdf(pdf_content: bytes):
    result = await extract_bytes(pdf_content, mime_type="application/pdf")
    return result.content


# Extract text from image bytes
async def process_uploaded_image(image_content: bytes):
    result = await extract_bytes(image_content, mime_type="image/jpeg")
    return result.content
```

### Forcing OCR

When extracting a PDF file or bytes, you might want to force OCR - for example, if the PDF includes images that have text that should be extracted etc.
You can do this by passing `force_ocr=True`:

```python
from kreuzberg import extract_bytes


# Extract text from PDF bytes and force OCR
async def process_uploaded_pdf(pdf_content: bytes):
    result = await extract_bytes(pdf_content, mime_type="application/pdf", force_ocr=True)
    return result.content
```

### Error Handling

Kreuzberg raises two exception types:

#### ValidationError

Raised when there are issues with input validation:

- Unsupported mime types
- Undetectable mime types
- Path doesn't point at an exist file

#### ParsingError

Raised when there are issues during the text extraction process:

- PDF parsing failures
- OCR errors
- Pandoc conversion errors

```python
from kreuzberg import extract_file
from kreuzberg.exceptions import ValidationError, ParsingError


async def safe_extract():
    try:
        result = await extract_file("document.doc")
        return result.content
    except ValidationError as e:
        print(f"Validation error: {e.message}")
        print(f"Context: {e.context}")
    except ParsingError as e:
        print(f"Parsing error: {e.message}")
        print(f"Context: {e.context}")  # Contains detailed error information
```

Both error types include helpful context information for debugging:

```python
try:
    result = await extract_file("scanned.pdf")
except ParsingError as e:
# e.context might contain:
# {
#    "file_path": "scanned.pdf",
#    "error": "Tesseract OCR failed: Unable to process image"
# }
```

### ExtractionResult

All extraction functions return an ExtractionResult named tuple containing:

- `content`: The extracted text as a string
- `mime_type`: The mime type of the output (either "text/plain" or, if pandoc is used- "text/markdown")

```python
from kreuzberg import ExtractionResult


async def process_document(path: str) -> str:
    result: ExtractionResult = await extract_file(path)
    return result.content


# or access the result as tuple

async def process_document(path: str) -> str:
    content, mime_type = await extract_file(path)
    # do something with mime_type
    return content
```

## Contribution

This library is open to contribution. Feel free to open issues or submit PRs. Its better to discuss issues before
submitting PRs to avoid disappointment.

### Local Development

1. Clone the repo
2. Install the system dependencies
3. Install the full dependencies with `uv sync`
4. Install the pre-commit hooks with:
   ```shell
   pre-commit install && pre-commit install --hook-type commit-msg
   ```
5. Make your changes and submit a PR

## License

This library uses the MIT license.
