"""Tests for PdfConfig configuration."""

from __future__ import annotations

from kreuzberg import ExtractionConfig, HierarchyConfig, PdfConfig


def test_pdf_config_default_construction() -> None:
    """PdfConfig should have sensible defaults."""
    config = PdfConfig()
    assert config.extract_images is False
    assert config.passwords is None
    assert config.extract_metadata is True
    assert config.hierarchy is None


def test_pdf_config_custom_values() -> None:
    """PdfConfig should accept custom values."""
    config = PdfConfig(
        extract_images=True,
        extract_metadata=False,
        passwords=["test123"],
    )
    assert config.extract_images is True
    assert config.extract_metadata is False
    assert config.passwords == ["test123"]


def test_pdf_config_extract_images() -> None:
    """PdfConfig should support image extraction control."""
    config = PdfConfig(extract_images=True)
    assert config.extract_images is True

    config = PdfConfig(extract_images=False)
    assert config.extract_images is False


def test_pdf_config_extract_metadata() -> None:
    """PdfConfig should support metadata extraction control."""
    config = PdfConfig(extract_metadata=True)
    assert config.extract_metadata is True

    config = PdfConfig(extract_metadata=False)
    assert config.extract_metadata is False


def test_pdf_config_single_password() -> None:
    """PdfConfig should support single password."""
    config = PdfConfig(passwords=["mypassword"])
    assert config.passwords == ["mypassword"]


def test_pdf_config_multiple_passwords() -> None:
    """PdfConfig should support multiple passwords."""
    config = PdfConfig(passwords=["password1", "password2", "password3"])
    assert config.passwords is not None
    assert len(config.passwords) == 3
    assert "password1" in config.passwords
    assert "password2" in config.passwords
    assert "password3" in config.passwords


def test_pdf_config_empty_password_list() -> None:
    """PdfConfig should support empty password list."""
    config = PdfConfig(passwords=[])
    assert config.passwords == []


def test_pdf_config_passwords_none() -> None:
    """PdfConfig should handle None passwords appropriately."""
    config = PdfConfig(passwords=None)
    assert config.passwords is None


def test_pdf_config_with_hierarchy() -> None:
    """PdfConfig should properly nest HierarchyConfig."""
    hierarchy = HierarchyConfig(enabled=True, k_clusters=8)
    config = PdfConfig(hierarchy=hierarchy)
    assert config.hierarchy is not None
    assert config.hierarchy.enabled is True
    assert config.hierarchy.k_clusters == 8


def test_pdf_config_none_hierarchy() -> None:
    """PdfConfig should handle None hierarchy appropriately."""
    config = PdfConfig(hierarchy=None)
    assert config.hierarchy is None


def test_pdf_config_in_extraction_config() -> None:
    """ExtractionConfig should properly nest PdfConfig."""
    pdf = PdfConfig(extract_images=True, extract_metadata=True)
    extraction = ExtractionConfig(pdf_options=pdf)
    assert extraction.pdf_options is not None
    assert extraction.pdf_options.extract_images is True
    assert extraction.pdf_options.extract_metadata is True


def test_pdf_config_encrypted_pdf_passwords() -> None:
    """PdfConfig should support encrypted PDF password handling."""
    passwords = ["attempt1", "attempt2", "correct_password"]
    config = PdfConfig(passwords=passwords)
    assert config.passwords is not None
    assert len(config.passwords) == 3
    assert config.passwords[2] == "correct_password"


def test_pdf_config_with_all_options() -> None:
    """PdfConfig should work with all options specified."""
    hierarchy = HierarchyConfig(
        enabled=True,
        k_clusters=6,
        include_bbox=True,
    )
    config = PdfConfig(
        extract_images=True,
        extract_metadata=True,
        passwords=["pwd1", "pwd2"],
        hierarchy=hierarchy,
    )

    assert config.extract_images is True
    assert config.extract_metadata is True
    assert config.passwords is not None
    assert len(config.passwords) == 2
    assert config.hierarchy is not None
    assert config.hierarchy.enabled is True


def test_pdf_config_special_characters_in_password() -> None:
    """PdfConfig should accept special characters in passwords."""
    config = PdfConfig(passwords=["p@$$w0rd!", "test#123"])
    assert config.passwords == ["p@$$w0rd!", "test#123"]


def test_pdf_config_unicode_passwords() -> None:
    """PdfConfig should accept unicode passwords."""
    config = PdfConfig(passwords=["пароль", "密码", "パスワード"])
    assert config.passwords is not None
    assert len(config.passwords) == 3


def test_pdf_config_long_password_list() -> None:
    """PdfConfig should support long password lists."""
    passwords = [f"password_{i}" for i in range(100)]
    config = PdfConfig(passwords=passwords)
    assert config.passwords is not None
    assert len(config.passwords) == 100


def test_pdf_config_extraction_without_hierarchy() -> None:
    """PdfConfig should work with extraction but no hierarchy."""
    config = PdfConfig(
        extract_images=True,
        extract_metadata=True,
        hierarchy=None,
    )
    assert config.extract_images is True
    assert config.extract_metadata is True
    assert config.hierarchy is None


def test_pdf_config_hierarchy_without_images() -> None:
    """PdfConfig should work with hierarchy but no image extraction."""
    hierarchy = HierarchyConfig(enabled=True)
    config = PdfConfig(
        extract_images=False,
        hierarchy=hierarchy,
    )
    assert config.extract_images is False
    assert config.hierarchy is not None


def test_pdf_config_minimal_encrypted_pdf() -> None:
    """PdfConfig should support minimal encrypted PDF setup."""
    config = PdfConfig(passwords=["secret"])
    assert config.passwords is not None
    assert len(config.passwords) == 1
    assert config.passwords[0] == "secret"


def test_pdf_config_realistic_scenario() -> None:
    """PdfConfig should support realistic PDF extraction scenario."""
    config = PdfConfig(
        extract_images=True,
        extract_metadata=True,
        passwords=["primary_pwd", "fallback_pwd"],
        hierarchy=HierarchyConfig(enabled=True, k_clusters=6),
    )

    assert config.extract_images is True
    assert config.extract_metadata is True
    assert config.passwords is not None
    assert len(config.passwords) == 2
    assert config.hierarchy is not None
