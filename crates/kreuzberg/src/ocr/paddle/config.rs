//! Configuration for PaddleOCR backend.

use std::path::PathBuf;

/// Configuration for PaddleOCR backend.
#[derive(Debug, Clone)]
pub struct PaddleOcrConfig {
    /// Path to detection model (*.onnx)
    pub detection_model: Option<PathBuf>,

    /// Path to classification model (*.onnx)
    pub classification_model: Option<PathBuf>,

    /// Path to recognition model (*.onnx)
    pub recognition_model: Option<PathBuf>,

    /// Directory for caching downloaded models
    pub cache_dir: PathBuf,

    /// Number of threads for inference
    pub num_threads: usize,

    /// Model version to use (v3, v4, v5)
    pub model_version: ModelVersion,

    /// Whether to use GPU acceleration (requires CUDA)
    pub use_gpu: bool,

    /// Minimum confidence threshold for detection
    pub det_threshold: f32,

    /// Minimum confidence threshold for recognition
    pub rec_threshold: f32,

    /// Whether to enable angle classification
    pub enable_angle_cls: bool,
}

impl Default for PaddleOcrConfig {
    fn default() -> Self {
        Self {
            detection_model: None,
            classification_model: None,
            recognition_model: None,
            cache_dir: default_cache_dir(),
            num_threads: num_cpus::get().min(4),
            model_version: ModelVersion::V4,
            use_gpu: false,
            det_threshold: 0.3,
            rec_threshold: 0.5,
            enable_angle_cls: true,
        }
    }
}

/// PaddleOCR model version.
#[derive(Debug, Clone, Copy, Default, PartialEq, Eq)]
pub enum ModelVersion {
    /// PP-OCRv3 - Balanced accuracy and speed
    V3,
    /// PP-OCRv4 - Improved accuracy (recommended)
    #[default]
    V4,
    /// PP-OCRv5 - Latest with best accuracy
    V5,
}

impl ModelVersion {
    /// Get model file names for this version.
    pub fn model_names(&self) -> (&'static str, &'static str, &'static str) {
        match self {
            ModelVersion::V3 => (
                "ch_PP-OCRv3_det_infer.onnx",
                "ch_ppocr_mobile_v2.0_cls_infer.onnx",
                "ch_PP-OCRv3_rec_infer.onnx",
            ),
            ModelVersion::V4 => (
                "ch_PP-OCRv4_det_infer.onnx",
                "ch_ppocr_mobile_v2.0_cls_infer.onnx",
                "ch_PP-OCRv4_rec_infer.onnx",
            ),
            ModelVersion::V5 => (
                "ch_PP-OCRv5_det_infer.onnx",
                "ch_ppocr_mobile_v2.0_cls_infer.onnx",
                "ch_PP-OCRv5_rec_infer.onnx",
            ),
        }
    }
}

/// Get default cache directory for PaddleOCR models.
fn default_cache_dir() -> PathBuf {
    dirs::cache_dir()
        .unwrap_or_else(|| PathBuf::from("."))
        .join("kreuzberg")
        .join("paddle-ocr")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_default_config() {
        let config = PaddleOcrConfig::default();
        assert!(config.num_threads > 0);
        assert_eq!(config.model_version, ModelVersion::V4);
        assert!(!config.use_gpu);
    }

    #[test]
    fn test_model_names() {
        let (det, cls, rec) = ModelVersion::V4.model_names();
        assert!(det.contains("v4") || det.contains("V4"));
        assert!(cls.contains("cls"));
        assert!(rec.contains("rec"));
    }
}
