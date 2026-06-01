-- 1
CREATE STORAGE CONNECTION IF NOT EXISTS java_oss
TYPE OSS
access_id = '<access_id>'
access_key = '<access_key>'
ENDPOINT = '<endpoint>';

-- 2
CREATE API CONNECTION IF NOT EXISTS java_fc
TYPE CLOUD_FUNCTION
PROVIDER = 'aliyun'
REGION = '<region>'
ROLE_ARN = '<role_arn>'
CODE_BUCKET = '<bucket>';

-- 3
CREATE EXTERNAL VOLUME IF NOT EXISTS java_vol
LOCATION 'oss://<bucket>/'
USING CONNECTION java_oss
DIRECTORY = (ENABLE = true);

-- 4
PUT '<project_dir>/dist/pii_mask.zip' TO VOLUME java_vol FILE 'pii_mask.zip';

-- 5
CREATE EXTERNAL FUNCTION IF NOT EXISTS <schema>.pii_mask
AS 'com.clickzetta.udf.PiiMaskUDF'
USING ARCHIVE 'volume://java_vol/pii_mask.zip'
CONNECTION java_fc
WITH PROPERTIES ('remote.udf.api'='java8.hive2.v0');

-- 6
SELECT <schema>.pii_mask('我的手机13812345678，邮箱alice@example.com，身份证310101199001011234');
