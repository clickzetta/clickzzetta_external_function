#!/usr/bin/env python3
"""从 config.json 生成 4-deploy.sql（替换所有占位符）"""
import json, os

root = os.path.dirname(os.path.abspath(__file__))
cfg = json.load(open(os.path.join(root, 'config.json')))
sql = open(os.path.join(root, '4-deploy.sql')).read()

replacements = {
    '<project_dir>':                    root,
    '<clickzetta.schema>':              cfg['clickzetta']['schema'],
    '<clickzetta.volume>':              cfg['clickzetta']['volume'],
    '<clickzetta.storage_connection>':   cfg['clickzetta']['storage_connection'],
    '<aliyun.fc.connection_name>':      cfg['aliyun']['fc']['connection_name'],
    '<aliyun.fc.region>':               cfg['aliyun']['fc']['region'],
    '<aliyun.ram.role_arn>':            cfg['aliyun']['ram']['role_arn'],
    '<aliyun.oss.access_id>':           cfg['aliyun']['oss']['access_id'],
    '<aliyun.oss.access_key>':          cfg['aliyun']['oss']['access_key'],
    '<aliyun.oss.endpoint>':            cfg['aliyun']['oss']['endpoint'],
    '<aliyun.oss.bucket>':              cfg['aliyun']['oss']['bucket'],
    '<dashscope.api_key>':              cfg['dashscope']['api_key'],
}

for ph, val in replacements.items():
    sql = sql.replace(ph, val)

out = os.path.join(root, 'dist', 'deploy_generated.sql')
os.makedirs(os.path.dirname(out), exist_ok=True)
open(out, 'w').write(sql)

remaining = [l.strip() for l in sql.split('\n') if '<' in l and '>' in l and 'config.json' not in l]
if remaining:
    print("⚠️ 残留占位符:")
    for r in remaining: print(f"   {r}")
else:
    print(f"✅ {out}")
