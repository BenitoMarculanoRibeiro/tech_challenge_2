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
    trim,
    coalesce
)

INPUT_DICIONARIO = (
    "s3://tc2-bronze/"
    "dicionario//"
)

INPUT_PATH_BRONZE = (
    "s3://tc2-bronze/"
    "uf/"
)
 
OUTPUT_PATH_SILVER = (
    "s3://tc2-silver/"
    "uf/"
)
  
def transform(df, df_dicionario):
 
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

    # Fazer o de para com o df dicionario 
    df_dicionario = df_dicionario.filter((col("id_tabela") == 'uf') & (col("nome_coluna") == "rede"))
    df_dicionario = df_dicionario.select("chave","valor")

    df = df.join(
        df_dicionario,
        df["rede"] == df_dicionario["chave"],
        how="left"
    )

    # Adiciona timestamp de processamento
    df = df.withColumn(
        "processed_at",
        current_timestamp()
    )
 
    return df
 
def load(input_path, spark_session):

    df = spark_session.read.parquet(input_path)
    
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
    spark_session = glueContext.spark_session
    job = Job(glueContext)
    job.init(args['JOB_NAME'], args)
 
    print("========================================")
    print("INICIANDO PROCESSAMENTO SILVER")
    print("========================================")
 
    print(f"\nLendo Bronze:")
    print(INPUT_PATH_BRONZE)

    df_bronze = load(INPUT_PATH_BRONZE, spark_session)
    df_dicionario = load(INPUT_DICIONARIO, spark_session)
 
    print("\nSchema original:")
    df_bronze.printSchema()
 
    df_silver = transform(df_bronze, df_dicionario)
 
    validate(df_silver)
 
    print("\nGravando Silver:")
    print(OUTPUT_PATH_SILVER)
 
    (
        df_silver
        .write
        .mode("overwrite")
        .partitionBy('ano')
        .option("compression", "snappy")
        .parquet(OUTPUT_PATH_SILVER)
    )
 
    print("\n========================================")
    print("SILVER CONCLUÍDA COM SUCESSO")
    print("========================================")

    job.commit()

if __name__ == "__main__":
    main()
 