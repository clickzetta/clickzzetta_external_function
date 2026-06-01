# 5 分钟入门：Python External Function

> 跑通云器 Lakehouse Python 外部函数的完整链路 — 零依赖，零 API Key。

---

## 1. 安装 cz-cli

详见 [cz-cli 使用指南](https://yunqi.tech/documents/cz-cli)。

---

## 2. 准备阿里云资源

以下操作在阿里云控制台完成，一次性。

### 2.1 开通函数计算 FC

打开 [函数计算控制台](https://fc.console.aliyun.com)，点击"立即开通"。选择**华东 2（上海）**。

### 2.2 创建 OSS Bucket + 获取 AccessKey

打开 [OSS 控制台](https://oss.console.aliyun.com) → 创建 Bucket：

- **Bucket 名称**：自定义，如 `my-udf-bucket`
- **地域**：华东 2（上海）
- 其他默认即可

打开 [RAM 用户管理](https://ram.console.aliyun.com/users) → 点你的用户名 → 创建 AccessKey，保存 AccessKey ID 和 AccessKey Secret。

### 2.3 创建 RAM 角色

打开 [RAM 控制台](https://ram.console.aliyun.com) → 身份管理 → 角色 → 创建角色：

- 选择**阿里云账号** → **其他云账号**
- 账号 ID：`1384322691904283`
- 角色名称自定义，如 `quickstart_role`
- 创建后进入角色详情 → **新增授权** → 添加 `AliyunFCFullAccess` + `AliyunOSSFullAccess`
- 复制角色 ARN（格式：`acs:ram::你的账号ID:role/quickstart_role`）

---

## 3. 填写配置

```bash
cp config.example.json config.json
```

打开 `config.json`，把以下字段换成你自己的值：

```
schema      → cz-cli sql "SELECT current_schema()" 的输出
bucket      → 2.2 创建的 Bucket 名称
access_id   → 2.2 的 AccessKey ID
access_key  → 2.2 的 AccessKey Secret
role_arn    → 2.3 的角色 ARN
endpoint    → 默认已填 oss-cn-shanghai.aliyuncs.com，不需要改
region      → 默认已填 cn-shanghai，不需要改
```

---

## 4. 打包、部署、测试

```bash
# 打包（1 KB）
bash build.sh

# 生成部署 SQL
python render_sql.py

# 部署
cz-cli sql -f dist/deploy.sql --write
```

看到 `HELLO WORLD` 就成功了。

---

## 5. 代码长什么样

`src/my_upper.py`：

```python
@annotate("*->string")
class my_upper(object):
    def evaluate(self, s):
        return s.upper() if s else s
```

一个类、一个 `evaluate` 方法、返回结果。就这么简单。

---

## 6. 清理

```sql
DROP FUNCTION IF EXISTS <schema>.my_upper;
DROP VOLUME IF EXISTS qs_vol;
DROP CONNECTION IF EXISTS qs_fc;
DROP CONNECTION IF EXISTS qs_oss;
```

OSS Bucket 和 RAM 角色去阿里云控制台手动删除。

---

## 接下来

- 30 个 AI 模型封装为 SQL 函数 → `../python_ai_function/`
- cz-cli 更多用法 → [使用指南](https://yunqi.tech/documents/cz-cli)
