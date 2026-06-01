#!/bin/bash
cd "$(dirname "$0")"
rm -f dist/ml_toolkit.zip
zip -j dist/ml_toolkit.zip src/ml_toolkit.py
echo "✅ dist/ml_toolkit.zip ($(du -h dist/ml_toolkit.zip | cut -f1))"
