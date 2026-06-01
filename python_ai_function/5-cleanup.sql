-- 云器 Lakehouse External Function 清理脚本
-- 使用前把所有 your_schema 替换为 config.json → clickzetta.schema
-- 执行：cz-cli sql -f 5-cleanup.sql --write

DROP FUNCTION IF EXISTS your_schema.ai_text_summarize;
DROP FUNCTION IF EXISTS your_schema.ai_text_translate;
DROP FUNCTION IF EXISTS your_schema.ai_text_sentiment_analyze;
DROP FUNCTION IF EXISTS your_schema.ai_text_extract_entities;
DROP FUNCTION IF EXISTS your_schema.ai_text_extract_keywords;
DROP FUNCTION IF EXISTS your_schema.ai_text_classify;
DROP FUNCTION IF EXISTS your_schema.ai_text_clean_normalize;
DROP FUNCTION IF EXISTS your_schema.ai_auto_tag_generate;
DROP FUNCTION IF EXISTS your_schema.ai_text_to_embedding;
DROP FUNCTION IF EXISTS your_schema.ai_semantic_similarity;
DROP FUNCTION IF EXISTS your_schema.ai_text_clustering_prepare;
DROP FUNCTION IF EXISTS your_schema.ai_find_similar_text;
DROP FUNCTION IF EXISTS your_schema.ai_document_search;
DROP FUNCTION IF EXISTS your_schema.ai_image_describe;
DROP FUNCTION IF EXISTS your_schema.ai_image_ocr;
DROP FUNCTION IF EXISTS your_schema.ai_image_analyze;
DROP FUNCTION IF EXISTS your_schema.ai_image_to_embedding;
DROP FUNCTION IF EXISTS your_schema.ai_image_similarity;
DROP FUNCTION IF EXISTS your_schema.ai_video_summarize;
DROP FUNCTION IF EXISTS your_schema.ai_chart_analyze;
DROP FUNCTION IF EXISTS your_schema.ai_document_parse;
DROP FUNCTION IF EXISTS your_schema.ai_customer_intent_analyze;
DROP FUNCTION IF EXISTS your_schema.ai_sales_lead_score;
DROP FUNCTION IF EXISTS your_schema.ai_review_analyze;
DROP FUNCTION IF EXISTS your_schema.ai_risk_text_detect;
DROP FUNCTION IF EXISTS your_schema.ai_contract_extract;
DROP FUNCTION IF EXISTS your_schema.ai_resume_parse;
DROP FUNCTION IF EXISTS your_schema.ai_customer_segment;
DROP FUNCTION IF EXISTS your_schema.ai_product_description_gen;
DROP FUNCTION IF EXISTS your_schema.ai_industry_classification;

DROP VOLUME IF EXISTS external_functions_prod;
DROP CONNECTION IF EXISTS shanghai_func_conn;
DROP CONNECTION IF EXISTS oss_sh_conn;
