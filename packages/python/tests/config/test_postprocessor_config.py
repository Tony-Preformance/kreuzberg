"""Tests for PostProcessorConfig configuration."""

from __future__ import annotations

from kreuzberg import ExtractionConfig, PostProcessorConfig


def test_postprocessor_config_default_construction() -> None:
    """PostProcessorConfig should have sensible defaults."""
    config = PostProcessorConfig()
    assert config.enabled is True
    assert config.enabled_processors is None
    assert config.disabled_processors is None


def test_postprocessor_config_custom_values() -> None:
    """PostProcessorConfig should accept custom values."""
    config = PostProcessorConfig(
        enabled=False,
        enabled_processors=["processor1", "processor2"],
    )
    assert config.enabled is False
    assert config.enabled_processors == ["processor1", "processor2"]


def test_postprocessor_config_enabled() -> None:
    """PostProcessorConfig should support enabling."""
    config = PostProcessorConfig(enabled=True)
    assert config.enabled is True


def test_postprocessor_config_disabled() -> None:
    """PostProcessorConfig should support disabling."""
    config = PostProcessorConfig(enabled=False)
    assert config.enabled is False


def test_postprocessor_config_single_enabled_processor() -> None:
    """PostProcessorConfig should support single enabled processor."""
    config = PostProcessorConfig(enabled_processors=["normalize"])
    assert config.enabled_processors == ["normalize"]


def test_postprocessor_config_multiple_enabled_processors() -> None:
    """PostProcessorConfig should support multiple enabled processors."""
    config = PostProcessorConfig(enabled_processors=["normalize", "fix_encoding", "trim"])
    assert config.enabled_processors is not None
    assert len(config.enabled_processors) == 3
    assert "normalize" in config.enabled_processors


def test_postprocessor_config_single_disabled_processor() -> None:
    """PostProcessorConfig should support single disabled processor."""
    config = PostProcessorConfig(disabled_processors=["experimental"])
    assert config.disabled_processors == ["experimental"]


def test_postprocessor_config_multiple_disabled_processors() -> None:
    """PostProcessorConfig should support multiple disabled processors."""
    config = PostProcessorConfig(disabled_processors=["experimental", "beta_feature"])
    assert config.disabled_processors is not None
    assert len(config.disabled_processors) == 2
    assert "experimental" in config.disabled_processors


def test_postprocessor_config_empty_enabled_list() -> None:
    """PostProcessorConfig should support empty enabled processors list."""
    config = PostProcessorConfig(enabled_processors=[])
    assert config.enabled_processors == []


def test_postprocessor_config_empty_disabled_list() -> None:
    """PostProcessorConfig should support empty disabled processors list."""
    config = PostProcessorConfig(disabled_processors=[])
    assert config.disabled_processors == []


def test_postprocessor_config_none_enabled_processors() -> None:
    """PostProcessorConfig should handle None enabled_processors."""
    config = PostProcessorConfig(enabled_processors=None)
    assert config.enabled_processors is None


def test_postprocessor_config_none_disabled_processors() -> None:
    """PostProcessorConfig should handle None disabled_processors."""
    config = PostProcessorConfig(disabled_processors=None)
    assert config.disabled_processors is None


def test_postprocessor_config_in_extraction_config() -> None:
    """ExtractionConfig should properly nest PostProcessorConfig."""
    postproc = PostProcessorConfig(enabled=True)
    extraction = ExtractionConfig(postprocessor=postproc)
    assert extraction.postprocessor is not None
    assert extraction.postprocessor.enabled is True


def test_postprocessor_config_whitelist_mode() -> None:
    """PostProcessorConfig should support whitelist mode."""
    config = PostProcessorConfig(
        enabled=True,
        enabled_processors=["normalize_whitespace", "fix_encoding"],
    )
    assert config.enabled_processors is not None
    assert len(config.enabled_processors) == 2


def test_postprocessor_config_blacklist_mode() -> None:
    """PostProcessorConfig should support blacklist mode."""
    config = PostProcessorConfig(
        enabled=True,
        disabled_processors=["experimental_feature", "beta"],
    )
    assert config.disabled_processors is not None
    assert len(config.disabled_processors) == 2


def test_postprocessor_config_both_lists() -> None:
    """PostProcessorConfig should support both enabled and disabled lists."""
    config = PostProcessorConfig(
        enabled=True,
        enabled_processors=["core_processor"],
        disabled_processors=["experimental"],
    )
    assert config.enabled_processors == ["core_processor"]
    assert config.disabled_processors == ["experimental"]


def test_postprocessor_config_many_processors() -> None:
    """PostProcessorConfig should support many processors."""
    enabled = [f"processor_{i}" for i in range(50)]
    config = PostProcessorConfig(enabled_processors=enabled)
    assert config.enabled_processors is not None
    assert len(config.enabled_processors) == 50


def test_postprocessor_config_complex_processor_names() -> None:
    """PostProcessorConfig should support complex processor names."""
    config = PostProcessorConfig(
        enabled_processors=[
            "normalize_whitespace",
            "fix_unicode_encoding",
            "remove_control_chars",
            "collapse_line_breaks",
        ]
    )
    assert config.enabled_processors is not None
    assert len(config.enabled_processors) == 4


def test_postprocessor_config_special_characters_in_names() -> None:
    """PostProcessorConfig should accept special characters in processor names."""
    config = PostProcessorConfig(enabled_processors=["processor-v2", "processor_beta", "processor.test"])
    assert config.enabled_processors is not None
    assert "processor-v2" in config.enabled_processors


def test_postprocessor_config_all_parameters() -> None:
    """PostProcessorConfig should work with all parameters specified."""
    config = PostProcessorConfig(
        enabled=True,
        enabled_processors=["normalize", "cleanup"],
        disabled_processors=["experimental"],
    )

    assert config.enabled is True
    assert config.enabled_processors is not None
    assert len(config.enabled_processors) == 2
    assert config.disabled_processors is not None
    assert len(config.disabled_processors) == 1


def test_postprocessor_config_realistic_scenario() -> None:
    """PostProcessorConfig should support realistic post-processing scenario."""
    config = PostProcessorConfig(
        enabled=True,
        enabled_processors=[
            "normalize_whitespace",
            "fix_encoding",
            "remove_control_chars",
        ],
    )

    assert config.enabled is True
    assert config.enabled_processors is not None
    assert len(config.enabled_processors) == 3
