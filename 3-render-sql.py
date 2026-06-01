#!/usr/bin/env python3
"""从 config.json 生成部署 SQL。步骤 1-3 按云平台自动生成，步骤 4-6 来自项目 4-deploy.sql"""
import os, json

root = os.getcwd()
if not os.path.exists(os.path.join(root, 'config.json')):
    root = os.path.dirname(os.path.abspath(__file__))
cfg = json.load(open(os.path.join(root, 'config.json')))
platform = cfg.get('platform', 'aliyun')
schema = cfg['schema']

def g(path, d=''):
    v = cfg
    for k in path.split('.'):
        if isinstance(v, dict) and k in v: v = v[k]
        else: return d
    return str(v)

# ---- 步骤 1-3：云平台 boilerplate ----
if platform == 'aliyun':
    boilerplate = f"""-- 1   Storage Connection (OSS)
CREATE STORAGE CONNECTION IF NOT EXISTS oss_conn
TYPE OSS
access_id = '{g('aliyun.oss.access_id')}'
access_key = '{g('aliyun.oss.access_key')}'
ENDPOINT = '{g('aliyun.oss.endpoint')}';

-- 2   API Connection (FC)
CREATE API CONNECTION IF NOT EXISTS fc_conn
TYPE CLOUD_FUNCTION
PROVIDER = 'aliyun'
REGION = '{g('aliyun.fc.region')}'
ROLE_ARN = '{g('aliyun.fc.role_arn')}'
CODE_BUCKET = '{g('aliyun.oss.bucket')}';

-- 3   External Volume
CREATE EXTERNAL VOLUME IF NOT EXISTS udf_vol
LOCATION 'oss://{g('aliyun.oss.bucket')}/'
USING CONNECTION oss_conn
DIRECTORY = (ENABLE = true);

"""
elif platform == 'tencent':
    boilerplate = f"""-- 1   Storage Connection (COS)
CREATE STORAGE CONNECTION IF NOT EXISTS cos_conn
TYPE COS
ACCESS_KEY = '{g('tencent.cos.access_key')}'
SECRET_KEY = '{g('tencent.cos.secret_key')}'
REGION = '{g('tencent.cos.region')}'
APP_ID = '{g('tencent.cos.app_id')}';

-- 2   API Connection (SCF)
CREATE API CONNECTION IF NOT EXISTS scf_conn
TYPE CLOUD_FUNCTION
PROVIDER = 'tencent'
REGION = '{g('tencent.scf.region')}'
ROLE_ARN = '{g('tencent.scf.role_arn')}'
NAMESPACE = '{g('tencent.scf.namespace', 'default')}'
CODE_BUCKET = '{g('tencent.cos.bucket')}';

-- 3   External Volume
CREATE EXTERNAL VOLUME IF NOT EXISTS udf_vol
LOCATION 'cosn://{g('tencent.cos.bucket')}/'
USING CONNECTION cos_conn
DIRECTORY = (ENABLE = true);

"""
else:  # aws
    boilerplate = f"""-- 1   Storage Connection (S3)
CREATE STORAGE CONNECTION IF NOT EXISTS s3_conn
TYPE S3
ACCESS_KEY_ID = '{g('aws.s3.access_key_id')}'
SECRET_ACCESS_KEY = '{g('aws.s3.secret_access_key')}'
ENDPOINT = '{g('aws.s3.endpoint')}'
REGION = '{g('aws.s3.region')}';

-- 2   API Connection (Lambda)
CREATE API CONNECTION IF NOT EXISTS lambda_conn
TYPE CLOUD_FUNCTION
PROVIDER = 'aws'
REGION = '{g('aws.lambda.region')}'
ROLE_ARN = '{g('aws.lambda.role_arn')}'
CODE_BUCKET = '{g('aws.s3.bucket')}';

-- 3   External Volume
CREATE EXTERNAL VOLUME IF NOT EXISTS udf_vol
LOCATION 's3://{g('aws.s3.bucket')}/'
USING CONNECTION s3_conn
DIRECTORY = (ENABLE = true);

"""

# ---- 通用占位符 ----
R = {
    '<project_dir>': root,
    '<schema>': schema,
    '<volume>': 'udf_vol',
    '<fc_conn>': 'fc_conn' if platform == 'aliyun' else ('scf_conn' if platform == 'tencent' else 'lambda_conn'),
    '<storage_conn>': 'oss_conn' if platform == 'aliyun' else ('cos_conn' if platform == 'tencent' else 's3_conn'),
    '<oss_url>': 'oss://' + g('aliyun.oss.bucket') + '/' if platform == 'aliyun'
                 else 'cosn://' + g('tencent.cos.bucket') + '/' if platform == 'tencent'
                 else 's3://' + g('aws.s3.bucket') + '/',
}

# ---- 渲染 4-deploy.sql ----
sql = boilerplate
project_sql = open(os.path.join(root, '4-deploy.sql')).read()
for ph, val in R.items():
    project_sql = project_sql.replace(ph, val)
sql += project_sql

os.makedirs(os.path.join(root, 'dist'), exist_ok=True)
out = os.path.join(root, 'dist', '4-deploy_generated.sql')
open(out, 'w').write(sql)

# ---- 渲染 5-cleanup.sql ----
if os.path.exists(os.path.join(root, '5-cleanup.sql')):
    cleanup = open(os.path.join(root, '5-cleanup.sql')).read()
    for ph, val in R.items():
        cleanup = cleanup.replace(ph, val)
    out2 = os.path.join(root, 'dist', '5-cleanup_generated.sql')
    open(out2, 'w').write(cleanup)

print(f"✅ dist/ — {platform}")
