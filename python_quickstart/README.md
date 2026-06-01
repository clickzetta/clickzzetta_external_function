# Python External Function 快速入门

> 最简单的云器 Lakehouse Python 外部函数。零依赖，零 API Key，5 分钟跑通。

---

## 1. 安装 cz-cli

详见 [cz-cli 使用指南](https://yunqi.tech/documents/cz-cli)。

---

## 2. 环境准备（一次性）

按 [SETUP.md](../SETUP.md) 完成阿里云 OSS / FC / RAM 角色配置。

---

## 3. 填写配置

```bash
cp config.example.json config.json
```

把以下字段换成你自己的值：

```
schema       → cz-cli sql "SELECT current_schema()" 的输出
bucket       → SETUP.md 创建的 Bucket 名称
access_id    → SETUP.md 的 AccessKey ID
access_key   → SETUP.md 的 AccessKey Secret
role_arn     → SETUP.md 的角色 ARN
```

---

## 4. 部署

```bash
python ../check-config.py
python 2-package.py
python ../render-sql.py
cz-cli sql -f dist/4-deploy_generated.sql --write
```

看到 `HELLO WORLD` 就成功了。

### 常见坑

| 错误 | 原因 | 解决 |
|------|------|------|
| `function not found` | 没加 schema 前缀 | `SELECT <schema>.my_upper('hello')` |
| `HTTP_GENERAL_ERROR(640)` | RAM 信任策略未配 / Bucket 跨地域 | 见 [SETUP.md > 验证信任策略](../SETUP.md) |
| `AccessDenied` | RAM 角色缺 OSS 权限 | 角色详情 → 新增授权 → `AliyunOSSFullAccess` |
| PUT 执行后 404 | 多行 PUT 被注释行中断 | PUT 命令一行写完，不拆行 |
| `deploy_generated.sql` 不存在 | 没跑渲染 | `python ../render-sql.py` |

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
| 文件 | 作用 |
|------|------|
| `config.example.json` | 配置模板 |
| `2-package.py` | 打包为 zip（1 KB） |
| `4-deploy.sql` | 部署模板：Connection → Volume → PUT → CREATE FUNCTION → 测试 |
| `5-cleanup.sql` | 删除函数、Volume、Connection |
| `../check-config.py` | 检查配置（共享） |
| `../render-sql.py` | 占位符替换（共享） |
| `../SETUP.md` | 云环境准备（共享） |

---

## 接下来

- SQL ML（scikit-learn + jieba）→ `../python_advanced/`
- 30 个 AI 函数 + 第三方依赖 → `../python_ai_function/`
- Java UDF/UDAF/UDTF → `../java_udf/`
