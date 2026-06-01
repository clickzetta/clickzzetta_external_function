-- 1
CREATE STORAGE CONNECTION IF NOT EXISTS java_oss
TYPE OSS
access_id = '<access_id>'
access_key = '<access_key>'
ENDPOINT = '<endpoint>';

-- 2
CREATE API CONNECTION IF NOT EXISTS java_fc
TYPE CLOUD_FUNCTION
PROVIDER = 'aliyun'
REGION = '<region>'
ROLE_ARN = '<role_arn>'
CODE_BUCKET = '<bucket>';

-- 3
CREATE EXTERNAL VOLUME IF NOT EXISTS java_vol
LOCATION 'oss://<bucket>/'
USING CONNECTION java_oss
DIRECTORY = (ENABLE = true);

-- 4
PUT '<project_dir>/dist/all_udf.zip' TO VOLUME java_vol FILE 'all_udf.zip';

-- 5a  UDF — 标量函数
CREATE EXTERNAL FUNCTION IF NOT EXISTS <schema>.pii_mask
AS 'com.clickzetta.udf.PiiMaskUDF'
USING ARCHIVE 'volume://java_vol/all_udf.zip'
CONNECTION java_fc
WITH PROPERTIES ('remote.udf.api'='java8.hive2.v0','remote.udf.protocol'='http.arrow.v0');

-- 5b  UDAF — 聚合函数（必须加 'remote.udf.category'='AGGREGATOR'）
CREATE EXTERNAL FUNCTION IF NOT EXISTS <schema>.agg_stats
AS 'com.clickzetta.udf.AggStatsUDAF'
USING ARCHIVE 'volume://java_vol/all_udf.zip'
CONNECTION java_fc
WITH PROPERTIES ('remote.udf.api'='java8.hive2.v0','remote.udf.category'='AGGREGATOR');

-- 5c  UDTF — 表函数（必须加 'remote.udf.category'='TABLE_VALUED'）
CREATE EXTERNAL FUNCTION IF NOT EXISTS <schema>.log_explode
AS 'com.clickzetta.udf.LogExplodeUDTF'
USING ARCHIVE 'volume://java_vol/all_udf.zip'
CONNECTION java_fc
WITH PROPERTIES ('remote.udf.api'='java8.hive2.v0','remote.udf.category'='TABLE_VALUED');

-- 6  测试

-- 6a  UDF：一行进一行出
SELECT <schema>.pii_mask('我的手机13812345678，邮箱alice@example.com，身份证310101199001011234');

-- 6b  UDAF：建表 → 插数 → 聚合
CREATE TABLE IF NOT EXISTS <schema>.java_udf_test_scores (val DOUBLE);
DELETE FROM <schema>.java_udf_test_scores;
INSERT INTO <schema>.java_udf_test_scores VALUES (3.5), (4.2), (2.8), (5.0), (3.9);
SELECT <schema>.agg_stats(val) FROM <schema>.java_udf_test_scores;

-- 6c  UDTF：一行拆成多行（LATERAL）
SELECT t.ts, t.event
FROM (SELECT '[2025-01-15 10:30:00] 用户登录
[2025-01-15 10:35:00] 查询订单
[2025-01-15 10:40:00] 提交支付' AS log) s,
LATERAL <schema>.log_explode(s.log) t;
