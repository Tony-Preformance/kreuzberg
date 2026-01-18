/**
 * PDFium WASM Loader
 *
 * Handles PDFium-specific WASM module loading and initialization.
 * Provides asynchronous loading of the PDFium WASM module with
 * proper error handling and browser environment detection.
 */

import { isBrowser } from "../runtime.js";
import type { WasmModule } from "./wasm-loader.js";

/**
 * Initialize PDFium WASM module asynchronously
 *
 * Loads and binds the PDFium WASM module for PDF extraction.
 * This function is designed for internal use and is called automatically
 * during WASM initialization in browser environments.
 *
 * PDFium provides high-performance PDF parsing and extraction capabilities,
 * enabling reliable text and metadata extraction from PDF documents.
 *
 * @param wasmModule - The loaded Kreuzberg WASM module
 *
 * @internal
 *
 * @example
 * ```typescript
 * // Called automatically during initWasm() in browser environments
 * // See wasm-loader.ts for integration
 * ```
 */
export async function initializePdfiumAsync(wasmModule: WasmModule): Promise<void> {
	if (!wasmModule || typeof wasmModule.initialize_pdfium_render !== "function") {
		return;
	}

	if (!isBrowser()) {
		console.debug("PDFium initialization skipped (non-browser environment)");
		return;
	}

	try {
		// @ts-expect-error - Dynamic module loading
		const pdfiumModule = await import("../pdfium.js");
		const pdfium = typeof pdfiumModule.default === "function" ? await pdfiumModule.default() : pdfiumModule;

		const success = wasmModule.initialize_pdfium_render(pdfium, wasmModule, false);
		if (!success) {
			console.warn("PDFium initialization returned false");
		}
	} catch (error) {
		console.debug("PDFium initialization error:", error);
	}
}
