"""
云器 Lakehouse Python External Function — AI SQL 函数集
30个AI SQL函数，基于百炼 DashScope SDK
依赖: dashscope>=1.23.4（通过 python 2-package.py --deps 打包）
模型配置: config.json
"""
import os, json, re, math
from datetime import datetime

# ---- 模型配置 ----
def _load_config():
    defaults = {"text": "deepseek-v3", "reasoning": "deepseek-r1",
                "embedding": "text-embedding-v4", "multimodal": "qwen-vl-plus"}
    try:
        for p in [os.path.join(os.path.dirname(__file__), "config.json"),
                  os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")]:
            if os.path.exists(p):
                cfg = json.load(open(p))
                for k in defaults:
                    if k in cfg.get("models", {}):
                        defaults[k] = cfg["models"][k]
                break
    except: pass
    return defaults

_MODEL = _load_config()
_MODEL_TEXT = _MODEL["text"]
_MODEL_REASONING = _MODEL["reasoning"]
_MODEL_EMBEDDING = _MODEL["embedding"]
_MODEL_MULTIMODAL = _MODEL["multimodal"]

# ---- 装饰器 ----
def annotate(signature):
    def d(cls): cls._signature = signature; return cls
    return d

try:
    from cz.udf import annotate
except ImportError: pass

# ---- dashscope 环境检测 ----
try:
    import dashscope
    from http import HTTPStatus
    HAS_DASHSCOPE = True
except ImportError:
    HAS_DASHSCOPE = False
    class HTTPStatus: OK = 200


def _call_llm(model, messages, temperature=0.7, max_tokens=2000, enable_search=False):
    """统一调用 dashscope 文本生成，返回响应文本"""
    responses = dashscope.Generation.call(
        model=model, messages=messages, stream=False,
        result_format='message', temperature=temperature,
        max_tokens=max_tokens, enable_search=enable_search
    )
    if responses.status_code == HTTPStatus.OK:
        if hasattr(responses.output, 'choices') and responses.output.choices:
            return responses.output.choices[0].message.content or ""
    return json.dumps({"error": True, "message": f"API调用失败: {responses.message}"}, ensure_ascii=False)


def _call_embed(model, texts):
    """批量文本向量化，返回 embedding 列表"""
    resp = dashscope.TextEmbedding.call(model=model, input=texts)
    if resp.status_code == HTTPStatus.OK:
        return [e["embedding"] for e in resp.output["embeddings"]]
    return []


def _call_mm_embed(model, images):
    """多模态向量化"""
    body = {"model": model, "input": {"contents": [{"image": url} for url in images]}}
    resp = dashscope.MultiModalEmbedding.call(**body)
    if resp.status_code == HTTPStatus.OK:
        return [e["embedding"] for e in resp.output["embeddings"]]
    return []


def _clean_md(content):
    """清理 markdown 代码块"""
    if not content: return content
    c = re.sub(r'^```(?:json)?\s*\n?', '', content.strip())
    return re.sub(r'\n?```\s*$', '', c).strip()


def _parse_json(content):
    """尝试解析 JSON，失败返回字符串"""
    c = _clean_md(content)
    try: return json.loads(c)
    except: return c


# ---- 文本处理 (8个) ----

@annotate("*->string")
class ai_text_summarize(object):
    def evaluate(self, text, api_key, model_name=_MODEL_TEXT, max_length=200):
        if not HAS_DASHSCOPE:
            err = {"error": True, "message": "dashscope 不可用，请确认安装: pip install dashscope>=1.23.4"}
            return json.dumps(err, ensure_ascii=False)
        try:
            dashscope.api_key = api_key
            msgs = [{"role": "system", "content": f"你是专业的文本摘要专家。将文本总结为不超过{max_length}字的摘要。"},
                    {"role": "user", "content": text}]
            content = _call_llm(model_name, msgs, max_tokens=max_length)
            return json.dumps({"summary": content.strip(), "original_length": len(text),
                               "model": model_name, "timestamp": datetime.now().isoformat()}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": True, "message": str(e)}, ensure_ascii=False)


@annotate("*->string")
class ai_text_translate(object):
    def evaluate(self, text, target_language, api_key, model_name=_MODEL_TEXT):
        if not HAS_DASHSCOPE: return json.dumps({"error": True, "message": "dashscope 不可用"}, ensure_ascii=False)
        try:
            dashscope.api_key = api_key
            msgs = [{"role": "system", "content": f"翻译成{target_language}，只输出译文。"},
                    {"role": "user", "content": text}]
            content = _call_llm(model_name, msgs, temperature=0.3, max_tokens=len(text)*3)
            return json.dumps({"translated_text": content.strip(), "original_text": text,
                               "target_language": target_language, "model": model_name}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": True, "message": str(e)}, ensure_ascii=False)


@annotate("*->string")
class ai_text_sentiment_analyze(object):
    def evaluate(self, text, api_key, model_name=_MODEL_TEXT):
        if not HAS_DASHSCOPE: return json.dumps({"error": True, "message": "dashscope 不可用"}, ensure_ascii=False)
        try:
            dashscope.api_key = api_key
            msgs = [{"role": "system", "content": '情感分析。返回JSON：{"sentiment":"positive|negative|neutral","confidence":0.95,"emotions":["joy"...],"keywords":[...]}。只输出JSON。'},
                    {"role": "user", "content": text}]
            content = _call_llm(model_name, msgs, temperature=0.1, max_tokens=300)
            r = _parse_json(content)
            if not isinstance(r, dict): r = {"sentiment_analysis": content}
            r["model"] = model_name
            return json.dumps(r, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": True, "message": str(e)}, ensure_ascii=False)


@annotate("*->string")
class ai_text_extract_entities(object):
    def evaluate(self, text, api_key, entity_types="all", model_name=_MODEL_TEXT):
        if not HAS_DASHSCOPE: return json.dumps({"error": True, "message": "dashscope 不可用"}, ensure_ascii=False)
        try:
            dashscope.api_key = api_key
            msgs = [{"role": "system", "content": f'提取实体（类型：{entity_types}）。返回JSON：{{"entities":[{{"text":"实体","type":"PERSON|ORG|LOC|MISC","confidence":0.95}}]}}。只输出JSON。'},
                    {"role": "user", "content": text}]
            content = _call_llm(model_name, msgs, temperature=0.2, max_tokens=500)
            r = _parse_json(content)
            if not isinstance(r, dict): r = {"entities": content}
            r["model"] = model_name
            return json.dumps(r, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": True, "message": str(e)}, ensure_ascii=False)


@annotate("*->string")
class ai_text_extract_keywords(object):
    def evaluate(self, text, api_key, max_keywords=10, model_name=_MODEL_TEXT):
        if not HAS_DASHSCOPE: return json.dumps({"error": True, "message": "dashscope 不可用"}, ensure_ascii=False)
        try:
            dashscope.api_key = api_key
            msgs = [{"role": "system", "content": f'提取{max_keywords}个关键词。返回JSON：{{"keywords":[{{"word":"词","weight":0.95,"category":"类"}}]}}。只输出JSON。'},
                    {"role": "user", "content": text}]
            content = _call_llm(model_name, msgs, temperature=0.3, max_tokens=500)
            r = _parse_json(content)
            if not isinstance(r, dict): r = {"keywords": content}
            r["model"] = model_name
            return json.dumps(r, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": True, "message": str(e)}, ensure_ascii=False)


@annotate("*->string")
class ai_text_classify(object):
    def evaluate(self, text, api_key, categories="auto", model_name=_MODEL_TEXT):
        if not HAS_DASHSCOPE: return json.dumps({"error": True, "message": "dashscope 不可用"}, ensure_ascii=False)
        try:
            dashscope.api_key = api_key
            msgs = [{"role": "system", "content": f'文本分类（类别：{categories}）。返回JSON：{{"category":"类","confidence":0.95,"subcategories":[...]}}。只输出JSON。'},
                    {"role": "user", "content": text}]
            content = _call_llm(model_name, msgs, temperature=0.2, max_tokens=300)
            r = _parse_json(content)
            if not isinstance(r, dict): r = {"classification": content}
            r["model"] = model_name
            return json.dumps(r, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": True, "message": str(e)}, ensure_ascii=False)


@annotate("*->string")
class ai_text_clean_normalize(object):
    def evaluate(self, text, api_key, operations="all", model_name=_MODEL_TEXT):
        if not HAS_DASHSCOPE: return json.dumps({"error": True, "message": "dashscope 不可用"}, ensure_ascii=False)
        try:
            dashscope.api_key = api_key
            msgs = [{"role": "system", "content": f'文本清理（操作：{operations}）。返回JSON：{{"cleaned_text":"文本","operations_applied":["去空格","标准化"],"changes_count":3}}。只输出JSON。'},
                    {"role": "user", "content": text}]
            content = _call_llm(model_name, msgs, temperature=0.1, max_tokens=len(text)*2)
            r = _parse_json(content)
            if not isinstance(r, dict): r = {"cleaned_text": content}
            r["operations"] = operations; r["model"] = model_name
            return json.dumps(r, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": True, "message": str(e)}, ensure_ascii=False)


@annotate("*->string")
class ai_auto_tag_generate(object):
    def evaluate(self, text, api_key, max_tags=10, model_name=_MODEL_TEXT):
        if not HAS_DASHSCOPE: return json.dumps({"error": True, "message": "dashscope 不可用"}, ensure_ascii=False)
        try:
            dashscope.api_key = api_key
            msgs = [{"role": "system", "content": f'生成{max_tags}个标签。返回JSON：{{"tags":[{{"tag":"标签","relevance":0.95,"category":"类"}}]}}。只输出JSON。'},
                    {"role": "user", "content": text}]
            content = _call_llm(model_name, msgs, temperature=0.3, max_tokens=500)
            r = _parse_json(content)
            if not isinstance(r, dict): r = {"tags": content}
            r["model"] = model_name
            return json.dumps(r, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": True, "message": str(e)}, ensure_ascii=False)


# ---- 向量处理 (5个) ----

@annotate("*->string")
class ai_text_to_embedding(object):
    def evaluate(self, text, api_key, model_name=_MODEL_EMBEDDING):
        if not HAS_DASHSCOPE: return json.dumps({"error": True, "message": "dashscope 不可用"}, ensure_ascii=False)
        try:
            dashscope.api_key = api_key
            embs = _call_embed(model_name, [text])
            return json.dumps({"embedding": embs[0] if embs else [], "model": model_name}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": True, "message": str(e)}, ensure_ascii=False)


@annotate("*->string")
class ai_semantic_similarity(object):
    def evaluate(self, text1, text2, api_key, model_name=_MODEL_EMBEDDING):
        if not HAS_DASHSCOPE: return json.dumps({"error": True, "message": "dashscope 不可用"}, ensure_ascii=False)
        try:
            dashscope.api_key = api_key
            embs = _call_embed(model_name, [text1, text2])
            if len(embs) >= 2:
                v1, v2 = embs[0], embs[1]
                dot = sum(a*b for a,b in zip(v1,v2))
                m1 = math.sqrt(sum(a*a for a in v1)); m2 = math.sqrt(sum(b*b for b in v2))
                sim = dot/(m1*m2) if m1 and m2 else 0
            else: sim = 0
            return json.dumps({"similarity": sim, "text1_length": len(text1),
                               "text2_length": len(text2), "model": model_name}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": True, "message": str(e)}, ensure_ascii=False)


@annotate("*->string")
class ai_text_clustering_prepare(object):
    def evaluate(self, texts_json, api_key, model_name=_MODEL_EMBEDDING):
        if not HAS_DASHSCOPE: return json.dumps({"error": True, "message": "dashscope 不可用"}, ensure_ascii=False)
        try:
            texts = json.loads(texts_json)
            dashscope.api_key = api_key
            embs = _call_embed(model_name, texts)
            return json.dumps({"embeddings": embs, "count": len(texts), "model": model_name}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": True, "message": str(e)}, ensure_ascii=False)


@annotate("*->string")
class ai_find_similar_text(object):
    def evaluate(self, query_text, candidate_texts_json, api_key, top_k=5, model_name=_MODEL_EMBEDDING):
        if not HAS_DASHSCOPE: return json.dumps({"error": True, "message": "dashscope 不可用"}, ensure_ascii=False)
        try:
            candidates = json.loads(candidate_texts_json)
            dashscope.api_key = api_key
            embs = _call_embed(model_name, [query_text] + candidates)
            if len(embs) >= 2:
                qv, results = embs[0], []
                for i, v in enumerate(embs[1:]):
                    dot = sum(a*b for a,b in zip(qv,v))
                    m1 = math.sqrt(sum(a*a for a in qv)); m2 = math.sqrt(sum(b*b for b in v))
                    results.append({"text": candidates[i], "similarity": dot/(m1*m2) if m1 and m2 else 0})
                results.sort(key=lambda x: x["similarity"], reverse=True)
            else: results = []
            return json.dumps({"similar_texts": results[:top_k], "total_candidates": len(candidates)}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": True, "message": str(e)}, ensure_ascii=False)


@annotate("*->string")
class ai_document_search(object):
    def evaluate(self, query, documents_json, api_key, top_k=3, model_name=_MODEL_EMBEDDING):
        if not HAS_DASHSCOPE: return json.dumps({"error": True, "message": "dashscope 不可用"}, ensure_ascii=False)
        try:
            docs = json.loads(documents_json)
            texts = [d if isinstance(d, str) else d.get("text", "") for d in docs]
            dashscope.api_key = api_key
            embs = _call_embed(model_name, [query] + texts)
            if len(embs) >= 2:
                qv, results = embs[0], []
                for i, v in enumerate(embs[1:]):
                    dot = sum(a*b for a,b in zip(qv,v))
                    m1 = math.sqrt(sum(a*a for a in qv)); m2 = math.sqrt(sum(b*b for b in v))
                    doc_id = docs[i].get("id", str(i)) if isinstance(docs[i], dict) else str(i)
                    snippet = texts[i][:200] + ("..." if len(texts[i]) > 200 else "")
                    results.append({"doc_id": doc_id, "score": dot/(m1*m2) if m1 and m2 else 0, "snippet": snippet})
                results.sort(key=lambda x: x["score"], reverse=True)
            else: results = []
            return json.dumps({"results": results[:top_k], "query": query, "total_docs": len(docs)}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": True, "message": str(e)}, ensure_ascii=False)


# ---- 多模态 (8个) ----

@annotate("*->string")
class ai_image_describe(object):
    def evaluate(self, image_url, api_key, prompt="描述这张图片", model_name=_MODEL_MULTIMODAL):
        if not HAS_DASHSCOPE: return json.dumps({"error": True, "message": "dashscope 不可用"}, ensure_ascii=False)
        try:
            dashscope.api_key = api_key
            msgs = [{"role": "system", "content": prompt},
                    {"role": "user", "content": [{"image": image_url}]}]
            content = _call_llm(model_name, msgs, max_tokens=500)
            return json.dumps({"description": content.strip(), "image_url": image_url, "model": model_name}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": True, "message": str(e)}, ensure_ascii=False)


@annotate("*->string")
class ai_image_ocr(object):
    def evaluate(self, image_url, api_key, language="auto", model_name=_MODEL_MULTIMODAL):
        if not HAS_DASHSCOPE: return json.dumps({"error": True, "message": "dashscope 不可用"}, ensure_ascii=False)
        try:
            dashscope.api_key = api_key
            msgs = [{"role": "system", "content": f'OCR识别（语言：{language}）。返回JSON：{{"text":"识别文字","confidence":0.95,"blocks":[...]}}。只输出JSON。'},
                    {"role": "user", "content": [{"image": image_url}]}]
            content = _call_llm(model_name, msgs, temperature=0.1, max_tokens=1000)
            r = _parse_json(content)
            if not isinstance(r, dict): r = {"ocr_result": content}
            r["model"] = model_name; r["image_url"] = image_url
            return json.dumps(r, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": True, "message": str(e)}, ensure_ascii=False)


@annotate("*->string")
class ai_image_analyze(object):
    def evaluate(self, image_url, api_key, analysis_type="general", model_name=_MODEL_MULTIMODAL):
        if not HAS_DASHSCOPE: return json.dumps({"error": True, "message": "dashscope 不可用"}, ensure_ascii=False)
        try:
            dashscope.api_key = api_key
            msgs = [{"role": "system", "content": f'分析图片（类型：{analysis_type}）。返回JSON：{{"analysis":"结果","objects":[...],"scene":"场景","confidence":0.9}}。只输出JSON。'},
                    {"role": "user", "content": [{"image": image_url}]}]
            content = _call_llm(model_name, msgs, temperature=0.3, max_tokens=500)
            r = _parse_json(content)
            if not isinstance(r, dict): r = {"analysis": content}
            r["model"] = model_name; r["analysis_type"] = analysis_type
            return json.dumps(r, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": True, "message": str(e)}, ensure_ascii=False)


@annotate("*->string")
class ai_image_to_embedding(object):
    def evaluate(self, image_url, api_key, model_name="multimodal-embedding-one-peace-v1"):
        if not HAS_DASHSCOPE: return json.dumps({"error": True, "message": "dashscope 不可用"}, ensure_ascii=False)
        try:
            dashscope.api_key = api_key
            embs = _call_mm_embed(model_name, [image_url])
            return json.dumps({"embedding": embs[0] if embs else [], "model": model_name}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": True, "message": str(e)}, ensure_ascii=False)


@annotate("*->string")
class ai_image_similarity(object):
    def evaluate(self, image_url1, image_url2, api_key, model_name="multimodal-embedding-one-peace-v1"):
        if not HAS_DASHSCOPE: return json.dumps({"error": True, "message": "dashscope 不可用"}, ensure_ascii=False)
        try:
            dashscope.api_key = api_key
            embs = _call_mm_embed(model_name, [image_url1, image_url2])
            if len(embs) >= 2:
                v1, v2 = embs[0], embs[1]
                dot = sum(a*b for a,b in zip(v1,v2))
                m1 = math.sqrt(sum(a*a for a in v1)); m2 = math.sqrt(sum(b*b for b in v2))
                sim = dot/(m1*m2) if m1 and m2 else 0
            else: sim = 0
            return json.dumps({"similarity": sim, "model": model_name}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": True, "message": str(e)}, ensure_ascii=False)


@annotate("*->string")
class ai_video_summarize(object):
    def evaluate(self, video_frames_json, api_key, model_name=_MODEL_MULTIMODAL):
        if not HAS_DASHSCOPE: return json.dumps({"error": True, "message": "dashscope 不可用"}, ensure_ascii=False)
        try:
            frames = json.loads(video_frames_json)
            dashscope.api_key = api_key
            msgs = [{"role": "system", "content": '总结视频帧内容。返回JSON：{"summary":"摘要","key_moments":[...],"duration_estimate":"时长"}。只输出JSON。'},
                    {"role": "user", "content": [{"image": f.get("url", str(f))} for f in frames[:5]]}]
            content = _call_llm(model_name, msgs, max_tokens=500)
            r = _parse_json(content)
            if not isinstance(r, dict): r = {"summary": content}
            r["model"] = model_name; r["frames_analyzed"] = min(len(frames), 5)
            return json.dumps(r, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": True, "message": str(e)}, ensure_ascii=False)


@annotate("*->string")
class ai_chart_analyze(object):
    def evaluate(self, chart_image_url, api_key, analysis_focus="data", model_name=_MODEL_MULTIMODAL):
        if not HAS_DASHSCOPE: return json.dumps({"error": True, "message": "dashscope 不可用"}, ensure_ascii=False)
        try:
            dashscope.api_key = api_key
            msgs = [{"role": "system", "content": f'分析图表（关注：{analysis_focus}）。返回JSON：{{"chart_type":"类型","data_summary":"摘要","trends":[...],"insights":[...]}}。只输出JSON。'},
                    {"role": "user", "content": [{"image": chart_image_url}]}]
            content = _call_llm(model_name, msgs, max_tokens=500)
            r = _parse_json(content)
            if not isinstance(r, dict): r = {"analysis": content}
            r["model"] = model_name; r["analysis_focus"] = analysis_focus
            return json.dumps(r, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": True, "message": str(e)}, ensure_ascii=False)


@annotate("*->string")
class ai_document_parse(object):
    def evaluate(self, doc_images_json, api_key, parse_type="structure", model_name=_MODEL_MULTIMODAL):
        if not HAS_DASHSCOPE: return json.dumps({"error": True, "message": "dashscope 不可用"}, ensure_ascii=False)
        try:
            pages = json.loads(doc_images_json)
            dashscope.api_key = api_key
            msgs = [{"role": "system", "content": f'解析文档（类型：{parse_type}）。返回JSON：{{"content":"内容","structure":"结构","tables":[...]}}。只输出JSON。'},
                    {"role": "user", "content": [{"image": p.get("url", str(p))} for p in pages[:3]]}]
            content = _call_llm(model_name, msgs, max_tokens=1000)
            r = _parse_json(content)
            if not isinstance(r, dict): r = {"content": content}
            r["model"] = model_name; r["parse_type"] = parse_type
            return json.dumps(r, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": True, "message": str(e)}, ensure_ascii=False)


# ---- 业务场景 (9个) ----

@annotate("*->string")
class ai_customer_intent_analyze(object):
    def evaluate(self, customer_text, api_key, business_context="general", model_name=_MODEL_TEXT):
        if not HAS_DASHSCOPE: return json.dumps({"error": True, "message": "dashscope 不可用"}, ensure_ascii=False)
        try:
            dashscope.api_key = api_key
            msgs = [{"role": "system", "content": f'分析客户意图（场景：{business_context}）。返回JSON：{{"intent":"意图","confidence":0.95,"urgency":"high|medium|low","emotions":["neutral"...],"action_required":"建议"}}。只输出JSON。'},
                    {"role": "user", "content": customer_text}]
            content = _call_llm(model_name, msgs, temperature=0.2, max_tokens=300)
            r = _parse_json(content)
            if not isinstance(r, dict): r = {"intent_analysis": content}
            r.update({"customer_text": customer_text, "business_context": business_context, "model": model_name})
            return json.dumps(r, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": True, "message": str(e)}, ensure_ascii=False)


@annotate("*->string")
class ai_sales_lead_score(object):
    def evaluate(self, lead_info, api_key, scoring_criteria="RFM", model_name=_MODEL_TEXT):
        if not HAS_DASHSCOPE: return json.dumps({"error": True, "message": "dashscope 不可用"}, ensure_ascii=False)
        try:
            dashscope.api_key = api_key
            msgs = [{"role": "system", "content": f'销售线索评分（标准：{scoring_criteria}）。返回JSON：{{"score":85,"grade":"A|B|C|D","probability":0.85,"factors":[{{"factor":"因素","impact":"positive|negative","weight":0.3}}],"next_action":"动作"}}。只输出JSON。'},
                    {"role": "user", "content": str(lead_info)}]
            content = _call_llm(model_name, msgs, temperature=0.2, max_tokens=300)
            r = _parse_json(content)
            if not isinstance(r, dict): r = {"lead_score": content}
            r.update({"lead_info": str(lead_info), "scoring_criteria": scoring_criteria, "model": model_name})
            return json.dumps(r, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": True, "message": str(e)}, ensure_ascii=False)


@annotate("*->string")
class ai_review_analyze(object):
    def evaluate(self, review_text, api_key, product_type="general", model_name=_MODEL_TEXT):
        if not HAS_DASHSCOPE: return json.dumps({"error": True, "message": "dashscope 不可用"}, ensure_ascii=False)
        try:
            dashscope.api_key = api_key
            msgs = [{"role": "system", "content": f'评论分析（产品类型：{product_type}）。返回JSON：{{"sentiment":"positive|negative|neutral","rating":5,"aspects":[{{"aspect":"方面","sentiment":"positive","detail":"详情"}}],"summary":"总结"}}。只输出JSON。'},
                    {"role": "user", "content": review_text}]
            content = _call_llm(model_name, msgs, temperature=0.2, max_tokens=500)
            r = _parse_json(content)
            if not isinstance(r, dict): r = {"review_analysis": content}
            r.update({"product_type": product_type, "model": model_name})
            return json.dumps(r, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": True, "message": str(e)}, ensure_ascii=False)


@annotate("*->string")
class ai_risk_text_detect(object):
    def evaluate(self, text, api_key, risk_types="all", model_name=_MODEL_TEXT):
        if not HAS_DASHSCOPE: return json.dumps({"error": True, "message": "dashscope 不可用"}, ensure_ascii=False)
        try:
            dashscope.api_key = api_key
            msgs = [{"role": "system", "content": f'风险检测（类型：{risk_types}）。返回JSON：{{"risk_level":"high|medium|low","risk_types":["欺诈"...],"confidence":0.95,"flagged_content":["内容"],"action_required":true}}。只输出JSON。'},
                    {"role": "user", "content": text}]
            content = _call_llm(model_name, msgs, temperature=0.1, max_tokens=300)
            r = _parse_json(content)
            if not isinstance(r, dict): r = {"risk_assessment": content}
            r.update({"original_text": text, "risk_types": risk_types, "model": model_name})
            return json.dumps(r, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": True, "message": str(e)}, ensure_ascii=False)


@annotate("*->string")
class ai_contract_extract(object):
    def evaluate(self, contract_text, api_key, extract_fields="all", model_name=_MODEL_TEXT):
        if not HAS_DASHSCOPE: return json.dumps({"error": True, "message": "dashscope 不可用"}, ensure_ascii=False)
        try:
            dashscope.api_key = api_key
            msgs = [{"role": "system", "content": f'合同提取（字段：{extract_fields}）。返回JSON：{{"parties":["甲方","乙方"],"amount":"金额","start_date":"开始","end_date":"结束","key_terms":["条款"],"risk_points":["风险"]}}。只输出JSON。'},
                    {"role": "user", "content": contract_text}]
            content = _call_llm(model_name, msgs, temperature=0.1, max_tokens=500)
            r = _parse_json(content)
            if not isinstance(r, dict): r = {"contract_info": content}
            r.update({"extract_fields": extract_fields, "contract_length": len(contract_text), "model": model_name})
            return json.dumps(r, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": True, "message": str(e)}, ensure_ascii=False)


@annotate("*->string")
class ai_resume_parse(object):
    def evaluate(self, resume_text, api_key, parse_depth="standard", model_name=_MODEL_TEXT):
        if not HAS_DASHSCOPE: return json.dumps({"error": True, "message": "dashscope 不可用"}, ensure_ascii=False)
        try:
            dashscope.api_key = api_key
            msgs = [{"role": "system", "content": f'简历解析（深度：{parse_depth}）。返回JSON：{{"name":"姓名","education":[{{"degree":"学位","school":"学校","major":"专业"}}],"experience":[{{"title":"职位","company":"公司","duration":"时长"}}],"skills":["技能"]}}。只输出JSON。'},
                    {"role": "user", "content": resume_text}]
            content = _call_llm(model_name, msgs, temperature=0.1, max_tokens=500)
            r = _parse_json(content)
            if not isinstance(r, dict): r = {"resume_info": content}
            r.update({"parse_depth": parse_depth, "resume_length": len(resume_text), "model": model_name})
            return json.dumps(r, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": True, "message": str(e)}, ensure_ascii=False)


@annotate("*->string")
class ai_customer_segment(object):
    def evaluate(self, customer_data, api_key, segmentation_model="RFM", model_name=_MODEL_TEXT):
        if not HAS_DASHSCOPE: return json.dumps({"error": True, "message": "dashscope 不可用"}, ensure_ascii=False)
        try:
            dashscope.api_key = api_key
            msgs = [{"role": "system", "content": f'客户分群（模型：{segmentation_model}）。返回JSON：{{"segment":"分群","scores":{{"R":5,"F":4,"M":5}},"total_score":85,"characteristics":["特征"],"recommendations":["建议"],"retention_probability":0.9}}。只输出JSON。'},
                    {"role": "user", "content": str(customer_data)}]
            content = _call_llm(model_name, msgs, temperature=0.2, max_tokens=300)
            r = _parse_json(content)
            if not isinstance(r, dict): r = {"segment": content}
            r.update({"segmentation_model": segmentation_model, "customer_data": str(customer_data), "model": model_name})
            return json.dumps(r, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": True, "message": str(e)}, ensure_ascii=False)


@annotate("*->string")
class ai_product_description_generate(object):
    def evaluate(self, product_info, api_key, style="professional", model_name=_MODEL_TEXT):
        if not HAS_DASHSCOPE: return json.dumps({"error": True, "message": "dashscope 不可用"}, ensure_ascii=False)
        try:
            dashscope.api_key = api_key
            msgs = [{"role": "system", "content": f'生成产品描述（风格：{style}）。返回JSON：{{"title":"标题","description":"描述","features":["特性"],"benefits":["卖点"],"target_audience":"目标用户","selling_points":["卖点"]}}。只输出JSON。'},
                    {"role": "user", "content": str(product_info)}]
            content = _call_llm(model_name, msgs, temperature=0.3, max_tokens=500)
            r = _parse_json(content)
            if not isinstance(r, dict): r = {"product_description": content}
            r.update({"style": style, "product_info": str(product_info), "model": model_name})
            return json.dumps(r, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": True, "message": str(e)}, ensure_ascii=False)


@annotate("*->string")
class ai_industry_classification(object):
    def evaluate(self, text, prompt, api_key, model_name, temperature=0.7, enable_search=False):
        if not HAS_DASHSCOPE: return json.dumps({"error": True, "message": "dashscope 不可用"}, ensure_ascii=False)
        try:
            dashscope.api_key = api_key
            msgs = [{"role": "system", "content": prompt}, {"role": "user", "content": text}]
            content = _call_llm(model_name, msgs, temperature=temperature, max_tokens=500, enable_search=enable_search)
            r = _parse_json(content)
            if not isinstance(r, dict): r = {"一级行业": "未知", "二级行业": "未知", "原始内容": content}
            r["model"] = model_name
            return json.dumps(r, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": True, "message": str(e)}, ensure_ascii=False)
