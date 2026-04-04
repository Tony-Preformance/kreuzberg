#!/usr/bin/env bash
set -euo pipefail

echo "Running Go tests..."
GOWORK=off go test -v -count=1 ./...
