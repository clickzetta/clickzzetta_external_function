#!/usr/bin/env python3
"""打包 — Maven 编译 + zip 打包（需要 JDK 8+ / Maven 3+）"""
import os, sys, zipfile, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
JAR = os.path.join(ROOT, 'target', 'clickzetta-java-udf-1.0.0-jar-with-dependencies.jar')
OUT = os.path.join(ROOT, 'dist', 'all_udf.zip')

print("🔨 Maven 编译 ...")
subprocess.run(['mvn', 'clean', 'package', '-q'], cwd=ROOT, check=True)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as zf:
    zf.write(JAR, os.path.basename(JAR))

print(f"✅ {OUT} ({os.path.getsize(OUT)} bytes)")
