//! PaddleOCR backend implementation.

use std::path::Path;
use std::sync::Arc;
use async_trait::async_trait;

use crate::Result;
use crate::core::config::OcrConfig;
use crate::plugins::{OcrBackend, OcrBackendType, Plugin};
use crate::types::{ExtractionResult, Metadata};

use super::config::PaddleOcrConfig;
use super::model_manager::{ModelManager, ModelPaths};
use super::{is_language_supported, map_language_code, SUPPORTED_LANGUAGES};

/// PaddleOCR backend using ONNX Runtime.
///
/// This backend provides high-quality OCR using PaddlePaddle's PP-OCR models
/// converted to ONNX format and run via ONNX Runtime.
///
/// # Advantages over Tesseract
///
/// - Superior CJK (Chinese, Japanese, Korean) recognition
/// - Better handling of complex layouts
/// - Faster inference on modern hardware
///
/// # Requirements
///
/// - ONNX Runtime (provided via `ort` crate)
/// - Model files (auto-downloaded on first use)
pub struct PaddleOcrBackend {
    config: PaddleOcrConfig,
    model_paths: Option<ModelPaths>,
    // TODO: Add paddle-ocr-rs OcrLite instance when implementing
    // ocr_engine: Option<Arc<paddle_ocr_rs::OcrLite>>,
}

impl PaddleOcrBackend {
    /// Create a new PaddleOCR backend with default configuration.
    pub fn new() -> Result<Self> {
        Self::with_config(PaddleOcrConfig::default())
    }

    /// Create a new PaddleOCR backend with custom configuration.
    pub fn with_config(config: PaddleOcrConfig) -> Result<Self> {
        Ok(Self {
            config,
            model_paths: None,
        })
    }

    /// Initialize the backend, downloading models if necessary.
    ///
    /// This is called lazily on first use, but can be called explicitly
    /// to pre-download models.
    pub async fn initialize(&mut self) -> Result<()> {
        if self.model_paths.is_some() {
            return Ok(());
        }

        let manager = ModelManager::new(&self.config);
        let paths = manager.ensure_models().await?;

        // TODO: Initialize paddle-ocr-rs OcrLite with model paths
        // let mut ocr = paddle_ocr_rs::OcrLite::new();
        // ocr.init_models(
        //     paths.detection.to_str().unwrap(),
        //     paths.classification.to_str().unwrap(),
        //     paths.recognition.to_str().unwrap(),
        //     self.config.num_threads as i32,
        // )?;
        // self.ocr_engine = Some(Arc::new(ocr));

        self.model_paths = Some(paths);
        Ok(())
    }

    /// Perform OCR on image bytes.
    async fn do_ocr(&self, image_bytes: &[u8], _language: &str) -> Result<String> {
        // Ensure models are loaded
        if self.model_paths.is_none() {
            return Err(crate::KreuzbergError::Ocr {
                message: "PaddleOCR backend not initialized. Call initialize() first.".to_string(),
                source: None,
            });
        }

        // TODO: Implement actual OCR using paddle-ocr-rs
        // 1. Decode image bytes to RGB8 using `image` crate
        // 2. Call ocr_engine.detect() with the image
        // 3. Collect and format results

        // Placeholder implementation
        let _ = image_bytes;
        Err(crate::KreuzbergError::Ocr {
            message: "PaddleOCR inference not yet implemented. \
                      Add paddle-ocr-rs dependency to complete implementation.".to_string(),
            source: None,
        })
    }
}

impl Plugin for PaddleOcrBackend {
    fn name(&self) -> &str {
        "paddle-ocr"
    }

    fn version(&self) -> String {
        env!("CARGO_PKG_VERSION").to_string()
    }

    fn initialize(&self) -> Result<()> {
        // Lazy initialization - actual init happens on first use
        Ok(())
    }

    fn shutdown(&self) -> Result<()> {
        // ONNX Runtime handles cleanup automatically
        Ok(())
    }
}

#[cfg_attr(not(target_arch = "wasm32"), async_trait)]
#[cfg_attr(target_arch = "wasm32", async_trait(?Send))]
impl OcrBackend for PaddleOcrBackend {
    async fn process_image(&self, image_bytes: &[u8], config: &OcrConfig) -> Result<ExtractionResult> {
        // Map language code
        let paddle_lang = map_language_code(&config.language)
            .unwrap_or("en");

        // Perform OCR
        let text = self.do_ocr(image_bytes, paddle_lang).await?;

        Ok(ExtractionResult {
            content: text,
            mime_type: "text/plain".to_string(),
            metadata: Metadata::default(),
            tables: vec![],
            detected_languages: Some(vec![config.language.clone()]),
            chunks: None,
            images: None,
            djot_content: None,
            pages: None,
            elements: None,
        })
    }

    async fn process_file(&self, path: &Path, config: &OcrConfig) -> Result<ExtractionResult> {
        // Read file and delegate to process_image
        let bytes = tokio::fs::read(path).await.map_err(|e| {
            crate::KreuzbergError::Io {
                message: format!("Failed to read image file: {}", e),
                path: Some(path.to_path_buf()),
                source: Some(Box::new(e)),
            }
        })?;

        self.process_image(&bytes, config).await
    }

    fn supports_language(&self, lang: &str) -> bool {
        is_language_supported(lang) || map_language_code(lang).is_some()
    }

    fn backend_type(&self) -> OcrBackendType {
        OcrBackendType::Custom
    }
}

impl Default for PaddleOcrBackend {
    fn default() -> Self {
        Self::new().expect("Failed to create default PaddleOcrBackend")
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_language_support() {
        let backend = PaddleOcrBackend::new().unwrap();

        // Direct codes
        assert!(backend.supports_language("ch"));
        assert!(backend.supports_language("en"));
        assert!(backend.supports_language("japan"));

        // Mapped codes
        assert!(backend.supports_language("chi_sim"));
        assert!(backend.supports_language("eng"));
        assert!(backend.supports_language("jpn"));

        // Unsupported
        assert!(!backend.supports_language("xyz"));
    }

    #[test]
    fn test_backend_info() {
        let backend = PaddleOcrBackend::new().unwrap();
        assert_eq!(backend.name(), "paddle-ocr");
        assert!(!backend.version().is_empty());
    }
}
