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

## 前置条件

已完成 `../python_quickstart/`，阿里云 OSS / FC / RAM 角色已就绪。

---

## 1. 填写配置

```bash
cp config.example.json config.json
```

与 quickstart 配置项相同。如果你已跑过 quickstart，直接复制那份 `config.json` 过来。

---

## 2. 打包 —— 理解第三方依赖打包

这是本示例的核心：**如何把 Python 第三方库和你的代码一起打包成 Function Compute 能执行的 zip**。

```bash
python 2-package.py
```

产物：`dist/ml_toolkit.zip`（~100 MB，含完整 Linux scikit-learn / scipy / numpy / jieba）。

### 为什么需要两次 pip install？

FC 运行时是 **Linux x86_64 + Python 3.10**。你在 macOS 上 `pip install` 拿到的是 macOS 的二进制文件（`.dylib`），放 FC 上完全跑不了。

`2-package.py` 分两步解决：

```
pip install --target pkg --platform manylinux2014_x86_64 --python-version 3.10 --only-binary :all: -r requirements.txt
```
→ 这一步告诉 pip："假装我是 Linux，只装预编译的 binary wheel"。拿到的是 scikit-learn + numpy + scipy 的 `.so` 文件（Linux ABI）。

```
pip install --target pkg -r requirements_pure.txt
```
→ 这一步不加 `--platform`，因为 jieba 没有预编译的 wheel（它是纯 Python 的 `.py` 文件）。纯 Python 包跨平台直接用。

### 为什么分两个 requirements 文件？

| 文件 | 类型 | 安装方式 |
|------|------|---------|
| `requirements.txt` | scikit-learn, numpy — 含 C 扩展的包 | `--only-binary :all:` + `--platform manylinux` |
| `requirements_pure.txt` | jieba — 纯 Python 的包 | 普通 `pip install` |

如果把 jieba 放进 `requirements.txt` 一起 `--only-binary :all:`，pip 会报错 "Could not find a version that satisfies the requirement"，因为 jieba 只有源码发布没有 binary wheel。

**记住这个规则：含 C 扩展的包放 `requirements.txt`，纯 Python 的包放 `requirements_pure.txt`。**

### 坑：为什么不能用我本机的 pip install？

本机（macOS）`pip install scikit-learn` 拿到的 `.so` 是 macOS ARM64 格式。FC 是 Linux x86_64，加载不了。这就是 `--platform manylinux2014_x86_64` 的作用——跨平台交叉下载。

### 坑：包太大怎么办？

scikit-learn + scipy ~100 MB 在 FC 冷启动（第一次请求）会慢几秒，之后缓存。如果不需异常检测功能，可以删掉 scikit-learn 的依赖，只保留 numpy (~20 MB)。

---

## 3. 部署

```bash
python 1-check-config.py      # 配置完整性检查
python 3-render-sql.py         # 渲染 SQL 模板
cz-cli sql -f dist/4-deploy_generated.sql --write
```

三层脚本的作用：
- `1-check-config.py`：预防性检查，避免部署到一半才发现 config 填错
- `3-render-sql.py`：将 `4-deploy.sql` 中的 `<xxx>` 占位符全部替换为 `config.json` 的实际值，同时渲染 `5-cleanup.sql`
- `cz-cli sql -f`：执行生成的 SQL，一次性走完 Connection → Volume → PUT → CREATE FUNCTION → 测试

---

## 4. 测试

```sql
-- PII 脱敏（手机号、邮箱、身份证自动识别）
SELECT <schema>.pii_mask('我的手机13812345678，邮箱alice@example.com，身份证310101199001011234');

-- 特征归一化（sklearn MinMaxScaler）
SELECT <schema>.feature_normalize('[10,20,30,40,50]', 'minmax');
SELECT <schema>.feature_normalize('[10,20,30,40,50]', 'zscore');

-- 异常检测（sklearn IsolationForest）
SELECT <schema>.anomaly_detect('[1,2,3,4,100]');

-- 情感评分（jieba 分词）
SELECT <schema>.sentiment_score('产品质量非常好，物流很快，非常满意！');
SELECT <schema>.sentiment_score('质量不行，太差了，很失望');

-- TF-IDF（sklearn TfidfVectorizer，char ngram 中文友好）
SELECT <schema>.tfidf_keywords('["AI和机器学习是未来方向","深度学习在图像识别取得突破","AI将改变各行各业"]', 3);
```

---

## 5. 调试：函数报错怎么查？

### 错误 1：`ImportError: No module named 'sklearn'`

`2-package.py` 没带 `--deps`（或没跑），zip 里只有代码没有 sklearn。重新打包。

### 错误 2：`OSError: cannot open shared object file`

打包时忘了 `--platform`，打包了 macOS 的 `.dylib`。FC 是 Linux，需要 `.so`。

### 错误 3：冷启动超时

首次调用需从 OSS 下载 100MB zip + 解压 + import sklearn，可能需要 5-10 秒。第二次就快了。如果超过 30 秒没返回，检查 OSS bucket 的地域是否和 FC 的 region 一致（不能跨地域）。

### 错误 4：结果不对但不报错

代码没异常，但逻辑不对（比如情感分析词库不匹配）。这种情况无法从 FC 日志排查——**先在本地测试好再部署**：

```bash
python3 -c "
import sys; sys.path.insert(0, 'src')
from ml_toolkit import sentiment_score
print(sentiment_score().evaluate('测试文本'))
"
```

---

## 6. 如何扩展

在 `src/ml_toolkit.py` 添加新的类（参照现有 `@annotate("*-&gt;string")` + `evaluate` 模式），需要的新库加到对应文件：

- 含 C 扩展的 → `requirements.txt`
- 纯 Python 的 → `requirements_pure.txt`

然后重新打包部署：

```bash
python 2-package.py
python 3-render-sql.py
cz-cli sql -f dist/4-deploy_generated.sql --write
```

---

## 7. 清理

```bash
cz-cli sql -f dist/5-cleanup_generated.sql --write
```

OSS Bucket 和 RAM 角色去阿里云控制台删除。

---

## 附录：脚本说明

| 文件 | 作用 |
|------|------|
| `config.example.json` | 配置模板 |
| `1-check-config.py` | 检查 config.json 完整性 |
| `2-package.py` | 打包代码 + Linux 依赖（~100 MB） |
| `3-render-sql.py` | 占位符替换 |
| `4-deploy.sql` | 部署 5 个函数并测试 |
| `5-cleanup.sql` | 清理 |
| `requirements.txt` | binary 依赖（scikit-learn, numpy） |
| `requirements_pure.txt` | 纯 Python 依赖（jieba） |

---

## 所有示例

```
clickzetta_external_function/
├── python_quickstart/   # 最简单，1 个函数
├── python_advanced/     # 5 个 ML/PII 函数 + 依赖打包（本示例）
├── python_ai_function/  # 30 个 AI 函数 + dashscope 依赖
└── java_udf/            # Java UDF/UDAF/UDTF
```
