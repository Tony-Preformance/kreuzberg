//! Validation function wrappers

pub fn validate_ocr_backend_impl(_backend: &str) -> extendr_api::Result<bool> {
    // OCR backend validation is handled at registration time
    // For now, accept any non-empty string
    Ok(!_backend.is_empty())
}

pub fn validate_language_code_impl(_code_str: &str) -> extendr_api::Result<bool> {
    // Language code validation is flexible - accept standard codes
    Ok(!_code_str.is_empty())
}

pub fn validate_output_format_impl(_format: &str) -> extendr_api::Result<bool> {
    // Check known output formats
    Ok(matches!(_format, "text" | "plain" | "markdown" | "html" | "json" | "element_based" | "unified" | "djot"))
}
