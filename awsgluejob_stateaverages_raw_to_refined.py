import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

## @params: [JOB_NAME]
args = getResolvedOptions(sys.argv, ['JOB_NAME'])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

df = spark.read.csv(
    "s3://hc-glue-bucket/csv_data_files/NH_StateUSAverages_Oct2024.csv",
    header=True,
    inferSchema=True
)

df = df.dropDuplicates()

print(f"Number of rows: {df.count()}")

df.printSchema()

df.write.mode("overwrite").parquet(
    "s3://hc-glue-bucket-refined/state_averages/"
)

job.commit()