#!/usr/bin/env bash
set -euo pipefail

echo "Running PHP tests..."
php vendor/bin/phpunit tests/
