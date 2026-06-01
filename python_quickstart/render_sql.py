#!/usr/bin/env python3
"""从 config.json 生成 deploy.sql"""
import json, os

root = os.path.dirname(os.path.abspath(__file__))
cfg = json.load(open(os.path.join(root, 'config.json')))
sql = open(os.path.join(root, 'deploy.sql')).read()

for ph, val in {
    '<schema>': cfg['schema'],
    '<bucket>': cfg['aliyun']['oss']['bucket'],
    '<endpoint>': cfg['aliyun']['oss']['endpoint'],
    '<access_id>': cfg['aliyun']['oss']['access_id'],
    '<access_key>': cfg['aliyun']['oss']['access_key'],
    '<region>': cfg['aliyun']['fc']['region'],
    '<role_arn>': cfg['aliyun']['fc']['role_arn'],
    '<project_dir>': root,
}.items():
    sql = sql.replace(ph, val)

out = os.path.join(root, 'dist', 'deploy.sql')
os.makedirs(os.path.dirname(out), exist_ok=True)
open(out, 'w').write(sql)
print(f"✅ {out}")
