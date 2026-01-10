# Go

<div align="center" style="display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; margin: 20px 0;">
  <!-- Language Bindings -->
  <a href="https://crates.io/crates/kreuzberg">
    <img src="https://img.shields.io/crates/v/kreuzberg?label=Rust&color=007ec6" alt="Rust">
  </a>
  <a href="https://hex.pm/packages/kreuzberg">
    <img src="https://img.shields.io/hexpm/v/kreuzberg?label=Elixir&color=007ec6" alt="Elixir">
  </a>
  <a href="https://pypi.org/project/kreuzberg/">
    <img src="https://img.shields.io/pypi/v/kreuzberg?label=Python&color=007ec6" alt="Python">
  </a>
  <a href="https://www.npmjs.com/package/@kreuzberg/node">
    <img src="https://img.shields.io/npm/v/@kreuzberg/node?label=Node.js&color=007ec6" alt="Node.js">
  </a>
  <a href="https://www.npmjs.com/package/@kreuzberg/wasm">
    <img src="https://img.shields.io/npm/v/@kreuzberg/wasm?label=WASM&color=007ec6" alt="WASM">
  </a>

  <a href="https://central.sonatype.com/artifact/dev.kreuzberg/kreuzberg">
    <img src="https://img.shields.io/maven-central/v/dev.kreuzberg/kreuzberg?label=Java&color=007ec6" alt="Java">
  </a>
  <a href="https://github.com/kreuzberg-dev/kreuzberg/releases">
    <img src="https://img.shields.io/github/v/tag/kreuzberg-dev/kreuzberg?label=Go&color=007ec6&filter=v4.0.0" alt="Go">
  </a>
  <a href="https://www.nuget.org/packages/Kreuzberg/">
    <img src="https://img.shields.io/nuget/v/Kreuzberg?label=C%23&color=007ec6" alt="C#">
  </a>
  <a href="https://packagist.org/packages/kreuzberg/kreuzberg">
    <img src="https://img.shields.io/packagist/v/kreuzberg/kreuzberg?label=PHP&color=007ec6" alt="PHP">
  </a>
  <a href="https://rubygems.org/gems/kreuzberg">
    <img src="https://img.shields.io/gem/v/kreuzberg?label=Ruby&color=007ec6" alt="Ruby">
  </a>

  <!-- Project Info -->
  <a href="https://github.com/kreuzberg-dev/kreuzberg/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License">
  </a>
  <a href="https://docs.kreuzberg.dev">
    <img src="https://img.shields.io/badge/docs-kreuzberg.dev-blue" alt="Documentation">
  </a>
</div>

<img width="1128" height="191" alt="Banner2" src="https://github.com/user-attachments/assets/419fc06c-8313-4324-b159-4b4d3cfce5c0" />

<div align="center" style="margin-top: 20px;">
  <a href="https://discord.gg/pXxagNK2zN">
      <img height="22" src="https://img.shields.io/badge/Discord-Join%20our%20community-7289da?logo=discord&logoColor=white" alt="Discord">
  </a>
</div>


Extract text, tables, images, and metadata from 56 file formats including PDF, Office documents, and images. Go bindings with context-aware async support, idiomatic Go API, and CGO-based native performance.


## Installation

### Package Installation




Install with go get:

```bash
go get github.com/kreuzberg-dev/kreuzberg/packages/go/v4
```

For more details on FFI setup and native library linking, see the [Go Setup Guide](https://kreuzberg.dev/bindings/go/setup/).




### System Requirements

- **Go 1.19+** required
- Optional: [ONNX Runtime](https://github.com/microsoft/onnxruntime/releases) version 1.22.x for embeddings support
- Optional: [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) for OCR functionality



## Quick Start

### Basic Extraction

Extract text, metadata, and structure from any supported document format:

```go
package main

import (
	"fmt"
	"log"

	"github.com/kreuzberg-dev/kreuzberg/packages/go/v4"
)

func main() {
	result, err := kreuzberg.ExtractFileSync("document.pdf", nil)
	if err != nil {
		log.Fatalf("extract failed: %v", err)
	}

	fmt.Println("Content:")
	fmt.Println(result.Content)

	fmt.Println("\nMetadata:")
	if result.Metadata != nil {
		fmt.Printf("Title: %v\n", result.Metadata["title"])
		fmt.Printf("Author: %v\n", result.Metadata["author"])
	}

	fmt.Printf("\nTables found: %d\n", len(result.Tables))
	fmt.Printf("Images found: %d\n", len(result.Images))
}
```


### Common Use Cases

#### Extract with Custom Configuration

Most use cases benefit from configuration to control extraction behavior:


**With OCR (for scanned documents):**

```go
package main

import (
	"fmt"
	"log"

	"github.com/kreuzberg-dev/kreuzberg/packages/go/v4"
)

func main() {
	result, err := kreuzberg.ExtractFileSync("document.pdf", nil)
	if err != nil {
		log.Fatalf("extract failed: %v", err)
	}

	fmt.Println("Extracted content:")
	if len(result.Content) > 200 {
		fmt.Println(result.Content[:200])
	} else {
		fmt.Println(result.Content)
	}
}
```




#### Table Extraction


See [Table Extraction Guide](https://kreuzberg.dev/features/table-extraction/) for detailed examples.



#### Processing Multiple Files


```go
package main

import (
	"fmt"
	"log"

	"github.com/kreuzberg-dev/kreuzberg/packages/go/v4"
)

func main() {
	backend := "tesseract"
	language := "eng"

	ocrConfig := &kreuzberg.OCRConfig{
		Backend:  &backend,
		Language: &language,
	}

	config := &kreuzberg.ExtractionConfig{
		OCR: ocrConfig,
	}

	result, err := kreuzberg.ExtractFileSync("scanned.pdf", config)
	if err != nil {
		log.Fatalf("extract failed: %v", err)
	}

	fmt.Println("Extracted text from scanned document:")
	fmt.Println(result.Content)
	fmt.Println("Used OCR backend: tesseract")
}
```





#### Async Processing

For non-blocking document processing:

```go
package main

import (
	"fmt"
	"log"

	"github.com/kreuzberg-dev/kreuzberg/packages/go/v4"
)

func main() {
	useCache := true
	enableQP := true

	config := &kreuzberg.ExtractionConfig{
		UseCache:                &useCache,
		EnableQualityProcessing: &enableQP,
	}

	result, err := kreuzberg.ExtractFileSync("contract.pdf", config)
	if err != nil {
		log.Fatalf("extract failed: %v", err)
	}

	fmt.Printf("Extracted %d characters\n", len(result.Content))
	fmt.Printf("Quality score: %v\n", result.Metadata["quality_score"])
	fmt.Printf("Processing time: %vms\n", result.Metadata["processing_time"])
}
```






### Next Steps

- **[Installation Guide](https://kreuzberg.dev/getting-started/installation/)** - Platform-specific setup
- **[API Documentation](https://kreuzberg.dev/api/)** - Complete API reference
- **[Examples & Guides](https://kreuzberg.dev/guides/)** - Full code examples and usage guides
- **[Configuration Guide](https://kreuzberg.dev/configuration/)** - Advanced configuration options
- **[Troubleshooting](https://kreuzberg.dev/troubleshooting/)** - Common issues and solutions



## Features

### Supported File Formats (56+)

56 file formats across 8 major categories with intelligent format detection and comprehensive metadata extraction.

#### Office Documents

| Category | Formats | Capabilities |
|----------|---------|--------------|
| **Word Processing** | `.docx`, `.odt` | Full text, tables, images, metadata, styles |
| **Spreadsheets** | `.xlsx`, `.xlsm`, `.xlsb`, `.xls`, `.xla`, `.xlam`, `.xltm`, `.ods` | Sheet data, formulas, cell metadata, charts |
| **Presentations** | `.pptx`, `.ppt`, `.ppsx` | Slides, speaker notes, images, metadata |
| **PDF** | `.pdf` | Text, tables, images, metadata, OCR support |
| **eBooks** | `.epub`, `.fb2` | Chapters, metadata, embedded resources |

#### Images (OCR-Enabled)

| Category | Formats | Features |
|----------|---------|----------|
| **Raster** | `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.bmp`, `.tiff`, `.tif` | OCR, table detection, EXIF metadata, dimensions, color space |
| **Advanced** | `.jp2`, `.jpx`, `.jpm`, `.mj2`, `.pnm`, `.pbm`, `.pgm`, `.ppm` | OCR, table detection, format-specific metadata |
| **Vector** | `.svg` | DOM parsing, embedded text, graphics metadata |

#### Web & Data

| Category | Formats | Features |
|----------|---------|----------|
| **Markup** | `.html`, `.htm`, `.xhtml`, `.xml`, `.svg` | DOM parsing, metadata (Open Graph, Twitter Card), link extraction |
| **Structured Data** | `.json`, `.yaml`, `.yml`, `.toml`, `.csv`, `.tsv` | Schema detection, nested structures, validation |
| **Text & Markdown** | `.txt`, `.md`, `.markdown`, `.rst`, `.org`, `.rtf` | CommonMark, GFM, reStructuredText, Org Mode |

#### Email & Archives

| Category | Formats | Features |
|----------|---------|----------|
| **Email** | `.eml`, `.msg` | Headers, body (HTML/plain), attachments, threading |
| **Archives** | `.zip`, `.tar`, `.tgz`, `.gz`, `.7z` | File listing, nested archives, metadata |

#### Academic & Scientific

| Category | Formats | Features |
|----------|---------|----------|
| **Citations** | `.bib`, `.biblatex`, `.ris`, `.enw`, `.csl` | Bibliography parsing, citation extraction |
| **Scientific** | `.tex`, `.latex`, `.typst`, `.jats`, `.ipynb`, `.docbook` | LaTeX, Jupyter notebooks, PubMed JATS |
| **Documentation** | `.opml`, `.pod`, `.mdoc`, `.troff` | Technical documentation formats |

**[Complete Format Reference](https://kreuzberg.dev/reference/formats/)**

### Key Capabilities

- **Text Extraction** - Extract all text content with position and formatting information
- **Metadata Extraction** - Retrieve document properties, creation date, author, etc.
- **Table Extraction** - Parse tables with structure and cell content preservation
- **Image Extraction** - Extract embedded images and render page previews
- **OCR Support** - Integrate multiple OCR backends for scanned documents

- **Async/Await** - Non-blocking document processing with concurrent operations


- **Plugin System** - Extensible post-processing for custom text transformation


- **Batch Processing** - Efficiently process multiple documents in parallel
- **Memory Efficient** - Stream large files without loading entirely into memory
- **Language Detection** - Detect and support multiple languages in documents
- **Configuration** - Fine-grained control over extraction behavior

### Performance Characteristics

| Format | Speed | Memory | Notes |
|--------|-------|--------|-------|
| **PDF (text)** | 10-100 MB/s | ~50MB per doc | Fastest extraction |
| **Office docs** | 20-200 MB/s | ~100MB per doc | DOCX, XLSX, PPTX |
| **Images (OCR)** | 1-5 MB/s | Variable | Depends on OCR backend |
| **Archives** | 5-50 MB/s | ~200MB per doc | ZIP, TAR, etc. |
| **Web formats** | 50-200 MB/s | Streaming | HTML, XML, JSON |



## OCR Support

Kreuzberg supports multiple OCR backends for extracting text from scanned documents and images:


- **Tesseract**


### OCR Configuration Example

```go
package main

import (
	"fmt"
	"log"

	"github.com/kreuzberg-dev/kreuzberg/packages/go/v4"
)

func main() {
	result, err := kreuzberg.ExtractFileSync("document.pdf", nil)
	if err != nil {
		log.Fatalf("extract failed: %v", err)
	}

	fmt.Println("Extracted content:")
	if len(result.Content) > 200 {
		fmt.Println(result.Content[:200])
	} else {
		fmt.Println(result.Content)
	}
}
```




## Async Support

This binding provides full async/await support for non-blocking document processing:

```go
package main

import (
	"fmt"
	"log"

	"github.com/kreuzberg-dev/kreuzberg/packages/go/v4"
)

func main() {
	useCache := true
	enableQP := true

	config := &kreuzberg.ExtractionConfig{
		UseCache:                &useCache,
		EnableQualityProcessing: &enableQP,
	}

	result, err := kreuzberg.ExtractFileSync("contract.pdf", config)
	if err != nil {
		log.Fatalf("extract failed: %v", err)
	}

	fmt.Printf("Extracted %d characters\n", len(result.Content))
	fmt.Printf("Quality score: %v\n", result.Metadata["quality_score"])
	fmt.Printf("Processing time: %vms\n", result.Metadata["processing_time"])
}
```




## Plugin System

Kreuzberg supports extensible post-processing plugins for custom text transformation and filtering.

For detailed plugin documentation, visit [Plugin System Guide](https://kreuzberg.dev/plugins/).






## Batch Processing

Process multiple documents efficiently:

```go
package main

import (
	"fmt"
	"log"

	"github.com/kreuzberg-dev/kreuzberg/packages/go/v4"
)

func main() {
	backend := "tesseract"
	language := "eng"

	ocrConfig := &kreuzberg.OCRConfig{
		Backend:  &backend,
		Language: &language,
	}

	config := &kreuzberg.ExtractionConfig{
		OCR: ocrConfig,
	}

	result, err := kreuzberg.ExtractFileSync("scanned.pdf", config)
	if err != nil {
		log.Fatalf("extract failed: %v", err)
	}

	fmt.Println("Extracted text from scanned document:")
	fmt.Println(result.Content)
	fmt.Println("Used OCR backend: tesseract")
}
```




## Configuration

For advanced configuration options including language detection, table extraction, OCR settings, and more:

**[Configuration Guide](https://kreuzberg.dev/configuration/)**

## Documentation

- **[Official Documentation](https://kreuzberg.dev/)**
- **[API Reference](https://kreuzberg.dev/reference/api-go/)**
- **[Examples & Guides](https://kreuzberg.dev/guides/)**

## Troubleshooting

For common issues and solutions, visit [Troubleshooting Guide](https://kreuzberg.dev/troubleshooting/).

## Contributing

Contributions are welcome! See [Contributing Guide](https://github.com/kreuzberg-dev/kreuzberg/blob/main/CONTRIBUTING.md).

## License

MIT License - see LICENSE file for details.

## Support

- **Discord Community**: [Join our Discord](https://discord.gg/pXxagNK2zN)
- **GitHub Issues**: [Report bugs](https://github.com/kreuzberg-dev/kreuzberg/issues)
- **Discussions**: [Ask questions](https://github.com/kreuzberg-dev/kreuzberg/discussions)
