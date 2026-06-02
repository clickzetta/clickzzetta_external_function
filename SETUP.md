# 环境准备 — 一次性

> 所有示例共享云环境，配一次四个项目通用。

---

## 0. 先确认你的 Lakehouse 在哪朵云

**外部函数的运行时（FC/SCF/Lambda）必须和 Lakehouse 实例在同一朵云、同一个地域（region）。** 配置之前先搞清楚：

```bash
# 列出所有可用的连接
cz-cli profile list
# 看 service 列：
#   alicloud.api.clickzetta.com  → 阿里云
#   tencentcloud.api.clickzetta.com → 腾讯云
#   aws.api.clickzetta.com → AWS
```

选择你要用的 profile，确保后续所有资源配置都在同一个 region。例如：

| Profile | 云 | Region |
|---------|---|--------|
| `aliyun_shanghai_prod` | 阿里云 | `cn-shanghai` |
| `tencent_shanghai_prod` | 腾讯云 | `ap-shanghai` |
| `aws_north-1_prod` | AWS | `cn-north-1` |

然后打开 `config.example.json`，把 `platform` 改成对应的云：

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
    "role_arn": "acs:ram::你的账号ID:role/CzUDFRole"
  }
}
```

### 1.3 编辑 AliyunFCFullAccess 策略（补充 ram:PassRole 权限）

[RAM 策略控制台](https://ram.console.aliyun.com/policies) → 搜索 **AliyunFCFullAccess** → 编辑，确认策略内容包含 `ram:PassRole` 部分（如果已有则跳过）：

```json
{
    "Version": "1",
    "Statement": [
        {
            "Action": "fc:*",
            "Resource": "*",
            "Effect": "Allow"
        },
        {
            "Action": "ram:PassRole",
            "Resource": "*",
            "Effect": "Allow",
            "Condition": {
                "StringEquals": {
                    "acs:Service": "fc.aliyuncs.com"
                }
            }
        }
    ]
}
```

> `ram:PassRole` 允许 FC 将角色传递给函数执行，缺少会导致 FC 扮演角色失败。

### 1.4 创建自定义 OSS 权限策略

[RAM 策略控制台](https://ram.console.aliyun.com/policies) → 创建权限策略 → **脚本编辑**，粘贴以下内容（替换 `your-bucket`）：

```json
{
    "Version": "1",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "oss:GetObject",
                "oss:ListObjects",
                "oss:PutObject",
                "oss:DeleteObject"
            ],
            "Resource": [
                "acs:oss:*:*:your-bucket",
                "acs:oss:*:*:your-bucket/*"
            ]
        }
    ]
}
```

> 注意：相同的 bucket 需要 `your-bucket` 和 `your-bucket/*` 两条 Resource 条目，否则授权不完整。

- 策略名称填 **`CzUdfOssAccess`**，点击**完成**

### 1.5 创建 RAM 角色

[RAM 控制台](https://ram.console.aliyun.com) → 身份管理 → 角色 → 创建角色：

- 角色类型：**阿里云账号** → **其他云账号**
- 账号 ID 填 `1384322691904283`（云器的阿里云主账号），点击**下一步**
- 在**选择权限**中勾选：
  - 系统策略：**`AliyunFCFullAccess`**（FC 全读写）
  - 自定义策略：**`CzUdfOssAccess`**（刚创建的 OSS 读写）
- 点击**下一步**，填写角色名称（例如 `CzUDFRole`），点击**确定**
- 创建成功后进入角色详情页，粘贴**角色 ARN**，填入 `config.json` → `aliyun.fc.role_arn`：
  ```
  acs:ram::你的账号ID:role/CzUDFRole
  ```

### 1.6 验证信任策略

角色详情页 → **信任策略**，确认包含：

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

> **信任策略** 决定了谁可以扮演这个角色。`Principal` 中的账号 `1384322691904283` 是云器的主账号，缺少会导致 FC 无法扮演角色，报 `HTTP_GENERAL_ERROR(640)`。

### 1.7 配置 External ID（可选，部署 API CONNECTION 后）

部署阶段 `CREATE API CONNECTION` 成功后，执行以下命令获取 External ID：

```sql
DESC CONNECTION fc_conn;
```

在返回结果中找到 `ExternalId` 字段。回到 [RAM 角色](https://ram.console.aliyun.com/roles) → `CzUDFRole` → **信任策略** → **编辑**，添加 `sts:ExternalId`：

```json
{
  "Statement": [{
    "Action": "sts:AssumeRole",
    "Condition": {
      "StringEquals": {
        "sts:ExternalId": "替换为DESC结果中的ExternalId"
      }
    },
    "Effect": "Allow",
    "Principal": { "RAM": ["acs:ram::1384322691904283:root"] }
  }],
  "Version": "1"
}
```

External ID 作为额外验证层，防止 ROLE_ARN 被第三方获取后未授权访问。

---

## 2. 腾讯云

### 2.1 开通云函数 SCF

[云函数控制台](https://console.cloud.tencent.com/scf) → 开通服务。

### 2.2 创建 COS Bucket + 密钥

[COS 控制台](https://console.cloud.tencent.com/cos) → 创建存储桶（与 SCF 同地域，例如 `ap-shanghai`）。

> 创建后，在存储桶列表中可以看到完整名称格式为 `Bucket名-APP_ID`（如 `qiliang-external-function-1253896122`）。**config.json 里只填 Bucket 名**，APP_ID 单独填。APP_ID 也在 [账号信息](https://console.cloud.tencent.com/developer) 页面可以找到。

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
    "role_arn": "qcs::cam::uin/你的账号ID:roleName/LakehouseRole"
  }
}
```

### 2.3 创建 CAM 自定义策略

[访问管理](https://console.cloud.tencent.com/cam) → 策略 → 新建自定义策略：

- 选择 **按策略语法创建** → 选择 **空白模板** → 粘贴以下 JSON：

```json
{
    "statement": [
        {
            "action": ["scf:*"],
            "effect": "allow",
            "resource": ["*"]
        },
        {
            "action": ["cos:*"],
            "effect": "allow",
            "resource": [
                "qcs::cos:<region>:uid/<APP_ID>:<bucket>-<APP_ID>/*"
            ]
        }
    ],
    "version": "2.0"
}
```

> 将 `<region>`、`<APP_ID>`、`<bucket>` 替换为实际值。例如 `qcs::cos:ap-shanghai:uid/1253896122:qiliang-external-function-1253896122/*`。

- 点击**下一步**，策略名称填 **`LakehouseAccess`**（必须这个名字），点击**完成**

### 2.4 创建 CAM 角色

[访问管理](https://console.cloud.tencent.com/cam) → 角色 → 新建角色：

- 角色载体：**腾讯云账户** → **其他主账号**
- 账号 ID 填 `100029595716`（云器的腾讯云主账号），点击**下一步**
- 勾选刚创建的 `LakehouseAccess` 策略
- 点击**下一步**，角色名称填 **`LakehouseRole`**（必须这个名字），点击**完成**
- 创建成功后进入角色详情页，复制**角色 ARN**，填入 `config.json` → `tencent.scf.role_arn`：
  ```
  qcs::cam::uin/你的账号ID:roleName/LakehouseRole
  ```

> ⚠️ 角色名必须叫 `LakehouseRole`。角色载体必须选「其他主账号」并信任云器账号 `100029595716`，**不是**「腾讯云产品服务」。

> ⚠️ 如果 `LakehouseAccess` 策略里少加了 COS 的权限（只有 SCF），部署阶段创建函数时会报 `AccessDenied (Status Code: 403)`。确保 COS 的资源 ARN 格式正确：`qcs::cos:<region>:uid/<APP_ID>:<bucket>-<APP_ID>/*`。

> 腾讯云 **必须** 提供 `namespace`，默认为 `default`。

### 2.5 注意：CODE_BUCKET 必须带 APP_ID

`CREATE API CONNECTION` 的 `CODE_BUCKET` 格式是 `Bucket名-APP_ID`（如 `qiliang-external-function-1253896122`），不能只填 Bucket 名。`3-render-sql.py` 会自动拼接。

### 2.6 配置 External ID（可选，部署 API CONNECTION 后）

部署阶段 `CREATE API CONNECTION` 成功后，执行以下命令获取 External ID：

```sql
DESC CONNECTION scf_conn;
```

在返回结果中找到 `ExternalId` 字段。然后回到腾讯云 [访问管理](https://console.cloud.tencent.com/cam) → 角色 → `LakehouseRole` → **角色载体** → **管理载体**：

- 选择 **添加账户** → **当前主账号**
- 填写云器主账号：`100029595716`
- 勾选**开启校验**，输入 DESC 结果中的 External ID
- 点击**确定** → **更新**

External ID 作为额外验证层，防止 ROLE_ARN 被第三方获取后未授权访问。

---

## 3. AWS

### 3.1 开通 Lambda

[Lambda 控制台](https://console.aws.amazon.com/lambda) → 开通。

### 3.2 创建 S3 Bucket

[S3 控制台](https://s3.console.aws.amazon.com) → 创建存储桶（与 Lambda 同地域，例如 `ap-southeast-1`）。

### 3.3 创建 IAM 用户 + AccessKey

[IAM 用户](https://console.aws.amazon.com/iam) → 创建用户：

- 用户名随意（如 `qiliang-udf`），不勾选控制台访问
- 直接附加策略：搜索勾选 `AmazonS3FullAccess`
- 创建完成后，进入该用户 → **安全凭证** → **创建访问密钥**
- 选择 **命令行接口 (CLI)** → 创建 → 保存 Access Key ID 和 Secret Access Key

填入 `config.json`：

```json
"aws": {
  "s3": {
    "bucket": "你的 Bucket 名",
    "region": "ap-southeast-1",
    "endpoint": "s3.<region>.amazonaws.com",
    "access_key_id": "你的 AccessKey ID",
    "secret_access_key": "你的 Secret Access Key"
  },
  "lambda": {
    "region": "ap-southeast-1",
    "role_arn": "arn:aws:iam::你的账号ID:role/你的角色名"
  }
}
```

> 中国区 endpoint 格式为 `s3.<region>.amazonaws.com.cn`，国际区为 `s3.<region>.amazonaws.com`。
> 中国区 region 如 `cn-north-1`、`cn-northwest-1`；国际区如 `ap-southeast-1`、`us-east-1`。

### 3.4 创建 IAM 策略

[IAM 控制台](https://console.aws.amazon.com/iam) → 策略 → 创建策略：

- 选择 **JSON** 方式，粘贴以下策略（替换 `<bucket>` 为实际 Bucket 名）：

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:GetObjectVersion",
                "s3:PutObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::<bucket>",
                "arn:aws:s3:::<bucket>/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": "lambda:*",
            "Resource": "*"
        }
    ]
}
```

> ⚠️ S3 必须包含 `PutObject`（平台需要把代码包写入 S3）。Lambda 必须包含全部操作。

- 点击**下一步**，策略名称填 **`LambdaS3ReadAccess`**，点击**创建**

### 3.5 创建 IAM 角色

[IAM 控制台](https://console.aws.amazon.com/iam) → 角色 → 创建角色：

- 信任实体类型：**AWS 服务** → **Lambda**
- 权限策略：勾选刚才创建的 `LambdaS3ReadAccess` 和 `AWSLambdaBasicExecutionRole`
- 点击**下一步**，角色名称填 **`Lambda-S3-Role`**，点击**创建**
- 创建成功后进入角色详情页，复制**角色 ARN**，填入 `config.json` → `aws.lambda.role_arn`：
  ```
  arn:aws:iam::你的账号ID:role/Lambda-S3-Role
  ```

### 3.6 配置信任策略（添加云器账号）

角色详情页 → **Trust relationships** → **编辑信任策略**，**追加**云器账号的信任关系：

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        },
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::014617434350:root"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
```

> ⚠️ `014617434350` 是云器国际站 AWS 账号；中国站用 `028022243208`。缺少云器账号的信任关系会报 `AccessDenied: sts:AssumeRole`。

> ⚠️ 别把权限策略的 JSON 贴到信任策略编辑器里——两个是不同页面。

---

## 完成标志

```bash
cz-cli status                              # 已连接
cz-cli sql "SELECT current_schema()"        # 返回 schema 名
```

然后进入任意子目录，`cp ../config.example.json config.json` 选择平台并填入字段，按对应 README 继续。

---

## 注意事项

| 错误 | 云 | 原因 | 解决 |
|------|---|------|------|
| `HTTP_GENERAL_ERROR(640)` | 阿里云 | RAM 信任策略未配 / 跨地域 | 见 1.6 |
| `ram:PassRole` 相关错误 | 阿里云 | AliyunFCFullAccess 缺少 ram:PassRole | 见 1.3，确认 Condition 含 `fc.aliyuncs.com` |
| `AccessDenied` | 全部 | 角色缺对象存储权限 | 补读权限（至少），见对应云的角色授权章节 |
| `AccessDenied: sts:AssumeRole` | AWS | 信任策略漏了云器账号 | 见 3.6，追加 `arn:aws:iam::014617434350:root` |
| `AccessDenied: s3:PutObject` | AWS | IAM 策略缺 S3 写权限 | 见 3.4，确保含 `s3:PutObject` |
| `AccessDenied: lambda:*` | AWS | IAM 策略缺 Lambda 权限 | 见 3.4，确保含 `lambda:*` |
| `AccessDenied` (403) | 腾讯云 | CAM 策略里漏了 COS 权限 | 见 2.3，确认 `LakehouseAccess` 含 `cos:*` |
| `AccessDenied` | 腾讯云 | CAM 角色载体选错 | 见 2.4，载体须为「其他主账号」信任 `100029595716` |
| `role arn is not exist` | 腾讯云 | 角色名不是 `LakehouseRole` | 见 2.4，角色名必须叫 `LakehouseRole` |
| PUT 404 after upload | 全部 | PUT 被注释行中断 | PUT 写成一行 |
| 冷启动超时 | 全部 | Bucket 和 FC 跨地域 | 确认 Bucket 与计算服务同地域 |
| `Namespace is required` | 腾讯云 | 没填 namespace | config 中填 `"namespace": "default"` |
