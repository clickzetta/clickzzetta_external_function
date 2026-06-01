# 云器 Lakehouse External Function 实战示例

> Python / Java 外部函数完整演示。支持阿里云、腾讯云、AWS。

---

## 快速开始

1. **[SETUP.md](SETUP.md)** — 选云、配环境（一次性）
2. `cp config.example.json config.json` — 选 platform + 填对应字段
3. **[python_quickstart](python_quickstart/)** — 5 分钟跑通
4. 按需选其他示例

---

## 示例

| 示例 | 语言 | 难度 | 说明 |
|------|------|------|------|
| [python_quickstart](python_quickstart/) | Python | ★ | 最简单的 UDF |
| [python_advanced](python_advanced/) | Python | ★★ | 5 个 ML 函数 + 第三方依赖 |
| [python_ai_function](python_ai_function/) | Python | ★★★ | 30 个 AI 函数 + dashscope SDK |
| [java_udf](java_udf/) | Java | ★★ | UDF / UDAF / UDTF |

---

## 共享文件

| 文件 | 谁用 | 作用 |
|------|------|------|
| `SETUP.md` | 全部 | 云环境准备（阿里云 / 腾讯云 / AWS） |
| `config.example.json` | quickstart / advanced / java_udf | 配置模板（选 platform，填云字段） |
| `1-check-config.py` | 同上 | 按 platform 校验 config |
| `3-render-sql.py` | 同上 | 按 platform 生成部署 SQL |

**`python_ai_function`** 配置结构不同（需要 models、dashscope），脚本和 `config.example.json` 独立放在自己目录下。

---

## 仓库结构

```
clickzetta_external_function/
├── SETUP.md                    # 云环境（全部共享）
├── config.example.json          # 配置模板（多平台）
├── 1-check-config.py            # ① 检查
├── 3-render-sql.py              # ③ 渲染
├── python_quickstart/           # 2-package.py / 4-deploy.sql / 5-cleanup.sql
├── python_advanced/             # 2-package.py / 4-deploy.sql / 5-cleanup.sql
├── python_ai_function/          # 独立（配置结构不同）
└── java_udf/                    # 2-package.py / 4-deploy.sql / 5-cleanup.sql
```
