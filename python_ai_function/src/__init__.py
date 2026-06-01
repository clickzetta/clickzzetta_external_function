"""
ClickZetta AI SQL Functions Package
基于百炼大模型的AI SQL函数集合
"""

__version__ = "1.0.0"
__author__ = "ClickZetta Team"

from .ai_functions_complete import (
    # 文本处理 (8个)
    ai_text_summarize,
    ai_text_translate,
    ai_text_sentiment_analyze,
    ai_text_extract_entities,
    ai_text_extract_keywords,
    ai_text_classify,
    ai_text_clean_normalize,
    ai_auto_tag_generate,
    # 向量处理 (5个)
    ai_text_to_embedding,
    ai_semantic_similarity,
    ai_text_clustering_prepare,
    ai_find_similar_text,
    ai_document_search,
    # 多模态处理 (8个)
    ai_image_describe,
    ai_image_ocr,
    ai_image_analyze,
    ai_image_to_embedding,
    ai_image_similarity,
    ai_video_summarize,
    ai_chart_analyze,
    ai_document_parse,
    # 业务场景 (9个)
    ai_customer_intent_analyze,
    ai_sales_lead_score,
    ai_review_analyze,
    ai_risk_text_detect,
    ai_contract_extract,
    ai_resume_parse,
    ai_customer_segment,
    ai_product_description_generate,
    ai_industry_classification,
)

__all__ = [
    # 文本处理
    'ai_text_summarize',
    'ai_text_translate',
    'ai_text_sentiment_analyze',
    'ai_text_extract_entities',
    'ai_text_extract_keywords',
    'ai_text_classify',
    'ai_text_clean_normalize',
    'ai_auto_tag_generate',
    # 向量处理
    'ai_text_to_embedding',
    'ai_semantic_similarity',
    'ai_text_clustering_prepare',
    'ai_find_similar_text',
    'ai_document_search',
    # 多模态处理
    'ai_image_describe',
    'ai_image_ocr',
    'ai_image_analyze',
    'ai_image_to_embedding',
    'ai_image_similarity',
    'ai_video_summarize',
    'ai_chart_analyze',
    'ai_document_parse',
    # 业务场景
    'ai_customer_intent_analyze',
    'ai_sales_lead_score',
    'ai_review_analyze',
    'ai_risk_text_detect',
    'ai_contract_extract',
    'ai_resume_parse',
    'ai_customer_segment',
    'ai_product_description_generate',
    'ai_industry_classification',
]
