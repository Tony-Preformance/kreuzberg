//! Core types for the PDF-to-Markdown pipeline.

use crate::pdf::hierarchy::SegmentData;

/// A line of text composed of segments sharing a common baseline.
#[derive(Debug, Clone)]
pub(super) struct PdfLine {
    pub segments: Vec<SegmentData>,
    pub baseline_y: f32,
    #[allow(dead_code)]
    pub y_top: f32,
    #[allow(dead_code)]
    pub y_bottom: f32,
    pub dominant_font_size: f32,
    pub is_bold: bool,
    pub is_italic: bool,
}

/// A paragraph composed of lines, with optional heading classification.
#[derive(Debug, Clone)]
pub(super) struct PdfParagraph {
    pub lines: Vec<PdfLine>,
    pub dominant_font_size: f32,
    pub heading_level: Option<u8>,
    #[allow(dead_code)]
    pub is_bold: bool,
    #[allow(dead_code)]
    pub is_italic: bool,
    pub is_list_item: bool,
}
