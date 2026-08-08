import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

# ============================================
# Glue Job: provider_info_curated
#
# Purpose:
# - Read refined Provider Information data
# - Rename selected columns for consistency
# - Created occupancy_rate calculation
# - Write curated Parquet files to S3
# ============================================

## @params: [JOB_NAME]
args = getResolvedOptions(sys.argv, ['JOB_NAME'])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Read refined data
print("Reading parquet...")

df = spark.read.parquet(
    "s3://hc-glue-bucket-refined/provider_info/"
)

# Remove any remaining duplicates
df = df.dropDuplicates()

# Create calculated column
from pyspark.sql.functions import col

df = df.withColumn(
    "occupancy_rate",
    col("Average Number of Residents per Day") /
    col("Number of Certified Beds")
)

df = (
    df
    .withColumnRenamed("CMS Certification Number (CCN)", "cms_certification_number_ccn")
    .withColumnRenamed("Provider Name", "provider_name")
    .withColumnRenamed("State", "state")
    .withColumnRenamed("Ownership Type", "ownership_type")
    .withColumnRenamed("Provider Type", "provider_type")
    .withColumnRenamed("Number of Certified Beds", "certified_beds")
    .withColumnRenamed("Average Number of Residents per Day", "average_residents_per_day")
    .withColumnRenamed("Provider Address", "provider_address")
    .withColumnRenamed("Zip Code", "zip_code")
    .withColumnRenamed("Long-Stay QM Rating", "long_stay_qm_rating")
    .withColumnRenamed("Short-Stay QM Rating", "short_stay_qm_rating")
    .withColumnRenamed("QM Rating", "qm_rating")
    .withColumnRenamed("Overall Rating", "overall_rating")
    .withColumnRenamed("Staffing Rating", "staffing_rating")
    .withColumnRenamed("Total nursing staff turnover", "total_nursing_staff_turnover")
    .withColumnRenamed("Registered nurse turnover", "registered_nurse_turnover")
)  # ✅ closing parenthesis added here

print("Rename the admin column....")

df = (
    df
    .withColumnRenamed("Number of administrators who have left the nursing home", "number_of_administrators_who_left_the_nursing_home")
)

print("Completed the rename of the admin column....")
    
df.write.mode("overwrite").parquet(
    "s3://hc-glue-bucket-curated/provider_info/"
)
df.printSchema()

print(df.columns)

job.commit()
