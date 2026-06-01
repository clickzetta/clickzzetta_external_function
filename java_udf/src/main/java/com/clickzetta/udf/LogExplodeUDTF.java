package com.clickzetta.udf;

import org.apache.hadoop.hive.ql.exec.UDFArgumentException;
import org.apache.hadoop.hive.ql.metadata.HiveException;
import org.apache.hadoop.hive.ql.udf.generic.GenericUDTF;
import org.apache.hadoop.hive.serde2.objectinspector.ObjectInspector;
import org.apache.hadoop.hive.serde2.objectinspector.ObjectInspectorFactory;
import org.apache.hadoop.hive.serde2.objectinspector.StructObjectInspector;
import org.apache.hadoop.hive.serde2.objectinspector.primitive.PrimitiveObjectInspectorFactory;
import org.apache.hadoop.hive.serde2.objectinspector.primitive.StringObjectInspector;
import java.util.ArrayList;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.HashSet;
import java.util.Set;

/**
 * UDTF — 事件拆解：输入一段带时间戳的日志文本，输出多行 <时间, 事件>
 *
 * SQL 用法:
 *   SELECT <schema>.log_explode(log_text) AS (ts, event);
 *   -- 或配合 LATERAL
 *   SELECT t.* FROM my_table, LATERAL <schema>.log_explode(log_text) t;
 *
 * DDL 必须加:
 *   WITH PROPERTIES ('remote.udf.api'='java8.hive2.v0', 'remote.udf.category'='TABLE_VALUED')
 */
public class LogExplodeUDTF extends GenericUDTF {

    private static final Pattern LINE_PAT = Pattern.compile("\\[(\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2})\\] (.+)");

    private StringObjectInspector textOI;

    @Override
    public StructObjectInspector initialize(ObjectInspector[] argOIs) throws UDFArgumentException {
        if (argOIs.length != 1) {
            throw new UDFArgumentException("log_explode() 需要一个参数");
        }
        textOI = (StringObjectInspector) argOIs[0];

        ArrayList<String> fieldNames = new ArrayList<>();
        ArrayList<ObjectInspector> fieldOIs = new ArrayList<>();
        fieldNames.add("ts");
        fieldOIs.add(PrimitiveObjectInspectorFactory.javaStringObjectInspector);
        fieldNames.add("event");
        fieldOIs.add(PrimitiveObjectInspectorFactory.javaStringObjectInspector);

        return ObjectInspectorFactory.getStandardStructObjectInspector(fieldNames, fieldOIs);
    }

    @Override
    public void process(Object[] record) throws HiveException {
        String text = textOI.getPrimitiveJavaObject(record[0]);
        if (text == null || text.isEmpty()) return;

        String[] lines = text.split("\n");
        for (String line : lines) {
            Matcher m = LINE_PAT.matcher(line.trim());
            if (m.find()) {
                String ts = m.group(1);
                String event = m.group(2);
                forward(new Object[]{ts, event});
            } else {
                // 无时间戳的行也输出
                forward(new Object[]{"", line.trim()});
            }
        }
    }

    @Override
    public void close() throws HiveException {
        // 无需清理
    }
}
