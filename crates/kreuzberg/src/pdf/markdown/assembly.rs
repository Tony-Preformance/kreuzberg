//! Final markdown assembly from classified paragraphs, with optional table interleaving.

use super::render::render_paragraph_to_output;
use super::types::PdfParagraph;

/// Assemble final markdown string from classified paragraphs across all pages.
pub(super) fn assemble_markdown(pages: Vec<Vec<PdfParagraph>>) -> String {
    let mut output = String::new();

    for (page_idx, paragraphs) in pages.iter().enumerate() {
        if page_idx > 0 && !output.is_empty() {
            output.push_str("\n\n");
        }

        for (para_idx, para) in paragraphs.iter().enumerate() {
            if para_idx > 0 {
                output.push_str("\n\n");
            }
            render_paragraph_to_output(para, &mut output);
        }
    }

    output
}

#[cfg(test)]
mod tests {
    use crate::pdf::hierarchy::SegmentData;

    use super::super::types::PdfLine;
    use super::*;

    fn plain_segment(text: &str) -> SegmentData {
        SegmentData {
            text: text.to_string(),
            x: 0.0,
            y: 0.0,
            width: 0.0,
            height: 12.0,
            font_size: 12.0,
            is_bold: false,
            is_italic: false,
            baseline_y: 700.0,
        }
    }

    fn make_paragraph(text: &str, heading_level: Option<u8>) -> PdfParagraph {
        PdfParagraph {
            lines: vec![PdfLine {
                segments: vec![plain_segment(text)],
                baseline_y: 700.0,
                y_top: 688.0,
                y_bottom: 700.0,
                dominant_font_size: 12.0,
                is_bold: false,
                is_italic: false,
            }],
            dominant_font_size: 12.0,
            heading_level,
            is_bold: false,
            is_italic: false,
            is_list_item: false,
        }
    }

    #[test]
    fn test_assemble_markdown_basic() {
        let pages = vec![vec![
            make_paragraph("Title", Some(1)),
            make_paragraph("Body text", None),
        ]];
        let result = assemble_markdown(pages);
        assert_eq!(result, "# Title\n\nBody text");
    }

    #[test]
    fn test_assemble_markdown_empty() {
        let result = assemble_markdown(vec![]);
        assert_eq!(result, "");
    }

    #[test]
    fn test_assemble_markdown_multiple_pages() {
        let pages = vec![
            vec![make_paragraph("Page 1", None)],
            vec![make_paragraph("Page 2", None)],
        ];
        let result = assemble_markdown(pages);
        assert_eq!(result, "Page 1\n\nPage 2");
    }
}
