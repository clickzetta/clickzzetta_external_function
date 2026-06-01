#!/bin/bash
# 打包 my_upper.zip — 只包含 my_upper.py
cd "$(dirname "$0")"
rm -f dist/my_upper.zip
zip -j dist/my_upper.zip src/my_upper.py
echo "✅ dist/my_upper.zip ($(du -h dist/my_upper.zip | cut -f1))"
