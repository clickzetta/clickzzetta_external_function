PUT '<project_dir>/dist/ml_toolkit.zip' TO VOLUME <volume> FILE 'ml_toolkit.zip';  -- 4. 上传

-- 5   CREATE 5 functions
CREATE EXTERNAL FUNCTION IF NOT EXISTS <schema>.pii_mask             AS 'ml_toolkit.pii_mask'             USING ARCHIVE 'volume://<volume>/ml_toolkit.zip' CONNECTION <fc_conn> WITH PROPERTIES ('remote.udf.api'='python3.mc.v0','remote.udf.protocol'='http.arrow.v0');
CREATE EXTERNAL FUNCTION IF NOT EXISTS <schema>.feature_normalize    AS 'ml_toolkit.feature_normalize'    USING ARCHIVE 'volume://<volume>/ml_toolkit.zip' CONNECTION <fc_conn> WITH PROPERTIES ('remote.udf.api'='python3.mc.v0','remote.udf.protocol'='http.arrow.v0');
CREATE EXTERNAL FUNCTION IF NOT EXISTS <schema>.anomaly_detect       AS 'ml_toolkit.anomaly_detect'       USING ARCHIVE 'volume://<volume>/ml_toolkit.zip' CONNECTION <fc_conn> WITH PROPERTIES ('remote.udf.api'='python3.mc.v0','remote.udf.protocol'='http.arrow.v0');
CREATE EXTERNAL FUNCTION IF NOT EXISTS <schema>.sentiment_score      AS 'ml_toolkit.sentiment_score'      USING ARCHIVE 'volume://<volume>/ml_toolkit.zip' CONNECTION <fc_conn> WITH PROPERTIES ('remote.udf.api'='python3.mc.v0','remote.udf.protocol'='http.arrow.v0');
CREATE EXTERNAL FUNCTION IF NOT EXISTS <schema>.tfidf_keywords       AS 'ml_toolkit.tfidf_keywords'       USING ARCHIVE 'volume://<volume>/ml_toolkit.zip' CONNECTION <fc_conn> WITH PROPERTIES ('remote.udf.api'='python3.mc.v0','remote.udf.protocol'='http.arrow.v0');

-- 6   验证
SELECT <schema>.pii_mask('我的手机13812345678，邮箱alice@example.com，身份证310101199001011234'),
       <schema>.feature_normalize('[10,20,30,40,50]', 'minmax'),
       <schema>.anomaly_detect('[1,2,3,4,100]'),
       <schema>.sentiment_score('产品质量非常好，物流很快，价格也便宜，下次还会再来买！'),
       <schema>.tfidf_keywords('["人工智能和机器学习是未来科技发展方向","深度学习在图像识别领域取得重大突破","人工智能将改变各行各业的运作方式"]', 3);
