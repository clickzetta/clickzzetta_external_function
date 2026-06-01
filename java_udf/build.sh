#!/bin/bash
# 编译 Java UDF 并打包
cd "$(dirname "$0")"
mvn clean package -q
# 创建 zip 包（兼容 clickzetta 外部函数格式）
rm -f dist/pii_mask.zip
zip -j dist/pii_mask.zip target/clickzetta-java-udf-1.0.0-jar-with-dependencies.jar
echo "✅ dist/pii_mask.zip ($(du -h dist/pii_mask.zip | cut -f1))"
