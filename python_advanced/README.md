# SQL ML — Python External Function 进阶

> 5 个 ML/PII 函数，基于 scikit-learn + jieba，演示第三方依赖打包

---

## 函数列表

| 函数 | 用到的库 | 输入 | 输出 |
|------|---------|------|------|
| `pii_mask` | re (标准库) | 文本 | 脱敏文本 + 检测统计 |
| `feature_normalize` | numpy + sklearn | JSON 数组 | Min-Max / Z-Score 归一化 |
| `anomaly_detect` | numpy + sklearn | JSON 数组 | IsolationForest 异常值 |
| `sentiment_score` | jieba | 文本 | 0~1 情感分数 |
| `tfidf_keywords` | sklearn | JSON 文档数组 | TF-IDF 关键词 |

---

## 前置条件

已完成 `../python_quickstart/`，阿里云 OSS / FC / RAM 角色已就绪。

---

## 1. 填写配置

```bash
cp config.example.json config.json
```

与 quickstart 配置项相同，填好的话复制一份过来。

---

## 2. 打包（含 Linux scikit-learn + jieba 依赖）

```bash
python 2-package.py
```

产物：`dist/ml_toolkit.zip`（~100 MB，含完整 Linux scikit-learn / numpy / scipy / jieba）

`2-package.py` 分两步安装依赖：
- **binary 依赖**（scikit-learn + numpy）：用 `--platform manylinux2014_x86_64 --only-binary :all:` 下载 Linux 版本
- **纯 Python 依赖**（jieba）：不加 platform 限制，直接安装跨平台 .py 文件

---

## 3. 部署

```bash
python 1-check-config.py
python 3-render-sql.py
cz-cli sql -f dist/4-deploy_generated.sql --write
```

---

## 4. 测试

```sql
-- PII 脱敏
SELECT <schema>.pii_mask('我的手机13812345678，邮箱alice@example.com，身份证310101199001011234');

-- 特征归一化（sklearn MinMaxScaler）
SELECT <schema>.feature_normalize('[10,20,30,40,50]', 'minmax');

-- 异常检测（sklearn IsolationForest）
SELECT <schema>.anomaly_detect('[1,2,3,4,100]');

-- 情感评分（jieba 分词）
SELECT <schema>.sentiment_score('产品质量非常好，物流很快，非常满意！');

-- TF-IDF 关键词（sklearn TfidfVectorizer）
SELECT <schema>.tfidf_keywords('["文档1","文档2","文档3"]', 3);
```

---

## 5. 如何扩展

`requirements.txt` 加需要的库 → `2-package.py` 重新打包 → 部署即可。

```bash
pip install your-package          # 本地测试
# 加到 requirements.txt 或 requirements_pure.txt
python 2-package.py               # 重新打包
cz-cli sql -f dist/4-deploy_generated.sql --write   # 重新部署
```

---

## 6. 清理

```bash
cz-cli sql -f dist/5-cleanup_generated.sql --write
```

---

## 附录：依赖打包原理

| 文件 | 内容 |
|------|------|
| `requirements.txt` | scikit-learn + numpy（binary，Linux manylinux wheel） |
| `requirements_pure.txt` | jieba（纯 Python，跨平台 .py） |
| `2-package.py` | 先装 binary 依赖，再装 pure Python |
