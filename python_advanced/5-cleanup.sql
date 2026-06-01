DROP FUNCTION IF EXISTS <schema>.pii_mask;
DROP FUNCTION IF EXISTS <schema>.feature_normalize;
DROP FUNCTION IF EXISTS <schema>.anomaly_detect;
DROP FUNCTION IF EXISTS <schema>.sentiment_score;
DROP FUNCTION IF EXISTS <schema>.tfidf_keywords;
DROP VOLUME IF EXISTS adv_vol;
DROP CONNECTION IF EXISTS adv_fc;
DROP CONNECTION IF EXISTS adv_oss;
