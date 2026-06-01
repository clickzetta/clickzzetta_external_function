#!/usr/bin/env python3
"""打包 — 纯 Python 代码，零依赖"""
import os, zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, 'dist', 'my_upper.zip')

with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as zf:
    path = os.path.join(ROOT, 'src', 'my_upper.py')
    zf.write(path, os.path.basename(path))

print(f"✅ {OUT} ({os.path.getsize(OUT)} bytes)")
