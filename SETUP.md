# 环境准备 — 一次性

> 所有示例共享同一套云环境。首次使用前完成一次即可，之后四个项目直接复用。

---

## 平台选择

| 平台 | 函数计算 | 对象存储 | 角色管理 |
|------|---------|---------|---------|
| 阿里云 | 函数计算 FC | OSS | RAM |
| 腾讯云 | 云函数 SCF | COS | CAM |
| AWS | Lambda | S3 | IAM |

<details>
<summary><b>阿里云</b></summary>

### 阿里云 — 函数计算 FC

打开 [函数计算控制台](https://fc.console.aliyun.com)，点击"立即开通"，选择**华东 2（上海）**（或你所在的地域）。

### 阿里云 — OSS Bucket

1. [OSS 控制台](https://oss.console.aliyun.com) → 创建 Bucket
2. **地域**：与 FC 同一地域（如华东 2 上海）
3. 创建后记下 Bucket 名称，填入 `config.json` → `aliyun.oss.bucket`

### 阿里云 — AccessKey

[RAM 用户管理](https://ram.console.aliyun.com/users) → 点你的用户 → 创建 AccessKey，记下 AccessKey ID 和 Secret。

### 阿里云 — RAM 角色

1. [RAM 控制台](https://ram.console.aliyun.com) → 身份管理 → 角色 → 创建角色
2. 类型：**阿里云账号** → **其他云账号**
3. 账号 ID：`1384322691904283`
4. 角色名自定义，如 `udf_role`
5. 创建后进入角色详情 → **新增授权** → 添加：
   - `AliyunFCFullAccess`（创建函数、写日志）
   - `AliyunOSSFullAccess`（下载代码包）
6. 复制角色 ARN（如 `acs:ram::1692111025976318:role/udf_role`），填入 `config.json` → `aliyun.fc.role_arn`

### 阿里云 — 验证信任策略

进角色详情 → 信任策略，确认以下内容存在：

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

没有的话编辑加进去。**缺少信任策略会出现 HTTP_GENERAL_ERROR(640)**。

### 阿里云 — 对应 config.json 字段

```json
{
  "aliyun": {
    "oss": {
      "bucket": "你的 Bucket 名",
      "endpoint": "oss-cn-shanghai.aliyuncs.com",
      "access_id": "你的 AccessKey ID",
      "access_key": "你的 AccessKey Secret"
    },
    "fc": {
      "region": "cn-shanghai",
      "role_arn": "acs:ram::你的账号ID:role/你的角色名"
    }
  }
}
```

</details>

<details>
<summary><b>腾讯云</b>（待补充）</summary>

### 腾讯云 — 云函数 SCF

打开 [云函数控制台](https://console.cloud.tencent.com/scf)，开通服务。

### 腾讯云 — COS Bucket

[COS 控制台](https://console.cloud.tencent.com/cos) → 创建存储桶，地域与 SCF 保持一致。

### 腾讯云 — CAM 角色

1. [访问管理控制台](https://console.cloud.tencent.com/cam) → 角色 → 新建角色
2. 选择**腾讯云产品服务** → 云函数 SCF
3. 授予 COS 读取权限 + SCF 完整权限
4. 记下 ROLE_ARN（格式：`qcs::cam::uin/账号ID:roleName/角色名`）

### 腾讯云 — 对应 config.json 字段

```json
{
  "tencent": {
    "cos": {
      "bucket": "你的 COS Bucket 名",
      "region": "ap-shanghai",
      "secret_id": "你的 SecretId",
      "secret_key": "你的 SecretKey"
    },
    "scf": {
      "region": "ap-shanghai",
      "namespace": "default",
      "role_arn": "qcs::cam::uin/你的账号ID:roleName/你的角色名"
    }
  }
}
```

> 腾讯云必须提供 `namespace` 参数。如果是阿里云或 AWS，填 `'default'` 或不填。

</details>

<details>
<summary><b>AWS</b>（待补充）</summary>

### AWS — Lambda

打开 [Lambda 控制台](https://console.aws.amazon.com/lambda)，开通服务。

### AWS — S3 Bucket

[S3 控制台](https://s3.console.aws.amazon.com) → 创建 Bucket，地域与 Lambda 一致。

### AWS — IAM 角色

1. [IAM 控制台](https://console.aws.amazon.com/iam) → 角色 → 创建角色
2. 选择**AWS 服务** → Lambda
3. 授予 S3 读取权限 + Lambda 执行权限
4. 记下 ROLE_ARN（格式：`arn:aws:iam::账号ID:role/角色名`）

### AWS — 对应 config.json 字段

```json
{
  "aws": {
    "s3": {
      "bucket": "你的 S3 Bucket 名",
      "region": "us-east-1",
      "access_key": "你的 Access Key",
      "secret_key": "你的 Secret Key"
    },
    "lambda": {
      "region": "us-east-1",
      "role_arn": "arn:aws:iam::你的账号ID:role/你的角色名"
    }
  }
}
```

</details>

---

## 完成标志

以下命令全部成功：

```bash
cz-cli status                              # 已连接
cz-cli sql "SELECT current_schema()"       # 返回 schema 名

# 三个平台之一对应的命令能成功：
# 阿里云
cz-cli sql "CREATE STORAGE CONNECTION IF NOT EXISTS test_oss TYPE OSS access_id='xx' access_key='xx' ENDPOINT='oss-cn-shanghai.aliyuncs.com'" --write
cz-cli sql "DROP CONNECTION test_oss" --write
```

完成后进入任意子目录，填写该项目的 `config.json`，即可按 README 继续。

---

## 附：跨平台通用排坑

| 错误 | 平台 | 原因 | 解决 |
|------|------|------|------|
| `HTTP_GENERAL_ERROR(640)` | 阿里云 | RAM 信任策略未配 / Bucket 跨地域 | 角色详情 → 信任策略，确认包含 `1384322691904283` |
| `AccessDenied` | 通用 | 角色缺对象存储权限 | 添加读 + 写对象存储的权限策略 |
| `function not found` | 通用 | SQL 没加 schema 前缀 | `SELECT <schema>.函数名(...)` |
| `Namespace is required` | 腾讯云 | DDL 缺 NAMESPACE | `NAMESPACE='default'` |
| PUT 404 after upload | 通用 | 多行 PUT 被注释行中断 | PUT 写成一行，前后不留注释 |
| 冷启动超时 (>30s) | 通用 | 函数计算与对象存储跨地域 | 确认 Bucket 和 FC 同地域 |
| `DomainNameNotFound` | 通用 | FC 域名 DNS 传播未完成 | 等 30 秒重试 |
