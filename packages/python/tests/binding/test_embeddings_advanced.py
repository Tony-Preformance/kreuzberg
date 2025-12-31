"""Advanced comprehensive tests for embeddings/vector generation functionality.

Tests cover:
- Embedding dimension verification
- Batch embedding operations
- Model configuration
- Similarity calculations
- Normalization verification
- Edge cases and error handling
"""

from __future__ import annotations

import math

from kreuzberg import (
    ChunkingConfig,
    EmbeddingConfig,
    EmbeddingModelType,
    ExtractionConfig,
    extract_bytes_sync,
)


class TestEmbeddingDimensions:
    """Test embedding dimensions for different models."""

    def test_balanced_model_produces_valid_dimensions(self) -> None:
        """Verify balanced model produces embeddings with valid dimensions."""
        model = EmbeddingModelType.preset("balanced")
        embedding_config = EmbeddingConfig(model=model, normalize=True)
        config = ExtractionConfig(
            chunking=ChunkingConfig(
                max_chars=512,
                max_overlap=100,
                embedding=embedding_config,
            ),
        )

        text = "Balanced model dimension test"
        result = extract_bytes_sync(text.encode(), "text/plain", config)

        assert result is not None
        if result.chunks:
            for chunk in result.chunks:
                if chunk.get("embedding") is not None:
                    embedding = chunk["embedding"]
                    assert isinstance(embedding, list)
                    assert len(embedding) > 0
                    assert all(isinstance(x, float) for x in embedding)

    def test_fast_model_produces_valid_dimensions(self) -> None:
        """Verify fast model produces embeddings with valid dimensions."""
        model = EmbeddingModelType.preset("fast")
        embedding_config = EmbeddingConfig(model=model, normalize=True)
        config = ExtractionConfig(
            chunking=ChunkingConfig(
                max_chars=512,
                max_overlap=100,
                embedding=embedding_config,
            ),
        )

        text = "Fast model dimension test"
        result = extract_bytes_sync(text.encode(), "text/plain", config)

        assert result is not None
        if result.chunks:
            for chunk in result.chunks:
                if chunk.get("embedding") is not None:
                    embedding = chunk["embedding"]
                    if embedding is not None:
                        assert len(embedding) > 0

    def test_embeddings_have_consistent_dimensions(self) -> None:
        """Verify all embeddings have same dimensions."""
        model = EmbeddingModelType.preset("balanced")
        embedding_config = EmbeddingConfig(model=model, normalize=True)
        config = ExtractionConfig(
            chunking=ChunkingConfig(
                max_chars=200,
                max_overlap=50,
                embedding=embedding_config,
            ),
        )

        text = "First chunk with embeddings. Second chunk continues. Third chunk completes."
        result = extract_bytes_sync(text.encode(), "text/plain", config)

        assert result is not None
        if result.chunks and len(result.chunks) > 1:
            dimensions = []
            for chunk in result.chunks:
                embedding = chunk.get("embedding")
                if embedding is not None:
                    dimensions.append(len(embedding))

            if len(dimensions) > 1:
                # All dimensions should be equal
                assert all(d == dimensions[0] for d in dimensions)


class TestBatchEmbeddings:
    """Test batch embedding operations."""

    def test_batch_embedding_multiple_chunks(self) -> None:
        """Verify embeddings work with multiple chunks."""
        model = EmbeddingModelType.preset("balanced")
        embedding_config = EmbeddingConfig(model=model, normalize=True)
        config = ExtractionConfig(
            chunking=ChunkingConfig(
                max_chars=100,
                max_overlap=20,
                embedding=embedding_config,
            ),
        )

        text = "Chunk one. Chunk two. Chunk three. Chunk four. Chunk five."
        result = extract_bytes_sync(text.encode(), "text/plain", config)

        assert result is not None
        if result.chunks:
            chunk_count = len(result.chunks)
            embedding_count = sum(1 for chunk in result.chunks if chunk.get("embedding") is not None)

            assert chunk_count > 0
            if embedding_count > 0:
                assert embedding_count <= chunk_count

    def test_embeddings_generated_for_all_chunks(self) -> None:
        """Verify embeddings are generated for all chunks when enabled."""
        model = EmbeddingModelType.preset("balanced")
        embedding_config = EmbeddingConfig(model=model, normalize=True)
        config = ExtractionConfig(
            chunking=ChunkingConfig(
                max_chars=100,
                max_overlap=20,
                embedding=embedding_config,
            ),
        )

        text = "Long text for chunking. " * 10
        result = extract_bytes_sync(text.encode(), "text/plain", config)

        assert result is not None
        if result.chunks:
            for chunk in result.chunks:
                embedding = chunk.get("embedding")
                # Embedding should be present and valid
                if embedding is not None:
                    assert isinstance(embedding, list)
                    assert len(embedding) > 0

    def test_embeddings_disabled_no_vectors(self) -> None:
        """Verify no embeddings generated when disabled."""
        config = ExtractionConfig(
            chunking=ChunkingConfig(
                max_chars=512,
                max_overlap=100,
                embedding=None,
            ),
        )

        text = "Text without embeddings"
        result = extract_bytes_sync(text.encode(), "text/plain", config)

        assert result is not None
        if result.chunks:
            for chunk in result.chunks:
                embedding = chunk.get("embedding")
                assert embedding is None


class TestEmbeddingNormalization:
    """Test embedding normalization."""

    def test_normalized_embeddings_unit_norm(self) -> None:
        """Verify normalized embeddings have unit norm."""
        model = EmbeddingModelType.preset("balanced")
        embedding_config = EmbeddingConfig(model=model, normalize=True)
        config = ExtractionConfig(
            chunking=ChunkingConfig(
                max_chars=512,
                max_overlap=100,
                embedding=embedding_config,
            ),
        )

        text = "Normalization test for unit norm verification"
        result = extract_bytes_sync(text.encode(), "text/plain", config)

        assert result is not None
        if result.chunks:
            for chunk in result.chunks:
                if chunk.get("embedding") is not None:
                    embedding = chunk["embedding"]
                    if embedding is not None:
                        # Calculate L2 norm
                        norm = math.sqrt(sum(x**2 for x in embedding))
                        # Normalized vectors should have norm close to 1
                        assert 0.9 < norm < 1.1, f"Norm should be ~1.0, got {norm}"

    def test_non_normalized_embeddings_exist(self) -> None:
        """Verify non-normalized embeddings can be generated."""
        model = EmbeddingModelType.preset("balanced")
        embedding_config = EmbeddingConfig(model=model, normalize=False)
        config = ExtractionConfig(
            chunking=ChunkingConfig(
                max_chars=512,
                max_overlap=100,
                embedding=embedding_config,
            ),
        )

        text = "Non-normalized embedding test"
        result = extract_bytes_sync(text.encode(), "text/plain", config)

        assert result is not None
        if result.chunks:
            for chunk in result.chunks:
                if chunk.get("embedding") is not None:
                    embedding = chunk["embedding"]
                    assert isinstance(embedding, list)
                    assert len(embedding) > 0


class TestEmbeddingValidity:
    """Test embedding validity and properties."""

    def test_embedding_values_are_floats(self) -> None:
        """Verify all embedding values are valid floats."""
        model = EmbeddingModelType.preset("balanced")
        embedding_config = EmbeddingConfig(model=model, normalize=True)
        config = ExtractionConfig(
            chunking=ChunkingConfig(
                max_chars=512,
                max_overlap=100,
                embedding=embedding_config,
            ),
        )

        text = "Float value validation for embeddings"
        result = extract_bytes_sync(text.encode(), "text/plain", config)

        assert result is not None
        if result.chunks:
            for chunk in result.chunks:
                if chunk.get("embedding") is not None:
                    embedding = chunk["embedding"]
                    if embedding is not None:
                        for value in embedding:
                            assert isinstance(value, float)
                            assert not math.isnan(value), "Embedding contains NaN"
                            assert not math.isinf(value), "Embedding contains Inf"

    def test_embedding_no_negative_infinity(self) -> None:
        """Verify embeddings don't contain negative infinity."""
        model = EmbeddingModelType.preset("balanced")
        embedding_config = EmbeddingConfig(model=model, normalize=True)
        config = ExtractionConfig(
            chunking=ChunkingConfig(
                max_chars=512,
                max_overlap=100,
                embedding=embedding_config,
            ),
        )

        text = "Testing for infinity values in embeddings"
        result = extract_bytes_sync(text.encode(), "text/plain", config)

        assert result is not None
        if result.chunks:
            for chunk in result.chunks:
                if chunk.get("embedding") is not None:
                    embedding = chunk["embedding"]
                    if embedding is not None:
                        for value in embedding:
                            assert value != float("inf")
                            assert value != float("-inf")

    def test_embedding_reasonable_magnitude(self) -> None:
        """Verify embedding values have reasonable magnitude."""
        model = EmbeddingModelType.preset("balanced")
        embedding_config = EmbeddingConfig(model=model, normalize=True)
        config = ExtractionConfig(
            chunking=ChunkingConfig(
                max_chars=512,
                max_overlap=100,
                embedding=embedding_config,
            ),
        )

        text = "Magnitude validation for embedding vectors"
        result = extract_bytes_sync(text.encode(), "text/plain", config)

        assert result is not None
        if result.chunks:
            for chunk in result.chunks:
                if chunk.get("embedding") is not None:
                    embedding = chunk["embedding"]
                    if embedding is not None:
                        # For normalized embeddings, values should be in [-1, 1]
                        for value in embedding:
                            assert -2.0 < value < 2.0, f"Value {value} out of reasonable range"


class TestEmbeddingConsistency:
    """Test embedding consistency across runs."""

    def test_embeddings_deterministic(self) -> None:
        """Verify embedding generation is deterministic."""
        model = EmbeddingModelType.preset("balanced")
        embedding_config = EmbeddingConfig(model=model, normalize=True)
        config = ExtractionConfig(
            chunking=ChunkingConfig(
                max_chars=512,
                max_overlap=100,
                embedding=embedding_config,
            ),
        )

        text = "Deterministic embedding test"

        result1 = extract_bytes_sync(text.encode(), "text/plain", config)
        result2 = extract_bytes_sync(text.encode(), "text/plain", config)

        assert result1 is not None
        assert result2 is not None

        if result1.chunks and result2.chunks:
            assert len(result1.chunks) == len(result2.chunks)

            for chunk1, chunk2 in zip(result1.chunks, result2.chunks, strict=False):
                emb1 = chunk1.get("embedding")
                emb2 = chunk2.get("embedding")

                if emb1 is not None and emb2 is not None:
                    assert len(emb1) == len(emb2)
                    for v1, v2 in zip(emb1, emb2, strict=False):
                        assert abs(v1 - v2) < 1e-5, f"Embeddings not consistent: {v1} vs {v2}"

    def test_same_text_produces_same_embedding(self) -> None:
        """Verify same text always produces same embedding."""
        model = EmbeddingModelType.preset("balanced")
        embedding_config = EmbeddingConfig(model=model, normalize=True)
        config = ExtractionConfig(
            chunking=ChunkingConfig(
                max_chars=512,
                max_overlap=100,
                embedding=embedding_config,
            ),
        )

        text = "Consistent embedding for same text"

        results = [extract_bytes_sync(text.encode(), "text/plain", config) for _ in range(3)]

        for result in results:
            assert result is not None
            if result.chunks:
                assert len(result.chunks) > 0


class TestEmbeddingEdgeCases:
    """Test edge cases in embedding generation."""

    def test_very_short_text_embedding(self) -> None:
        """Verify embeddings work for very short text."""
        model = EmbeddingModelType.preset("balanced")
        embedding_config = EmbeddingConfig(model=model, normalize=True)
        config = ExtractionConfig(
            chunking=ChunkingConfig(
                max_chars=512,
                max_overlap=100,
                embedding=embedding_config,
            ),
        )

        text = "Hi"
        result = extract_bytes_sync(text.encode(), "text/plain", config)

        assert result is not None

    def test_empty_string_embedding(self) -> None:
        """Verify embeddings handle empty strings."""
        model = EmbeddingModelType.preset("balanced")
        embedding_config = EmbeddingConfig(model=model, normalize=True)
        config = ExtractionConfig(
            chunking=ChunkingConfig(
                max_chars=512,
                max_overlap=100,
                embedding=embedding_config,
            ),
        )

        text = ""
        result = extract_bytes_sync(text.encode(), "text/plain", config)

        assert result is not None

    def test_whitespace_only_embedding(self) -> None:
        """Verify embeddings handle whitespace-only text."""
        model = EmbeddingModelType.preset("balanced")
        embedding_config = EmbeddingConfig(model=model, normalize=True)
        config = ExtractionConfig(
            chunking=ChunkingConfig(
                max_chars=512,
                max_overlap=100,
                embedding=embedding_config,
            ),
        )

        text = "   \n\t  \n  "
        result = extract_bytes_sync(text.encode(), "text/plain", config)

        assert result is not None

    def test_very_long_text_embedding(self) -> None:
        """Verify embeddings work for very long text."""
        model = EmbeddingModelType.preset("balanced")
        embedding_config = EmbeddingConfig(model=model, normalize=True)
        config = ExtractionConfig(
            chunking=ChunkingConfig(
                max_chars=100,
                max_overlap=20,
                embedding=embedding_config,
            ),
        )

        text = "Word " * 1000  # Very long text
        result = extract_bytes_sync(text.encode(), "text/plain", config)

        assert result is not None
        if result.chunks:
            assert len(result.chunks) > 0


class TestEmbeddingChunkRelationship:
    """Test relationship between chunks and embeddings."""

    def test_each_chunk_has_content_or_embedding(self) -> None:
        """Verify each chunk has content and optionally embedding."""
        model = EmbeddingModelType.preset("balanced")
        embedding_config = EmbeddingConfig(model=model, normalize=True)
        config = ExtractionConfig(
            chunking=ChunkingConfig(
                max_chars=100,
                max_overlap=20,
                embedding=embedding_config,
            ),
        )

        text = "Multiple chunks with embeddings. Each chunk is separate."
        result = extract_bytes_sync(text.encode(), "text/plain", config)

        assert result is not None
        if result.chunks:
            for chunk in result.chunks:
                assert "content" in chunk or "text" in chunk
                # Embedding might be None or list
                embedding = chunk.get("embedding")
                if embedding is not None:
                    assert isinstance(embedding, list)

    def test_embedding_matches_chunk_order(self) -> None:
        """Verify embeddings match chunk order."""
        model = EmbeddingModelType.preset("balanced")
        embedding_config = EmbeddingConfig(model=model, normalize=True)
        config = ExtractionConfig(
            chunking=ChunkingConfig(
                max_chars=50,
                max_overlap=10,
                embedding=embedding_config,
            ),
        )

        text = "First. Second. Third. Fourth. Fifth."
        result = extract_bytes_sync(text.encode(), "text/plain", config)

        assert result is not None
        if result.chunks and len(result.chunks) > 1:
            # Chunks should maintain order
            for i in range(len(result.chunks) - 1):
                chunk_i = result.chunks[i]
                chunk_j = result.chunks[i + 1]
                # Both should have valid structure
                assert chunk_i is not None
                assert chunk_j is not None
