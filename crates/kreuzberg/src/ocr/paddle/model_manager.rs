//! Model download and cache management for PaddleOCR.

use std::path::{Path, PathBuf};
use crate::Result;
use super::config::{ModelVersion, PaddleOcrConfig};

/// Base URL for downloading PaddleOCR ONNX models.
const MODEL_BASE_URL: &str = "https://huggingface.co/mg-chao/paddle-ocr-onnx/resolve/main";

/// Manages PaddleOCR model files (download, cache, validation).
pub struct ModelManager {
    cache_dir: PathBuf,
    version: ModelVersion,
}

impl ModelManager {
    /// Create a new model manager.
    pub fn new(config: &PaddleOcrConfig) -> Self {
        Self {
            cache_dir: config.cache_dir.clone(),
            version: config.model_version,
        }
    }

    /// Ensure all required models are available, downloading if necessary.
    pub async fn ensure_models(&self) -> Result<ModelPaths> {
        // Create cache directory if it doesn't exist
        tokio::fs::create_dir_all(&self.cache_dir).await.map_err(|e| {
            crate::KreuzbergError::Io {
                message: format!("Failed to create model cache directory: {}", e),
                path: Some(self.cache_dir.clone()),
                source: Some(Box::new(e)),
            }
        })?;

        let (det_name, cls_name, rec_name) = self.version.model_names();

        let det_path = self.ensure_model(det_name).await?;
        let cls_path = self.ensure_model(cls_name).await?;
        let rec_path = self.ensure_model(rec_name).await?;

        Ok(ModelPaths {
            detection: det_path,
            classification: cls_path,
            recognition: rec_path,
        })
    }

    /// Ensure a single model file is available.
    async fn ensure_model(&self, model_name: &str) -> Result<PathBuf> {
        let model_path = self.cache_dir.join(model_name);

        if model_path.exists() {
            tracing::debug!("Model already cached: {}", model_path.display());
            return Ok(model_path);
        }

        tracing::info!("Downloading model: {}", model_name);
        self.download_model(model_name, &model_path).await?;

        Ok(model_path)
    }

    /// Download a model file from the repository.
    async fn download_model(&self, model_name: &str, dest: &Path) -> Result<()> {
        let url = format!("{}/{}", MODEL_BASE_URL, model_name);

        // TODO: Implement actual download using reqwest or ureq
        // For now, return an error indicating models need to be manually placed
        Err(crate::KreuzbergError::Ocr {
            message: format!(
                "Model download not yet implemented. Please manually download {} from {} to {}",
                model_name,
                url,
                dest.display()
            ),
            source: None,
        })
    }

    /// Validate that a model file is a valid ONNX file.
    #[allow(dead_code)]
    fn validate_model(&self, path: &Path) -> Result<()> {
        // Basic validation: check file exists and has reasonable size
        let metadata = std::fs::metadata(path).map_err(|e| {
            crate::KreuzbergError::Io {
                message: format!("Cannot access model file: {}", e),
                path: Some(path.to_path_buf()),
                source: Some(Box::new(e)),
            }
        })?;

        if metadata.len() < 1024 {
            return Err(crate::KreuzbergError::Validation {
                message: format!("Model file too small, possibly corrupted: {}", path.display()),
                source: None,
            });
        }

        Ok(())
    }
}

/// Paths to the three required PaddleOCR model files.
#[derive(Debug, Clone)]
pub struct ModelPaths {
    /// Detection model path
    pub detection: PathBuf,
    /// Classification model path
    pub classification: PathBuf,
    /// Recognition model path
    pub recognition: PathBuf,
}
