use ort::session::Session;
use ort::value::Tensor;
use ort::{inputs, session::builder::SessionBuilder};
use std::collections::HashMap;

use crate::{base_net::BaseNet, ocr_error::OcrError, ocr_result::TextLine, ocr_utils::OcrUtils};

const CRNN_DST_HEIGHT: u32 = 48;
const MEAN_VALUES: [f32; 3] = [127.5, 127.5, 127.5];
const NORM_VALUES: [f32; 3] = [1.0 / 127.5, 1.0 / 127.5, 1.0 / 127.5];

#[derive(Debug)]
pub struct CrnnNet {
    session: Option<Session>,
    keys: Vec<String>,
    input_names: Vec<String>,
}

impl BaseNet for CrnnNet {
    fn new() -> Self {
        Self {
            session: None,
            keys: Vec::new(),
            input_names: Vec::new(),
        }
    }

    fn set_input_names(&mut self, input_names: Vec<String>) {
        self.input_names = input_names;
    }

    fn set_session(&mut self, session: Option<Session>) {
        self.session = session;
    }
}

impl CrnnNet {
    pub fn init_model(
        &mut self,
        path: &str,
        num_thread: usize,
        builder_fn: Option<fn(SessionBuilder) -> Result<SessionBuilder, ort::Error>>,
    ) -> Result<(), OcrError> {
        BaseNet::init_model(self, path, num_thread, builder_fn)?;

        self.keys = self.get_keys()?;

        Ok(())
    }

    pub fn init_model_dict_file(
        &mut self,
        path: &str,
        num_thread: usize,
        builder_fn: Option<fn(SessionBuilder) -> Result<SessionBuilder, ort::Error>>,
        dict_file_path: &str,
    ) -> Result<(), OcrError> {
        BaseNet::init_model(self, path, num_thread, builder_fn)?;

        self.read_keys_from_file(dict_file_path)?;

        Ok(())
    }

    pub fn init_model_from_memory(
        &mut self,
        model_bytes: &[u8],
        num_thread: usize,
        builder_fn: Option<fn(SessionBuilder) -> Result<SessionBuilder, ort::Error>>,
    ) -> Result<(), OcrError> {
        BaseNet::init_model_from_memory(self, model_bytes, num_thread, builder_fn)?;

        self.keys = self.get_keys()?;

        Ok(())
    }

    fn get_keys(&mut self) -> Result<Vec<String>, OcrError> {
        let session = self.session.as_ref().ok_or(OcrError::SessionNotInitialized)?;

        let metadata = session.metadata()?;
        let model_charater_list = metadata.custom("character").ok_or_else(|| {
            OcrError::Io(std::io::Error::new(
                std::io::ErrorKind::NotFound,
                "crnn_net character not found in metadata",
            ))
        })?;

        // Estimate capacity (safe division by using checked arithmetic)
        let capacity = if !model_charater_list.is_empty() {
            (model_charater_list.len() as f32 / 3.9) as usize
        } else {
            10 // default capacity if list is empty
        };
        let mut keys = Vec::with_capacity(capacity);

        keys.push("#".to_string());

        keys.extend(model_charater_list.split('\n').map(|s: &str| s.to_string()));

        keys.push(" ".to_string());

        Ok(keys)
    }

    fn read_keys_from_file(&mut self, path: &str) -> Result<(), OcrError> {
        let content = std::fs::read_to_string(path)?;
        let mut keys = Vec::new();

        // Prepend CTC blank token and append space token to match get_keys() layout.
        // The ONNX model's output index 0 = blank, last index = space.
        keys.push("#".to_string());
        keys.extend(content.split('\n').map(|s| s.to_string()));
        keys.push(" ".to_string());

        self.keys = keys;
        Ok(())
    }

    pub fn get_text_lines(
        &mut self,
        part_imgs: &[image::RgbImage],
        angle_rollback_records: &HashMap<usize, image::RgbImage>,
        angle_rollback_threshold: f32,
    ) -> Result<Vec<TextLine>, OcrError> {
        let mut text_lines = Vec::new();

        for (index, img) in part_imgs.iter().enumerate() {
            let mut text_line = self.get_text_line(img)?;

            if (text_line.text_score.is_nan() || text_line.text_score < angle_rollback_threshold)
                && let Some(angle_rollback_record) = angle_rollback_records.get(&index)
            {
                text_line = self.get_text_line(angle_rollback_record)?;
            }

            text_lines.push(text_line);
        }

        Ok(text_lines)
    }

    fn get_text_line(&mut self, img_src: &image::RgbImage) -> Result<TextLine, OcrError> {
        let Some(session) = &mut self.session else {
            return Err(OcrError::SessionNotInitialized);
        };

        let scale = CRNN_DST_HEIGHT as f32 / img_src.height() as f32;
        let dst_width = (img_src.width() as f32 * scale) as u32;

        let src_resize = image::imageops::resize(
            img_src,
            dst_width,
            CRNN_DST_HEIGHT,
            image::imageops::FilterType::Triangle,
        );

        let input_tensors = OcrUtils::substract_mean_normalize(&src_resize, &MEAN_VALUES, &NORM_VALUES);

        let input_tensors = Tensor::from_array(input_tensors)?;

        let outputs = session.run(inputs![self.input_names[0].clone() => input_tensors])?;

        let (_, red_data) = outputs.iter().next().ok_or_else(|| {
            OcrError::Io(std::io::Error::new(
                std::io::ErrorKind::InvalidData,
                "No output tensors found in CRNN session output",
            ))
        })?;

        let (shape, src_data) = red_data.try_extract_tensor::<f32>()?;
        let dimensions = shape;
        let height = *dimensions.get(1).ok_or_else(|| {
            OcrError::Io(std::io::Error::new(
                std::io::ErrorKind::InvalidData,
                "CRNN output tensor missing height dimension (index 1)",
            ))
        })? as usize;
        let width = *dimensions.get(2).ok_or_else(|| {
            OcrError::Io(std::io::Error::new(
                std::io::ErrorKind::InvalidData,
                "CRNN output tensor missing width dimension (index 2)",
            ))
        })? as usize;
        let src_data: Vec<f32> = src_data.to_vec();

        Self::score_to_text_line(&src_data, height, width, &self.keys)
    }

    fn score_to_text_line(
        output_data: &[f32],
        height: usize,
        width: usize,
        keys: &[String],
    ) -> Result<TextLine, OcrError> {
        let mut text_line = TextLine::default();
        let mut last_index = 0;

        let mut text_score_sum = 0.0;
        let mut text_score_count = 0;
        for i in 0..height {
            let start = i * width;
            let stop = (i + 1) * width;
            let slice = &output_data[start..stop.min(output_data.len())];

            let (max_index, max_value) =
                slice
                    .iter()
                    .enumerate()
                    .fold((0, f32::MIN), |(max_idx, max_val), (idx, &val)| {
                        if val > max_val { (idx, val) } else { (max_idx, max_val) }
                    });

            if max_index > 0 && max_index < keys.len() && !(i > 0 && max_index == last_index) {
                text_line.text.push_str(&keys[max_index]);
                text_score_sum += max_value;
                text_score_count += 1;
            }
            last_index = max_index;
        }

        // Avoid division by zero: handle case where no characters were found
        text_line.text_score = if text_score_count > 0 {
            text_score_sum / text_score_count as f32
        } else {
            0.0
        };
        Ok(text_line)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_score_to_text_line_skips_blank_index() {
        // keys[0] = "#" (CTC blank), keys[1] = "a", keys[2] = "b"
        let keys = vec!["#".to_string(), "a".to_string(), "b".to_string()];
        // 3 timesteps, 3 classes each. Simulate: blank, "a", "b"
        let output = vec![
            1.0, 0.0, 0.0, // timestep 0: max at index 0 (blank) -> skip
            0.0, 0.9, 0.1, // timestep 1: max at index 1 ("a")
            0.0, 0.1, 0.8, // timestep 2: max at index 2 ("b")
        ];
        let result = CrnnNet::score_to_text_line(&output, 3, 3, &keys).unwrap();
        assert_eq!(result.text, "ab");
    }

    #[test]
    fn test_score_to_text_line_deduplicates_consecutive() {
        let keys = vec!["#".to_string(), "h".to_string(), "i".to_string()];
        // 4 timesteps: "h", "h", "i", "i" -> should deduplicate to "hi"
        let output = vec![
            0.0, 0.9, 0.0, // "h"
            0.0, 0.8, 0.0, // "h" again (same index, skip)
            0.0, 0.0, 0.9, // "i"
            0.0, 0.0, 0.8, // "i" again (same index, skip)
        ];
        let result = CrnnNet::score_to_text_line(&output, 4, 3, &keys).unwrap();
        assert_eq!(result.text, "hi");
    }

    #[test]
    fn test_read_keys_from_file_has_blank_and_space() {
        let dir = std::env::temp_dir().join("kreuzberg_test_dict");
        std::fs::create_dir_all(&dir).unwrap();
        let dict_path = dir.join("test_dict.txt");
        std::fs::write(&dict_path, "a\nb\nc").unwrap();

        let mut net = CrnnNet::new();
        net.read_keys_from_file(dict_path.to_str().unwrap()).unwrap();

        // Should be: ["#", "a", "b", "c", " "]
        assert_eq!(net.keys[0], "#");
        assert_eq!(net.keys[1], "a");
        assert_eq!(net.keys[2], "b");
        assert_eq!(net.keys[3], "c");
        assert_eq!(net.keys[net.keys.len() - 1], " ");

        std::fs::remove_dir_all(&dir).ok();
    }
}
