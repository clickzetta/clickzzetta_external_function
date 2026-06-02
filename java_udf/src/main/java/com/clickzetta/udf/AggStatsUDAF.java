package com.clickzetta.udf;

import org.apache.hadoop.hive.ql.metadata.HiveException;
import org.apache.hadoop.hive.ql.udf.generic.GenericUDAFEvaluator;
import org.apache.hadoop.hive.ql.udf.generic.GenericUDAFResolver2;
import org.apache.hadoop.hive.ql.udf.generic.GenericUDAFParameterInfo;
import org.apache.hadoop.hive.serde2.objectinspector.ObjectInspector;
import org.apache.hadoop.hive.serde2.objectinspector.ObjectInspectorFactory;
import org.apache.hadoop.hive.serde2.objectinspector.primitive.PrimitiveObjectInspectorFactory;
import org.apache.hadoop.hive.serde2.objectinspector.primitive.DoubleObjectInspector;
import org.apache.hadoop.hive.serde2.typeinfo.TypeInfo;
import org.apache.hadoop.io.DoubleWritable;

/**
 * UDAF — 聚合统计：SUM, AVG, MIN, MAX, COUNT
 * 基于 Hive 2.x GenericUDAFResolver2
 *
 * SQL 用法:
 *   SELECT <schema>.agg_stats(val) FROM table;
 *
 * DDL 必须加:
 *   WITH PROPERTIES ('remote.udf.api'='java8.hive2.v0', 'remote.udf.category'='AGGREGATOR')
 */
public class AggStatsUDAF implements GenericUDAFResolver2 {

    @Override
    public GenericUDAFEvaluator getEvaluator(GenericUDAFParameterInfo info) {
        return new AggStatsEvaluator();
    }

    public GenericUDAFEvaluator getEvaluator(TypeInfo[] parameters) {
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
