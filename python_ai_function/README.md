# Python 外部函数实战：30 个 AI SQL 函数

> 演示如何使用云器 Lakehouse 的 Python External Function，将 AI 模型封装为 SQL 函数 — SELECT 就能调用。

---

## 1. 是什么

把 30 个 AI 模型封装为云器 Lakehouse 外部函数，SELECT 就能调——这是最终效果。但更重要的，是把这整个流程跑通之后，你就知道怎么写自己的 External Function 了：包怎么打、依赖怎么处理、SQL 怎么建、出错了怎么排查。

| 类别 | 数量 | 函数 |
|------|------|------|
| 文本处理 | 8 | 摘要、翻译、情感、实体提取、关键词、分类、清理、标签 |
| 向量处理 | 5 | 向量化、相似度、聚类准备、相似搜索、文档搜索 |
| 多模态 | 8 | 图片描述、OCR、分析、向量化、相似度、视频摘要、图表分析、文档解析 |
| 业务场景 | 9 | 客户意图、销售评分、评论分析、风险检测、合同提取、简历解析、客户分群、产品描述、行业分类 |

---

## 2. 你需要什么

| 资源 | 为什么需要 | 获取方式 |
|------|-----------|----------|
| 云器 Lakehouse 实例 | SQL 就在这里跑 | 云器平台提供 |
| 阿里云 OSS Bucket | 存放代码包，函数计算从这里拉取 | 下文第 3 节 |
| 阿里云 RAM 角色 | 授权函数计算访问 OSS | 下文第 3 节 |
| 百炼 API Key | 调 AI 模型 | [百炼控制台](https://bailian.console.aliyun.com) |
| Python 3.10+ | 本地打包 | `python3 --version` |
| cz-cli | 连接云器 Lakehouse，需要安装和配置 | 见下文第 0 步 |

> **OSS、RAM 角色、函数计算必须在同一地域**。推荐 `cn-shanghai`。

---

## 0. 安装 cz-cli

详见 [cz-cli 使用指南](https://yunqi.tech/documents/cz-cli)。

---

## 3. 填写配置

先复制配置模板，然后打开，边看下文边填：

```bash
cp config.example.json config.json
```

`config.json` 含密钥，已在 `.gitignore` 中不会被提交。大部分字段用默认值，以下四步只改对应的几行。

### 第〇步：获取 schema

```bash
cz-cli sql "SELECT current_schema()"
```

把输出填到 `config.json` → `clickzetta.schema`。此字段决定函数建在哪个 schema 下，调用时也必须加这个前缀。

> 两套阿里云凭证，用途不同：
> - **AK/SK**（`aliyun.oss.access_id/key`）→ 云器 Lakehouse 用它们操作 External Volume（PUT 上传、列目录）
> - **RAM 角色**（`aliyun.ram.role_arn`）→ 函数计算扮演它从 OSS 读取代码包

### 第一项：开通函数计算 FC

外部函数运行时依赖阿里云函数计算。去 [函数计算控制台](https://fc.console.aliyun.com) 点"立即开通"（免费，按调用量计费）。已在用的是**华东 2（上海）**。

### 第二项：获取百炼 API Key

1. [百炼控制台](https://bailian.console.aliyun.com) → API Key 管理
2. 复制 Key，填入 `config.json` → `dashscope.api_key`

### 第三项：创建 OSS Bucket 并填入

1. [OSS 控制台](https://oss.console.aliyun.com) → 创建 Bucket
2. 地域选 **华东 2（上海）**，标准存储，私有
3. 创建后，将 Bucket 名填入 `config.json` → `aliyun.oss.bucket`
4. 同时需要一对 AccessKey：[RAM 用户管理](https://ram.console.aliyun.com/users) 找到你的用户，创建 AccessKey，填入 `config.json` → `aliyun.oss.access_id` / `aliyun.oss.access_key`

### 第四项：创建 RAM 角色并填入

1. [RAM 控制台](https://ram.console.aliyun.com) → 身份管理 → 角色 → 创建角色
2. 类型：**阿里云账号** → **其他云账号**
3. 账号 ID：`1384322691904283`（云器平台）
4. 角色名自定义，如 `czudfroleshanghai`
5. 创建完成后进入角色详情页 → 新增授权，添加 `AliyunFCFullAccess` + `AliyunOSSFullAccess`
6. 复制角色 ARN，填入 `config.json` → `aliyun.ram.role_arn`
7. 同一个阿里云账号，前面用的是你的 AK/SK 操作 Volume，这里创建的角色是给函数计算用来读 OSS 的

---

## 4. 打包

```bash
pip install -r requirements.txt           # 仅第一次需要
python 2-package.py --deps          # 含 Linux dashscope 依赖，约 15MB
```

产物：`dist/clickzetta_ai_functions_full.zip`

> `--deps` 读 `requirements.txt`，自动下载 Linux x86_64 平台的依赖包。不加 `--deps` 只打包代码（6KB）。

---

## 5. 部署

```bash
# 1. 检查配置
python 1-check-config.py

# 2. 生成部署 SQL（自动替换所有占位符）
python 3-render-sql.py

# 3. 执行（PUT 命令需通过 JDBC 客户端执行，cz-cli 支持）
cz-cli sql -f dist/deploy_generated.sql --write
```

`dist/deploy_generated.sql` 包含完整流程：Storage Connection → API CONNECTION → External Volume → PUT 上传 → CREATE EXTERNAL FUNCTION → 验证。

也可以复制到 Studio（或 JDBC 客户端）中逐段执行。**PUT 命令不支持 Web UI**，须通过 cz-cli 或 JDBC 客户端。

---

## 6. 验证

`3-render-sql.py` 已自动替换好，直接执行生成文件末尾的 SELECT 语句即可：

```sql
SELECT <你的schema>.ai_text_summarize('你好世界', '<你的api_key>');
SELECT <你的schema>.ai_text_to_embedding('测试', '<你的api_key>');
```

---

## 7. 函数调用

| 参数 | 必填 | 说明 |
|------|------|------|
| 业务参数 | 是 | text / image_url 等 |
| `api_key` | 是 | 百炼 API Key |
| `model_name` | 否 | 覆盖 `config.json` 中 models 的默认值 |

所有函数返回 JSON。调用时必须加 schema 前缀，用 `JSON_EXTRACT` 取值：

```sql
SELECT JSON_EXTRACT(<schema>.ai_text_summarize(content, 'key'), '$.summary') FROM articles;
```

---

## 8. 如何清理

```bash
cz-cli sql -f 5-cleanup.sql --write
```

依次删除所有函数、Volume、Connection。OSS Bucket 和 RAM 角色需去阿里云控制台手动删除。

---

## 9. 故障排查

| 错误 | 原因 | 解决 |
|------|------|------|
| `function not found` | Schema 不匹配 | `SHOW FUNCTIONS` 确认，加 schema 前缀 |
| `dashscope 不可用` | FC 缺少依赖 | `python 2-package.py --deps` 重新打包上传 |
| `HTTP_GENERAL_ERROR(640)` | FC 无法读 OSS | 见下方 [640 错误详解](#640) |
| `AccessDenied` | RAM 角色缺权限 | 加 `AliyunOSSFullAccess` |
| `Model access denied` | API Key 没开模型 | 百炼控制台开通 |

---

## 10. 常见问题

**Q: 换模型？** 改 `config.json` → `models`，重新打包部署。

**Q: 加自定义函数？** 在 `ai_functions_complete.py` 中参照 `@annotate` + `evaluate` 模式加类，重新打包。

**Q: `--deps` 和纯代码包怎么选？** FC 环境自带 dashscope 时用纯代码（6KB），否则用 `--deps`（15MB）。不确定就用 `--deps`。

---

### <a id="640"></a>HTTP_GENERAL_ERROR(640) 详解

这个错误表示函数计算无法从 OSS 读取代码包。通常有两个原因：

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

如果没有这段，点击编辑加进去。

2. **OSS Bucket 地域与函数计算不一致。** `config.json` 中 `aliyun.fc.region`、`aliyun.oss.endpoint`、Bucket 所在地域必须相同（都写 `cn-shanghai`）。

---

## 附录：脚本说明

| 文件 | 作用 |
|------|------|
| `config.example.json` | 配置模板，复制为 `config.json` 后填写。每项都有 `_用途` 注释 |
| `config.json` | 真实配置（gitignore），含密钥 |
| `1-check-config.py` | 检查 `config.json` 所有字段是否完整、格式是否正确 |
| `2-package.py` | 打包脚本。读取 `requirements.txt`，`--deps` 时下载 Linux 依赖并打包 |
| `3-render-sql.py` | 读取 `config.json`，将 `4-deploy.sql` 中的占位符替换为真实值 |
| `4-deploy.sql` | 部署模板。1→6 步：创建连接 → Volume → PUT → 函数 → 验证 |
| `5-cleanup.sql` | 删除所有函数、Volume、Connection |

执行顺序：1 → 2 → 3 → 4 → 5。

---

> **版本**: v1.0 | **适用平台**: 云器 Lakehouse + 阿里云函数计算
