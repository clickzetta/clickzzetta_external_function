# SQL ML — Python External Function 进阶

> 5 个 ML/PII 函数，让 SQL 具备数据处理能力 — 脱敏、归一化、异常检测、情感分析、关键词提取

---

## 前置条件

已完成 `../python_quickstart/`，阿里云 OSS / FC / RAM 角色已就绪。

---

## 函数列表

| 函数 | 输入 | 输出 | 场景 |
|------|------|------|------|
| `pii_mask` | 文本 | 脱敏后文本 + 检测统计 | 敏感数据合规 |
| `feature_normalize` | JSON 数组 | Min-Max / Z-Score 归一化 | ML 特征工程 |
| `anomaly_detect` | JSON 数组 | IQR 异常值 | 数据质量监控 |
| `sentiment_score` | 文本 | 0~1 情感分数 | 客服分析 |
| `tfidf_keywords` | JSON 文档数组 | TF-IDF 关键词 | 文本挖掘 |

全部零外部依赖，纯 Python 标准库实现。

---

## 1. 填写配置

```bash
cp config.example.json config.json
```

配置项与 quickstart 相同。如果已跑过 quickstart，填一样的值即可。

---

## 2. 部署

```bash
python 1-check-config.py
bash 2-package.sh
python 3-render-sql.py
cz-cli sql -f dist/4-deploy_generated.sql --write
```

---

## 3. 用法示例

### PII 脱敏

```sql
SELECT <schema>.pii_mask('我的手机13812345678，邮箱alice@example.com，身份证310101199001011234');
-- → {"masked": "我的手机<phone>，邮箱<email>，身份证<id_card>",
--    "detected": [{"type":"id_card","count":1},{"type":"email","count":1},{"type":"phone","count":1}]}
```

### 特征归一化

```sql
SELECT <schema>.feature_normalize('[10,20,30,40,50]', 'minmax');
-- → {"normalized": [0.0, 0.25, 0.5, 0.75, 1.0]}

SELECT <schema>.feature_normalize('[10,20,30,40,50]', 'zscore');
-- → Z-Score 标准化
```

### 异常检测

```sql
SELECT <schema>.anomaly_detect('[1,2,3,4,100]');
-- → {"outliers": [{"index":4, "value":100, "direction":"high"}]}
```

### 情感评分

```sql
SELECT <schema>.sentiment_score('产品质量非常好，物流很快，非常满意，推荐！');
-- → {"score": 1.0, "label": "positive"}

SELECT <schema>.sentiment_score('质量不行，太差了，很失望');
-- → {"score": 0.4, "label": "negative"}
```

### TF-IDF 关键词

```sql
SELECT <schema>.tfidf_keywords('["AI和机器学习是未来方向","深度学习在图像识别取得突破","AI将改变各行各业"]', 3);
-- → {"keywords": [[{"word":"AI","score":0.23},...],...]}
```

---

## 4. 清理

```bash
cz-cli sql -f dist/5-cleanup_generated.sql --write
```

---

## 附录：脚本说明

| 文件 | 作用 |
|------|------|
| `config.example.json` | 配置模板 |
| `1-check-config.py` | 检查 config.json |
| `2-package.sh` | 打包 ml_toolkit.py |
| `3-render-sql.py` | 替换占位符 |
| `4-deploy.sql` | 部署 5 个 ML 函数 |
| `5-cleanup.sql` | 清理 |

---

## 所有示例

```
clickzetta_external_function/
├── python_quickstart/   # 最简单，1 个函数
├── python_advanced/     # 5 个 ML/PII 函数（本示例）
├── python_ai_function/  # 30 个 AI 函数 + 第三方依赖
└── java_udf/            # Java 外部函数
```
