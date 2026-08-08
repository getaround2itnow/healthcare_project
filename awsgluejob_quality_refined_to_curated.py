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

print("========== QUALITY CURATED VERSION 2026-07-15 ==========")

# Read refined data
print("Reading parquet...")

df = spark.read.parquet(
    "s3://hc-glue-bucket-refined/quality/"
)

print("renaming columns")

df = (
    df
    .withColumnRenamed("Q1 Measure Score", "q1_measure_score")
    .withColumnRenamed("Q2 Measure Score", "q2_measure_score")
    .withColumnRenamed("Q3 Measure Score", "q3_measure_score")
    .withColumnRenamed("Q4 Measure Score", "q4_measure_score")
)

df = df.withColumnRenamed(
    "CMS Certification Number (CCN)",
    "cms_certification_number_ccn"
)

df = df.withColumnRenamed(
    "Provider Name",
    "provider_name"
)

df = df.withColumnRenamed(
    "Measure Code",
    "measure_code"
)

df = df.withColumnRenamed(
    "Measure Description",
    "measure_description"
)

df = df.withColumnRenamed(
    "Provider Address",
    "provider_address"
)

df = df.withColumnRenamed(
    "Zip Code",
    "zip_code"
)

df = df.withColumnRenamed(
    "Resident Type",
    "resident_type"
)


df = (
    df
    .withColumnRenamed(
        "Q1 Measure Score",
        "q1_measure_score"
    )
    .withColumnRenamed(
        "Q2 Measure Score",
        "q2_measure_score"
    )
    .withColumnRenamed(
        "Q3 Measure Score",
        "q3_measure_score"
    )
    .withColumnRenamed(
        "Q4 Measure Score",
        "q4_measure_score"
    )
    .withColumnRenamed(
        "Four Quarter Average Score",
        "four_quarter_average_score"
    )
    .withColumnRenamed(
        "Measure Period",
        "measure_period"
    )
    .withColumnRenamed(
        "Processing Date",
        "processing_date"
    )
)

print("columns renamed")

# Remove any remaining duplicates
df = df.dropDuplicates()

# Create calculated column "missing_quarter_count"
df = df.withColumn(
    "missing_quarter_count",
    (
        F.when(F.col("q1_measure_score").isNull(), 1).otherwise(0) +
        F.when(F.col("q2_measure_score").isNull(), 1).otherwise(0) +
        F.when(F.col("q3_measure_score").isNull(), 1).otherwise(0) +
        F.when(F.col("q4_measure_score").isNull(), 1).otherwise(0)
    )
)

print("missing_quarter_count column created")    
    
print("Creating column sum_of_available_quarterly_scores")
df = df.withColumn(
    "sum_of_available_quarterly_scores",
    F.coalesce(F.col("q1_measure_score"), F.lit(0.0)) +
    F.coalesce(F.col("q2_measure_score"), F.lit(0.0)) +
    F.coalesce(F.col("q3_measure_score"), F.lit(0.0)) +
    F.coalesce(F.col("q4_measure_score"), F.lit(0.0))
)

print("sum_of_available_quarterly_scores created....;")

print("Creating column max_quarterly_measure_score")
df = df.withColumn(
    "max_quarterly_measure_score",
    F.greatest(
        F.col("q1_measure_score"),
        F.col("q2_measure_score"),
        F.col("q3_measure_score"),
        F.col("q4_measure_score")
    )
)
print("max_quarterly_measure_score column created")

print("Creating column min_quarterly_measure_score")
df = df.withColumn(
    "min_quarterly_measure_score",
    F.least(
        F.col("q1_measure_score"),
        F.col("q2_measure_score"),
        F.col("q3_measure_score"),
        F.col("q4_measure_score")
    )
)
print("min_quarterly_measure_score column created")

print("Creating column quarterly_score_range")
df = df.withColumn(
    "quarterly_score_range",
    F.greatest(
        F.col("q1_measure_score"),
        F.col("q2_measure_score"),
        F.col("q3_measure_score"),
        F.col("q4_measure_score")
    )
    -
    F.least(
        F.col("q1_measure_score"),
        F.col("q2_measure_score"),
        F.col("q3_measure_score"),
        F.col("q4_measure_score")
    )
)
print("quarterly_score_range column created")

print("Schema BEFORE writing:")

df.printSchema()

print("Writing curated data...")

df.write.mode("overwrite").parquet(
    "s3://hc-glue-bucket-curated/quality/"
)

print("Write complete.")

print(df.columns)

job.commit()