/**
 * WASM Module Loader
 *
 * Handles WASM module loading, initialization, and state management.
 * Provides a clean interface for loading the Kreuzberg WASM module
 * with support for concurrent initialization calls.
 */

import { wrapWasmError } from "../adapters/wasm-adapter.js";
import { hasWasm, isBrowser } from "../runtime.js";
import { initializePdfiumAsync } from "./pdfium-loader.js";

export type WasmModule = {
	extractBytes: (data: Uint8Array, mimeType: string, config: Record<string, unknown> | null) => Promise<unknown>;
	extractBytesSync: (data: Uint8Array, mimeType: string, config: Record<string, unknown> | null) => unknown;
	batchExtractBytes: (
		dataList: Uint8Array[],
		mimeTypes: string[],
		config: Record<string, unknown> | null,
	) => Promise<unknown>;
	batchExtractBytesSync: (
		dataList: Uint8Array[],
		mimeTypes: string[],
		config: Record<string, unknown> | null,
	) => unknown;
	extractFile: (file: File, mimeType: string | null, config: Record<string, unknown> | null) => Promise<unknown>;
	batchExtractFiles: (files: File[], config: Record<string, unknown> | null) => Promise<unknown>;

	detectMimeFromBytes: (data: Uint8Array) => string;
	normalizeMimeType: (mimeType: string) => string;
	getMimeFromExtension: (extension: string) => string | null;
	getExtensionsForMime: (mimeType: string) => string[];

	loadConfigFromString: (content: string, format: string) => Record<string, unknown>;
	discoverConfig: () => Record<string, unknown>;

	version: () => string;
	get_module_info: () => ModuleInfo;

	register_ocr_backend: (backend: unknown) => void;
	unregister_ocr_backend: (name: string) => void;
	list_ocr_backends: () => string[];
	clear_ocr_backends: () => void;

	register_post_processor: (processor: unknown) => void;
	unregister_post_processor: (name: string) => void;
	list_post_processors: () => string[];
	clear_post_processors: () => void;

	register_validator: (validator: unknown) => void;
	unregister_validator: (name: string) => void;
	list_validators: () => string[];
	clear_validators: () => void;

	initialize_pdfium_render: (pdfiumWasmModule: unknown, localWasmModule: unknown, debug: boolean) => boolean;
	read_block_from_callback_wasm: (param: number, position: number, pBuf: number, size: number) => number;
	write_block_from_callback_wasm: (param: number, buf: number, size: number) => number;

	default?: () => Promise<void>;
};

export type ModuleInfo = {
	name: () => string;
	version: () => string;
	free: () => void;
};

/** WASM module instance */
let wasm: WasmModule | null = null;

/** Initialize flag */
let initialized = false;

/** Initialization error (if any) */
let initializationError: Error | null = null;

/** Initialization promise for handling concurrent init calls */
let initializationPromise: Promise<void> | null = null;

/**
 * Get the loaded WASM module
 *
 * @returns The WASM module instance or null if not loaded
 * @internal
 */
export function getWasmModule(): WasmModule | null {
	return wasm;
}

/**
 * Check if WASM module is initialized
 *
 * @returns True if WASM module is initialized, false otherwise
 */
export function isInitialized(): boolean {
	return initialized;
}

/**
 * Get initialization error if module failed to load
 *
 * @returns The error that occurred during initialization, or null if no error
 * @internal
 */
export function getInitializationError(): Error | null {
	return initializationError;
}

/**
 * Get WASM module version
 *
 * @throws {Error} If WASM module is not initialized
 * @returns The version string of the WASM module
 */
export function getVersion(): string {
	if (!initialized) {
		throw new Error("WASM module not initialized. Call initWasm() first.");
	}

	if (!wasm) {
		throw new Error("WASM module not loaded. Call initWasm() first.");
	}

	return wasm.version();
}

/**
 * Initialize the WASM module
 *
 * This function must be called once before using any extraction functions.
 * It loads and initializes the WASM module in the current runtime environment,
 * automatically selecting the appropriate WASM variant for the detected runtime.
 *
 * Multiple calls to initWasm() are safe and will return immediately if already initialized.
 *
 * @throws {Error} If WASM module fails to load or is not supported in the current environment
 *
 * @example Basic Usage
 * ```typescript
 * import { initWasm } from '@kreuzberg/wasm';
 *
 * async function main() {
 *   await initWasm();
 *   // Now you can use extraction functions
 * }
 *
 * main().catch(console.error);
 * ```
 *
 * @example With Error Handling
 * ```typescript
 * import { initWasm, getWasmCapabilities } from '@kreuzberg/wasm';
 *
 * async function initializeKreuzberg() {
 *   const caps = getWasmCapabilities();
 *   if (!caps.hasWasm) {
 *     throw new Error('WebAssembly is not supported in this environment');
 *   }
 *
 *   try {
 *     await initWasm();
 *     console.log('Kreuzberg initialized successfully');
 *   } catch (error) {
 *     console.error('Failed to initialize Kreuzberg:', error);
 *     throw error;
 *   }
 * }
 * ```
 */
export async function initWasm(): Promise<void> {
	if (initialized) {
		return;
	}

	if (initializationPromise) {
		return initializationPromise;
	}

	initializationPromise = (async () => {
		try {
			if (!hasWasm()) {
				throw new Error("WebAssembly is not supported in this environment");
			}

			let wasmModule: unknown;
			// Use const variables to make imports dynamic and bypass TypeScript's static module resolution.
			// This allows typecheck to pass when the WASM module hasn't been built yet (e.g., in CI).
			const pkgPath = "../pkg/kreuzberg_wasm.js";
			const fallbackPath = "./kreuzberg_wasm.js";
			try {
				wasmModule = await import(/* @vite-ignore */ pkgPath);
			} catch {
				wasmModule = await import(/* @vite-ignore */ fallbackPath);
			}
			wasm = wasmModule as unknown as WasmModule;

			if (wasm && typeof wasm.default === "function") {
				await wasm.default();
			}

			if (isBrowser() && wasm && typeof wasm.initialize_pdfium_render === "function") {
				initializePdfiumAsync(wasm).catch((error) => {
					console.warn("PDFium auto-initialization failed (PDF extraction disabled):", error);
				});
			}

			initialized = true;
			initializationError = null;
		} catch (error) {
			initializationError = error instanceof Error ? error : new Error(String(error));
			throw wrapWasmError(error, "initializing Kreuzberg WASM module");
		}
	})();

	return initializationPromise;
}
