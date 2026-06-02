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
cp ../config.example.json config.json
```

打开 `config.json`：
1. 确认 `platform` 是你的云（`aliyun` / `tencent` / `aws`）
2. 按 [SETUP.md](../SETUP.md) 填你选的那朵云的对应字段
3. `schema` 填 `cz-cli sql "SELECT current_schema()"` 的输出

---

## 4. 部署（在 `python_quickstart/` 目录下执行）

```bash
python ../1-check-config.py
python 2-package.py
python ../3-render-sql.py
cz-cli sql -f dist/4-deploy_generated.sql --write
```

看到 `HELLO WORLD` 就成功了。

---

## 5. 本地测试

部署前可以先在本地跑一下，确认代码没问题：

```bash
python3 -c "
import sys; sys.path.insert(0, 'src')
from my_upper import my_upper
print(my_upper().evaluate('hello'))
"
# → HELLO
```

FC 环境没有日志，代码逻辑 bug 只能返回错误 JSON，本地先测通再部署省很多时间。

---

### 常见坑

| 错误 | 原因 | 解决 |
|------|------|------|
| `function not found` | 没加 schema 前缀，这是硬性要求 | `SELECT <schema>.my_upper('hello')` |
| `HTTP_GENERAL_ERROR(640)` | RAM 信任策略未配 / Bucket 跨地域 | 见 [SETUP.md](../SETUP.md) 对应云章节 |
| `AccessDenied` | RAM 角色缺 OSS 权限 | 角色详情 → 新增授权 → `AliyunOSSFullAccess` |
| 改完 `config.json` 部署没变化 | 改了配置但没重新渲染 SQL | 改完 config 后必须重跑 `python ../3-render-sql.py` |
| 第一次调用很久没返回 | FC 冷启动，首次需从对象存储下载 zip | 等 5-10 秒，不是挂了 |
| `deploy_generated.sql` 不存在 | 没跑渲染 | `python ../3-render-sql.py` |
| 所有脚本都要从项目目录内执行 | 共享脚本用 `../` 引用，不在项目目录内路径不对 | `cd python_quickstart` 后再执行 |

---

## 6. 代码

`src/my_upper.py`，一个类、一个 `evaluate` 方法：

```python
@annotate("*->string")
class my_upper(object):
    def evaluate(self, s):
        return s.upper() if s else s
```

---

## 7. 清理

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
| 文件 | 作用 |
|------|------|
| `../config.example.json` | 配置模板（共享） |
| `../1-check-config.py` | 检查 config.json（共享） |
| `2-package.py` | 打包为 zip（1 KB） |
| `../3-render-sql.py` | 占位符替换（共享） |
| `4-deploy.sql` | 部署模板 |
| `5-cleanup.sql` | 清理 |
| `../SETUP.md` | 云环境准备（共享） |

---

## 接下来

- SQL ML（scikit-learn + jieba）→ `../python_advanced/`
- 30 个 AI 函数 + 第三方依赖 → `../python_ai_function/`
- Java UDF/UDAF/UDTF → `../java_udf/`
