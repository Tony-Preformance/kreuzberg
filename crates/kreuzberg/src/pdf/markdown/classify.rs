//! Heading classification for paragraphs using font-size clustering.

use super::constants::{MAX_HEADING_DISTANCE_MULTIPLIER, MAX_HEADING_WORD_COUNT};
use super::types::PdfParagraph;

/// Classify paragraphs as headings or body using the global heading map.
pub(super) fn classify_paragraphs(paragraphs: &mut [PdfParagraph], heading_map: &[(f32, Option<u8>)]) {
    for para in paragraphs.iter_mut() {
        // Count actual words across all segments in the paragraph
        let word_count: usize = para
            .lines
            .iter()
            .flat_map(|l| l.segments.iter())
            .map(|s| s.text.split_whitespace().count())
            .sum();

        let heading_level = find_heading_level(para.dominant_font_size, heading_map);

        if let Some(level) = heading_level
            && word_count <= MAX_HEADING_WORD_COUNT
        {
            para.heading_level = Some(level);
        }
    }
}

/// Find the heading level for a given font size by matching against the cluster centroids.
pub(super) fn find_heading_level(font_size: f32, heading_map: &[(f32, Option<u8>)]) -> Option<u8> {
    if heading_map.is_empty() {
        return None;
    }
    if heading_map.len() == 1 {
        return heading_map[0].1;
    }

    let mut best_distance = f32::INFINITY;
    let mut best_level: Option<u8> = None;
    for &(centroid, level) in heading_map {
        let dist = (font_size - centroid).abs();
        if dist < best_distance {
            best_distance = dist;
            best_level = level;
        }
    }

    // Compute average inter-cluster gap
    let mut centroids: Vec<f32> = heading_map.iter().map(|(c, _)| *c).collect();
    centroids.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
    let gaps: Vec<f32> = centroids.windows(2).map(|w| (w[1] - w[0]).abs()).collect();
    let avg_gap = if gaps.is_empty() {
        f32::INFINITY
    } else {
        gaps.iter().sum::<f32>() / gaps.len() as f32
    };

    if best_distance > MAX_HEADING_DISTANCE_MULTIPLIER * avg_gap {
        return None;
    }

    best_level
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::pdf::hierarchy::SegmentData;

    fn make_paragraph(font_size: f32, segment_count: usize) -> PdfParagraph {
        let segments: Vec<SegmentData> = (0..segment_count)
            .map(|i| SegmentData {
                text: format!("word{}", i),
                x: i as f32 * 50.0,
                y: 700.0,
                width: 40.0,
                height: font_size,
                font_size,
                is_bold: false,
                is_italic: false,
                baseline_y: 700.0,
            })
            .collect();

        PdfParagraph {
            lines: vec![super::super::types::PdfLine {
                segments,
                baseline_y: 700.0,
                y_top: 700.0 - font_size,
                y_bottom: 700.0,
                dominant_font_size: font_size,
                is_bold: false,
                is_italic: false,
            }],
            dominant_font_size: font_size,
            heading_level: None,
            is_bold: false,
            is_italic: false,
            is_list_item: false,
        }
    }

    #[test]
    fn test_classify_heading() {
        let heading_map = vec![(18.0, Some(1)), (12.0, None)];
        let mut paragraphs = vec![make_paragraph(18.0, 3)];
        classify_paragraphs(&mut paragraphs, &heading_map);
        assert_eq!(paragraphs[0].heading_level, Some(1));
    }

    #[test]
    fn test_classify_body() {
        let heading_map = vec![(18.0, Some(1)), (12.0, None)];
        let mut paragraphs = vec![make_paragraph(12.0, 5)];
        classify_paragraphs(&mut paragraphs, &heading_map);
        assert_eq!(paragraphs[0].heading_level, None);
    }

    #[test]
    fn test_classify_too_many_segments_for_heading() {
        let heading_map = vec![(18.0, Some(1)), (12.0, None)];
        let mut paragraphs = vec![make_paragraph(18.0, 20)]; // > MAX_HEADING_WORD_COUNT
        classify_paragraphs(&mut paragraphs, &heading_map);
        assert_eq!(paragraphs[0].heading_level, None);
    }

    #[test]
    fn test_find_heading_level_empty_map() {
        assert_eq!(find_heading_level(12.0, &[]), None);
    }

    #[test]
    fn test_find_heading_level_single_entry() {
        assert_eq!(find_heading_level(12.0, &[(12.0, Some(1))]), Some(1));
    }

    #[test]
    fn test_find_heading_level_outlier_rejected() {
        let heading_map = vec![(12.0, None), (16.0, Some(2)), (20.0, Some(1))];
        // Font size 50.0 is way too far from any centroid
        assert_eq!(find_heading_level(50.0, &heading_map), None);
    }

    #[test]
    fn test_find_heading_level_close_match() {
        let heading_map = vec![(12.0, None), (16.0, Some(2)), (20.0, Some(1))];
        assert_eq!(find_heading_level(15.5, &heading_map), Some(2));
    }

    #[test]
    fn test_classify_few_segments_many_words_not_heading() {
        // 3 segments but each contains many words — total word count exceeds threshold
        let segments: Vec<SegmentData> = (0..3)
            .map(|i| SegmentData {
                text: "one two three four five six".to_string(),
                x: i as f32 * 200.0,
                y: 700.0,
                width: 180.0,
                height: 18.0,
                font_size: 18.0,
                is_bold: false,
                is_italic: false,
                baseline_y: 700.0,
            })
            .collect();

        let mut paragraphs = vec![PdfParagraph {
            lines: vec![super::super::types::PdfLine {
                segments,
                baseline_y: 700.0,
                y_top: 682.0,
                y_bottom: 700.0,
                dominant_font_size: 18.0,
                is_bold: false,
                is_italic: false,
            }],
            dominant_font_size: 18.0,
            heading_level: None,
            is_bold: false,
            is_italic: false,
            is_list_item: false,
        }];
        // 3 segments × 6 words = 18 words > MAX_HEADING_WORD_COUNT
        let heading_map = vec![(18.0, Some(1)), (12.0, None)];
        classify_paragraphs(&mut paragraphs, &heading_map);
        assert_eq!(paragraphs[0].heading_level, None);
    }
}
