# Java External Function — PII 数据脱敏

> ClickZetta 支持 Java 编写的外部函数，通过继承 Hive GenericUDF 实现

---

## 前置条件

- JDK 8+
- Maven 3+
- 已完成 `../python_quickstart/` 或 `../python_ai_function/`，阿里云资源已就绪
- ClickZetta 实例（API Connection 和 Volume 已存在）

---

## 和 Python External Function 的区别

| | Python | Java |
|------|--------|------|
| 语言 | Python 3.10 | Java 8 |
| 函数类型 | UDF | UDF / UDAF / UDTF |
| 入口 | `def evaluate()` | `GenericUDF.evaluate()` |
| DDL 属性 | `python3.mc.v0` | `java8.hive2.v0` |
| 打包 | `zip -j` | Maven + `jar-with-dependencies` |

---

## 1. 填写配置

```bash
cp config.example.json config.json
```

配置项与 quickstart 相同。

---

## 2. 编译与部署

```bash
# 编译（Maven）
cd java_udf
mvn clean package

# 打包为 ClickZetta 要求的 zip 格式
bash build.sh

# 检查配置
python 1-check-config.py

# 渲染 SQL
python 3-render-sql.py

# 部署
cz-cli sql -f dist/4-deploy_generated.sql --write
```

看到脱敏后的文本返回即表示成功。

---

## 3. 代码核心框架

`PiiMaskUDF.java`：

```java
public class PiiMaskUDF extends GenericUDF {

    @Override
    public ObjectInspector initialize(ObjectInspector[] arguments) {
        // 1. 参数校验
        // 2. 返回输出类型
        return PrimitiveObjectInspectorFactory.javaStringObjectInspector;
    }

    @Override
    public Object evaluate(DeferredObject[] arguments) {
        // 业务逻辑：正则匹配 → 脱敏替换
        return maskedText;
    }

    @Override
    public String getDisplayString(String[] children) {
        return "pii_mask(...)";
    }
}
```

三个必须实现的方法：
- `initialize()` — 参数类型校验，声明返回类型
- `evaluate()` — 核心业务逻辑，每行数据调用一次
- `getDisplayString()` — 函数名展示

---

## 4. SQL DDL

```sql
CREATE EXTERNAL FUNCTION <schema>.pii_mask
AS 'com.clickzetta.udf.PiiMaskUDF'
USING ARCHIVE 'volume://java_vol/pii_mask.zip'
CONNECTION shanghai_func_conn
WITH PROPERTIES ('remote.udf.api'='java8.hive2.v0');
--                  ^^^^^^^^^ 注意：Java 用的是 java8.hive2.v0，不是 python3.mc.v0
```

---

## 5. 测试

```sql
SELECT <schema>.pii_mask('我的手机13812345678，邮箱alice@example.com，身份证310101199001011234');
-- → "我的手机138****5678，邮箱a***@example.com，身份证310101********1234"
```

---

## 6. 清理

```bash
cz-cli sql -f dist/5-cleanup_generated.sql --write
```
