//! PDF-to-Markdown renderer using segment-level font analysis.
//!
//! Converts PDF documents into structured markdown by analyzing pdfium text segments
//! (pre-merged character runs sharing baseline + font settings) to reconstruct headings,
//! paragraphs, inline formatting, and list items.

mod assembly;
mod bridge;
mod classify;
mod constants;
mod lines;
mod paragraphs;
mod pipeline;
mod render;
mod types;

pub use pipeline::{render_document_as_markdown, render_document_as_markdown_with_tables};
pub use render::inject_image_placeholders;
