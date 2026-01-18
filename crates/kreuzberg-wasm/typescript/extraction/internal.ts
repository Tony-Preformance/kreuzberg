/**
 * Internal extraction module helpers
 *
 * Provides internal utilities and access to the WASM module state.
 */

type WasmModule = {
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

type ModuleInfo = {
	name: () => string;
	version: () => string;
	free: () => void;
};

let wasm: WasmModule | null = null;
let initialized = false;

/**
 * Set the WASM module (internal use only)
 */
export function setWasmModule(module: WasmModule | null): void {
	wasm = module;
}

/**
 * Set the initialized flag (internal use only)
 */
export function setInitialized(value: boolean): void {
	initialized = value;
}

/**
 * Get the WASM module
 *
 * @returns The WASM module
 * @throws {Error} If WASM module is not loaded
 */
export function getWasmModule(): WasmModule {
	if (!wasm) {
		throw new Error("WASM module not loaded. Call initWasm() first.");
	}

	return wasm;
}

/**
 * Check if WASM module is initialized
 *
 * @returns True if WASM module is initialized
 */
export function isInitialized(): boolean {
	return initialized;
}
