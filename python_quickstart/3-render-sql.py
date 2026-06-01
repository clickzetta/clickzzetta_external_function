#!/usr/bin/env python3
"""从 config.json 生成 4-deploy.sql 和 5-cleanup.sql"""
import os, json

root = os.path.dirname(os.path.abspath(__file__))
cfg = json.load(open(os.path.join(root, 'config.json')))

repl = {
    '<project_dir>': root,
    '<schema>': cfg['schema'],
    '<bucket>': cfg['aliyun']['oss']['bucket'],
    '<endpoint>': cfg['aliyun']['oss']['endpoint'],
    '<access_id>': cfg['aliyun']['oss']['access_id'],
    '<access_key>': cfg['aliyun']['oss']['access_key'],
    '<region>': cfg['aliyun']['fc']['region'],
    '<role_arn>': cfg['aliyun']['fc']['role_arn'],
}

for fn in ['4-deploy.sql', '5-cleanup.sql']:
    sql = open(os.path.join(root, fn)).read()
    for ph, val in repl.items():
        sql = sql.replace(ph, val)
    out = os.path.join(root, 'dist', fn.replace('.sql', '_generated.sql'))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, 'w').write(sql)

print("✅ dist/4-deploy_generated.sql + dist/5-cleanup_generated.sql")
