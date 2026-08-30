#!/bin/bash
cd "$(dirname "$0")"
rm -f data/sessions/*.json 2>/dev/null || true
find data/media -mindepth 1 -maxdepth 1 -type d -exec rm -rf {} + 2>/dev/null || true
echo "Local demo session/media data cleared."
