package com.clickzetta.udf;

import org.apache.hadoop.hive.ql.exec.UDFArgumentException;
import org.apache.hadoop.hive.ql.metadata.HiveException;
import org.apache.hadoop.hive.ql.udf.generic.GenericUDAFEvaluator;
import org.apache.hadoop.hive.ql.udf.generic.GenericUDAFResolver2;
import org.apache.hadoop.hive.ql.udf.generic.SimpleGenericUDAFParameterInfo;
import org.apache.hadoop.hive.serde2.objectinspector.ObjectInspector;
import org.apache.hadoop.hive.serde2.objectinspector.ObjectInspectorFactory;
import org.apache.hadoop.hive.serde2.objectinspector.primitive.PrimitiveObjectInspectorFactory;
import org.apache.hadoop.hive.serde2.objectinspector.primitive.DoubleObjectInspector;
import org.apache.hadoop.hive.serde2.lazy.LazyDouble;
import org.apache.hadoop.io.DoubleWritable;

/**
 * UDAF — 文本评分聚合：对每行返回一个 JSON 分数，聚合后输出 avg/min/max/count
 *
 * SQL 用法:
 *   SELECT <schema>.agg_stats(score_json) FROM article_ratings;
 *
 * DDL 必须加:
 *   WITH PROPERTIES ('remote.udf.api'='java8.hive2.v0', 'remote.udf.category'='AGGREGATOR')
 */
public class AggStatsUDAF extends GenericUDAFResolver2 {

    @Override
    public GenericUDAFEvaluator getEvaluator(SimpleGenericUDAFParameterInfo info) throws UDFArgumentException {
        return getEvaluator(info.getAllParameters());
    }

    @Override
    public GenericUDAFEvaluator getEvaluator(TypeInfo[] parameters) throws UDFArgumentException {
        return new AggStatsEvaluator();
    }

    public static class AggStatsEvaluator extends GenericUDAFEvaluator {

        private DoubleObjectInspector inputOI;

        static class AggBuffer extends AbstractAggregationBuffer {
            double sum = 0;
            double min = Double.MAX_VALUE;
            double max = Double.MIN_VALUE;
            long count = 0;
        }

        @Override
        public ObjectInspector init(Mode m, ObjectInspector[] parameters) throws HiveException {
            super.init(m, parameters);
            if (m == Mode.PARTIAL1 || m == Mode.COMPLETE) {
                inputOI = (DoubleObjectInspector) parameters[0];
            }
            // 返回 output: {sum, min, max, count}
            return ObjectInspectorFactory.getStandardListObjectInspector(
                    PrimitiveObjectInspectorFactory.writableDoubleObjectInspector);
        }

        @Override
        public AggregationBuffer getNewAggregationBuffer() throws HiveException {
            AggBuffer buf = new AggBuffer();
            reset(buf);
            return buf;
        }

        @Override
        public void reset(AggregationBuffer agg) throws HiveException {
            AggBuffer buf = (AggBuffer) agg;
            buf.sum = 0;
            buf.min = Double.MAX_VALUE;
            buf.max = Double.MIN_VALUE;
            buf.count = 0;
        }

        @Override
        public void iterate(AggregationBuffer agg, Object[] parameters) throws HiveException {
            AggBuffer buf = (AggBuffer) agg;
            double val = inputOI.get(parameters[0]);
            buf.sum += val;
            buf.min = Math.min(buf.min, val);
            buf.max = Math.max(buf.max, val);
            buf.count++;
        }

        @Override
        public Object terminatePartial(AggregationBuffer agg) throws HiveException {
            AggBuffer buf = (AggBuffer) agg;
            return new Object[]{
                new DoubleWritable(buf.sum),
                new DoubleWritable(buf.min),
                new DoubleWritable(buf.max),
                new DoubleWritable(buf.count)
            };
        }

        @Override
        public void merge(AggregationBuffer agg, Object partial) throws HiveException {
            AggBuffer buf = (AggBuffer) agg;
            Object[] parts = ((java.util.List<DoubleWritable>) partial).toArray();
            buf.sum += ((DoubleWritable) parts[0]).get();
            buf.min = Math.min(buf.min, ((DoubleWritable) parts[1]).get());
            buf.max = Math.max(buf.max, ((DoubleWritable) parts[2]).get());
            buf.count += ((DoubleWritable) parts[3]).get();
        }

        @Override
        public Object terminate(AggregationBuffer agg) throws HiveException {
            AggBuffer buf = (AggBuffer) agg;
            double avg = buf.count > 0 ? buf.sum / buf.count : 0;
            return java.util.Arrays.asList(
                new DoubleWritable(buf.sum),
                new DoubleWritable(avg),
                new DoubleWritable(buf.min == Double.MAX_VALUE ? 0 : buf.min),
                new DoubleWritable(buf.max == Double.MIN_VALUE ? 0 : buf.max),
                new DoubleWritable(buf.count)
            );
        }
    }
}
