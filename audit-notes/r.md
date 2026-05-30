# R Binding Audit — Code Inspection Only

**Date:** 2026-05-30  
**Scope:** Code inspection of `/packages/r/` and `/e2e/r/` (no builds, no test execution)  
**Auditor:** Systematic bug audit (read-only inspection)

---

## Summary

**Total findings:** 11  
**By category:**
- BINDING_BUG: 5
- TEST_FIXTURE: 3
- ALEF_GAP: 2
- ROOT_CAUSE: 1

---

## Detailed Findings

### 1. BINDING_BUG — Runtime creation on every call (performance regression)
**File:** `/packages/r/src/rust/src/lib.rs`  
**Lines:** 11029–11039, 11201–11211 (batch_extract_bytes, embed_texts_async; similar pattern elsewhere)  
**Issue:**  
Each call to `batch_extract_bytes()`, `batch_extract_files()`, and `embed_texts_async()` creates a new Tokio runtime with `Runtime::new()`. This is a severe performance bottleneck — creating a runtime is O(milliseconds) per call and serializes across all calls. The docstring in extendr-wrappers.R (line 54) states "Uses the global Tokio runtime for 100x+ performance improvement" but the Rust code is creating a new runtime instead of using a global one.

**Suggested fix:**  
Initialize a global `lazy_static::Lazy<Tokio::Runtime>` or `OnceLock<Runtime>` at library load time. Replace `Runtime::new()` with a reference to the global runtime.

```rust
lazy_static::lazy_static! {
    static ref GLOBAL_RUNTIME: tokio::runtime::Runtime = 
        tokio::runtime::Runtime::new().expect("failed to create runtime");
}
// In functions: let result = GLOBAL_RUNTIME.block_on(async { ... });
```

---

### 2. BINDING_BUG — Error message truncation to 255 chars (info loss)
**File:** `/packages/r/src/rust/src/lib.rs`  
**Lines:** 11002–11012, 11043–11053, etc. (all error handling in wrapper functions)  
**Issue:**  
All error strings are truncated to 255 characters via `.chars().take(255).collect()`. Complex extraction errors with context chains and file paths will be silently truncated. R users see incomplete error messages, making debugging hard.

**Suggested fix:**  
Remove the truncation. R error strings can exceed 255 chars. If there's a real constraint, document it and raise an error instead of silently truncating.

---

### 3. BINDING_BUG — Runtime create per call creates nested runtime panic
**File:** `/packages/r/src/rust/src/lib.rs`  
**Lines:** 11029–11040, 11201–11211  
**Issue:**  
If a user calls `batch_extract_bytes()` from inside a Tokio async context (e.g., from a custom async plugin callback), the nested `Runtime::new()` will panic. Tokio does not allow nested runtime creation. This breaks the plugin bridge pattern where R callbacks might be called from async extraction code.

**Suggested fix:**  
Use a global runtime (see issue #1) or detect the runtime context and use `block_in_place()` if already in a runtime.

---

### 4. TEST_FIXTURE — Weak test assertions (always pass)
**File:** `/e2e/r/tests/test_batch.R`  
**Lines:** 8–58  
**Issue:**  
All batch tests end with `expect_true(TRUE)` (lines 10, 15, 21, 26, 32, 37, 42, 47, 52, 57). This makes every test pass regardless of whether the actual extraction succeeded. The test only validates that the R function was callable, not that results are correct. Tests should verify content, error states, or structural properties of the result.

**Suggested fix:**  
Replace `expect_true(TRUE)` with meaningful assertions. Example:
```r
expect_true(length(result) >= 1)
expect_true(is.list(result[[1]]))
expect_true(!is.null(result[[1]]$content))
```

---

### 5. TEST_FIXTURE — Weak embedding test assertions
**File:** `/e2e/r/tests/test_embeddings.R`  
**Lines:** 8–32  
**Issue:**  
Tests pass weak or no assertions. Line 10: `expect_true(TRUE)`. Line 26: checks for NULL, empty, or NA (valid for "unknown preset") but doesn't distinguish success from intentional fallback. Tests should validate that known presets return valid embeddings and unknown presets cleanly fail.

**Suggested fix:**  
```r
# For known preset, validate it returns a matrix/list of embeddings
result <- embed_texts(texts = c("Hello"), config = EmbeddingConfig$from_json(...))
expect_true(is.list(result))
expect_equal(length(result), 1)
expect_true(is.numeric(result[[1]]))

# For unknown preset, expect explicit NULL (not NA/empty)
result <- get_embedding_preset(name = "nonexistent-xyz")
expect_null(result)
```

---

### 6. TEST_FIXTURE — Plugin trait bridge test doesn't exercise trait calls
**File:** `/e2e/r/tests/test_plugin_api.R`  
**Lines:** 8–83  
**Issue:**  
Tests register trait-bridge plugins but never call their methods to verify the bridge works. Test at line 16 registers `register_document_extractor_trait_bridge` with an `extract_bytes` method, then immediately unregisters it without calling the bridge. If the bridge is broken, the test won't detect it.

**Suggested fix:**  
After registration, call the plugin method and validate the result:
```r
invisible(register_document_extractor(r_backend_register_document_extractor_trait_bridge))
# Try to use it in an extraction (or call it directly if API supports it)
# Then unregister
unregister_document_extractor("test-extractor")
```

---

### 7. ALEF_GAP — `output_format` field not exposed in Rust wrapper
**File:** `/packages/r/src/rust/src/lib.rs`  
**Lines:** 357  
**Issue:**  
In `ExtractionConfig::needs_image_processing()`, line 357 sets `output_format: Default::default()` instead of using `self.output_format`. This means any `output_format` configuration from the R-side config is silently ignored. The public API includes `output_format` field (line 247), but it's not actually used when checking image processing requirements.

**Suggested fix:**  
Change line 357 to:
```rust
output_format: self.output_format.clone(),
```

---

### 8. ALEF_GAP — `concurrency` field always default in needs_image_processing
**File:** `/packages/r/src/rust/src/lib.rs`  
**Lines:** 370  
**Issue:**  
Similar to issue #7: `concurrency: Default::default()` (line 370) ignores the R-configured concurrency value. If a user sets custom concurrency limits, they're lost when `needs_image_processing()` is called.

**Suggested fix:**  
Change line 370 to use the passed config's concurrency value (though this may require handling Option conversion).

---

### 9. ROOT_CAUSE — `render_pdf_page_to_png` page_index cast loses precision
**File:** `/packages/r/src/rust/src/lib.rs`  
**Lines:** 11244–11247  
**Issue:**  
R passes `page_index` as `f64` (floating-point), which is cast to `usize` via `as usize` (line 11247). If the user passes 0.5 or 1.9, truncation to integer silently occurs without error. This can cause off-by-one errors. The R signature should enforce integer type.

**Suggested fix:**  
- Change R wrapper signature to accept `integer` not `numeric`  
- Add validation before cast: `if page_index.fract() != 0.0 { return Err(...) }`

---

### 10. BINDING_BUG — Plugin bridge `r_obj.dollar()` error handling inconsistent
**File:** `/packages/r/src/rust/src/lib.rs`  
**Lines:** 11360–11382  
**Issue:**  
Plugin bridge validation (e.g., ROcrBackendBridge::new) checks `.dollar()` return for null/NA but doesn't distinguish "method missing" from "method returns NA". An R backend that returns NA from `name()` is treated as invalid. Also, error strings say "R object missing required method" but the real issue might be "method returned NA".

**Suggested fix:**  
```rust
match r_obj.dollar("name") {
    Ok(v) if !v.is_null() && !v.is_na() => {
        if let Some(s) = v.as_str() { ... }
        else { return Err("method 'name' did not return a string".to_string()); }
    }
    _ => return Err("method 'name' missing or returned NA".to_string()),
}
```

---

### 11. BINDING_BUG — Missing NA checking in optional parameter unwrap
**File:** `/packages/r/src/rust/src/lib.rs`  
**Lines:** 11244–11247 (render_pdf_page_to_png)  
**Issue:**  
Optional parameters like `dpi: Option<i32>` and `password: Option<String>` are passed through directly. If an R user passes `NA` (which extendr maps to `None`), it works correctly. However, the wrapper doesn't validate that numeric NA is distinct from explicit NULL. If extendr's NA-to-Option mapping is broken or inconsistent, this silently produces wrong behavior.

**Suggested fix:**  
Document the NA→None mapping clearly in roxygen docs. Add tests for NA parameter passing.

---

## Fixture Path Issues

All e2e tests use `.resolve_fixture()` (defined in `setup-fixtures.R` line 13–19) which searches for test_documents in `../../../test_documents` relative to the test directory. This path is correct for the e2e/r/tests/ → e2e/ → repo structure, but if tests are run from a different working directory, fixtures won't be found. No validation is performed; tests just fail silently.

---

## Blocked-on-Build Issues

The following items require a fresh build/test run to confirm:

1. **Runtime creation bottleneck** — performance regression vs global runtime. Requires profiling.
2. **Nested runtime panic** — only triggers if user calls batch functions from async context. Requires integration test that invokes extraction from a plugin callback.
3. **Plugin trait bridge functionality** — does the bridge actually invoke R closures? Requires running e2e tests.
4. **Fixture path resolution** — does `test_documents/` exist and are paths correct? Requires running tests.

---

## Dependency & Configuration Notes

**R Binding Cargo.toml** (`packages/r/src/rust/Cargo.toml`):
- extendr-api 0.9 (current)
- kreuzberg features: full, pdf, ocr, paddle-ocr, paddle-ocr-types, layout-detection, layout-types, embeddings, etc.
- tokio 1.x (multithreaded runtime feature)

No outstanding dep conflicts observed in syntax. However, the runtime creation pattern suggests the binding was written before tokio's global runtime was mature or before the cost of creating runtimes per call was understood.

---

## Recommendations

### Immediate (blocking production use):
1. Fix issue #1 (global runtime) — performance is severely degraded
2. Fix issue #2 (error truncation) — users can't debug failures
3. Fix issue #7, #8 (output_format, concurrency default) — config silently ignored

### High priority (correctness):
4. Fix issue #3 (nested runtime panic)
5. Fix issue #9 (page_index precision loss)
6. Fix issue #10 (plugin bridge error clarity)

### Medium priority (test quality):
7. Replace weak test assertions in issues #4, #5, #6
8. Add plugin trait bridge invocation test

### Documentation:
9. Clarify NA handling in roxygen docs
10. Document runtime and concurrency constraints

---

## Files Audited

- `/packages/r/DESCRIPTION` — Version 5.0.0.9003, extendr 0.4.2
- `/packages/r/NAMESPACE` — Generated by alef, 100+ exports
- `/packages/r/R/kreuzberg.R` — Auto-generated roxygen stub
- `/packages/r/R/extendr-wrappers.R` — 3052 lines of auto-generated wrappers
- `/packages/r/src/rust/src/lib.rs` — ~12,862 lines, hand-written + alef-generated
- `/packages/r/src/rust/Cargo.toml` — Dependency config
- `/e2e/r/tests/*.R` — 20 test files, all auto-generated by alef
- `/e2e/r/setup-fixtures.R` — Fixture path resolution
- `/e2e/r/run_tests.R` — Test runner

**Total lines inspected:** ~16,000 (Rust + R combined)

---

**Audit completed:** Code-only inspection. No cargo invocations, no test runs.
