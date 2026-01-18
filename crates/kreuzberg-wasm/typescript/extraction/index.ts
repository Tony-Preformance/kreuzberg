/**
 * Extraction module
 *
 * Provides comprehensive extraction functionality for various document formats.
 * Includes byte-based, file-based, and batch processing capabilities.
 */

export { extractBytes, extractBytesSync } from "./bytes.js";
export { batchExtractBytes, batchExtractBytesSync, batchExtractFiles } from "./batch.js";
export { extractFile, extractFromFile } from "./files.js";
export type { ExtractionResult, ExtractionConfig } from "../types.js";
