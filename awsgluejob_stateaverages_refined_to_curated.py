import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql import functions as F
from pyspark.sql.functions import col

## @params: [JOB_NAME]
args = getResolvedOptions(sys.argv, ['JOB_NAME'])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

job = Job(glueContext)
job.init(args['JOB_NAME'], args)

print("========== STATE AVERAGES CURATED VERSION 2026-07-15 ==========")

# Read refined data
print("Reading parquet...")

df = spark.read.parquet(
    "s3://hc-glue-bucket-refined/state_averages/"
)

# Remove any remaining duplicates
df = df.dropDuplicates()

print("Creating column all_cycle_total_health_deficiencies")
df = df.withColumn(
    "all_cycle_total_health_deficiencies",
    F.coalesce(F.col("Cycle 1 Total Number of Health Deficiencies"), F.lit(0.0)) +
    F.coalesce(F.col("Cycle 2 Total Number of Health Deficiencies"), F.lit(0.0)) +
    F.coalesce(F.col("Cycle 3 Total Number of Health Deficiencies"), F.lit(0.0)) 
)

print("all_cycle_total_health_deficiencies column created....")

df = (
    df
    .withColumnRenamed("State or Nation", "state")
    .withColumnRenamed("Processing Date", "processing_date")
)

print("Creating column total_health_deficiencies_range")
df = df.withColumn(
    "total_health_deficiencies_range",
    F.greatest(
        F.col("Cycle 1 Total Number of Health Deficiencies"),
        F.col("Cycle 2 Total Number of Health Deficiencies"),
        F.col("Cycle 3 Total Number of Health Deficiencies")
    )
    -
    F.least(
        F.col("Cycle 1 Total Number of Health Deficiencies"),
        F.col("Cycle 2 Total Number of Health Deficiencies"),
        F.col("Cycle 3 Total Number of Health Deficiencies")
    )
)

print("total_health_deficiencies_range column created....")

print("Schema BEFORE writing:")

df.printSchema()

print("Writing curated data...")

df.write.mode("overwrite").parquet(
    "s3://hc-glue-bucket-curated/state_averages/"
)

print("Write complete.")

print(df.columns)

job.commit()