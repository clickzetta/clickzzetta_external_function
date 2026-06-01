package com.clickzetta.udf;

import org.apache.hadoop.hive.ql.exec.UDFArgumentException;
import org.apache.hadoop.hive.ql.exec.UDFArgumentLengthException;
import org.apache.hadoop.hive.ql.metadata.HiveException;
import org.apache.hadoop.hive.ql.udf.generic.GenericUDF;
import org.apache.hadoop.hive.serde2.objectinspector.ObjectInspector;
import org.apache.hadoop.hive.serde2.objectinspector.ObjectInspectorUtils;
import org.apache.hadoop.hive.serde2.objectinspector.primitive.PrimitiveObjectInspectorFactory;
import org.apache.hadoop.hive.serde2.objectinspector.primitive.StringObjectInspector;
import java.util.regex.Pattern;
import java.util.regex.Matcher;

/**
 * PII 数据脱敏 UDF
 * 自动识别并替换：手机号、邮箱、身份证号
 * <p>
 * SQL 用法:
 * SELECT <schema>.pii_mask(content) FROM sensitive_table;
 */
public class PiiMaskUDF extends GenericUDF {

    private StringObjectInspector textOI;

    private static final Pattern PHONE = Pattern.compile("1[3-9]\\d{9}");
    private static final Pattern EMAIL = Pattern.compile("[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}");
    private static final Pattern ID_CARD = Pattern.compile("[1-9]\\d{5}(19|20)\\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\\d|3[01])\\d{3}[\\dXx]");

    @Override
    public ObjectInspector initialize(ObjectInspector[] arguments) throws UDFArgumentException {
        if (arguments.length != 1) {
            throw new UDFArgumentLengthException("pii_mask 需要一个参数：要脱敏的文本");
        }
        ObjectInspector arg = arguments[0];
        if (arg.getCategory() != ObjectInspector.Category.PRIMITIVE) {
            throw new UDFArgumentException("pii_mask 只接受基础类型参数");
        }
        if (((org.apache.hadoop.hive.serde2.objectinspector.PrimitiveObjectInspector) arg)
                .getPrimitiveCategory() != org.apache.hadoop.hive.serde2.objectinspector.PrimitiveObjectInspector.PrimitiveCategory.STRING) {
            throw new UDFArgumentException("pii_mask 需要 STRING 类型参数");
        }
        textOI = (StringObjectInspector) arg;
        return PrimitiveObjectInspectorFactory.javaStringObjectInspector;
    }

    @Override
    public Object evaluate(DeferredObject[] arguments) throws HiveException {
        String text = textOI.getPrimitiveJavaObject(arguments[0].get());
        if (text == null || text.isEmpty()) return "";

        text = PHONE.matcher(text).replaceAll(m ->
                m.group().substring(0, 3) + "****" + m.group().substring(7));
        text = EMAIL.matcher(text).replaceAll(m ->
                m.group().charAt(0) + "***@" + m.group().split("@")[1]);
        text = ID_CARD.matcher(text).replaceAll(m ->
                m.group().substring(0, 6) + "********" + m.group().substring(14));

        return text;
    }

    @Override
    public String getDisplayString(String[] children) {
        return "pii_mask(" + children[0] + ")";
    }
}
