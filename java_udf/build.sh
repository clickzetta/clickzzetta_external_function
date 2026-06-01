#!/bin/bash
cd "$(dirname "$0")"
mvn clean package -q
rm -f dist/all_udf.zip
zip -j dist/all_udf.zip target/clickzetta-java-udf-1.0.0-jar-with-dependencies.jar
echo "✅ dist/all_udf.zip ($(du -h dist/all_udf.zip | cut -f1))"
