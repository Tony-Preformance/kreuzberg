"""Tests for HierarchyConfig configuration."""

from __future__ import annotations

from kreuzberg import HierarchyConfig, PdfConfig


def test_hierarchy_config_default_construction() -> None:
    """HierarchyConfig should have sensible defaults."""
    config = HierarchyConfig()
    assert config.enabled is True
    assert config.k_clusters == 6
    assert config.include_bbox is True
    assert config.ocr_coverage_threshold is None


def test_hierarchy_config_custom_values() -> None:
    """HierarchyConfig should accept custom values."""
    config = HierarchyConfig(
        enabled=False,
        k_clusters=8,
        include_bbox=False,
        ocr_coverage_threshold=0.5,
    )
    assert config.enabled is False
    assert config.k_clusters == 8
    assert config.include_bbox is False
    assert config.ocr_coverage_threshold == 0.5


def test_hierarchy_config_enabled() -> None:
    """HierarchyConfig should support enabling."""
    config = HierarchyConfig(enabled=True)
    assert config.enabled is True


def test_hierarchy_config_disabled() -> None:
    """HierarchyConfig should support disabling."""
    config = HierarchyConfig(enabled=False)
    assert config.enabled is False


def test_hierarchy_config_k_clusters_small() -> None:
    """HierarchyConfig should support small k_clusters values."""
    config = HierarchyConfig(k_clusters=2)
    assert config.k_clusters == 2


def test_hierarchy_config_k_clusters_medium() -> None:
    """HierarchyConfig should support medium k_clusters values."""
    config = HierarchyConfig(k_clusters=10)
    assert config.k_clusters == 10


def test_hierarchy_config_k_clusters_large() -> None:
    """HierarchyConfig should support large k_clusters values."""
    config = HierarchyConfig(k_clusters=50)
    assert config.k_clusters == 50


def test_hierarchy_config_k_clusters_very_large() -> None:
    """HierarchyConfig should support very large k_clusters values."""
    config = HierarchyConfig(k_clusters=1000)
    assert config.k_clusters == 1000


def test_hierarchy_config_include_bbox_true() -> None:
    """HierarchyConfig should support bounding box inclusion."""
    config = HierarchyConfig(include_bbox=True)
    assert config.include_bbox is True


def test_hierarchy_config_include_bbox_false() -> None:
    """HierarchyConfig should support bounding box exclusion."""
    config = HierarchyConfig(include_bbox=False)
    assert config.include_bbox is False


def test_hierarchy_config_ocr_coverage_threshold_zero() -> None:
    """HierarchyConfig should accept zero ocr_coverage_threshold."""
    config = HierarchyConfig(ocr_coverage_threshold=0.0)
    assert config.ocr_coverage_threshold == 0.0


def test_hierarchy_config_ocr_coverage_threshold_mid_range() -> None:
    """HierarchyConfig should accept mid-range ocr_coverage_threshold."""
    config = HierarchyConfig(ocr_coverage_threshold=0.5)
    assert config.ocr_coverage_threshold == 0.5


def test_hierarchy_config_ocr_coverage_threshold_high() -> None:
    """HierarchyConfig should accept high ocr_coverage_threshold."""
    config = HierarchyConfig(ocr_coverage_threshold=0.9)
    assert config.ocr_coverage_threshold is not None
    assert abs(config.ocr_coverage_threshold - 0.9) < 0.01


def test_hierarchy_config_ocr_coverage_threshold_one() -> None:
    """HierarchyConfig should accept ocr_coverage_threshold of 1.0."""
    config = HierarchyConfig(ocr_coverage_threshold=1.0)
    assert config.ocr_coverage_threshold == 1.0


def test_hierarchy_config_ocr_coverage_threshold_none() -> None:
    """HierarchyConfig should handle None ocr_coverage_threshold."""
    config = HierarchyConfig(ocr_coverage_threshold=None)
    assert config.ocr_coverage_threshold is None


def test_hierarchy_config_in_pdf_config() -> None:
    """PdfConfig should properly nest HierarchyConfig."""
    hierarchy = HierarchyConfig(enabled=True, k_clusters=8)
    pdf = PdfConfig(hierarchy=hierarchy)
    assert pdf.hierarchy is not None
    assert pdf.hierarchy.enabled is True
    assert pdf.hierarchy.k_clusters == 8


def test_hierarchy_config_aggressive_clustering() -> None:
    """HierarchyConfig should support aggressive clustering."""
    config = HierarchyConfig(
        enabled=True,
        k_clusters=20,
        include_bbox=True,
    )
    assert config.k_clusters == 20
    assert config.include_bbox is True


def test_hierarchy_config_minimal_clustering() -> None:
    """HierarchyConfig should support minimal clustering."""
    config = HierarchyConfig(
        enabled=True,
        k_clusters=2,
        include_bbox=False,
    )
    assert config.k_clusters == 2
    assert config.include_bbox is False


def test_hierarchy_config_with_ocr_threshold() -> None:
    """HierarchyConfig should work with OCR coverage threshold."""
    config = HierarchyConfig(
        enabled=True,
        k_clusters=6,
        ocr_coverage_threshold=0.7,
    )
    assert config.ocr_coverage_threshold is not None
    assert abs(config.ocr_coverage_threshold - 0.7) < 0.01


def test_hierarchy_config_without_ocr_threshold() -> None:
    """HierarchyConfig should work without OCR coverage threshold."""
    config = HierarchyConfig(
        enabled=True,
        k_clusters=6,
        ocr_coverage_threshold=None,
    )
    assert config.ocr_coverage_threshold is None


def test_hierarchy_config_various_cluster_counts() -> None:
    """HierarchyConfig should accept various cluster counts."""
    for k in [2, 3, 4, 5, 6, 7, 8, 10, 15, 20, 50, 100]:
        config = HierarchyConfig(k_clusters=k)
        assert config.k_clusters == k


def test_hierarchy_config_various_thresholds() -> None:
    """HierarchyConfig should accept various threshold values."""
    for threshold in [0.0, 0.25, 0.5, 0.75, 1.0]:
        config = HierarchyConfig(ocr_coverage_threshold=threshold)
        assert config.ocr_coverage_threshold == threshold


def test_hierarchy_config_all_parameters() -> None:
    """HierarchyConfig should work with all parameters specified."""
    config = HierarchyConfig(
        enabled=True,
        k_clusters=8,
        include_bbox=True,
        ocr_coverage_threshold=0.6,
    )

    assert config.enabled is True
    assert config.k_clusters == 8
    assert config.include_bbox is True
    assert config.ocr_coverage_threshold is not None
    assert abs(config.ocr_coverage_threshold - 0.6) < 0.01


def test_hierarchy_config_realistic_document_scenario() -> None:
    """HierarchyConfig should support realistic document hierarchy scenario."""
    config = HierarchyConfig(
        enabled=True,
        k_clusters=6,
        include_bbox=True,
        ocr_coverage_threshold=0.5,
    )

    assert config.enabled is True
    assert config.k_clusters == 6
    assert config.include_bbox is True
