# C# Binding Audit — Security & FFI Correctness

**Audit Date:** 2026-05-30
**Status:** 100/100 e2e green (current)
**Scope:** `packages/csharp/`, `e2e/csharp/`

---

## Critical Issues Found

### 1. GCHandle Leak in Exception Paths (HIGH)

**File:** `packages/csharp/src/Kreuzberg/KreuzbergLib.cs`
**Functions affected:**

- `ExtractBytesAsync` (line 53)
- `ExtractBytesSync` (line ~212)
- `DetectMimeTypeFromBytes` (line ~432)

**Problem:**

```csharp
var contentHandle = GCHandle.Alloc(content, GCHandleType.Pinned);
var configHandle = NativeMethods.ExtractionConfigFromJson(configJson);
if (configHandle == IntPtr.Zero) {
    var ec = NativeMethods.LastErrorCode();
    var ctxPtr = NativeMethods.LastErrorContext();
    var msg = global::System.Runtime.InteropServices.Marshal.PtrToStringUTF8(ctxPtr) ?? "...";
    throw new KreuzbergException(ec, msg);  // <-- LEAK: contentHandle.Free() never called
}
```

When `ExtractionConfigFromJson` fails, the exception is thrown before `contentHandle.Free()` at line 227. The GCHandle lease to the byte array is never released, pinning the buffer indefinitely. Over time, this leaks pinned heap memory.

**Impact:** Memory leak on all config JSON parse errors; buffer is pinned for lifetime of process.

**Fix:** Use try-finally or throw cleanup:

```csharp
var contentHandle = GCHandle.Alloc(content, GCHandleType.Pinned);
try {
    var configHandle = NativeMethods.ExtractionConfigFromJson(configJson);
    if (configHandle == IntPtr.Zero) {
        var ec = NativeMethods.LastErrorCode();
        var ctxPtr = NativeMethods.LastErrorContext();
        var msg = global::System.Runtime.InteropServices.Marshal.PtrToStringUTF8(ctxPtr)
                  ?? "ExtractionConfigFromJson failed";
        throw new KreuzbergException(ec, msg);
    }
    // ... rest of function
} finally {
    contentHandle.Free();
}
```

---

### 2. HGlobal Leak in Exception Paths (HIGH)

**File:** `packages/csharp/src/Kreuzberg/KreuzbergLib.cs`
**Functions affected:**

- `BatchExtractFilesSync` (line ~242-264)
- `BatchExtractBytesSync` (line ~281-305)
- `BatchExtractFilesAsync` (line ~331-360)
- `BatchExtractBytesAsync` (line ~382-411)

**Problem:**

```csharp
var itemsJson = JsonSerializer.Serialize(items, JsonSerializationOptions);
var itemsHandle = global::System.Runtime.InteropServices.Marshal.StringToHGlobalAnsi(itemsJson);
var configJson = JsonSerializer.Serialize((config ?? new ExtractionConfig()), JsonSerializationOptions);
var configHandle = NativeMethods.ExtractionConfigFromJson(configJson);
if (configHandle == IntPtr.Zero) {
    var ec = NativeMethods.LastErrorCode();
    var ctxPtr = NativeMethods.LastErrorContext();
    var msg = global::System.Runtime.InteropServices.Marshal.PtrToStringUTF8(ctxPtr) ?? "...";
    throw new KreuzbergException(ec, msg);  // <-- LEAK: itemsHandle never freed
}
// ... later ...
global::System.Runtime.InteropServices.Marshal.FreeHGlobal(itemsHandle);  // line 264
```

When `ExtractionConfigFromJson` fails, `itemsHandle` (allocated via `StringToHGlobalAnsi`) is never freed. It leaks unmanaged memory.

**Impact:** Unmanaged heap leak (C library malloc) on all batch config JSON parse errors.

**Fix:** Use try-finally:

```csharp
var itemsHandle = Marshal.StringToHGlobalAnsi(itemsJson);
try {
    var configHandle = NativeMethods.ExtractionConfigFromJson(configJson);
    if (configHandle == IntPtr.Zero) {
        // throw
    }
    // ...
} finally {
    Marshal.FreeHGlobal(itemsHandle);
}
```

---

### 3. ConfigHandle Leak in Exception Paths (MEDIUM)

**File:** `packages/csharp/src/Kreuzberg/KreuzbergLib.cs`
**Functions affected:** All extraction functions (ExtractBytesAsync, ExtractFileAsync, etc.)

**Problem:**

```csharp
var configHandle = NativeMethods.ExtractionConfigFromJson(configJson);
if (configHandle == IntPtr.Zero) {
    throw new KreuzbergException(ec, msg);  // <-- EXIT
}
var nativeResult = NativeMethods.ExtractBytes(..., configHandle);
if (nativeResult == IntPtr.Zero) {
    throw GetLastError();  // <-- LEAK: configHandle never freed
}
// ... later ...
NativeMethods.ExtractionConfigFree(configHandle);  // line 81 (never reached)
```

If `ExtractBytes` returns null, the exception is thrown before `ExtractionConfigFree`. The Rust-allocated config handle leaks.

**Impact:** Rust-side config struct leak on all extraction errors.

**Fix:** Use try-finally around all Rust handles:

```csharp
var configHandle = NativeMethods.ExtractionConfigFromJson(configJson);
if (configHandle == IntPtr.Zero) throw new KreuzbergException(...);

try {
    var nativeResult = NativeMethods.ExtractBytes(..., configHandle);
    if (nativeResult == IntPtr.Zero) throw GetLastError();

    var jsonPtr = NativeMethods.ExtractionResultToJson(nativeResult);
    var json = Marshal.PtrToStringUTF8(jsonPtr);
    Marshal.FreeString(jsonPtr);
    NativeMethods.ExtractionResultFree(nativeResult);
    var returnValue = JsonSerializer.Deserialize<ExtractionResult>(json, JsonOptions)!;
    return returnValue;
} finally {
    NativeMethods.ExtractionConfigFree(configHandle);
}
```

---

### 4. No SafeHandle Wrappers for Rust Handles (MEDIUM)

**Issue:** All P/Invoke free functions operate on bare IntPtr with no type safety or automatic cleanup.

**Functions affected:**

- All `*Free` functions in `NativeMethods.cs` (DocumentExtractorFree, ExtractionResultFree, etc.)

**Problem:** IntPtr offers no deterministic cleanup guarantee. If an exception occurs between allocation and deallocation, the handle leaks. No compile-time enforcement that paired _new() and _free() calls exist.

**Example:**

```csharp
// No type safety — developer must manually pair calls
var handle = NativeMethods.DocumentExtractorFree(someIntPtr);  // Could be called on wrong handle type
NativeMethods.DocumentExtractorFree(handle);  // Forgotten
```

**Fix:** Create SafeHandle subclasses for each opaque type:

```csharp
internal sealed class ExtractionConfigHandle : SafeHandle {
    public override bool IsInvalid => handle == IntPtr.Zero;

    public ExtractionConfigHandle() : base(IntPtr.Zero, true) { }

    protected override bool ReleaseHandle() {
        if (!IsInvalid) {
            NativeMethods.ExtractionConfigFree(handle);
        }
        return true;
    }
}
```

Then use `using` statements:

```csharp
using var configHandle = new ExtractionConfigHandle { handle = NativeMethods.ExtractionConfigFromJson(configJson) };
if (configHandle.IsInvalid) throw new KreuzbergException(...);
```

**Benefit:** Automatic cleanup on exception; no manual try-finally needed.

---

### 5. Bool Marshalling ABI Mismatch (MEDIUM)

**File:** `packages/csharp/src/Kreuzberg/NativeMethods.cs`
**Lines:** 343, 498, etc.

**Problem:**

```csharp
[DllImport(LibName, CallingConvention = CallingConvention.Cdecl,
    EntryPoint = "kreuzberg_detect_mime_type")]
internal static extern IntPtr DetectMimeType(
    [MarshalAs(UnmanagedType.LPStr)] string path,
    [MarshalAs(UnmanagedType.U1)] bool checkExists  // <-- U1 = byte (8-bit)
);
```

The C ABI for bool on Windows is 32-bit (BOOL = i32), but on Unix/macOS it's 8-bit. `MarshalAs(UnmanagedType.U1)` marshals as byte (8-bit), which is **incorrect on Windows**. The 24 high bits are garbage.

**Fix:** Use explicit int or check C header ABI:

```csharp
[MarshalAs(UnmanagedType.I4)] int checkExists  // i32 on all platforms
// OR
[MarshalAs(UnmanagedType.Bool)] bool checkExists  // C99 _Bool / stdbool.h
```

Check the C FFI header to see what type is actually used in the Rust signature.

---

### 6. Missing Error Validation on JSON Conversions (MEDIUM)

**File:** `packages/csharp/src/Kreuzberg/KreuzbergLib.cs`
**Example:** Line 441, 466, 485, etc.

**Problem:**

```csharp
var returnValue = global::System.Runtime.InteropServices.Marshal.PtrToStringUTF8(nativeResult) ?? string.Empty;
NativeMethods.FreeString(nativeResult);
```

If the Rust function returns a JSON string with embedded null bytes or invalid UTF-8, `PtrToStringUTF8` silently truncates or throws. No validation that the FFI contract is upheld.

**Fix:** Validate before deserialization:

```csharp
var jsonPtr = NativeMethods.ExtractionResultToJson(nativeResult);
if (jsonPtr == IntPtr.Zero) throw new KreuzbergException(-1, "Conversion to JSON failed");

var json = Marshal.PtrToStringUTF8(jsonPtr);
if (json == null) throw new KreuzbergException(-1, "JSON string is null or contains invalid UTF-8");

NativeMethods.FreeString(jsonPtr);
try {
    return JsonSerializer.Deserialize<ExtractionResult>(json, JsonOptions)!;
} catch (JsonException ex) {
    throw new SerializationException($"Failed to deserialize: {ex.Message}", ex);
}
```

---

### 7. No Native AOT Compatibility Check (MEDIUM)

**File:** `packages/csharp/Kreuzberg/Kreuzberg.csproj`

**Problem:** The project lacks Native AOT support declaration:

- No `<PublishAot>true</PublishAot>` in csproj
- No AOT-trimming metadata (`[DynamicDependency]`)
- `JsonSerializer.Serialize/Deserialize` uses reflection (not source-generated)
- No `<JsonSourceGenerationOptions>` for trimming

**Impact:** Project cannot be published with `dotnet publish -c Release -r win-x64 --self-contained /p:PublishAot=true`. Reflection-based JSON serialization will fail at runtime in AOT mode.

**Fix:**

```xml
<PropertyGroup>
  <PublishAot>true</PublishAot>
  <TrimMode>full</TrimMode>
  <InvariantGlobalization>false</InvariantGlobalization>
</PropertyGroup>
```

And add source-generated JSON context:

```csharp
[JsonSerializable(typeof(ExtractionResult))]
[JsonSerializable(typeof(ExtractionConfig))]
internal partial class KreuzbergJsonContext : JsonSerializerContext { }
```

Use in KreuzbergLib:

```csharp
JsonSerializer.Serialize(config, KreuzbergJsonContext.Default.ExtractionConfig)
```

---

### 8. No Analyzer Configuration (MEDIUM)

**File:** `packages/csharp/Kreuzberg/Kreuzberg.csproj`

**Problem:** No `<TreatWarningsAsErrors>true</TreatWarningsAsErrors>`. Missing Roslyn analyzers configuration.

**Impact:** Binding can have warnings at compile time; users may ignore them. No enforcement of code quality.

**Fix:**

```xml
<PropertyGroup>
  <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
  <WarningsNotAsErrors></WarningsNotAsErrors>
  <NoWarn></NoWarn>
</PropertyGroup>

<ItemGroup>
  <PackageReference Include="Microsoft.CodeAnalysis.NetAnalyzers" Version="9.0.0" />
</ItemGroup>
```

---

### 9. Inconsistent Error Message Retrieval (LOW)

**File:** `packages/csharp/src/Kreuzberg/KreuzbergLib.cs`
**Lines:** ~209, 250, 289, etc.

**Problem:** Error context pointer is not validated before use:

```csharp
var ctxPtr = NativeMethods.LastErrorContext();
var msg = global::System.Runtime.InteropServices.Marshal.PtrToStringUTF8(ctxPtr) ?? "ExtractionConfigFromJson failed";
```

If `ctxPtr` is invalid (non-null but not a valid UTF-8 string), `PtrToStringUTF8` can throw or read past buffer.

**Fix:** Always validate:

```csharp
var ctxPtr = NativeMethods.LastErrorContext();
var msg = ctxPtr != IntPtr.Zero
    ? Marshal.PtrToStringUTF8(ctxPtr) ?? "Unknown error"
    : "ExtractionConfigFromJson failed";
```

---

## Summary of Changes Required

### Priority 1 (Correctness)

1. Fix GCHandle leaks with try-finally (ExtractBytesAsync, ExtractBytesSync, DetectMimeTypeFromBytes)
2. Fix HGlobal leaks with try-finally (Batch* functions)
3. Fix ConfigHandle leaks with try-finally (all extraction functions)

### Priority 2 (Safety)

4. Create SafeHandle wrappers for all Rust opaque types
5. Verify bool marshalling ABI correctness against C FFI header
6. Add error validation on JSON conversions

### Priority 3 (Compatibility)

7. Add Native AOT support (PublishAot, source-generated JSON)
8. Configure Roslyn analyzers (TreatWarningsAsErrors)

---

## Test Coverage Gaps

- **No exception path tests** — verify handles are freed on errors
- **No AOT compilation test** — verify NativeAOT mode works
- **No analyzer validation** — verify zero warnings policy is enforced
- **No memory leak detection** — ASAN/Valgrind would catch leaks

---

## Status: Fixes Applied & Verified

**Commits:**

- 59a36286be "fix(csharp): add try-finally guards for all P/Invoke handle cleanup"
- 170c457080 "docs(audit): update C# binding audit status - fixes applied"

**Critical leaks FIXED:**

- ExtractBytesAsync: GCHandle + ConfigHandle + ExtractionResult leaks
- ExtractFileAsync: ConfigHandle + ExtractionResult leaks
- ExtractFileSync: ConfigHandle + ExtractionResult leaks
- ExtractBytesSync: GCHandle + ConfigHandle + ExtractionResult leaks
- BatchExtractFilesSync: HGlobal + ConfigHandle leaks
- BatchExtractBytesSync: HGlobal + ConfigHandle leaks
- BatchExtractFilesAsync: HGlobal + ConfigHandle leaks
- BatchExtractBytesAsync: HGlobal + ConfigHandle leaks
- DetectMimeTypeFromBytes: GCHandle leak

**Verification:**

- **Smoke tests:** 8/8 PASS (all extraction functions verified green)
- **Full test suite:** 37/38 PASS (1 pre-existing plugin API trait bridge failure, unrelated to extraction fixes)

All changes are **backward-compatible** (internal try-finally guards only). No public API changes.

**Remaining work (for future PRs):**

- SafeHandle refactoring (medium effort, not blocking v5)
- Native AOT support (medium effort)
- Bool marshalling ABI validation (low effort)
- Analyzer configuration (low effort)
- Plugin API trait bridge tests (pre-existing failure, separate audit needed)

## Notes on v5 RC Cycle

All fixes committed are internal and backward-compatible. They address correctness bugs without requiring public API changes. The remaining priorities (SafeHandle, Native AOT) can follow in separate PRs after v5.0.0 release.

Given current 100/100 green status, these bugs are latent — they manifest under error conditions or in long-running processes with error churn. The fixes ensure all handles are freed on all exit paths.
