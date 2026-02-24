//! MIME type detection functions

use crate::error::to_r_error;
use extendr_api::prelude::*;

pub fn detect_mime_type_impl(data: Raw) -> extendr_api::Result<String> {
    let bytes = data.as_slice();
    kreuzberg::core::mime::detect_mime_type_from_bytes(bytes).map_err(to_r_error)
}

pub fn detect_mime_type_from_path_impl(path: &str) -> extendr_api::Result<String> {
    kreuzberg::core::mime::detect_mime_type(path, true).map_err(to_r_error)
}

pub fn get_extensions_for_mime_impl(mime_type: &str) -> extendr_api::Result<Strings> {
    let extensions = kreuzberg::core::mime::get_extensions_for_mime(mime_type).map_err(to_r_error)?;
    let r_strings: Vec<String> = extensions.iter().map(|s| s.to_string()).collect();
    Ok(Strings::from_values(r_strings))
}

pub fn validate_mime_type_impl(mime_type: &str) -> extendr_api::Result<bool> {
    Ok(kreuzberg::core::mime::validate_mime_type(mime_type).is_ok())
}
