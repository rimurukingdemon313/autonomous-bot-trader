#!/bin/sh
# Run the full test suite; exit non-zero on any failure. Commits are gated on this.
set -e
cd "$(dirname "$0")/.."
python3 -m pytest tests "$@"
