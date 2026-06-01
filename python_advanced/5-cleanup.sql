DROP FUNCTION IF EXISTS <schema>.pii_mask;
DROP FUNCTION IF EXISTS <schema>.feature_normalize;
DROP FUNCTION IF EXISTS <schema>.anomaly_detect;
DROP FUNCTION IF EXISTS <schema>.sentiment_score;
DROP FUNCTION IF EXISTS <schema>.tfidf_keywords;
DROP VOLUME IF EXISTS <volume>;
DROP CONNECTION IF EXISTS <fc_conn>;
DROP CONNECTION IF EXISTS <storage_conn>;
