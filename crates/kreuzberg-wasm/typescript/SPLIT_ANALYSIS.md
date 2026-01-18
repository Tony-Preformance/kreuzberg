# Index.ts Split Analysis

## Overview
The `index.ts` file (1,032 lines) serves as the main entry point for the Kreuzberg WASM module. It exports all public APIs and contains initialization logic, extraction functions, and OCR enablement functionality.

## File Statistics
- **Total Lines**: 1,032
- **Current File Location**: `/crates/kreuzberg-wasm/typescript/index.ts`
- **Organization**: Monolithic with multiple functional categories mixed together

---

## Detailed Inventory

### 1. Imports and Dependencies

#### Direct Imports (File-based)
```typescript
import { configToJS, fileToUint8Array, jsToExtractionResult, wrapWasmError } from "./adapters/wasm-adapter.js";
import { registerOcrBackend } from "./ocr/registry.js";
import { TesseractWasmBackend } from "./ocr/tesseract-wasm-backend.js";
import { detectRuntime, hasWasm, isBrowser } from "./runtime.js";
import type { ExtractionConfig as ExtractionConfigType, ExtractionResult } from "./types.js";
```

#### Re-exported Dependencies (passed through index.ts)
```typescript
// From adapters/wasm-adapter.js
configToJS, fileToUint8Array, isValidExtractionResult, jsToExtractionResult, wrapWasmError

// From ocr/registry.js
clearOcrBackends, getOcrBackend, listOcrBackends, registerOcrBackend, unregisterOcrBackend

// From ocr/tesseract-wasm-backend.js
TesseractWasmBackend

// From plugin-registry.js
clearPostProcessors, clearValidators, getPostProcessor, getValidator,
listPostProcessors, listValidators, registerPostProcessor, registerValidator,
unregisterPostProcessor, unregisterValidator, PostProcessor (type), Validator (type)

// From runtime.js
detectRuntime, getRuntimeInfo, getRuntimeVersion, getWasmCapabilities,
hasBigInt, hasBlob, hasFileApi, hasModuleWorkers, hasSharedArrayBuffer,
hasWasm, hasWasmStreaming, hasWorkers, isBrowser, isBun, isDeno, isNode,
isServerEnvironment, isWebEnvironment, RuntimeType (type), WasmCapabilities (type)

// From types.js
All type exports (Chunk, ChunkingConfig, ChunkMetadata, ExtractedImage,
ExtractionConfig, ExtractionResult, ImageExtractionConfig, LanguageDetectionConfig,
Metadata, OcrBackendProtocol, OcrConfig, PageContent, PageExtractionConfig,
PdfConfig, PostProcessorConfig, Table, TesseractConfig, TokenReductionConfig)
```

#### Dynamic Imports (runtime)
```typescript
// Line 335-337: WASM module loading
const pkgPath = "../pkg/kreuzberg_wasm.js";
const fallbackPath = "./kreuzberg_wasm.js";
try {
    wasmModule = await import(/* @vite-ignore */ pkgPath);
} catch {
    wasmModule = await import(/* @vite-ignore */ fallbackPath);
}

// Line 302: PDFium loading
const pdfiumModule = await import("./pdfium.js");

// Line 551, 560: Node.js fs/promises
const { readFile } = await import("node:fs/promises");

// Line 555-558: Deno runtime access
const deno = (globalThis as Record<string, unknown>).Deno as {
    readFile: (path: string) => Promise<Uint8Array>;
};
```

---

### 2. Internal State & Type Definitions

#### Module-level State (lines 231-240)
```typescript
let wasm: WasmModule | null = null;                    // WASM module instance
let initialized = false;                                // Initialization flag
let initializationError: Error | null = null;          // Error tracking
let initializationPromise: Promise<void> | null = null; // Concurrent init handling
```

#### Type Definitions
```typescript
// WasmModule interface (lines 176-223)
- extractBytes() / extractBytesSync()
- batchExtractBytes() / batchExtractBytesSync()
- extractFile() / batchExtractFiles()
- MIME type detection/normalization functions
- Configuration loading functions
- Version info
- OCR backend management
- Post-processor and validator management
- PDFium initialization
- Memory/block operations

// ModuleInfo interface (lines 225-229)
- name()
- version()
- free()
```

---

### 3. Exported Functions by Category

#### Category A: Initialization & Module State (5 functions)
**Purpose**: Load and manage WASM module lifecycle

1. **`initWasm(): Promise<void>`** (lines 314-360)
   - Main initialization entry point
   - Loads WASM module from package or fallback
   - Calls WASM default function if available
   - Triggers async PDFium initialization in browser
   - Handles concurrent init calls with promise caching
   - Implements try-catch with error wrapping

2. **`isInitialized(): boolean`** (lines 374-376)
   - Check initialization status
   - Simple state getter

3. **`getVersion(): string`** (lines 390-400)
   - Retrieve WASM module version
   - Requires initialization
   - Delegates to wasm.version()

4. **`getInitializationError(): Error | null`** (lines 409-411)
   - Retrieve any initialization error
   - Returns null if no error occurred
   - Internal API

5. **`initializePdfiumAsync(wasmModule: WasmModule): Promise<void>`** (lines 290-312)
   - Helper function for PDFium setup
   - Browser-only (checks isBrowser())
   - Dynamic import of pdfium.js
   - Handles both factory and module patterns
   - Graceful error handling with debug logging

#### Category B: Bytes Extraction - Basic (4 functions)
**Purpose**: Extract from raw document bytes

1. **`extractBytes(data, mimeType, config?): Promise<ExtractionResult>`** (lines 454-488)
   - Core async extraction function
   - Validates input (non-empty data, MIME type required)
   - Normalizes config with configToJS()
   - Calls wasm.extractBytes()
   - Result validation and conversion with jsToExtractionResult()
   - Error wrapping

2. **`extractBytesSync(data, mimeType, config?): ExtractionResult`** (lines 660-694)
   - Synchronous counterpart to extractBytes
   - Same validation and conversion flow
   - Calls wasm.extractBytesSync()
   - For use when async is not possible

3. **`extractFile(path, mimeType?, config?): Promise<ExtractionResult>`** (lines 525-582)
   - Extract from filesystem (Node.js, Deno, Bun)
   - Runtime detection with detectRuntime()
   - File reading per-runtime:
     - Node.js: fs.readFile
     - Deno: Deno.readFile
     - Bun: fs.readFile
   - MIME type detection via wasm.detectMimeFromBytes() if not provided
   - Normalization with wasm.normalizeMimeType()
   - Delegates to extractBytes()

4. **`extractFromFile(file, mimeType?, config?): Promise<ExtractionResult>`** (lines 616-639)
   - Browser-friendly File/Blob extraction
   - Wrapper around fileToUint8Array() and extractBytes()
   - Infers MIME type from file.type or defaults to 'application/octet-stream'
   - Normalizes MIME type
   - Error distinguishes between File and Blob

#### Category C: Batch Extraction (3 functions)
**Purpose**: Process multiple documents efficiently

1. **`batchExtractBytes(files, config?): Promise<ExtractionResult[]>`** (lines 717-783)
   - Batch async extraction from byte arrays
   - Input validation:
     - Array type check
     - Non-empty array required
     - Per-file validation (index-based error reporting):
       - Object type
       - data: Uint8Array
       - mimeType: string
       - data non-empty
   - Separate arrays for data and mimeTypes
   - Calls wasm.batchExtractBytes()
   - Result validation and per-item conversion
   - Index-aware error messages

2. **`batchExtractBytesSync(files, config?): ExtractionResult[]`** (lines 806-872)
   - Synchronous counterpart to batchExtractBytes
   - Identical validation logic
   - Calls wasm.batchExtractBytesSync()
   - Identical result processing

3. **`batchExtractFiles(files, config?): Promise<ExtractionResult[]>`** (lines 895-931)
   - Browser-friendly File array extraction
   - Input validation (array, non-empty, File type)
   - Per-file conversion with fileToUint8Array()
   - Infers MIME types or uses 'application/octet-stream' default
   - Delegates to batchExtractBytes()

#### Category D: OCR (1 function)
**Purpose**: Enable OCR capabilities

1. **`enableOcr(): Promise<void>`** (lines 1012-1032)
   - Initializes Tesseract WASM backend
   - Browser-only (checks isBrowser())
   - Creates TesseractWasmBackend instance
   - Calls backend.initialize()
   - Registers with registerOcrBackend()
   - Error handling with message extraction

---

### 4. Internal Helper Functions

#### Private/Internal Helpers (used within index.ts)
None explicitly private, but effectively internal:

1. **`initializePdfiumAsync()`** (lines 290-312)
   - Called from initWasm() as async void fire-and-forget
   - Not exported
   - Decoupled error handling (catch + console.warn)

#### Re-exported Helpers (from dependencies)
These are imported and re-exported from other modules:

**From adapters/wasm-adapter.js:**
- configToJS() - Converts TypeScript config to JS object
- fileToUint8Array() - Converts File/Blob to Uint8Array
- jsToExtractionResult() - Converts JS object to ExtractionResult
- wrapWasmError() - Wraps errors with context

**From runtime.js:**
- detectRuntime() - Identifies execution environment
- hasWasm() - Checks WASM support
- isBrowser() - Checks if browser environment

**From ocr/registry.js:**
- registerOcrBackend() - Registers OCR backend

---

### 5. Validation & Error Handling Patterns

#### Initialization Guards (used in every exported function)
```typescript
if (!initialized) {
    throw new Error("WASM module not initialized. Call initWasm() first.");
}

if (!wasm) {
    throw new Error("WASM module not loaded. Call initWasm() first.");
}
```

#### Input Validation Patterns
1. **Single bytes extraction**: Non-empty data, MIME type required
2. **File extraction**: Path required, runtime check
3. **Batch extraction**:
   - Array type verification
   - Non-empty array requirement
   - Per-item object structure validation
   - Per-item data validation
   - Index-specific error messages

#### Error Wrapping
All functions wrap errors with `wrapWasmError(error, context)` for consistent error messages.

---

## Proposed Split Structure

Based on the refactoring plan, here's how to organize the code:

### Target Directory Structure
```
typescript/
├── index.ts (re-exports from subdirectories)
├── initialization/
│   ├── wasm-loader.ts       (WASM module loading, ~60 lines)
│   └── pdfium-loader.ts     (PDFium initialization, ~25 lines)
├── extraction/
│   ├── bytes.ts             (extractBytes, extractBytesSync, ~50 lines)
│   ├── files.ts             (extractFile, extractFromFile, ~70 lines)
│   └── batch.ts             (batchExtractBytes, batchExtractBytesSync, batchExtractFiles, ~100 lines)
├── ocr/
│   └── enabler.ts           (enableOcr, ~25 lines)
├── state.ts                 (shared module state, ~10 lines)
└── types.ts (existing - contains type definitions)
```

### Migration Plan by Function

#### Phase 1: Extract Initialization Code
**Target**: `initialization/wasm-loader.ts` + `initialization/pdfium-loader.ts`

**Functions to migrate**:
- `initWasm()` (primary) → wasm-loader.ts
- `initializePdfiumAsync()` → pdfium-loader.ts
- `isInitialized()` → wasm-loader.ts or state.ts
- `getVersion()` → wasm-loader.ts or utils
- `getInitializationError()` → state.ts

**Dependencies needed**:
- `detectRuntime`, `hasWasm`, `isBrowser` from runtime.js
- `wrapWasmError` from adapters/wasm-adapter.js
- `configToJS`, `fileToUint8Array`, `jsToExtractionResult` (for other phases)

**Shared state**:
- `wasm: WasmModule | null`
- `initialized: boolean`
- `initializationError: Error | null`
- `initializationPromise: Promise<void> | null`

#### Phase 2: Extract Bytes Extraction Code
**Target**: `extraction/bytes.ts`

**Functions to migrate**:
- `extractBytes()`
- `extractBytesSync()`

**Dependencies**:
- Shared state from Phase 1
- `configToJS`, `jsToExtractionResult`, `wrapWasmError` from adapters
- WasmModule type

**Co-located validation**:
- Input validation (non-empty data, MIME type)
- Result validation

#### Phase 3: Extract File Extraction Code
**Target**: `extraction/files.ts`

**Functions to migrate**:
- `extractFile()`
- `extractFromFile()`

**Dependencies**:
- `extractBytes` from extraction/bytes.ts
- `detectRuntime`, `isBrowser` from runtime.js
- `fileToUint8Array`, `wrapWasmError` from adapters
- Node.js fs/promises (runtime import)
- Deno global (runtime check)

**Co-located validation**:
- File path required check
- Runtime compatibility check
- MIME type detection

#### Phase 4: Extract Batch Operations
**Target**: `extraction/batch.ts`

**Functions to migrate**:
- `batchExtractBytes()`
- `batchExtractBytesSync()`
- `batchExtractFiles()`

**Dependencies**:
- `extractBytes` from extraction/bytes.ts
- `fileToUint8Array`, `wrapWasmError` from adapters
- Shared state

**Co-located validation**:
- Array type checks
- Per-index error reporting
- File type validation

#### Phase 5: Extract OCR Setup
**Target**: `ocr/enabler.ts`

**Functions to migrate**:
- `enableOcr()`

**Dependencies**:
- `isBrowser` from runtime.js
- `TesseractWasmBackend` from ocr/tesseract-wasm-backend.js
- `registerOcrBackend` from ocr/registry.js
- Shared state

#### Phase 6: Consolidate State
**Target**: `state.ts`

**Exports**:
- `wasm: WasmModule | null`
- `initialized: boolean`
- `initializationError: Error | null`
- `initializationPromise: Promise<void> | null`
- Getter/setter functions if needed

#### Phase 7: Update index.ts
**New index.ts** (simplified re-export hub):
- Import and re-export initialization exports
- Import and re-export extraction exports
- Import and re-export OCR exports
- Maintain backward compatibility with all existing exports
- Keep type exports as-is

---

## Dependency Graph for Splitting

```
index.ts (current)
├── adapters/wasm-adapter.js
│   ├── configToJS
│   ├── fileToUint8Array
│   ├── jsToExtractionResult
│   └── wrapWasmError
├── ocr/registry.js
│   └── registerOcrBackend
├── ocr/tesseract-wasm-backend.js
│   └── TesseractWasmBackend
├── runtime.js
│   ├── detectRuntime
│   ├── hasWasm
│   └── isBrowser
└── types.js
    └── ExtractionConfig, ExtractionResult

After split:
initialization/wasm-loader.ts
├── Shared state (from state.ts)
├── runtime.js (detectRuntime, hasWasm)
├── adapters/wasm-adapter.js (wrapWasmError)
└── Dynamic imports (kreuzberg_wasm.js)

initialization/pdfium-loader.ts
├── Shared state (from state.ts)
├── runtime.js (isBrowser)
└── Dynamic imports (pdfium.js)

extraction/bytes.ts
├── Shared state (from state.ts)
├── adapters/wasm-adapter.js (configToJS, jsToExtractionResult, wrapWasmError)
└── types.js (ExtractionConfig, ExtractionResult)

extraction/files.ts
├── extraction/bytes.ts (extractBytes)
├── runtime.js (detectRuntime, isBrowser)
├── adapters/wasm-adapter.js (fileToUint8Array, wrapWasmError)
├── Shared state (from state.ts)
└── Dynamic imports (node:fs/promises, Deno global)

extraction/batch.ts
├── extraction/bytes.ts (extractBytes)
├── adapters/wasm-adapter.js (fileToUint8Array, wrapWasmError)
├── Shared state (from state.ts)
└── types.js (ExtractionResult)

ocr/enabler.ts
├── Shared state (from state.ts)
├── runtime.js (isBrowser)
├── ocr/tesseract-wasm-backend.js (TesseractWasmBackend)
└── ocr/registry.js (registerOcrBackend)

index.ts (new)
├── Re-exports from initialization/
├── Re-exports from extraction/
├── Re-exports from ocr/enabler.ts
├── Re-exports from existing dependencies
└── Type re-exports
```

---

## Summary Statistics

### By Category
| Category | Functions | Lines (est.) | Files |
|----------|-----------|--------------|-------|
| Initialization | 5 | 130 | 2 |
| Bytes Extraction | 2 | 90 | 1 |
| File Extraction | 2 | 120 | 1 |
| Batch Operations | 3 | 180 | 1 |
| OCR Setup | 1 | 25 | 1 |
| Shared State | 4 vars | 10 | 1 |
| **Total** | **17** | **~1,032** | **7** |

### Complexity Breakdown
- **Initialization**: Medium (dynamic imports, error handling, state management)
- **Bytes Extraction**: Low (input validation, delegation to WASM)
- **File Extraction**: Medium (runtime detection, file I/O abstractions)
- **Batch Operations**: Medium (array validation, index-specific error reporting)
- **OCR Setup**: Low (initialization wrapper)

### Shared Concerns
1. **State Management**: Module-level variables (4 variables)
2. **Initialization Guards**: Pattern repeated in every exported function
3. **Error Wrapping**: Consistent error handling via wrapWasmError()
4. **Runtime Detection**: Used in file extraction and OCR
5. **WASM Module Access**: Accessed by all extraction and batch functions

---

## Notes for Implementation

1. **State Consolidation**: Consider creating `state.ts` to reduce duplication of initialization checks
2. **Guard Pattern**: Consider extracting `assertInitialized()` helper to DRY up guard code
3. **Type Safety**: Maintain WasmModule type definition (may move to separate file or keep in initialization)
4. **PDFium Async Behavior**: Fire-and-forget async initialization should have clear documentation
5. **Error Messages**: Ensure consistency across split modules in error messages
6. **Re-export Completeness**: index.ts must re-export ALL current exports for backward compatibility
7. **Documentation**: Module-level JSDoc comments should be replicated or consolidated in index.ts
