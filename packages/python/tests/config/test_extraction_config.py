"""Tests for ExtractionConfig configuration."""

from __future__ import annotations

import pytest

from kreuzberg import (
    ChunkingConfig,
    ExtractionConfig,
    ImageExtractionConfig,
    KeywordConfig,
    LanguageDetectionConfig,
    OcrConfig,
    PageConfig,
    PdfConfig,
    PostProcessorConfig,
    TokenReductionConfig,
)


def test_extraction_config_default_construction() -> None:
    """ExtractionConfig should have sensible defaults."""
    config = ExtractionConfig()
    assert config.use_cache is True
    assert config.enable_quality_processing is True
    assert config.ocr is None
    assert config.force_ocr is False
    assert config.chunking is None
    assert config.images is None
    assert config.pdf_options is None
    assert config.token_reduction is None
    assert config.language_detection is None
    assert config.keywords is None
    assert config.postprocessor is None
    assert config.max_concurrent_extractions is None
    assert config.html_options is None
    assert config.pages is None


def test_extraction_config_custom_values() -> None:
    """ExtractionConfig should accept custom values."""
    config = ExtractionConfig(
        use_cache=False,
        enable_quality_processing=False,
        force_ocr=True,
        max_concurrent_extractions=8,
    )
    assert config.use_cache is False
    assert config.enable_quality_processing is False
    assert config.force_ocr is True
    assert config.max_concurrent_extractions == 8


def test_extraction_config_with_ocr() -> None:
    """ExtractionConfig should properly nest OcrConfig."""
    ocr = OcrConfig(backend="tesseract", language="eng")
    config = ExtractionConfig(ocr=ocr)
    assert config.ocr is not None
    assert config.ocr.backend == "tesseract"
    assert config.ocr.language == "eng"


def test_extraction_config_with_chunking() -> None:
    """ExtractionConfig should properly nest ChunkingConfig."""
    chunking = ChunkingConfig(max_chars=512, max_overlap=100)
    config = ExtractionConfig(chunking=chunking)
    assert config.chunking is not None
    assert config.chunking.max_chars == 512
    assert config.chunking.max_overlap == 100


def test_extraction_config_with_images() -> None:
    """ExtractionConfig should properly nest ImageExtractionConfig."""
    images = ImageExtractionConfig(extract_images=True, target_dpi=300)
    config = ExtractionConfig(images=images)
    assert config.images is not None
    assert config.images.extract_images is True
    assert config.images.target_dpi == 300


def test_extraction_config_with_pdf_options() -> None:
    """ExtractionConfig should properly nest PdfConfig."""
    pdf_opts = PdfConfig(extract_images=True, extract_metadata=True)
    config = ExtractionConfig(pdf_options=pdf_opts)
    assert config.pdf_options is not None
    assert config.pdf_options.extract_images is True
    assert config.pdf_options.extract_metadata is True


def test_extraction_config_with_language_detection() -> None:
    """ExtractionConfig should properly nest LanguageDetectionConfig."""
    lang_detect = LanguageDetectionConfig(enabled=True, min_confidence=0.9)
    config = ExtractionConfig(language_detection=lang_detect)
    assert config.language_detection is not None
    assert config.language_detection.enabled is True
    assert config.language_detection.min_confidence == 0.9


def test_extraction_config_with_keywords() -> None:
    """ExtractionConfig should properly nest KeywordConfig."""
    keywords = KeywordConfig(max_keywords=20)
    config = ExtractionConfig(keywords=keywords)
    assert config.keywords is not None
    assert config.keywords.max_keywords == 20


def test_extraction_config_with_token_reduction() -> None:
    """ExtractionConfig should properly nest TokenReductionConfig."""
    token_reduction = TokenReductionConfig(mode="moderate")
    config = ExtractionConfig(token_reduction=token_reduction)
    assert config.token_reduction is not None
    assert config.token_reduction.mode == "moderate"


def test_extraction_config_with_page_config() -> None:
    """ExtractionConfig should properly nest PageConfig."""
    pages = PageConfig(extract_pages=True)
    config = ExtractionConfig(pages=pages)
    assert config.pages is not None
    assert config.pages.extract_pages is True


def test_extraction_config_with_postprocessor() -> None:
    """ExtractionConfig should properly nest PostProcessorConfig."""
    postproc = PostProcessorConfig(enabled=True)
    config = ExtractionConfig(postprocessor=postproc)
    assert config.postprocessor is not None
    assert config.postprocessor.enabled is True


def test_extraction_config_html_options_valid() -> None:
    """ExtractionConfig should accept valid HTML options."""
    options = {
        "extract_metadata": True,
        "wrap": True,
        "wrap_width": 80,
        "heading_style": "atx",
    }
    config = ExtractionConfig(html_options=options)
    assert config.html_options == options


def test_extraction_config_html_options_invalid_heading() -> None:
    """ExtractionConfig should reject invalid heading_style."""
    with pytest.raises(ValueError, match="heading_style"):
        ExtractionConfig(html_options={"heading_style": "invalid"})


def test_extraction_config_none_ocr() -> None:
    """ExtractionConfig should handle None OCR appropriately."""
    config = ExtractionConfig(ocr=None)
    assert config.ocr is None


def test_extraction_config_none_chunking() -> None:
    """ExtractionConfig should handle None chunking appropriately."""
    config = ExtractionConfig(chunking=None)
    assert config.chunking is None


def test_extraction_config_edge_case_max_concurrent_zero() -> None:
    """ExtractionConfig should accept zero max_concurrent_extractions."""
    config = ExtractionConfig(max_concurrent_extractions=0)
    assert config.max_concurrent_extractions == 0


def test_extraction_config_edge_case_max_concurrent_large() -> None:
    """ExtractionConfig should accept large max_concurrent_extractions."""
    config = ExtractionConfig(max_concurrent_extractions=1000)
    assert config.max_concurrent_extractions == 1000


def test_extraction_config_from_file_not_found() -> None:
    """ExtractionConfig.from_file should raise for missing files."""
    with pytest.raises((FileNotFoundError, OSError, RuntimeError, ValueError)):
        ExtractionConfig.from_file("/nonexistent/file.toml")


def test_extraction_config_all_options_together() -> None:
    """ExtractionConfig should properly nest all sub-configs together."""
    config = ExtractionConfig(
        use_cache=True,
        enable_quality_processing=False,
        ocr=OcrConfig(backend="tesseract"),
        force_ocr=True,
        chunking=ChunkingConfig(max_chars=1024),
        images=ImageExtractionConfig(extract_images=True),
        pdf_options=PdfConfig(extract_metadata=True),
        token_reduction=TokenReductionConfig(mode="moderate"),
        language_detection=LanguageDetectionConfig(enabled=True),
        keywords=KeywordConfig(max_keywords=15),
        pages=PageConfig(extract_pages=True),
        postprocessor=PostProcessorConfig(enabled=True),
        max_concurrent_extractions=4,
    )

    assert config.use_cache is True
    assert config.enable_quality_processing is False
    assert config.ocr is not None
    assert config.force_ocr is True
    assert config.chunking is not None
    assert config.images is not None
    assert config.pdf_options is not None
    assert config.token_reduction is not None
    assert config.language_detection is not None
    assert config.keywords is not None
    assert config.pages is not None
    assert config.postprocessor is not None
    assert config.max_concurrent_extractions == 4
