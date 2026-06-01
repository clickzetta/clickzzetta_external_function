# Java External Function — PII 数据脱敏

> 云器 Lakehouse 支持 Java 编写的外部函数，通过继承 Hive GenericUDF 实现。

---

## 前置条件

- JDK 8+ / Maven 3+
- 阿里云 OSS / FC / RAM 角色已就绪（首次使用参考 `../python_quickstart/` 第 2 节）

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

与 quickstart 配置项相同。

---

## 2. 编译

```bash
mvn clean package
bash build.sh     # 将 jar 打包为 ClickZetta 的 zip 格式
```

---

## 3. 部署

```bash
python 1-check-config.py
python 3-render-sql.py
cz-cli sql -f dist/4-deploy_generated.sql --write
```

看到脱敏后的文本返回即成功。

---

## 4. 代码核心框架

`PiiMaskUDF.java` 必须实现三个方法：

```java
public class PiiMaskUDF extends GenericUDF {

    @Override
    public ObjectInspector initialize(ObjectInspector[] arguments) {
        // 1. 参数类型校验
        // 2. 声明返回类型
        return PrimitiveObjectInspectorFactory.javaStringObjectInspector;
    }

    @Override
    public Object evaluate(DeferredObject[] arguments) {
        // 核心逻辑：正则匹配 → 脱敏替换
        return maskedText;
    }

    @Override
    public String getDisplayString(String[] children) {
        return "pii_mask(...)";
    }
}
```

---

## 5. 测试

```sql
SELECT <schema>.pii_mask('我的手机13812345678，邮箱alice@example.com，身份证310101199001011234');
-- → "我的手机<phone>，邮箱<email>，身份证<id_card>"
```

---

## 6. 清理

```bash
cz-cli sql -f dist/5-cleanup_generated.sql --write
```

---

## 附录：脚本说明

| 文件 | 作用 |
|------|------|
| `config.example.json` | 配置模板 |
| `pom.xml` | Maven 构建文件，依赖 hive-exec 2.3.9 |
| `build.sh` | Maven 编译 + 打包为 zip |
| `1-check-config.py` | 检查 `config.json` 完整性 |
| `3-render-sql.py` | 替换占位符，生成 4/5 的 `_generated.sql` |
| `4-deploy.sql` | 部署模板 |
| `5-cleanup.sql` | 删除函数、Volume、Connection |
