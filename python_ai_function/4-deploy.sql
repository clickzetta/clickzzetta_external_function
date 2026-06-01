-- 云器 Lakehouse External Function 部署脚本
-- python 2-package.py --deps && python 1-check-config.py && python 3-render-sql.py && cz-cli sql -f dist/4-deploy_generated.sql --write

-- 1. Storage Connection（OSS 认证，供 External Volume 使用）
CREATE STORAGE CONNECTION IF NOT EXISTS <clickzetta.storage_connection>
TYPE OSS
access_id = '<aliyun.oss.access_id>'
access_key = '<aliyun.oss.access_key>'
ENDPOINT = '<aliyun.oss.endpoint>';

-- 2. API Connection（阿里云函数计算 FC 认证）
CREATE API CONNECTION IF NOT EXISTS <aliyun.fc.connection_name>
TYPE CLOUD_FUNCTION
PROVIDER = 'aliyun'
REGION = '<aliyun.fc.region>'
ROLE_ARN = '<aliyun.ram.role_arn>'
CODE_BUCKET = '<aliyun.oss.bucket>';

-- 3. External Volume（挂载 OSS Bucket 到 Schema）
CREATE EXTERNAL VOLUME IF NOT EXISTS <clickzetta.volume>
LOCATION 'oss://<aliyun.oss.bucket>/'
USING CONNECTION <clickzetta.storage_connection>
DIRECTORY = (ENABLE = true);

-- 4. 上传代码包到 External Volume
--    先执行：python 2-package.py --deps
PUT '<project_dir>/dist/clickzetta_ai_functions_full.zip' TO VOLUME <clickzetta.volume> FILE 'clickzetta_ai_functions_full.zip';

-- 5. 创建 External Function
--    DDL: CREATE EXTERNAL FUNCTION [schema_name.]function_name
--    ARCHIVE: volume://[{workspace}.][{schema}.]volume/file
--    调用时也必须加 schema 前缀，这是云器 Lakehouse 硬性要求
CREATE EXTERNAL FUNCTION IF NOT EXISTS <clickzetta.schema>.ai_text_summarize            AS 'ai_functions_complete.ai_text_summarize'            USING ARCHIVE 'volume://<clickzetta.volume>/clickzetta_ai_functions_full.zip' CONNECTION <aliyun.fc.connection_name> WITH PROPERTIES ('remote.udf.api'='python3.mc.v0','remote.udf.protocol'='http.arrow.v0');
-- CREATE EXTERNAL FUNCTION IF NOT EXISTS <clickzetta.schema>.ai_text_translate             AS 'ai_functions_complete.ai_text_translate'             USING ARCHIVE 'volume://<clickzetta.volume>/clickzetta_ai_functions_full.zip' CONNECTION <aliyun.fc.connection_name> WITH PROPERTIES ('remote.udf.api'='python3.mc.v0','remote.udf.protocol'='http.arrow.v0');
-- CREATE EXTERNAL FUNCTION IF NOT EXISTS <clickzetta.schema>.ai_text_sentiment_analyze     AS 'ai_functions_complete.ai_text_sentiment_analyze'     USING ARCHIVE 'volume://<clickzetta.volume>/clickzetta_ai_functions_full.zip' CONNECTION <aliyun.fc.connection_name> WITH PROPERTIES ('remote.udf.api'='python3.mc.v0','remote.udf.protocol'='http.arrow.v0');
-- CREATE EXTERNAL FUNCTION IF NOT EXISTS <clickzetta.schema>.ai_text_extract_entities      AS 'ai_functions_complete.ai_text_extract_entities'      USING ARCHIVE 'volume://<clickzetta.volume>/clickzetta_ai_functions_full.zip' CONNECTION <aliyun.fc.connection_name> WITH PROPERTIES ('remote.udf.api'='python3.mc.v0','remote.udf.protocol'='http.arrow.v0');
-- CREATE EXTERNAL FUNCTION IF NOT EXISTS <clickzetta.schema>.ai_text_extract_keywords      AS 'ai_functions_complete.ai_text_extract_keywords'      USING ARCHIVE 'volume://<clickzetta.volume>/clickzetta_ai_functions_full.zip' CONNECTION <aliyun.fc.connection_name> WITH PROPERTIES ('remote.udf.api'='python3.mc.v0','remote.udf.protocol'='http.arrow.v0');
-- CREATE EXTERNAL FUNCTION IF NOT EXISTS <clickzetta.schema>.ai_text_classify              AS 'ai_functions_complete.ai_text_classify'              USING ARCHIVE 'volume://<clickzetta.volume>/clickzetta_ai_functions_full.zip' CONNECTION <aliyun.fc.connection_name> WITH PROPERTIES ('remote.udf.api'='python3.mc.v0','remote.udf.protocol'='http.arrow.v0');
-- CREATE EXTERNAL FUNCTION IF NOT EXISTS <clickzetta.schema>.ai_text_clean_normalize       AS 'ai_functions_complete.ai_text_clean_normalize'       USING ARCHIVE 'volume://<clickzetta.volume>/clickzetta_ai_functions_full.zip' CONNECTION <aliyun.fc.connection_name> WITH PROPERTIES ('remote.udf.api'='python3.mc.v0','remote.udf.protocol'='http.arrow.v0');
-- CREATE EXTERNAL FUNCTION IF NOT EXISTS <clickzetta.schema>.ai_auto_tag_generate          AS 'ai_functions_complete.ai_auto_tag_generate'          USING ARCHIVE 'volume://<clickzetta.volume>/clickzetta_ai_functions_full.zip' CONNECTION <aliyun.fc.connection_name> WITH PROPERTIES ('remote.udf.api'='python3.mc.v0','remote.udf.protocol'='http.arrow.v0');
-- CREATE EXTERNAL FUNCTION IF NOT EXISTS <clickzetta.schema>.ai_text_to_embedding          AS 'ai_functions_complete.ai_text_to_embedding'          USING ARCHIVE 'volume://<clickzetta.volume>/clickzetta_ai_functions_full.zip' CONNECTION <aliyun.fc.connection_name> WITH PROPERTIES ('remote.udf.api'='python3.mc.v0','remote.udf.protocol'='http.arrow.v0');
-- CREATE EXTERNAL FUNCTION IF NOT EXISTS <clickzetta.schema>.ai_semantic_similarity        AS 'ai_functions_complete.ai_semantic_similarity'        USING ARCHIVE 'volume://<clickzetta.volume>/clickzetta_ai_functions_full.zip' CONNECTION <aliyun.fc.connection_name> WITH PROPERTIES ('remote.udf.api'='python3.mc.v0','remote.udf.protocol'='http.arrow.v0');
-- CREATE EXTERNAL FUNCTION IF NOT EXISTS <clickzetta.schema>.ai_text_clustering_prepare    AS 'ai_functions_complete.ai_text_clustering_prepare'    USING ARCHIVE 'volume://<clickzetta.volume>/clickzetta_ai_functions_full.zip' CONNECTION <aliyun.fc.connection_name> WITH PROPERTIES ('remote.udf.api'='python3.mc.v0','remote.udf.protocol'='http.arrow.v0');
-- CREATE EXTERNAL FUNCTION IF NOT EXISTS <clickzetta.schema>.ai_find_similar_text          AS 'ai_functions_complete.ai_find_similar_text'          USING ARCHIVE 'volume://<clickzetta.volume>/clickzetta_ai_functions_full.zip' CONNECTION <aliyun.fc.connection_name> WITH PROPERTIES ('remote.udf.api'='python3.mc.v0','remote.udf.protocol'='http.arrow.v0');
-- CREATE EXTERNAL FUNCTION IF NOT EXISTS <clickzetta.schema>.ai_document_search            AS 'ai_functions_complete.ai_document_search'            USING ARCHIVE 'volume://<clickzetta.volume>/clickzetta_ai_functions_full.zip' CONNECTION <aliyun.fc.connection_name> WITH PROPERTIES ('remote.udf.api'='python3.mc.v0','remote.udf.protocol'='http.arrow.v0');
-- CREATE EXTERNAL FUNCTION IF NOT EXISTS <clickzetta.schema>.ai_image_describe             AS 'ai_functions_complete.ai_image_describe'             USING ARCHIVE 'volume://<clickzetta.volume>/clickzetta_ai_functions_full.zip' CONNECTION <aliyun.fc.connection_name> WITH PROPERTIES ('remote.udf.api'='python3.mc.v0','remote.udf.protocol'='http.arrow.v0');
-- CREATE EXTERNAL FUNCTION IF NOT EXISTS <clickzetta.schema>.ai_image_ocr                  AS 'ai_functions_complete.ai_image_ocr'                  USING ARCHIVE 'volume://<clickzetta.volume>/clickzetta_ai_functions_full.zip' CONNECTION <aliyun.fc.connection_name> WITH PROPERTIES ('remote.udf.api'='python3.mc.v0','remote.udf.protocol'='http.arrow.v0');
-- CREATE EXTERNAL FUNCTION IF NOT EXISTS <clickzetta.schema>.ai_image_analyze              AS 'ai_functions_complete.ai_image_analyze'              USING ARCHIVE 'volume://<clickzetta.volume>/clickzetta_ai_functions_full.zip' CONNECTION <aliyun.fc.connection_name> WITH PROPERTIES ('remote.udf.api'='python3.mc.v0','remote.udf.protocol'='http.arrow.v0');
-- CREATE EXTERNAL FUNCTION IF NOT EXISTS <clickzetta.schema>.ai_image_to_embedding         AS 'ai_functions_complete.ai_image_to_embedding'         USING ARCHIVE 'volume://<clickzetta.volume>/clickzetta_ai_functions_full.zip' CONNECTION <aliyun.fc.connection_name> WITH PROPERTIES ('remote.udf.api'='python3.mc.v0','remote.udf.protocol'='http.arrow.v0');
-- CREATE EXTERNAL FUNCTION IF NOT EXISTS <clickzetta.schema>.ai_image_similarity            AS 'ai_functions_complete.ai_image_similarity'            USING ARCHIVE 'volume://<clickzetta.volume>/clickzetta_ai_functions_full.zip' CONNECTION <aliyun.fc.connection_name> WITH PROPERTIES ('remote.udf.api'='python3.mc.v0','remote.udf.protocol'='http.arrow.v0');
-- CREATE EXTERNAL FUNCTION IF NOT EXISTS <clickzetta.schema>.ai_video_summarize            AS 'ai_functions_complete.ai_video_summarize'            USING ARCHIVE 'volume://<clickzetta.volume>/clickzetta_ai_functions_full.zip' CONNECTION <aliyun.fc.connection_name> WITH PROPERTIES ('remote.udf.api'='python3.mc.v0','remote.udf.protocol'='http.arrow.v0');
-- CREATE EXTERNAL FUNCTION IF NOT EXISTS <clickzetta.schema>.ai_chart_analyze              AS 'ai_functions_complete.ai_chart_analyze'              USING ARCHIVE 'volume://<clickzetta.volume>/clickzetta_ai_functions_full.zip' CONNECTION <aliyun.fc.connection_name> WITH PROPERTIES ('remote.udf.api'='python3.mc.v0','remote.udf.protocol'='http.arrow.v0');
-- CREATE EXTERNAL FUNCTION IF NOT EXISTS <clickzetta.schema>.ai_document_parse             AS 'ai_functions_complete.ai_document_parse'             USING ARCHIVE 'volume://<clickzetta.volume>/clickzetta_ai_functions_full.zip' CONNECTION <aliyun.fc.connection_name> WITH PROPERTIES ('remote.udf.api'='python3.mc.v0','remote.udf.protocol'='http.arrow.v0');
-- CREATE EXTERNAL FUNCTION IF NOT EXISTS <clickzetta.schema>.ai_customer_intent_analyze    AS 'ai_functions_complete.ai_customer_intent_analyze'    USING ARCHIVE 'volume://<clickzetta.volume>/clickzetta_ai_functions_full.zip' CONNECTION <aliyun.fc.connection_name> WITH PROPERTIES ('remote.udf.api'='python3.mc.v0','remote.udf.protocol'='http.arrow.v0');
-- CREATE EXTERNAL FUNCTION IF NOT EXISTS <clickzetta.schema>.ai_sales_lead_score            AS 'ai_functions_complete.ai_sales_lead_score'            USING ARCHIVE 'volume://<clickzetta.volume>/clickzetta_ai_functions_full.zip' CONNECTION <aliyun.fc.connection_name> WITH PROPERTIES ('remote.udf.api'='python3.mc.v0','remote.udf.protocol'='http.arrow.v0');
-- CREATE EXTERNAL FUNCTION IF NOT EXISTS <clickzetta.schema>.ai_review_analyze             AS 'ai_functions_complete.ai_review_analyze'             USING ARCHIVE 'volume://<clickzetta.volume>/clickzetta_ai_functions_full.zip' CONNECTION <aliyun.fc.connection_name> WITH PROPERTIES ('remote.udf.api'='python3.mc.v0','remote.udf.protocol'='http.arrow.v0');
-- CREATE EXTERNAL FUNCTION IF NOT EXISTS <clickzetta.schema>.ai_risk_text_detect            AS 'ai_functions_complete.ai_risk_text_detect'            USING ARCHIVE 'volume://<clickzetta.volume>/clickzetta_ai_functions_full.zip' CONNECTION <aliyun.fc.connection_name> WITH PROPERTIES ('remote.udf.api'='python3.mc.v0','remote.udf.protocol'='http.arrow.v0');
-- CREATE EXTERNAL FUNCTION IF NOT EXISTS <clickzetta.schema>.ai_contract_extract            AS 'ai_functions_complete.ai_contract_extract'            USING ARCHIVE 'volume://<clickzetta.volume>/clickzetta_ai_functions_full.zip' CONNECTION <aliyun.fc.connection_name> WITH PROPERTIES ('remote.udf.api'='python3.mc.v0','remote.udf.protocol'='http.arrow.v0');
-- CREATE EXTERNAL FUNCTION IF NOT EXISTS <clickzetta.schema>.ai_resume_parse               AS 'ai_functions_complete.ai_resume_parse'               USING ARCHIVE 'volume://<clickzetta.volume>/clickzetta_ai_functions_full.zip' CONNECTION <aliyun.fc.connection_name> WITH PROPERTIES ('remote.udf.api'='python3.mc.v0','remote.udf.protocol'='http.arrow.v0');
-- CREATE EXTERNAL FUNCTION IF NOT EXISTS <clickzetta.schema>.ai_customer_segment            AS 'ai_functions_complete.ai_customer_segment'            USING ARCHIVE 'volume://<clickzetta.volume>/clickzetta_ai_functions_full.zip' CONNECTION <aliyun.fc.connection_name> WITH PROPERTIES ('remote.udf.api'='python3.mc.v0','remote.udf.protocol'='http.arrow.v0');
-- CREATE EXTERNAL FUNCTION IF NOT EXISTS <clickzetta.schema>.ai_product_description_generate    AS 'ai_functions_complete.ai_product_description_generateerate' USING ARCHIVE 'volume://<clickzetta.volume>/clickzetta_ai_functions_full.zip' CONNECTION <aliyun.fc.connection_name> WITH PROPERTIES ('remote.udf.api'='python3.mc.v0','remote.udf.protocol'='http.arrow.v0');
-- CREATE EXTERNAL FUNCTION IF NOT EXISTS <clickzetta.schema>.ai_industry_classification     AS 'ai_functions_complete.ai_industry_classification'     USING ARCHIVE 'volume://<clickzetta.volume>/clickzetta_ai_functions_full.zip' CONNECTION <aliyun.fc.connection_name> WITH PROPERTIES ('remote.udf.api'='python3.mc.v0','remote.udf.protocol'='http.arrow.v0');

-- 6. 验证（调用时必须加 schema 前缀）
SELECT <clickzetta.schema>.ai_text_summarize('你好世界', '<dashscope.api_key>');
