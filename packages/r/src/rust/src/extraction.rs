//! File and bytes extraction functions (sync + async via Tokio)

use crate::config::parse_config;
use crate::error::kreuzberg_error;
#[cfg(not(target_arch = "wasm32"))]
use crate::error::to_r_error;
use crate::result::extraction_result_to_list;
use extendr_api::prelude::*;

pub fn extract_file_sync_impl(path: &str, mime_type: Nullable<&str>, config_json: Nullable<&str>) -> extendr_api::Result<List> {
    #[cfg(not(target_arch = "wasm32"))]
    {
        let config = parse_config(config_json)?;
        let mime = match mime_type {
            Nullable::NotNull(m) => Some(m),
            Nullable::Null => None,
        };
        let result = kreuzberg::extract_file_sync(path, mime, &config).map_err(kreuzberg_error)?;
        extraction_result_to_list(result)
    }
    #[cfg(target_arch = "wasm32")]
    {
        let _ = (path, mime_type, config_json);
        Err("File extraction is not supported on WebAssembly".into())
    }
}

pub fn extract_file_impl(path: &str, mime_type: Nullable<&str>, config_json: Nullable<&str>) -> extendr_api::Result<List> {
    #[cfg(not(target_arch = "wasm32"))]
    {
        let config = parse_config(config_json)?;
        let mime = match mime_type {
            Nullable::NotNull(m) => Some(m),
            Nullable::Null => None,
        };
        let runtime = tokio::runtime::Runtime::new().map_err(to_r_error)?;
        let result = runtime
            .block_on(async { kreuzberg::extract_file(path, mime, &config).await })
            .map_err(kreuzberg_error)?;
        extraction_result_to_list(result)
    }
    #[cfg(target_arch = "wasm32")]
    {
        let _ = (path, mime_type, config_json);
        Err("Async file extraction is not supported on WebAssembly".into())
    }
}

pub fn extract_bytes_sync_impl(data: Raw, mime_type: &str, config_json: Nullable<&str>) -> extendr_api::Result<List> {
    let config = parse_config(config_json)?;
    let bytes = data.as_slice();
    let result = kreuzberg::extract_bytes_sync(bytes, mime_type, &config).map_err(kreuzberg_error)?;
    extraction_result_to_list(result)
}

pub fn extract_bytes_impl(data: Raw, mime_type: &str, config_json: Nullable<&str>) -> extendr_api::Result<List> {
    #[cfg(not(target_arch = "wasm32"))]
    {
        let config = parse_config(config_json)?;
        let bytes = data.as_slice();
        let runtime = tokio::runtime::Runtime::new().map_err(to_r_error)?;
        let result = runtime
            .block_on(async { kreuzberg::extract_bytes(bytes, mime_type, &config).await })
            .map_err(kreuzberg_error)?;
        extraction_result_to_list(result)
    }
    #[cfg(target_arch = "wasm32")]
    {
        extract_bytes_sync_impl(data, mime_type, config_json)
    }
}
