"""
SQL ML 工具集 — 基于 scikit-learn 的机器学习 + jieba 中文分词
通过 python 2-package.py --deps 打包依赖
"""
import json, math, os, re
from collections import Counter


def annotate(signature):
    def d(cls): cls._signature = signature; return cls
    return d
try: from cz.udf import annotate
except ImportError: pass


# ---------- ① PII 脱敏 ----------
_PII_RULES = [
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
    def evaluate(self, text):
        if not text: return json.dumps({"masked": "", "detected": []}, ensure_ascii=False)
        result, found = text, []
        for ptype, pattern, mask_fn in _PII_RULES:
            matches = list(re.finditer(pattern, result))
            if matches:
                found.append({"type": ptype, "count": len(matches)})
                for m in reversed(matches):
                    result = result[:m.start()] + "<" + ptype + ">" + result[m.end():]
        return json.dumps({"masked": result, "detected": found}, ensure_ascii=False)


# ---------- ② 特征归一化（sklearn）----------
@annotate("*->string")
class feature_normalize(object):
    def evaluate(self, values_json, method="minmax"):
        try:
            vals = json.loads(values_json)
            if not vals: return json.dumps({"error": "empty"}, ensure_ascii=False)
            import numpy as np
            X = np.array(vals, dtype=float).reshape(-1, 1)

            if method == "minmax":
                from sklearn.preprocessing import MinMaxScaler
                norm = MinMaxScaler().fit_transform(X).ravel().tolist()
            elif method == "zscore":
                from sklearn.preprocessing import StandardScaler
                norm = StandardScaler().fit_transform(X).ravel().tolist()
            else:
                return json.dumps({"error": f"unknown: {method}"}, ensure_ascii=False)

            return json.dumps({"method": method,
                               "original_range": [min(vals), max(vals)],
                               "normalized": [round(v, 6) for v in norm]}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)


# ---------- ③ 异常检测（sklearn）----------
@annotate("*->string")
class anomaly_detect(object):
    def evaluate(self, values_json, contamination=0.1):
        try:
            from sklearn.ensemble import IsolationForest
            import numpy as np
            vals = json.loads(values_json)
            X = np.array(vals, dtype=float).reshape(-1, 1)
            clf = IsolationForest(contamination=float(contamination), random_state=42)
            preds = clf.fit_predict(X)
            outliers = [{"index": i, "value": v} for i, (v, p) in enumerate(zip(vals, preds)) if p == -1]
            return json.dumps({"outlier_count": len(outliers), "outliers": outliers}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)


# ---------- ④ TF-IDF 关键词（sklearn）----------
@annotate("*->string")
class tfidf_keywords(object):
    def evaluate(self, docs_json, top_k=5):
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            docs = json.loads(docs_json)
            if len(docs) < 2:
                return json.dumps({"error": "至少需要 2 篇文档"}, ensure_ascii=False)

            # 用单字 + 双字特征解决中文分词问题（FC 环境 jieba 可能不可用）
            vec = TfidfVectorizer(analyzer='char', ngram_range=(1, 2), max_features=500)
            tfidf = vec.fit_transform(docs)
            feature_names = vec.get_feature_names_out()

            results = []
            for i in range(len(docs)):
                row = tfidf[i].toarray()[0]
                top_indices = row.argsort()[-int(top_k):][::-1]
                keywords = [{"word": feature_names[j], "score": round(float(row[j]), 4)}
                            for j in top_indices]
                results.append(keywords)

            return json.dumps({"doc_count": len(docs), "keywords": results}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)


# ---------- ⑤ 情感评分（jieba + sklearn）----------
_POS = set("优秀 出色 完美 棒 好 满意 喜欢 赞 推荐 漂亮 精彩 给力 好用 方便 快 高效 便宜 实惠 开心 高兴 惊喜 值 超值 良心 靠谱 给力 强大 稳定 流畅 安全".split())
_NEG = set("差 烂 垃圾 坑 坏 糟糕 失望 后悔 慢 卡 贵 难用 麻烦 费劲 差劲 劣质 虚假 骗 坑爹 崩溃 死机 掉线 没用 不值 差评 恶心 生气 愤怒 难过 心塞".split())

@annotate("*->string")
class sentiment_score(object):
    def evaluate(self, text):
        if not text: return json.dumps({"error": "empty"}, ensure_ascii=False)
        try:
            import jieba
            words = list(jieba.cut(text))
        except ImportError:
            words = re.findall(r'[一-鿿]+', text)
        pos = sum(1 for w in words if w in _POS)
        neg = sum(1 for w in words if w in _NEG)
        total = pos + neg
        score = pos / total if total > 0 else 0.5
        return json.dumps({"score": round(score, 4), "positive_words": pos,
                           "negative_words": neg, "label": "positive" if score > 0.55
                           else ("negative" if score < 0.45 else "neutral")}, ensure_ascii=False)
