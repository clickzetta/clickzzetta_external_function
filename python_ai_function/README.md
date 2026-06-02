# 30 个 AI SQL 函数 — Python External Function 完整示范

> 跑通之后你就知道怎么写 External Function 了：包怎么打、依赖怎么处理、SQL 怎么建、出错了怎么排查。

---

## 1. 安装 cz-cli + 环境准备

详见 [cz-cli 使用指南](https://yunqi.tech/documents/cz-cli)。

按 [SETUP.md](../SETUP.md) 完成阿里云 OSS / FC / RAM 角色配置（一次性，与 quickstart / advanced 共享）。

---

## 2. 获取百炼 API Key

打开 [百炼控制台](https://bailian.console.aliyun.com) → API Key 管理，复制 Key，后续填入 config.json → `dashscope.api_key`。

---

## 3. 填写配置

```bash
# 获取 schema
cz-cli sql "SELECT current_schema()"

# 复制配置模板
cp config.example.json config.json
```

打开 `config.json`，把以下字段换成你自己的值：

```
clickzetta.schema           → 上面 cz-cli 输出的 schema
dashscope.api_key            → 1.2 的百炼 API Key
aliyun.oss.bucket            → 1.3 的 Bucket 名称
aliyun.oss.access_id         → 1.3 的 AccessKey ID
aliyun.oss.access_key        → 1.3 的 AccessKey Secret
aliyun.ram.role_arn          → 1.4 的角色 ARN
aliyun.oss.endpoint          → oss-cn-shanghai.aliyuncs.com（不变）
aliyun.fc.region             → cn-shanghai（不变）
```

其余字段保持默认值。

---

## 3. 打包、检查、部署（在 `python_ai_function/` 目录下执行）

```bash
pip install -r requirements.txt
python 2-package.py --deps
python 1-check-config.py
python 3-render-sql.py
cz-cli sql -f dist/4-deploy_generated.sql --write
```

看到 AI 摘要返回结果就成功了。

---

## 4. 测试

部署时已自动执行测试（`deploy.sql` 末尾的 SELECT）。或在 `dist/4-deploy_generated.sql` 末尾找，也可以修改占位符后手动执行：

```sql
-- 摘要
SELECT <schema>.ai_text_summarize('人工智能正在改变世界。', '<api_key>');

-- 翻译
SELECT <schema>.ai_text_translate('Hello, how are you?', '中文', '<api_key>');

-- 向量化
SELECT <schema>.ai_text_to_embedding('机器学习很有趣', '<api_key>');

-- 语义相似度
SELECT <schema>.ai_semantic_similarity('苹果好吃', '苹果是健康水果', '<api_key>');
```

`<api_key>` 替换为 `config.json` → `dashscope.api_key` 的值。

所有函数返回 JSON，用 `JSON_EXTRACT` 取值：

```sql
SELECT JSON_EXTRACT(<schema>.ai_text_summarize(content, 'key'), '$.summary') FROM articles;
```

---

## 5. 清理

```bash
cz-cli sql -f dist/5-cleanup_generated.sql --write
```

OSS Bucket 和 RAM 角色去阿里云控制台手动删除。

---

## 故障排查

| 错误 | 原因 | 解决 |
|------|------|------|
| `function not found` | 没加 schema 前缀 | 调用时加 `<schema>.` 前缀 |
| `dashscope 不可用` | FC 没有依赖 | `python 2-package.py --deps` 重新打包上传 |
| `HTTP_GENERAL_ERROR(640)` | FC 读不了 OSS | 见下方 640 详解 |
| `AccessDenied` | RAM 角色缺 OSS 写权限 | 添加 `AliyunOSSFullAccess` |
| `Model access denied` | API Key 没开通该模型 | 百炼控制台开通对应模型 |

### <a id="640"></a>HTTP_GENERAL_ERROR(640) 详解

1. **RAM 角色信任策略未配。** 进 RAM 控制台 → 角色详情 → 信任策略，确认包含：

```json
{
  "Statement": [{
    "Action": "sts:AssumeRole",
    "Effect": "Allow",
    "Principal": { "RAM": ["acs:ram::1384322691904283:root"] }
  }],
  "Version": "1"
}
```

没有的话编辑加进去。

2. **地域不一致。** OSS Bucket、FC region、oss.endpoint 必须同地域（都是 `cn-shanghai`）。

---

## 附录：脚本说明

| 文件 | 作用 |
|------|------|
| `config.example.json` | 配置模板，复制为 `config.json` 后填写 |
| `config.json` | 真实配置（gitignore） |
| `1-check-config.py` | 检查 `config.json` 所有字段是否完整、格式是否正确 |
| `2-package.py` | 读取 `requirements.txt`，`--deps` 时下载 Linux 依赖并打包 |
| `3-render-sql.py` | 读取 `config.json`，将 `4-deploy.sql` 中的占位符替换为真实值 |
| `4-deploy.sql` | 部署模板。1→6 步：创建连接 → Volume → PUT → 函数 → 验证 |
| `5-cleanup.sql` | 删除所有函数、Volume、Connection |

---

## 函数列表

| 类别 | 数量 | 函数 |
|------|------|------|
| 文本处理 | 8 | 摘要、翻译、情感、实体提取、关键词、分类、清理、标签 |
| 向量处理 | 5 | 向量化、相似度、聚类准备、相似搜索、文档搜索 |
| 多模态 | 8 | 图片描述、OCR、分析、向量化、相似度、视频摘要、图表分析、文档解析 |
| 业务场景 | 9 | 客户意图、销售评分、评论分析、风险检测、合同提取、简历解析、客户分群、产品描述、行业分类 |
