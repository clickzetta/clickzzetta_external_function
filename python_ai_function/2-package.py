#!/usr/bin/env python3
"""通用打包脚本 — 将项目代码打包为云器 Lakehouse 外部函数部署包

用法:
  python 2-package.py             纯代码（FC 运行时自带依赖）
  python 2-package.py --deps      代码 + requirements.txt 的 Linux 依赖
"""
import os, sys, zipfile, shutil, subprocess, argparse

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, 'dist', 'clickzetta_ai_functions_full.zip')

# 要打包的源文件（相对于项目根目录）
SOURCES = ['src/ai_functions_complete.py', 'config.json']


def build(with_deps=False):
    tmp = os.path.join(ROOT, '.pkg_tmp')
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)

    for src in SOURCES:
        path = os.path.join(ROOT, src)
        if os.path.exists(path):
            shutil.copy(path, tmp)

    if with_deps:
        req = os.path.join(ROOT, 'requirements.txt')
        if os.path.exists(req):
            print("📦 安装依赖（Linux x86_64）...")
            subprocess.run([
                sys.executable, '-m', 'pip', 'install',
                '-r', req,
                '--target', tmp,
                '--platform', 'manylinux2014_x86_64',
                '--python-version', '3.10',
                '--only-binary', ':all:',
            ], check=True)

    print("📦 打包 ...")
    with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as zf:
        for dirpath, _, files in os.walk(tmp):
            for f in files:
                path = os.path.join(dirpath, f)
                zf.write(path, os.path.relpath(path, tmp))

    kb = os.path.getsize(OUT) / 1024
    label, size = ("MB", kb / 1024) if kb >= 1024 else ("KB", kb)
    print(f"✅ {OUT}  ({size:.1f} {label})")
    shutil.rmtree(tmp)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description='通用外部函数打包工具')
    p.add_argument('--deps', action='store_true',
                   help='打包 requirements.txt 中的 Linux 依赖')
    build(with_deps=p.parse_args().deps)
