# Java External Function 完整演示

> 覆盖 UDF / UDAF / UDTF 三种类型，全部基于 Hive GenericUDF API

---

## 前置条件

- JDK 8+ / Maven 3+
- 阿里云 OSS / FC / RAM 角色已就绪（首次使用参考 `../python_quickstart/` 第 2 节）

---

## 三种函数类型

| 类型 | 基类 | 输入 → 输出 | DDL 关键属性 | 本示例函数 |
|------|------|-------------|-------------|-----------|
| **UDF** | `GenericUDF` | 1 行 → 1 行 | `'remote.udf.api'='java8.hive2.v0'` | `pii_mask` — PII 脱敏 |
| **UDAF** | `GenericUDAFResolver2` | 多行 → 1 行（聚合） | 加 `'remote.udf.category'='AGGREGATOR'` | `agg_stats` — SUM/AVG/MIN/MAX/COUNT |
| **UDTF** | `GenericUDTF` | 1 行 → 多行（展开） | 加 `'remote.udf.category'='TABLE_VALUED'` | `log_explode` — 日志拆解 |

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
bash build.sh     # jar → zip
```

---

## 3. 部署

```bash
python 1-check-config.py
python 3-render-sql.py
cz-cli sql -f dist/4-deploy_generated.sql --write
```

---

## 4. 代码

### UDF — PiiMaskUDF

```java
public class PiiMaskUDF extends GenericUDF {
    public ObjectInspector initialize(ObjectInspector[] args) { ... }   // 参数校验
    public Object evaluate(DeferredObject[] args) { ... }               // 正则脱敏
    public String getDisplayString(String[] children) { ... }
}
```

### UDAF — AggStatsUDAF

```java
public class AggStatsUDAF extends GenericUDAFResolver2 {
    public GenericUDAFEvaluator getEvaluator(TypeInfo[] params) {
        return new AggStatsEvaluator();  // 内部类实现 iterate/merge/terminate 等
    }
}
```

UDAF 必须实现：`iterate()` 逐行累加、`merge()` 合并分区结果、`terminate()` 输出最终值。

### UDTF — LogExplodeUDTF

```java
public class LogExplodeUDTF extends GenericUDTF {
    public StructObjectInspector initialize(ObjectInspector[] args) { ... }  // 声明输出列
    public void process(Object[] record) { forward(new Object[]{ts, evt}); }  // 每行输出多行
    public void close() { }
}
```

UDTF 调用时必须用 `LATERAL` 语法。

---

## 5. 测试

### UDF

```sql
SELECT <schema>.pii_mask('我的手机13812345678，邮箱alice@example.com，身份证310101199001011234');
```

### UDAF（需先建测试表）

```sql
CREATE TABLE test_scores (val DOUBLE);
INSERT INTO test_scores VALUES (3.5), (4.2), (2.8), (5.0);
SELECT <schema>.agg_stats(val) FROM test_scores;
-- → [sum, avg, min, max, count]
```

### UDTF

```sql
SELECT t.ts, t.event
FROM (SELECT '[2025-01-15 10:30:00] 用户登录
[2025-01-15 10:35:00] 查询订单' AS log) s,
LATERAL <schema>.log_explode(s.log) t;
-- → 10:30:00 | 用户登录
--    10:35:00 | 查询订单
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
| `pom.xml` | Maven，依赖 hive-exec 2.3.9 |
| `build.sh` | `mvn package` + zip 打包 |
| `1-check-config.py` | 检查 config.json |
| `3-render-sql.py` | 占位符替换 |
| `4-deploy.sql` | 部署 3 种类型函数 + 测试 |
| `5-cleanup.sql` | 清理 |
