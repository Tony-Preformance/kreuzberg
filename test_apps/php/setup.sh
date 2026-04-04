#!/usr/bin/env bash
set -euo pipefail

echo "Setting up PHP test app..."
pie install kreuzberg/kreuzberg || echo "PIE install skipped (extension may already be loaded)"
composer install
echo "Setup complete."
