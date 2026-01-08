#!/usr/bin/env pwsh
# Configure bindgen compatibility headers for Windows
# Used by: ci-ruby.yaml - Configure bindgen compatibility headers step

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Write-Host "=== Configuring bindgen compatibility headers for Windows ===" -ForegroundColor Cyan
Write-Host ""

# Check environment
Write-Host "Environment check:" -ForegroundColor Yellow
Write-Host "  GITHUB_WORKSPACE: $env:GITHUB_WORKSPACE"
Write-Host "  Target: MSVC (x86_64-pc-windows-msvc)"
Write-Host ""

$includeRoot = "$env:GITHUB_WORKSPACE\packages\ruby\ext\kreuzberg_rb\native\include"
$compat = "$includeRoot\msvc_compat"

# Verify directories exist
Write-Host "Verifying include directories:" -ForegroundColor Yellow
if (Test-Path $includeRoot) {
    Write-Host "  [OK] Include root exists: $includeRoot" -ForegroundColor Green
} else {
    Write-Host "  [WARN] Include root missing: $includeRoot" -ForegroundColor Red
}

if (Test-Path $compat) {
    Write-Host "  [OK] MSVC compat directory exists: $compat" -ForegroundColor Green
} else {
    Write-Host "  [WARN] MSVC compat directory missing: $compat" -ForegroundColor Red
}
Write-Host ""

$includeRoot = $includeRoot -replace '\\','/'
$compatForward = $compat -replace '\\','/'

# NOTE: We intentionally do NOT use GCC include paths for bindgen.
# GCC intrinsic headers (ia32intrin.h, immintrin.h, etc.) are incompatible with Clang
# and cause parsing errors. Clang/LLVM uses its own built-in includes instead.
Write-Host "GCC include paths: Skipped (using Clang built-in includes instead)" -ForegroundColor Yellow
Write-Host ""

# Build the extra clang args with all necessary paths and flags
# NOTE: Do NOT add -blocklist-header flags here - those are bindgen CLI options, not clang options.
# Clang will misinterpret them as "-b locklist-header=xxx" which fails.
# NOTE: Do NOT add GCC include paths - GCC intrinsic headers are incompatible with Clang.
# Let Clang use its own built-in include paths instead.
$extra = "-I$includeRoot -I$compatForward -fms-extensions -fstack-protector-strong -fno-omit-frame-pointer -fno-fast-math"

# Check for Clang installation and add its include path if available
$llvmInclude = "C:/Program Files/LLVM/lib/clang"
if (Test-Path $llvmInclude) {
    # Find the latest clang version directory
    $clangVersionDir = Get-ChildItem -Path $llvmInclude -Directory | Sort-Object Name -Descending | Select-Object -First 1
    if ($clangVersionDir) {
        $clangInclude = "$($clangVersionDir.FullName)/include" -replace '\\','/'
        if (Test-Path $clangInclude) {
            $extra += " -isystem$clangInclude"
            Write-Host "  Added Clang include: $clangInclude" -ForegroundColor Green
        }
    }
}

# For MSVC target, we use the Windows SDK headers via clang's MSVC compatibility
# No sysroot needed - clang finds MSVC headers automatically on Windows
$extra += " --target=x86_64-pc-windows-msvc"
Write-Host "Target: x86_64-pc-windows-msvc" -ForegroundColor Green
Write-Host ""

# Check for clang
Write-Host "Checking for clang:" -ForegroundColor Yellow
$clangPath = Get-Command clang -ErrorAction SilentlyContinue
if ($clangPath) {
    Write-Host "  [OK] clang found: $($clangPath.Source)" -ForegroundColor Green
    try {
        $clangVersion = & clang --version 2>&1 | Select-Object -First 1
        Write-Host "  Version: $clangVersion" -ForegroundColor Green
    } catch {
        Write-Host "  [WARN] Could not get clang version" -ForegroundColor Yellow
    }
} else {
    Write-Host "  [WARN] clang not found in PATH" -ForegroundColor Red
    Write-Host "  PATH entries:" -ForegroundColor Yellow
    $env:PATH -split ';' | Select-Object -First 10 | ForEach-Object { Write-Host "    $_" }
}
Write-Host ""

# Set for MSVC target formats (bindgen uses different naming conventions)
Write-Host "Setting BINDGEN_EXTRA_CLANG_ARGS environment variables:" -ForegroundColor Yellow
Add-Content -Path $env:GITHUB_ENV -Value "BINDGEN_EXTRA_CLANG_ARGS=$extra"
Add-Content -Path $env:GITHUB_ENV -Value "BINDGEN_EXTRA_CLANG_ARGS_x86_64-pc-windows-msvc=$extra"
Add-Content -Path $env:GITHUB_ENV -Value "BINDGEN_EXTRA_CLANG_ARGS_x86_64_pc_windows_msvc=$extra"

Write-Host "  BINDGEN_EXTRA_CLANG_ARGS = $extra" -ForegroundColor Green
Write-Host ""
Write-Host "Configuration complete" -ForegroundColor Green
