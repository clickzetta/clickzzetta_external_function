-- 1
CREATE STORAGE CONNECTION IF NOT EXISTS qs_oss
TYPE OSS
access_id = '<access_id>'
access_key = '<access_key>'
ENDPOINT = '<endpoint>';

-- 2
CREATE API CONNECTION IF NOT EXISTS qs_fc
TYPE CLOUD_FUNCTION
PROVIDER = 'aliyun'
REGION = '<region>'
ROLE_ARN = '<role_arn>'
CODE_BUCKET = '<bucket>';

-- 3
CREATE EXTERNAL VOLUME IF NOT EXISTS qs_vol
LOCATION 'oss://<bucket>/'
USING CONNECTION qs_oss
DIRECTORY = (ENABLE = true);

-- 4
PUT '<project_dir>/dist/my_upper.zip'
TO VOLUME qs_vol
FILE 'my_upper.zip';

-- 5
CREATE EXTERNAL FUNCTION IF NOT EXISTS <schema>.my_upper
AS 'my_upper.my_upper'
USING ARCHIVE 'volume://qs_vol/my_upper.zip'
CONNECTION qs_fc
WITH PROPERTIES ('remote.udf.api'='python3.mc.v0', 'remote.udf.protocol'='http.arrow.v0');

-- 6
SELECT <schema>.my_upper('hello world');
