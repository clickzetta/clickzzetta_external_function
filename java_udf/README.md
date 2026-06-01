# Java External Function — UDF / UDAF / UDTF 完整演示

> 云器 Lakehouse 支持 Java 编写外部函数，基于 Hive GenericUDF API。本示例覆盖三种类型。

---

## 前置条件

- JDK 8+ / Maven 3+
- [SETUP.md](../SETUP.md) 的云环境已完成（一次性，与 Python 示例共享）

---

## 三种类型速览

| 类型 | 基类 | 输入 → 输出 | DDL 属性 | 本示例函数 |
|------|------|-------------|---------|-----------|
| **UDF** | `GenericUDF` | 1 行 → 1 行 | `'java8.hive2.v0'` | `pii_mask` — PII 脱敏 |
| **UDAF** | `GenericUDAFResolver2` | 多行 → 1 行 | 加 `'AGGREGATOR'` | `agg_stats` — SUM/AVG/MIN/MAX/COUNT |
| **UDTF** | `GenericUDTF` | 1 行 → N 行 | 加 `'TABLE_VALUED'` | `log_explode` — 日志拆解 |

### 和 Python External Function 的区别

| | Python | Java |
|------|--------|------|
| 函数类型 | UDF | UDF / UDAF / UDTF |
| 入口方法 | `evaluate()` | `GenericUDF.evaluate()` / `GenericUDAFEvaluator` / `GenericUDTF.process()` |
| DDL | `'python3.mc.v0'` | `'java8.hive2.v0'` + 可选的 `'AGGREGATOR'` 或 `'TABLE_VALUED'` |
| 打包 | `zip` (纯 .py) | Maven `jar-with-dependencies` → zip |
| 依赖 | pip 下载 Linux 版 | Maven scope=provided（Hive 运行环境自带） |

---

## 1. 填写配置

```bash
cp ../config.example.json config.json
```

与 quickstart 配置相同。

---

## 2. 编译

```bash
python 2-package.py     # Maven 编译 + zip 打包
```

产物：`dist/all_udf.zip`（~1 MB，只含你自己的 class + 第三方依赖 class，不含 Hive 本身）。

### 为什么 Hive 依赖是 provided？

`pom.xml` 里 `hive-exec` 的 scope 是 `provided`：

```xml
<dependency>
    <groupId>org.apache.hive</groupId>
    <artifactId>hive-exec</artifactId>
    <version>2.3.9</version>
    <scope>provided</scope>
</dependency>
```

`provided` 表示编译时需要 Hive 的类定义，但不打包进 jar。FC 的 Java 运行时已经包含了 `hive-exec.jar`。如果 scope 写成 `compile`，jar 会膨胀到 ~20MB 且可能与运行时冲突。

---

## 3. 部署

```bash
python ../1-check-config.py
python ../3-render-sql.py
cz-cli sql -f dist/4-deploy_generated.sql --write
```

---

## 4. 代码详解

### UDF — `PiiMaskUDF.java`

```java
public class PiiMaskUDF extends GenericUDF {

    private StringObjectInspector textOI;       // 输入类型

    public ObjectInspector initialize(ObjectInspector[] args) {
        // ✅ 参数个数校验 —— 保证调用时不会参数数不对而报奇怪的错
        checkArgsSize(args, 1, 1);
        // ✅ 参数类型校验
        checkArgPrimitive(args, 0);
        // ✅ 声明返回类型
        return PrimitiveObjectInspectorFactory.javaStringObjectInspector;
    }

    public Object evaluate(DeferredObject[] args) {
        String text = textOI.getPrimitiveJavaObject(args[0].get());
        // 业务逻辑
        return maskedResult;
    }

    public String getDisplayString(String[] children) {
        return "pii_mask(...)";
    }
}
```

**必须实现的三个方法：**
- `initialize(args)` — 只调一次。参数个数/类型校验 + 声明返回值类型
- `evaluate(args)` — 每行数据调一次。核心业务逻辑
- `getDisplayString(children)` — 返回函数名展示字符串

**坑：NullPointerException in evaluate**

FC 可能传入 NULL 值。`evaluate` 的第一行通常是：
```java
String text = textOI.getPrimitiveJavaObject(args[0].get());
if (text == null) return "";
```

### UDAF — `AggStatsUDAF.java`

UDAF 有**两个类**：

```
AggStatsUDAF extends GenericUDAFResolver2   // 外层：路由到 Evaluator
  └─ AggStatsEvaluator extends GenericUDAFEvaluator  // 内层：聚合逻辑
```

**Evaluator 的五个模式：**
1. `init(PARTIAL1)` — 原始数据到达第一个节点，创建 buffer，对每条原始数据调 `iterate()`
2. `init(PARTIAL2)` — 合并多个上游节点的部分结果，调 `merge()`
3. `init(FINAL)` — 所有数据聚合完毕，`merge()` 后调 `terminate()` 输出最终结果
4. `init(COMPLETE)` — 数据在一个节点时直接走 `iterate()` + `terminate()`

**必须实现的方法：**

| 方法 | 调用时机 | 作用 |
|------|---------|------|
| `getNewAggregationBuffer()` | 每个分区开始 | 创建空 buffer |
| `reset(buf)` | buffer 创建 / 分区间切换 | 归零 |
| `iterate(buf, args)` | 每条数据 | 累加到 buffer |
| `terminatePartial(buf)` | 分区处理完 | 输出中间结果 |
| `merge(buf, partial)` | 合并分区 | 合并到全局 buffer |
| `terminate(buf)` | 全部处理完 | 输出最终结果 |

**坑：UDAF DDL 忘了加 `AGGREGATOR`**

```sql
-- ❌ 缺了这句，函数创建成功但调用时报错
-- ✅ 必须加
WITH PROPERTIES ('remote.udf.category'='AGGREGATOR')
```

### UDTF — `LogExplodeUDTF.java`

```java
public class LogExplodeUDTF extends GenericUDTF {

    public StructObjectInspector initialize(ObjectInspector[] args) {
        // 声明输出的列名和类型
        ArrayList<String> names = new ArrayList<>();
        ArrayList<ObjectInspector> types = new ArrayList<>();
        names.add("ts");       // 列名 1
        types.add(JavaStringObjectInspector);  // 类型 1
        names.add("event");    // 列名 2
        types.add(JavaStringObjectInspector);  // 类型 2
        return ObjectInspectorFactory.getStandardStructObjectInspector(names, types);
    }

    public void process(Object[] record) throws HiveException {
        // forward() 表示"输出一行"
        forward(new Object[]{"2025-01-15 10:30:00", "用户登录"});
        forward(new Object[]{"2025-01-15 10:35:00", "查询订单"});
        // 一行输入 → 多行输出
    }

    public void close() { /* 清理 */ }
}
```

**必须实现的三个方法：**
- `initialize(args)` — 声明输出列的数量、名称、类型
- `process(record)` — 对每个输入行，可以调多次 `forward()` 输出多行
- `close()` — 清理资源

**坑：UDTF 必须用 LATERAL**

```sql
-- ❌ SELECT func(log) FROM my_table;  不行
-- ✅ SELECT t.ts, t.event FROM my_table, LATERAL func(log) t;
```

**坑：UDTF DDL 忘了加 `TABLE_VALUED`**

```sql
-- ❌ 缺了这句，函数创建成功但调用时报 "not a table function"
-- ✅ 必须加
WITH PROPERTIES ('remote.udf.category'='TABLE_VALUED')
```

---

## 5. 测试

### UDF

```sql
SELECT <schema>.pii_mask('我的手机13812345678，邮箱alice@example.com，身份证310101199001011234');
-- → {"masked": "我的手机<phone>，邮箱<email>，身份证<id_card>", ...}
```

### UDAF

```sql
INSERT INTO <schema>.java_udf_test_scores VALUES (3.5), (4.2), (2.8), (5.0), (3.9);
SELECT <schema>.agg_stats(val) FROM <schema>.java_udf_test_scores;
-- → [sum, avg, min, max, count]
```

### UDTF

```sql
SELECT t.ts, t.event
FROM (SELECT '[2025-01-15 10:30:00] 用户登录
[2025-01-15 10:35:00] 查询订单
[2025-01-15 10:40:00] 提交支付' AS log) s,
LATERAL <schema>.log_explode(s.log) t;
-- → 3 行
```

---

## 6. 调试

### None of these will work:

- `System.out.println()` — 没有 stdout 终端
- `System.err.println()` — 同上
- `throw new RuntimeException("debug")` — FC 只返回 "Internal error" 没有堆栈

### What does work:

1. **本地单元测试。** 编写 JUnit 测试覆盖 `evaluate()` 逻辑，本地跑通后再部署
2. **return 调试。** 遇到问题时，让 `evaluate()` 返回 `"DEBUG: input was " + value`，从 SQL 结果里看
3. **只改一个函数。** 三个函数放一个 jar 没关系，但只调试一个，一个一个来

### 常见坑：

- **`ClassNotFoundException`**：`AS` 路径写错了包名，或 jar 里缺少类
- **`MethodNotFoundException`**：类名对但方法签名不对（参数类型和个数）
- **初始化失败**：`initialize()` 抛异常 → 函数创建成功但一调就崩。checkArgPrimitive/checkArgsSize 一定要写
- **UDAF 无数据**：表有 0 行时会返回 NULL，不是报错
- **UDTF 列数不匹配**：`SELECT *` 加 UDTF 可能列数混乱，建议显式列出列名 `t.ts, t.event`

---

## 7. 清理

```bash
cz-cli sql -f dist/5-cleanup_generated.sql --write
```

---

## 附录：脚本说明

| 文件 | 作用 |
|------|------|
| `pom.xml` | Maven 构建，hive-exec:2.3.9 (provided) |
| `2-package.py` | Maven 编译 + zip 打包 |
| `4-deploy.sql` | 部署 3 种类型函数 + 建表 + 测试 |
| `5-cleanup.sql` | 清理 |
| `../config.example.json` | 配置模板（共享） |
| `../1-check-config.py` | 检查配置（共享） |
| `../3-render-sql.py` | 占位符替换（共享） |
| `../SETUP.md` | 云环境准备（共享） |
