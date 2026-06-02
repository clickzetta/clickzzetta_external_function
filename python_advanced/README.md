# SQL ML — Python External Function 进阶

> 5 个 ML/PII 函数，基于 scikit-learn + jieba，演示第三方依赖打包。

---

## 函数列表

| 函数 | 用到的库 | DDL 属性 |
|------|---------|---------|
| `pii_mask` | re | `python3.mc.v0` |
| `feature_normalize` | numpy + sklearn | `python3.mc.v0` |
| `anomaly_detect` | numpy + sklearn | `python3.mc.v0` |
| `sentiment_score` | jieba | `python3.mc.v0` |
| `tfidf_keywords` | sklearn | `python3.mc.v0` |

---

## 前置

[SETUP.md](../SETUP.md) 的云环境已完成。如已运行过 quickstart，直接复制那份 `config.json` 过来即可。

---

## 1. 打包与部署（在 `python_advanced/` 目录下执行）

```bash
python 2-package.py          # 打包代码 + Linux 依赖（~100 MB）
python ../1-check-config.py   # 检查配置
python ../3-render-sql.py     # 渲染 SQL
cz-cli sql -f dist/4-deploy_generated.sql --write  # 部署
```

产物：`dist/ml_toolkit.zip`。

### 为什么需要两次 pip install？

FC 运行时是 **Linux x86_64 + Python 3.10**。macOS 上 `pip install` 拿到的是 macOS 的 `.dylib`，FC 跑不了。

`2-package.py` 分两步解决：

**第一步 — 二进制依赖：**
```
pip install --target pkg --platform manylinux2014_x86_64 --python-version 3.10 --only-binary :all: -r requirements.txt
```
告诉 pip："假装我是 Linux，只装预编译的 binary wheel"。结果：`scikit-learn/numpy/scipy` 的 Linux `.so` 文件。

**第二步 — 纯 Python 依赖：**
```
pip install --target pkg -r requirements_pure.txt
```
不加 `--platform`，因为 jieba 是纯 `.py` 文件，跨平台直接用。

### 两个 requirements 文件的规则

| 文件 | 放什么 | 安装方式 |
|------|--------|---------|
| `requirements.txt` | 含 C 扩展的包（scikit-learn, numpy） | `--only-binary :all:` + `--platform manylinux` |
| `requirements_pure.txt` | 纯 Python 包（jieba） | 普通 `pip install` |

如果把纯 Python 包放进 `requirements.txt` 一起 `--only-binary :all:`，pip 会报 `No matching distribution found`。

---

## 2. 本地测试

部署前先在本地跑一下，确认代码没问题：

```bash
# 安装本地依赖用于测试
pip install -r requirements.txt -r requirements_pure.txt

# 逐个测试函数
python3 -c "
import sys; sys.path.insert(0, 'src')
from ml_toolkit import pii_mask, feature_normalize, sentiment_score
print(pii_mask().evaluate('我的手机13812345678'))
print(feature_normalize().evaluate('[1,2,3,4,5]', 'minmax'))
print(sentiment_score().evaluate('产品质量非常好'))
"
```

FC 环境没有 Python 日志，代码逻辑 bug 只能返回错误 JSON。**先测通再部署，省很多时间。**

---

## 3. 测试（SQL）

```sql
SELECT <schema>.pii_mask('我的手机13812345678，邮箱alice@example.com，身份证310101199001011234');
SELECT <schema>.feature_normalize('[10,20,30,40,50]', 'minmax');
SELECT <schema>.anomaly_detect('[1,2,3,4,100]');
SELECT <schema>.sentiment_score('产品质量非常好，物流很快，非常满意！');
SELECT <schema>.tfidf_keywords('["AI和机器学习是未来方向","深度学习在图像识别取得突破","AI将改变各行各业"]', 3);
```

---

### 注意事项

| 现象 | 原因 | 处理 |
|----|------|------|
| `ImportError: No module named 'sklearn'` | zip 里没 sklearn，打包时没跑 `2-package.py` | 重跑 `python 2-package.py` |
| `OSError: cannot open shared object file` | 打包了 macOS 的 `.dylib`，FC 需要 Linux `.so` | 确认 `2-package.py` 中 `--platform manylinux2014_x86_64` |
| 冷启动超时（>30s） | 100MB zip 从对象存储下载慢 | 检查 Bucket 和 FC 是否同地域，首次调用等 5-10 秒 |
| 结果不对但不报错 | 代码逻辑 bug，FC 没有 Python 日志 | 先 `python3 -c "from ml_toolkit import ..."` 本地测好再部署 |
| `function not found` | 没加 schema 前缀 | `SELECT <schema>.xxx(...)` |
| 改完 `config.json` 部署没变化 | 改了配置但没重新渲染 SQL | 重跑 `python ../3-render-sql.py` |

---

## 4. 如何扩展

加新库 → 对应 `requirements.txt` 或 `requirements_pure.txt` → 重新打包部署。

---

## 5. 清理

```bash
cz-cli sql -f dist/5-cleanup_generated.sql --write
```

对象存储 Bucket 和角色去对应云控制台删除。

---

## 附录：脚本说明

| 文件 | 作用 |
|------|------|
| `2-package.py` | 打包代码 + Linux 依赖（~100 MB） |
| `4-deploy.sql` | 部署 5 个函数并测试 |
| `5-cleanup.sql` | 清理 |
| `requirements.txt` | binary 依赖（scikit-learn, numpy） |
| `requirements_pure.txt` | 纯 Python 依赖（jieba） |
| `../config.example.json` | 配置模板（共享） |
| `../1-check-config.py` | 检查配置（共享） |
| `../3-render-sql.py` | 占位符替换（共享） |
| `../SETUP.md` | 云环境准备（共享） |

---

## 所有示例

```
clickzetta_external_function/
├── SETUP.md / 1-check-config.py / 3-render-sql.py / config.example.json    # 共享
├── python_quickstart/    # 最简单，1 个函数
├── python_advanced/      # 5 个 ML 函数 + 依赖打包（本示例）
├── python_ai_function/   # 30 个 AI 函数 + dashscope 依赖
└── java_udf/             # Java UDF/UDAF/UDTF
```
