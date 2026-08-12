import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    TimestampType,
    ArrayType,
    MapType
)


from pyspark.sql.functions import (
    col,
    current_timestamp,
    upper,
    trim
)

 
INPUT_PATH = (
    "s3://tc2-bronze/"
    "uf/"
)
 
OUTPUT_PATH = (
    "s3://tc2-silver/"
    "uf/"
)
  
def transform(df):
 
    # Remove registros completamente duplicados
    df = df.dropDuplicates()
 
    # Padroniza a sigla da UF
    df = df.withColumn(
        "sigla_uf",
        upper(trim(col("sigla_uf")))
    )
 
    # Garante tipos numéricos
    df = (
        df
        .withColumn("ano", col("ano").cast("integer"))
        .withColumn("serie", col("serie").cast("integer"))
        .withColumn("rede", col("rede").cast("integer"))
        .withColumn(
            "taxa_alfabetizacao",
            col("taxa_alfabetizacao").cast("double")
        )
        .withColumn(
            "media_portugues",
            col("media_portugues").cast("double")
        )
    )
 
    # Adiciona timestamp de processamento
    df = df.withColumn(
        "processed_at",
        current_timestamp()
    )
 
    return df
 
 
def validate(df):
 
    print("========================================")
    print("VALIDAÇÃO DA SILVER - UF")
    print("========================================")
 
    print("\nQuantidade de registros:")
    print(df.count())
 
    print("\nSchema:")
    df.printSchema()
 
    print("\nValores distintos de UF:")
    df.select("sigla_uf").distinct().orderBy("sigla_uf").show()
 
    print("\nAnos disponíveis:")
    df.select("ano").distinct().orderBy("ano").show()
 
    print("\nPrimeiros registros:")
    df.show(10, truncate=False)
 
 
def main():
 
    args = getResolvedOptions(sys.argv, ['JOB_NAME'])

    sc = SparkContext()
    glueContext = GlueContext(sc)
    spark = glueContext.spark_session
    job = Job(glueContext)
    job.init(args['JOB_NAME'], args)
 
    print("========================================")
    print("INICIANDO PROCESSAMENTO SILVER")
    print("========================================")
 
    print(f"\nLendo Bronze:")
    print(INPUT_PATH)
 
    df = spark.read.parquet(INPUT_PATH)
 
    print("\nSchema original:")
    df.printSchema()
 
    df_silver = transform(df)
 
    validate(df_silver)
 
    print("\nGravando Silver:")
    print(OUTPUT_PATH)
 
    (
        df_silver
        .write
        .mode("overwrite")
        .option("compression", "snappy")
        .parquet(OUTPUT_PATH)
    )
 
    print("\n========================================")
    print("SILVER CONCLUÍDA COM SUCESSO")
    print("========================================")

    job.commit()

if __name__ == "__main__":
    main()
 