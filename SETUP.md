# 环境准备 — 一次性

> 所有示例共享云环境。选你用的云，配一次，四个项目通用。

---

## 0. 选云、填 platform

打开 `config.example.json`，第一件事——把 `platform` 改成你的云：

```json
"platform": "aliyun"   // 或 "tencent" 或 "aws"
```

---

## 1. 阿里云

### 1.1 开通函数计算 FC

[函数计算控制台](https://fc.console.aliyun.com) → "立即开通" → **华东 2（上海）**。

### 1.2 创建 OSS Bucket + AccessKey

[OSS 控制台](https://oss.console.aliyun.com) → 创建 Bucket（与 FC 同地域，标准存储，私有）。

[RAM 用户管理](https://ram.console.aliyun.com/users) → 创建 AccessKey。

填入 `config.json`：

```json
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
```

### 1.3 创建 RAM 角色

[RAM 控制台](https://ram.console.aliyun.com) → 身份管理 → 角色 → 创建角色：

- 类型：**阿里云账号** → **其他云账号**，账号 ID `1384322691904283`
- 创建后 → 新增授权 → `AliyunFCFullAccess` + `AliyunOSSFullAccess`
- 复制角色 ARN，填入 `config.json` → `aliyun.fc.role_arn`

### 1.4 验证信任策略

角色详情 → 信任策略，确认包含：

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

缺少会报 `HTTP_GENERAL_ERROR(640)`。

---

## 2. 腾讯云

### 2.1 开通云函数 SCF

[云函数控制台](https://console.cloud.tencent.com/scf) → 开通服务。

### 2.2 创建 COS Bucket + 密钥

[COS 控制台](https://console.cloud.tencent.com/cos) → 创建存储桶（与 SCF 同地域）。

[访问管理](https://console.cloud.tencent.com/cam/capi) → 创建密钥。

填入 `config.json`：

```json
"tencent": {
  "cos": {
    "bucket": "你的 Bucket 名",
    "region": "ap-shanghai",
    "app_id": "你的 APP_ID（必须）",
    "access_key": "你的 SecretId",
    "secret_key": "你的 SecretKey"
  },
  "scf": {
    "region": "ap-shanghai",
    "namespace": "default",
    "role_arn": "qcs::cam::uin/你的账号ID:roleName/你的角色名"
  }
}
```

### 2.3 创建 CAM 角色

[访问管理](https://console.cloud.tencent.com/cam) → 角色 → 新建角色：

- 选择 **腾讯云产品服务** → 云函数 SCF
- 授予 COS 读取权限 + SCF 执行权限
- 复制角色 ARN → `tencent.scf.role_arn`

> 腾讯云 **必须** 提供 `namespace`，默认为 `default`。

---

## 3. AWS

### 3.1 开通 Lambda

[Lambda 控制台](https://console.aws.amazon.com/lambda) → 开通。

### 3.2 创建 S3 Bucket + AccessKey

[S3 控制台](https://s3.console.aws.amazon.com) → 创建 Bucket（与 Lambda 同地域）。

[IAM 用户](https://console.aws.amazon.com/iam) → 创建 AccessKey。

填入 `config.json`：

```json
"aws": {
  "s3": {
    "bucket": "你的 Bucket 名",
    "region": "cn-north-1",
    "endpoint": "s3.cn-north-1.amazonaws.com.cn",
    "access_key_id": "你的 AccessKey ID",
    "secret_access_key": "你的 Secret Access Key"
  },
  "lambda": {
    "region": "cn-north-1",
    "role_arn": "arn:aws:iam::你的账号ID:role/你的角色名"
  }
}
```

> 国际站 endpoint 用 `s3.amazonaws.com`，region 用 `us-east-1` 等。

### 3.3 创建 IAM 角色

[IAM 控制台](https://console.aws.amazon.com/iam) → 角色 → 创建角色：

- AWS 服务 → Lambda
- 授予 S3 读取 + Lambda 执行权限
- 信任策略中 Account ID 填 `028022243208`（中国站）
- 复制 ARN → `aws.lambda.role_arn`

---

## 完成标志

```bash
cz-cli status                              # 已连接
cz-cli sql "SELECT current_schema()"        # 返回 schema 名
```

然后进入任意子目录，`cp ../config.example.json config.json` 选择平台并填入字段，按对应 README 继续。

---

## 常见坑（通用）

| 错误 | 原因 | 解决 |
|------|------|------|
| `HTTP_GENERAL_ERROR(640)` | 阿里云信任策略未配 / 跨地域 | 见 1.4 |
| `AccessDenied` | 角色缺对象存储权限 | 补读+写权限 |
| PUT 404 after upload | PUT 被注释行中断 | PUT 写成一行 |
| 冷启动超时 | Bucket 和 FC 跨地域 | 确认同地域 |
| `Namespace is required` | 腾讯云没填 namespace | config 中填 `"namespace": "default"` |
