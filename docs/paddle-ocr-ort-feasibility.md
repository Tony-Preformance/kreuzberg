# PaddleOCR via ONNX Runtime - Feasibility Assessment

## Executive Summary

**Verdict: FEASIBLE with low-medium integration effort**

Integrating PaddleOCR into Kreuzberg using ONNX Runtime is feasible and recommended. The `paddle-ocr-rs` crate provides a mature, well-tested implementation that:
- Uses the same `ort` version (2.0.0-rc.11) already in kreuzberg's dependency tree
- Supports PP-OCRv3, v4, and v5 models
- Uses pure Rust image processing (no OpenCV dependency)
- Reports 0.95-0.99 confidence scores in benchmarks

## Technical Analysis

### Dependency Compatibility

| Dependency | Kreuzberg Version | paddle-ocr-rs Version | Compatible |
|------------|-------------------|----------------------|------------|
| ort | 2.0.0-rc.11 | 2.0.0-rc.11 | ✅ Yes |
| image | 0.25.x | Compatible | ✅ Yes |
| ndarray | 0.16.x | Compatible | ✅ Yes |

### Model Requirements

PaddleOCR requires three ONNX model files:
1. **Detection model** (~3-5MB): `ch_PP-OCRv4_det_infer.onnx`
2. **Classification model** (~1MB): `ch_ppocr_mobile_v2.0_cls_infer.onnx`
3. **Recognition model** (~10-15MB): `ch_PP-OCRv4_rec_infer.onnx`

**Total model size: ~15-25MB** (much smaller than discussed in #306)

Model sources:
- [PaddleOCR Model Zoo](https://github.com/PaddlePaddle/PaddleOCR/blob/main/doc/doc_en/models_list_en.md)
- Pre-converted ONNX models via paddle2onnx

### Architecture Fit

```
┌─────────────────────────────────────────────────────────────┐
│                     OcrConfig                                │
│  (backend: "paddleocr" | "tesseract" | "auto")              │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   OcrBackend Trait                           │
│  - process_image(&[u8], &OcrConfig) -> ExtractionResult     │
│  - supports_language(&str) -> bool                          │
│  - backend_type() -> OcrBackendType                         │
└─────────────────────────────────────────────────────────────┘
          ↓                                    ↓
┌─────────────────────┐           ┌─────────────────────────┐
│  TesseractBackend   │           │   PaddleOcrBackend      │
│  (existing)         │           │   (new)                 │
│                     │           │                         │
│  - kreuzberg-       │           │  - paddle-ocr-rs        │
│    tesseract crate  │           │  - ort (shared with     │
│  - libtesseract     │           │    fastembed)           │
└─────────────────────┘           └─────────────────────────┘
```

### Implementation Plan

#### Phase 1: Core Integration (1-2 days)
1. Add `paddle-ocr-rs` as optional dependency
2. Create `PaddleOcrBackend` implementing `OcrBackend` trait
3. Add `OcrBackendType::PaddleOcr` variant
4. Model file management (download/cache on first use)

#### Phase 2: Configuration (0.5 day)
1. Add `PaddleOcrConfig` struct with model paths, thread count
2. Extend `OcrConfig` with paddle-specific options
3. Language mapping (paddle codes ↔ kreuzberg codes)

#### Phase 3: Testing & Documentation (1 day)
1. Unit tests with sample images
2. Benchmark vs Tesseract (accuracy + speed)
3. Documentation and examples

### Resource Estimates

| Metric | Tesseract | PaddleOCR (ONNX) |
|--------|-----------|------------------|
| Binary size delta | baseline | +2-3MB |
| Runtime memory | ~100-200MB | ~150-300MB |
| Model files | ~15MB (per lang) | ~20-25MB (all langs) |
| Cold start | ~500ms | ~300ms |
| Inference (A4 page) | ~1-3s | ~0.5-1.5s |

### Feature Flag Design

```toml
[features]
default = ["ocr-tesseract"]
ocr-tesseract = ["dep:kreuzberg-tesseract"]
ocr-paddle = ["dep:paddle-ocr-rs"]
ocr-all = ["ocr-tesseract", "ocr-paddle"]
```

### Docker Image Impact

| Image Variant | Current Size | With PaddleOCR |
|---------------|--------------|----------------|
| kreuzberg:core | ~1.0-1.3GB | +25-30MB |
| kreuzberg:full | ~1.5-2.1GB | +25-30MB |

**Note:** Much smaller than Python-based PaddleOCR (~3GB+) because:
- No Python runtime needed
- No PyTorch/PaddlePaddle frameworks
- Only ONNX Runtime (~50MB) + model files (~25MB)

### Language Support Comparison

| Engine | Languages | CJK Quality | Latin Quality |
|--------|-----------|-------------|---------------|
| Tesseract | 100+ | Good | Excellent |
| PaddleOCR | 14 optimized | Excellent | Very Good |

PaddleOCR excels at: Chinese, Japanese, Korean, Arabic, Devanagari
Tesseract excels at: European languages, historical documents

### Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| ort version conflict | Low | High | Already using same version |
| Model download failures | Medium | Medium | Bundled fallback, retry logic |
| Accuracy regression | Low | Medium | A/B testing, user choice |
| Memory pressure | Medium | Low | Lazy loading, session pooling |

## Recommendation

**Proceed with implementation** using the following approach:

1. **Optional feature flag** - Don't force PaddleOCR on users who don't need it
2. **Auto-download models** - First use triggers model download to cache dir
3. **Backend selection** - Let users choose via `OcrConfig.backend`
4. **Hybrid mode** - Allow fallback to Tesseract for unsupported languages

## References

- [paddle-ocr-rs](https://github.com/mg-chao/paddle-ocr-rs) - Rust ONNX implementation
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) - Original Python implementation
- [ort](https://github.com/pykeio/ort) - ONNX Runtime Rust bindings
- [Discussion #306](https://github.com/kreuzberg-dev/kreuzberg/discussions/306) - Original feature request

## Next Steps

1. [ ] Create `crates/kreuzberg-paddle` or add to `crates/kreuzberg/src/ocr/paddle/`
2. [ ] Implement `PaddleOcrBackend`
3. [ ] Add model download/cache management
4. [ ] Write tests with CJK and Latin test images
5. [ ] Benchmark accuracy and performance vs Tesseract
6. [ ] Update documentation
