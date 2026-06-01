#!/usr/bin/env python3
"""从 config.json 生成 4-deploy.sql 和 5-cleanup.sql"""
import os, json

root = os.path.dirname(os.path.abspath(__file__))
cfg = json.load(open(os.path.join(root, 'config.json')))

repl = {
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
    '<schema>':                         cfg['clickzetta']['schema'],
}

for fn in ['4-deploy.sql', '5-cleanup.sql']:
    sql = open(os.path.join(root, fn)).read()
    for ph, val in repl.items():
        sql = sql.replace(ph, val)
    out = os.path.join(root, 'dist', fn.replace('.sql', '_generated.sql'))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, 'w').write(sql)

print("✅ dist/4-deploy_generated.sql + dist/5-cleanup_generated.sql")
