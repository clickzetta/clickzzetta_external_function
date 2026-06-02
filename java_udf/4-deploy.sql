PUT '<project_dir>/dist/all_udf.zip' TO VOLUME <volume> FILE 'all_udf.zip';  -- 4. 上传代码包

-- 5a  UDF
CREATE EXTERNAL FUNCTION IF NOT EXISTS <schema>.pii_mask
AS 'com.clickzetta.udf.PiiMaskUDF'
USING ARCHIVE 'volume://<volume>/all_udf.zip'
CONNECTION <fc_conn>
WITH PROPERTIES ('remote.udf.api'='java8.hive2.v0','remote.udf.protocol'='http.arrow.v0');

-- 5b  UDAF（必须加 'remote.udf.category'='AGGREGATOR'）
CREATE EXTERNAL FUNCTION IF NOT EXISTS <schema>.agg_stats
AS 'com.clickzetta.udf.AggStatsUDAF'
USING ARCHIVE 'volume://<volume>/all_udf.zip'
CONNECTION <fc_conn>
WITH PROPERTIES ('remote.udf.api'='java8.hive2.v0','remote.udf.category'='AGGREGATOR');

-- 5c  UDTF（必须加 'remote.udf.category'='TABLE_VALUED'）
CREATE EXTERNAL FUNCTION IF NOT EXISTS <schema>.log_explode
AS 'com.clickzetta.udf.LogExplodeUDTF'
USING ARCHIVE 'volume://<volume>/all_udf.zip'
CONNECTION <fc_conn>
WITH PROPERTIES ('remote.udf.api'='java8.hive2.v0','remote.udf.category'='TABLE_VALUED');

-- 6   测试

SELECT <schema>.pii_mask('我的手机13812345678，邮箱alice@example.com，身份证310101199001011234');

CREATE TABLE IF NOT EXISTS <schema>.java_udf_test_scores (val DOUBLE);
DELETE FROM <schema>.java_udf_test_scores WHERE 1=1;
INSERT INTO <schema>.java_udf_test_scores VALUES (3.5), (4.2), (2.8), (5.0), (3.9);
SELECT <schema>.agg_stats(val) FROM <schema>.java_udf_test_scores;

SELECT t.ts, t.event
FROM (SELECT '[2025-01-15 10:30:00] 用户登录
[2025-01-15 10:35:00] 查询订单
[2025-01-15 10:40:00] 提交支付' AS log) s,
LATERAL <schema>.log_explode(s.log) t;
