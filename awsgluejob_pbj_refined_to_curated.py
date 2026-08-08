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

print("========== PBJ CURATED VERSION 2026-07-15 ==========")

# Read refined data
print("Reading parquet...")

df = spark.read.parquet(
    "s3://hc-glue-bucket-refined/pbj/"
)

df = (
    df
    .withColumnRenamed("PROVNUM", "cms_certification_number_ccn")
    .withColumnRenamed("PROVNAME", "provider_name")
    .withColumnRenamed("STATE", "state")
)

# Remove any remaining duplicates
df = df.dropDuplicates()

# Create calculated column
from pyspark.sql.functions import col

print("Creating Total_Nurse_Hrs....")

df = df.withColumn(
    "Total_Nurse_Hrs",
    col("Hrs_RN") +
    col("Hrs_LPN") +
    col("Hrs_CNA")
)

print("Total_Nurse_Hrs created....")

print("Creating RN_Percentage....")

df = df.withColumn(
    "RN_Percentage",
    col("Hrs_RN") / col("Total_Nurse_Hrs")
)

print("RN_Percentage created....")

print("Creating Total_emp_Nurse_Hrs....")

df = df.withColumn(
    "Total_emp_Nurse_Hrs",
    col("Hrs_RN_emp") +
    col("Hrs_LPN_emp") +
    col("Hrs_CNA_emp")
)

print("Total_emp_Nurse_Hrs created....")

print("Creating Emp_Nurse_Percentage....")

df = df.withColumn(
    "Emp_Nurse_Percentage",
    col("Hrs_RN_emp") / col("Total_emp_Nurse_Hrs")
)

df = df.withColumn(
    "employee_hrs",
    col("Hrs_RN_emp") +
    col("Hrs_LPN_emp") +
    col("Hrs_CNA_emp") +
    col("Hrs_NAtrn_emp") +
    col("Hrs_MedAide_emp")
    )
    
df = df.withColumn(
    "contractor_hrs",
    col("Hrs_RN_ctr") +
    col("Hrs_LPN_ctr") +
    col("Hrs_CNA_ctr") +
    col("Hrs_NAtrn_ctr") +
    col("Hrs_MedAide_ctr")
    )
    
print("Emp_Nurse_Percentage created....")

print("Schema BEFORE writing:")
df.printSchema()

print("Writing curated data...")

df.write.mode("overwrite").parquet(
    "s3://hc-glue-bucket-curated/pbj/"
)

print("Write complete.")

print(df.columns)

job.commit()