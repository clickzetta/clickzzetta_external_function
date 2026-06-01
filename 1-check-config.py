#!/usr/bin/env python3
"""检查 config.json 参数完整性 — 支持 aliyun / tencent / aws"""
import json, sys, os

root = os.getcwd()
if not os.path.exists(os.path.join(root, 'config.json')):
    root = os.path.dirname(os.path.abspath(__file__))
cfg = json.load(open(os.path.join(root, 'config.json')))
errors = []

def check(path, label):
    v = cfg
    for k in path.split('.'):
        if isinstance(v, dict) and k in v: v = v[k]
        else: errors.append(f"缺少字段: {path}（{label}）"); return None
    if not v or (isinstance(v, str) and not v.strip()):
        errors.append(f"字段为空: {path}（{label}）")
    return v

platform = cfg.get('platform', 'aliyun')
check('schema', 'Schema 名')

if platform == 'aliyun':
    check('aliyun.fc.region', 'FC 地域')
    check('aliyun.fc.role_arn', 'FC 角色 ARN')
    check('aliyun.oss.bucket', 'OSS Bucket')
    check('aliyun.oss.endpoint', 'OSS Endpoint')
    check('aliyun.oss.access_id', 'AccessKey ID')
    check('aliyun.oss.access_key', 'AccessKey Secret')
    arn = cfg.get('aliyun', {}).get('fc', {}).get('role_arn', '')
    ep = cfg.get('aliyun', {}).get('oss', {}).get('endpoint', '')
    region = cfg.get('aliyun', {}).get('fc', {}).get('region', '')
    if arn and not arn.startswith('acs:ram::'): errors.append("fc.role_arn 格式不对（应 acs:ram:: 开头）")

elif platform == 'tencent':
    check('tencent.scf.region', 'SCF 地域')
    check('tencent.scf.role_arn', 'SCF 角色 ARN')
    check('tencent.scf.namespace', 'SCF 命名空间')
    check('tencent.cos.bucket', 'COS Bucket')
    check('tencent.cos.region', 'COS 地域')
    check('tencent.cos.app_id', 'COS APP_ID')
    check('tencent.cos.access_key', 'COS SecretId')
    check('tencent.cos.secret_key', 'COS SecretKey')
    arn = cfg.get('tencent', {}).get('scf', {}).get('role_arn', '')
    ep = region = cfg.get('tencent', {}).get('scf', {}).get('region', '')

elif platform == 'aws':
    check('aws.lambda.region', 'Lambda 地域')
    check('aws.lambda.role_arn', 'Lambda 角色 ARN')
    check('aws.s3.bucket', 'S3 Bucket')
    check('aws.s3.region', 'S3 地域')
    check('aws.s3.endpoint', 'S3 Endpoint')
    check('aws.s3.access_key_id', 'AccessKey ID')
    check('aws.s3.secret_access_key', 'Secret Access Key')
    arn = cfg.get('aws', {}).get('lambda', {}).get('role_arn', '')
    ep = region = cfg.get('aws', {}).get('lambda', {}).get('region', '')
else:
    errors.append(f"platform 无效: {platform}（填 aliyun / tencent / aws）")

if ep and region and region not in ep:
    errors.append(f"地域不一致: {region} 不在 {ep}")

if errors:
    print(f"❌ {len(errors)} 个问题:")
    for e in errors: print(f"  - {e}")
    sys.exit(1)

print(f"✅ {platform} — schema={check('schema','')}")
