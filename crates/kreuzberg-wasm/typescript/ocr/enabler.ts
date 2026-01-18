/**
 * OCR enabler module
 *
 * Provides convenient functions for enabling and setting up OCR backends.
 */

import { registerOcrBackend } from "../ocr/registry.js";
import { TesseractWasmBackend } from "../ocr/tesseract-wasm-backend.js";
import { isBrowser } from "../runtime.js";
import { isInitialized } from "../extraction/internal.js";

/**
 * Enable OCR functionality with tesseract-wasm backend
 *
 * Convenience function that automatically initializes and registers the Tesseract WASM backend.
 * This is the recommended approach for enabling OCR in WASM-based applications.
 *
 * ## Browser Requirement
 *
 * This function requires a browser environment with support for:
 * - WebWorkers (for Tesseract processing)
 * - createImageBitmap (for image conversion)
 * - Blob API
 *
 * ## Network Requirement
 *
 * Training data will be loaded from jsDelivr CDN on first use of each language.
 * Ensure network access to cdn.jsdelivr.net is available.
 *
 * @throws {Error} If not in browser environment or tesseract-wasm is not available
 *
 * @example Basic Usage
 * ```typescript
 * import { enableOcr, extractBytes, initWasm } from '@kreuzberg/wasm';
 *
 * async function main() {
 *   // Initialize WASM module
 *   await initWasm();
 *
 *   // Enable OCR with tesseract-wasm
 *   await enableOcr();
 *
 *   // Now you can use OCR in extraction
 *   const imageBytes = new Uint8Array(buffer);
 *   const result = await extractBytes(imageBytes, 'image/png', {
 *     ocr: { backend: 'tesseract-wasm', language: 'eng' }
 *   });
 *
 *   console.log(result.content); // Extracted text
 * }
 *
 * main().catch(console.error);
 * ```
 *
 * @example With Progress Tracking
 * ```typescript
 * import { enableOcr, TesseractWasmBackend } from '@kreuzberg/wasm';
 *
 * async function setupOcrWithProgress() {
 *   const backend = new TesseractWasmBackend();
 *   backend.setProgressCallback((progress) => {
 *     console.log(`OCR Progress: ${progress}%`);
 *     updateProgressBar(progress);
 *   });
 *
 *   await backend.initialize();
 *   registerOcrBackend(backend);
 * }
 *
 * setupOcrWithProgress().catch(console.error);
 * ```
 *
 * @example Multiple Languages
 * ```typescript
 * import { enableOcr, extractBytes, initWasm } from '@kreuzberg/wasm';
 *
 * await initWasm();
 * await enableOcr();
 *
 * // Extract English text
 * const englishResult = await extractBytes(engImageBytes, 'image/png', {
 *   ocr: { backend: 'tesseract-wasm', language: 'eng' }
 * });
 *
 * // Extract German text - model is cached after first use
 * const germanResult = await extractBytes(deImageBytes, 'image/png', {
 *   ocr: { backend: 'tesseract-wasm', language: 'deu' }
 * });
 * ```
 */
export async function enableOcr(): Promise<void> {
	if (!isInitialized()) {
		throw new Error("WASM module not initialized. Call initWasm() first.");
	}

	if (!isBrowser()) {
		throw new Error(
			"OCR is only available in browser environments. TesseractWasmBackend requires Web Workers and createImageBitmap.",
		);
	}

	try {
		const backend = new TesseractWasmBackend();
		await backend.initialize();

		registerOcrBackend(backend);
	} catch (error) {
		const message = error instanceof Error ? error.message : String(error);
		throw new Error(`Failed to enable OCR: ${message}`);
	}
}
