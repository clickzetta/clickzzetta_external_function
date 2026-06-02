PUT '<project_dir>/dist/my_upper.zip' TO VOLUME <volume> FILE 'my_upper.zip';  -- 4. 上传

-- 5   CREATE FUNCTION
CREATE EXTERNAL FUNCTION IF NOT EXISTS <schema>.my_upper
AS 'my_upper.my_upper'
USING ARCHIVE 'volume://<volume>/my_upper.zip'
CONNECTION <fc_conn>
WITH PROPERTIES ('remote.udf.api'='python3.mc.v0', 'remote.udf.protocol'='http.arrow.v0');

-- 6   验证
SELECT <schema>.my_upper('hello world');
