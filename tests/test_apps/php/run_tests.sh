#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

# Set library paths for the Rust FFI extension
export DYLD_LIBRARY_PATH="$REPO_ROOT/target/release:${DYLD_LIBRARY_PATH:-}"
export LD_LIBRARY_PATH="$REPO_ROOT/target/release:${LD_LIBRARY_PATH:-}"

# Ensure PHP autoloader is available
if [ ! -d "$REPO_ROOT/packages/php/vendor" ]; then
  echo "Installing PHP dependencies..."
  (cd "$REPO_ROOT/packages/php" && composer install --no-interaction --quiet)
fi

# If the kreuzberg extension is not already loaded, try to load it via -d flag
PHP_EXT_ARGS=""
if ! php -m 2>/dev/null | grep -q kreuzberg; then
  KREUZBERG_LIB="$REPO_ROOT/target/release/deps/libkreuzberg_php.dylib"
  if [ ! -f "$KREUZBERG_LIB" ]; then
    KREUZBERG_LIB="$REPO_ROOT/target/release/libkreuzberg_php.so"
  fi
  if [ -f "$KREUZBERG_LIB" ]; then
    PHP_EXT_ARGS="-d extension=$KREUZBERG_LIB"
  fi
fi

echo "Running Kreuzberg PHP test suite..."
echo ""

php "$PHP_EXT_ARGS" "$SCRIPT_DIR/main.php"
