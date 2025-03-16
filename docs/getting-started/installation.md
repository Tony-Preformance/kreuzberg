# Installation

Kreuzberg is composed of a core package and several `optional` dependencies, which users can install at their discretion.

## Kreuzberg Core Package

The Kreuzberg core package can be installed using pip with:

```shell
pip install kreuzberg
```

Kreuzberg relies on `pandoc`, which is a required system dependency. To install it, follow the instructions below:

### Ubuntu/Debian

```shell
sudo apt-get install pandoc
```

### macOS

```shell
brew install pandoc
```

### Windows

```shell
choco install -y pandoc
```

## OCR

OCR is an optional feature. Kreuzberg supports multiple OCR backends. To understand the differences between these, please read the [OCR Backends documentation](../user-guide/ocr-backends.md).

If you want to be able to extract text from images and non-searchable PDFs, you will need to install one of the following OCR backends:

### Tesseract

To install it you can follow the instructions in the [Tesseract documentation](https://tesseract-ocr.github.io/), or use one of the following commands if applicable to your system:

#### Ubuntu/Debian

```shell
sudo apt-get install tesseract-ocr
```

#### macOS

```shell
brew install tesseract
```

#### Windows

```shell
choco install -y tesseract
```

__Note__: You will also need to install language support for the languages of choice other than English. Again see the [Tesseract documentation](https://tesseract-ocr.github.io/) for your system.

#### EasyOCR OCR Backend

EasyOCR is a Python based OCR backend that has a wide language support and strong performance.

```shell
pip install "kreuzberg[easyocr]"
```

#### PaddleOCR OCRBackend

```shell
pip install "kreuzberg[paddleocr]"
```

### Chunking

Chunking is an optional feature - useful for RAG applications among others. Kreuzberg uses the excellent `semantic-text-splitter` package for chunking. To install Kreuzberg with chunking support, you can use:

```shell
pip install "kreuzberg[chunking]"
```
