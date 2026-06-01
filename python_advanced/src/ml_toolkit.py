"""
SQL ML 工具集 — 数据脱敏 / 特征工程 / 异常检测 / 情感分析
纯 Python 标准库，无需任何外部依赖
"""
import json, re, math
from collections import Counter


def annotate(signature):
    def d(cls): cls._signature = signature; return cls
    return d
try: from cz.udf import annotate
except ImportError: pass


# ---------- ① PII 脱敏 ----------
_PII_PATTERNS = [
    ("id_card", r'(?<!\d)[1-9]\d{5}(19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx](?!\d)',
     lambda m: m[0][:6] + '********' + m[0][-4:]),
    ("email", r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
     lambda m: m[0][0] + '***@' + m[0].split('@')[1]),
    ("phone", r'(?<!\d)1[3-9]\d{9}(?!\d)',
     lambda m: m[0][:3] + '****' + m[0][-4:]),
    ("ip", r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',
     lambda m: m[0].rsplit('.', 1)[0] + '.***'),
    ("bank_card", r'(?<!\d)\d{16,19}(?!\d)',
     lambda m: m[0][:4] + ' **** **** ' + m[0][-4:]),
]

@annotate("*->string")
class pii_mask(object):
    """自动识别并脱敏手机号、邮箱、身份证、银行卡号、IP"""
    def evaluate(self, text):
        if not text: return json.dumps({"masked": "", "detected": []}, ensure_ascii=False)
        result, found = text, []
        for ptype, pattern, mask_fn in _PII_PATTERNS:
            matches = list(re.finditer(pattern, result))
            if matches:
                found.append({"type": ptype, "count": len(matches)})
                for m in reversed(matches):
                    result = result[:m.start()] + "<" + ptype + ">" + result[m.end():]
        return json.dumps({"masked": result, "detected": found}, ensure_ascii=False)


# ---------- ② 特征归一化 ----------
@annotate("*->string")
class feature_normalize(object):
    """Min-Max 或 Z-Score 归一化。输入 JSON 数组 [1,2,3,...]，输出归一化数组"""
    def evaluate(self, values_json, method="minmax"):
        try:
            vals = json.loads(values_json)
            if not vals: return json.dumps({"error": "empty"}, ensure_ascii=False)
            if method == "minmax":
                lo, hi = min(vals), max(vals)
                rng = hi - lo
                norm = [(v - lo) / rng for v in vals] if rng > 0 else [0.5] * len(vals)
            elif method == "zscore":
                n = len(vals)
                mean = sum(vals) / n
                std = math.sqrt(sum((v - mean) ** 2 for v in vals) / n)
                norm = [(v - mean) / std for v in vals] if std > 0 else [0.0] * n
            else:
                return json.dumps({"error": f"unknown method: {method}"}, ensure_ascii=False)
            return json.dumps({"method": method, "original_range": [min(vals), max(vals)],
                               "normalized": [round(v, 6) for v in norm]}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)


# ---------- ③ IQR 异常检测 ----------
@annotate("*->string")
class anomaly_detect(object):
    """IQR 异常检测。输入 JSON 数组，输出异常值的下标和值"""
    def evaluate(self, values_json, multiplier=1.5):
        try:
            vals = json.loads(values_json)
            if len(vals) < 4: return json.dumps({"error": "need >= 4 points"}, ensure_ascii=False)
            s = sorted(vals)
            n = len(s)
            q1 = s[n // 4]
            q3 = s[3 * n // 4]
            iqr = q3 - q1
            low, high = q1 - multiplier * iqr, q3 + multiplier * iqr
            outliers = [{"index": i, "value": v, "direction": "high" if v > high else "low"}
                        for i, v in enumerate(vals) if v < low or v > high]
            return json.dumps({"q1": q1, "q3": q3, "iqr": iqr, "bounds": [low, high],
                               "outlier_count": len(outliers), "outliers": outliers}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)


# ---------- ④ 情感评分（词库） ----------
_POS = set("优秀 出色 完美 棒 好 满意 喜欢 赞 推荐 漂亮 精彩 给力 好用 方便 快 高效 便宜 实惠 开心 高兴 惊喜 值 超值 良心 靠谱 给力 强大 稳定 流畅 安全".split())
_NEG = set("差 烂 垃圾 坑 坏 糟糕 失望 后悔 慢 卡 贵 难用 麻烦 费劲 差劲 劣质 虚假 骗 坑爹 崩溃 死机 掉线 没用 不值 差评 恶心 生气 愤怒 难过 心塞".split())

@annotate("*->string")
class sentiment_score(object):
    """基于中文情感词库的情感评分。输入文本，输出 0~1 分数（1=正向）"""
    def evaluate(self, text):
        if not text: return json.dumps({"error": "empty"}, ensure_ascii=False)
        pos, neg = 0, 0
        for w in _POS:
            pos += text.count(w)
        for w in _NEG:
            neg += text.count(w)
        total = pos + neg
        score = pos / total if total > 0 else 0.5
        return json.dumps({"score": round(score, 4), "positive_words": pos,
                           "negative_words": neg, "label": "positive" if score > 0.55 else ("negative" if score < 0.45 else "neutral")}, ensure_ascii=False)


# ---------- ⑤ TF-IDF 关键词提取 ----------
@annotate("*->string")
class tfidf_keywords(object):
    """TF-IDF 关键词提取。输入 JSON 文档数组 ["doc1","doc2",...]，返回每个文档的 top-k 关键词"""
    def evaluate(self, docs_json, top_k=5):
        try:
            docs = json.loads(docs_json)
            if not docs: return json.dumps({"error": "empty"}, ensure_ascii=False)
            tokenized = [re.findall(r'[一-鿿]{2,}|[a-zA-Z]{3,}', d.lower()) for d in docs]
            N = len(docs)
            df = Counter()
            for tokens in tokenized:
                for w in set(tokens):
                    df[w] += 1
            results = []
            for tokens in tokenized:
                tf = Counter(tokens)
                scores = {w: (tf[w] / max(len(tokens),1)) * math.log((N + 1) / (df[w] + 1))
                          for w in set(tokens)}
                top = sorted(scores.items(), key=lambda x: -x[1])[:top_k]
                results.append([{"word": w, "score": round(s, 4)} for w, s in top])
            return json.dumps({"doc_count": N, "keywords": results}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)
