#!/usr/bin/env bash
set -euo pipefail

echo "Setting up Go test app..."
go generate github.com/kreuzberg-dev/kreuzberg/packages/go/v4/...
GOWORK=off go mod tidy
echo "Setup complete."
