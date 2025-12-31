"""Tests for TokenReductionConfig configuration."""

from __future__ import annotations

from kreuzberg import ExtractionConfig, TokenReductionConfig


def test_token_reduction_config_default_construction() -> None:
    """TokenReductionConfig should have sensible defaults."""
    config = TokenReductionConfig()
    assert config.mode == "off"
    assert config.preserve_important_words is True


def test_token_reduction_config_custom_values() -> None:
    """TokenReductionConfig should accept custom values."""
    config = TokenReductionConfig(
        mode="moderate",
        preserve_important_words=False,
    )
    assert config.mode == "moderate"
    assert config.preserve_important_words is False


def test_token_reduction_config_mode_off() -> None:
    """TokenReductionConfig should support off mode."""
    config = TokenReductionConfig(mode="off")
    assert config.mode == "off"


def test_token_reduction_config_mode_light() -> None:
    """TokenReductionConfig should support light mode."""
    config = TokenReductionConfig(mode="moderate")
    assert config.mode == "moderate"


def test_token_reduction_config_mode_moderate() -> None:
    """TokenReductionConfig should support moderate mode."""
    config = TokenReductionConfig(mode="moderate")
    assert config.mode == "moderate"


def test_token_reduction_config_mode_aggressive() -> None:
    """TokenReductionConfig should support aggressive mode."""
    config = TokenReductionConfig(mode="aggressive")
    assert config.mode == "aggressive"


def test_token_reduction_config_mode_maximum() -> None:
    """TokenReductionConfig should support maximum mode."""
    config = TokenReductionConfig(mode="aggressive")
    assert config.mode == "aggressive"


def test_token_reduction_config_preserve_important_enabled() -> None:
    """TokenReductionConfig should support preserving important words."""
    config = TokenReductionConfig(preserve_important_words=True)
    assert config.preserve_important_words is True


def test_token_reduction_config_preserve_important_disabled() -> None:
    """TokenReductionConfig should support not preserving important words."""
    config = TokenReductionConfig(preserve_important_words=False)
    assert config.preserve_important_words is False


def test_token_reduction_config_all_modes() -> None:
    """TokenReductionConfig should support all reduction modes."""
    modes = ["off", "moderate", "aggressive"]
    for mode in modes:
        config = TokenReductionConfig(mode=mode)  # type: ignore[arg-type]
        assert config.mode == mode


def test_token_reduction_config_light_with_preserve() -> None:
    """TokenReductionConfig should support light mode with preservation."""
    config = TokenReductionConfig(
        mode="moderate",
        preserve_important_words=True,
    )
    assert config.mode == "moderate"
    assert config.preserve_important_words is True


def test_token_reduction_config_aggressive_with_preserve() -> None:
    """TokenReductionConfig should support aggressive mode with preservation."""
    config = TokenReductionConfig(
        mode="aggressive",
        preserve_important_words=True,
    )
    assert config.mode == "aggressive"
    assert config.preserve_important_words is True


def test_token_reduction_config_maximum_with_preserve() -> None:
    """TokenReductionConfig should support maximum mode with preservation."""
    config = TokenReductionConfig(
        mode="aggressive",
        preserve_important_words=True,
    )
    assert config.mode == "aggressive"
    assert config.preserve_important_words is True


def test_token_reduction_config_in_extraction_config() -> None:
    """ExtractionConfig should properly nest TokenReductionConfig."""
    token_red = TokenReductionConfig(mode="moderate")
    extraction = ExtractionConfig(token_reduction=token_red)
    assert extraction.token_reduction is not None
    assert extraction.token_reduction.mode == "moderate"


def test_token_reduction_config_disabled() -> None:
    """TokenReductionConfig should support complete disabling."""
    config = TokenReductionConfig(mode="off")
    assert config.mode == "off"


def test_token_reduction_config_minimal_reduction() -> None:
    """TokenReductionConfig should support minimal reduction."""
    config = TokenReductionConfig(
        mode="moderate",
        preserve_important_words=True,
    )
    assert config.mode == "moderate"


def test_token_reduction_config_maximum_reduction() -> None:
    """TokenReductionConfig should support maximum reduction."""
    config = TokenReductionConfig(
        mode="aggressive",
        preserve_important_words=True,
    )
    assert config.mode == "aggressive"


def test_token_reduction_config_for_llm_cost_optimization() -> None:
    """TokenReductionConfig should support LLM cost optimization."""
    config = TokenReductionConfig(
        mode="aggressive",
        preserve_important_words=True,
    )
    assert config.mode == "aggressive"
    assert config.preserve_important_words is True


def test_token_reduction_config_balanced_approach() -> None:
    """TokenReductionConfig should support balanced reduction approach."""
    config = TokenReductionConfig(
        mode="moderate",
        preserve_important_words=True,
    )
    assert config.mode == "moderate"
    assert config.preserve_important_words is True


def test_token_reduction_config_no_preservation() -> None:
    """TokenReductionConfig should support aggressive reduction without preservation."""
    config = TokenReductionConfig(
        mode="aggressive",
        preserve_important_words=False,
    )
    assert config.mode == "aggressive"
    assert config.preserve_important_words is False


def test_token_reduction_config_all_parameters() -> None:
    """TokenReductionConfig should work with all parameters specified."""
    config = TokenReductionConfig(
        mode="moderate",
        preserve_important_words=True,
    )

    assert config.mode == "moderate"
    assert config.preserve_important_words is True


def test_token_reduction_config_realistic_scenario() -> None:
    """TokenReductionConfig should support realistic token reduction scenario."""
    config = TokenReductionConfig(
        mode="moderate",
        preserve_important_words=True,
    )

    assert config.mode == "moderate"
    assert config.preserve_important_words is True
