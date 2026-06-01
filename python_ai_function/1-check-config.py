#!/usr/bin/env python3
"""检查 config.json 参数完整性和正确性"""
import json, sys, os

errors = []

try:
    cfg = json.load(open(os.path.join(os.path.dirname(__file__), 'config.json')))
except FileNotFoundError:
    print("❌ config.json 不存在，请先 cp config.example.json config.json")
    sys.exit(1)
except json.JSONDecodeError as e:
    print(f"❌ config.json 格式错误: {e}")
    sys.exit(1)

def check(path, label, empty_ok=False):
    """检查嵌套字段是否存在且非空"""
    keys = path.split('.')
    v = cfg
    for k in keys:
        if isinstance(v, dict) and k in v:
            v = v[k]
        else:
            if not empty_ok:
                errors.append(f"缺少字段: {path}（{label}）")
            return None
    if not empty_ok and (v is None or (isinstance(v, str) and v.strip() == '')):
        errors.append(f"字段为空: {path}（{label}）")
    return v

# models
for m in ['text', 'reasoning', 'embedding', 'multimodal']:
    check(f'models.{m}', f'AI 模型名')

# aliyun.oss
check('aliyun.oss.bucket', 'OSS Bucket 名称')
check('aliyun.oss.endpoint', 'OSS Endpoint')
check('aliyun.oss.access_id', 'AccessKey ID')
check('aliyun.oss.access_key', 'AccessKey Secret')

# aliyun.ram
check('aliyun.ram.role_arn', 'RAM 角色 ARN')
check('aliyun.ram.trust_account', '信任账号ID')

# aliyun.fc
check('aliyun.fc.region', 'FC 地域')
check('aliyun.fc.connection_name', 'API Connection 名称')

# clickzetta
check('clickzetta.schema', 'Schema 名称')
check('clickzetta.volume', 'Volume 名称')
check('clickzetta.storage_connection', 'Storage Connection 名称')

# dashscope
check('dashscope.api_key', '百炼 API Key')

# 地域一致性
oss_ep = cfg.get('aliyun', {}).get('oss', {}).get('endpoint', '')
fc_region = cfg.get('aliyun', {}).get('fc', {}).get('region', '')
if oss_ep and fc_region:
    if fc_region not in oss_ep:
        errors.append(f"地域不一致: aliyun.fc.region={fc_region} 与 aliyun.oss.endpoint={oss_ep}")

# role_arn 格式
arn = cfg.get('aliyun', {}).get('ram', {}).get('role_arn', '')
if arn and not arn.startswith('acs:ram::'):
    errors.append(f"role_arn 格式不正确: {arn}（应以 acs:ram:: 开头）")

# api_key 格式
ak = cfg.get('dashscope', {}).get('api_key', '')
if ak and not ak.startswith('sk-'):
    errors.append(f"api_key 格式不正确: {ak}（应以 sk- 开头）")

# access_key 格式（警告，不强拦）
access_id = cfg.get('aliyun', {}).get('oss', {}).get('access_id', '')
if access_id and not access_id.startswith('LTAI'):
    errors.append(f"access_id 格式可能不对: {access_id}（通常以 LTAI 开头）")

if errors:
    print(f"❌ 发现 {len(errors)} 个问题：")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
else:
    print("✅ config.json 所有参数完整")
    print(f"   Schema:  {check('clickzetta.schema','')}")
    print(f"   Volume:  {check('clickzetta.volume','')}")
    print(f"   Bucket:  {check('aliyun.oss.bucket','')}")
    print(f"   Region:  {check('aliyun.fc.region','')}")
