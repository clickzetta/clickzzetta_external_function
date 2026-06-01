# Python External Function 快速入门

> 最简单的云器 Lakehouse Python 外部函数。零依赖，零 API Key，5 分钟跑通。

---

## 1. 安装 cz-cli

详见 [cz-cli 使用指南](https://yunqi.tech/documents/cz-cli)。

---

## 2. 准备阿里云资源

以下操作在阿里云控制台完成，一次性。

### 2.1 开通函数计算 FC

[函数计算控制台](https://fc.console.aliyun.com) → "立即开通" → 选择**华东 2（上海）**。

### 2.2 创建 OSS Bucket + 获取 AccessKey

[OSS 控制台](https://oss.console.aliyun.com) → 创建 Bucket：**地域**华东 2（上海），名称自定义。

[RAM 用户管理](https://ram.console.aliyun.com/users) → 点你的用户 → 创建 AccessKey，记下 ID 和 Secret。

### 2.3 创建 RAM 角色

[RAM 控制台](https://ram.console.aliyun.com) → 身份管理 → 角色 → 创建角色：

- 选择**阿里云账号** → **其他云账号**
- 账号 ID：`1384322691904283`
- 角色名自定义，如 `quickstart_role`
- 创建后 → **新增授权** → 添加 `AliyunFCFullAccess` + `AliyunOSSFullAccess`
- 复制角色 ARN

---

## 3. 填写配置

```bash
cp config.example.json config.json
```

把以下字段换成你自己的值：

```
schema       → cz-cli sql "SELECT current_schema()" 的输出
bucket       → 2.2 创建的 Bucket 名称
access_id    → 2.2 的 AccessKey ID
access_key   → 2.2 的 AccessKey Secret
role_arn     → 2.3 的角色 ARN
```

---

## 4. 部署

```bash
python 1-check-config.py
python 2-package.py
python 3-render-sql.py
cz-cli sql -f dist/4-deploy_generated.sql --write
```

看到 `HELLO WORLD` 就成功了。

### 常见坑

| 错误 | 原因 | 解决 |
|------|------|------|
| `function not found` | 没加 schema 前缀 | `SELECT <schema>.my_upper('hello')` |
| `HTTP_GENERAL_ERROR(640)` | RAM 角色没配信任策略 / Bucket 跨地域 | RAM 控制台检查信任策略，确认 OSS 和 FC 都是 `cn-shanghai` |
| `AccessDenied` | RAM 角色缺 OSS 权限 | 角色详情 → 新增授权 → `AliyunOSSFullAccess` |
| PUT 执行后 404 | `cz-cli -f` 多行 PUT 解析失败 | PUT 命令前后不要有注释行 |
| `deploy_generated.sql` 不存在 | 没跑 `3-render-sql.py` | `python 3-render-sql.py` |

---

## 5. 代码

`src/my_upper.py`，一个类、一个 `evaluate` 方法：

```python
@annotate("*->string")
class my_upper(object):
    def evaluate(self, s):
        return s.upper() if s else s
```

---

## 6. 清理

```bash
cz-cli sql -f dist/5-cleanup_generated.sql --write
```

OSS Bucket 和 RAM 角色去阿里云控制台手动删除。

---

## 附录：脚本说明

| 文件 | 作用 |
|------|------|
| `config.example.json` | 配置模板 |
| `1-check-config.py` | 检查 `config.json` 完整性 |
| `2-package.py` | 打包 `my_upper.py` 为 zip（1 KB） |
| `3-render-sql.py` | 将 `4-deploy.sql` 和 `5-cleanup.sql` 的占位符替换为 `config.json` 的值 |
| `4-deploy.sql` | 部署模板：Storage Connection → API Connection → Volume → PUT → CREATE FUNCTION → 测试 |
| `5-cleanup.sql` | 删除函数、Volume、Connection |

---

## 接下来

- SQL ML 实战（scikit-learn + jieba）→ `../python_advanced/`
- 30 个 AI 函数 + 第三方依赖 → `../python_ai_function/`
- Java UDF → `../java_udf/`
