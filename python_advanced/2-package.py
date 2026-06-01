#!/usr/bin/env python3
"""打包 — 代码 + Linux scikit-learn/numpy (binary) + jieba (pure Python)"""
import os, sys, zipfile, shutil, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, 'dist', 'ml_toolkit.zip')

def build():
    tmp = os.path.join(ROOT, '.pkg_tmp')
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)

    # 1. 代码
    shutil.copy(os.path.join(ROOT, 'src', 'ml_toolkit.py'), tmp)

    pip_base = [sys.executable, '-m', 'pip', 'install', '--target', tmp,
                '--platform', 'manylinux2014_x86_64', '--python-version', '3.10']

    prj = os.path.dirname(__file__)

    # 2. binary 依赖 (scikit-learn + numpy)
    print("📦 scikit-learn + numpy (Linux binary) ...")
    subprocess.run(pip_base + ['--only-binary', ':all:',
                    '-r', os.path.join(prj, 'requirements.txt')], check=True)

    # 3. 纯 Python 依赖，无 platform 限制
    print("📦 jieba (pure Python) ...")
    subprocess.run([sys.executable, '-m', 'pip', 'install', '--target', tmp,
                    '-r', os.path.join(prj, 'requirements_pure.txt')], check=True)

    # 4. 打包
    print("📦 zip ...")
    with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as zf:
        for dirpath, _, files in os.walk(tmp):
            for f in files:
                path = os.path.join(dirpath, f)
                zf.write(path, os.path.relpath(path, tmp))

    size_mb = os.path.getsize(OUT) / 1024 / 1024
    print(f"✅ {OUT} ({size_mb:.1f} MB)")
    shutil.rmtree(tmp)

if __name__ == '__main__':
    build()
