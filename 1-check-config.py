#!/usr/bin/env python3
"""检查 config.json 参数完整性"""
import json, sys, os

root = os.getcwd()
if not os.path.exists(os.path.join(root, 'config.json')):
    root = os.path.dirname(os.path.abspath(__file__))
cfg = json.load(open(os.path.join(root, 'config.json')))
errors = []

def check(path, label):
    keys = path.split('.')
    v = cfg
    for k in keys:
        if isinstance(v, dict) and k in v:
            v = v[k]
        else:
            errors.append(f"缺少字段: {path}（{label}）")
            return None
    if not v or (isinstance(v, str) and not v.strip()):
        errors.append(f"字段为空: {path}（{label}）")
    return v

check('schema', 'Schema 名')
check('aliyun.oss.bucket', 'OSS Bucket 名称')
check('aliyun.oss.endpoint', 'OSS Endpoint')
check('aliyun.oss.access_id', 'AccessKey ID')
check('aliyun.oss.access_key', 'AccessKey Secret')
check('aliyun.fc.region', 'FC 地域')
check('aliyun.fc.role_arn', 'RAM 角色 ARN')

ep = cfg.get('aliyun', {}).get('oss', {}).get('endpoint', '')
region = cfg.get('aliyun', {}).get('fc', {}).get('region', '')
if ep and region and region not in ep:
    errors.append(f"地域不一致: fc.region={region} oss.endpoint={ep}")

arn = cfg.get('aliyun', {}).get('fc', {}).get('role_arn', '')
if arn and not arn.startswith('acs:ram::'):
    errors.append(f"role_arn 格式不对: {arn}")

if errors:
    print(f"❌ {len(errors)} 个问题:")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)

print(f"✅ all — schema={check('schema','')} bucket={check('aliyun.oss.bucket','')} region={region}")
