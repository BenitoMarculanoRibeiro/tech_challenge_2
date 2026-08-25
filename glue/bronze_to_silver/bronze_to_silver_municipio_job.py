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
    coalesce,
    lit,
    broadcast,
    when
)

# Colunas da bronze/municipio que possuem de-para no dicionario:
# nome da coluna na origem -> nome da coluna descritiva na silver
COLUNAS_DE_PARA_DICIONARIO = {
    "rede": "rede_descricao",
    "serie": "serie_descricao",
}

VALOR_NAO_MAPEADO = "Nao informado"




INPUT_DICIONARIO = (
    "s3://tc2-bronze/"
    "dicionario/"
)

INPUT_MUNICIPIOS_IBGE = (
    "s3://tc2-bronze/"
    "municipio_ibge/"
)



INPUT_PATH_BRONZE = (
    "s3://tc2-bronze/"
    "municipio/"
)
 
OUTPUT_PATH_SILVER = (
    "s3://tc2-silver/"
    "municipio/"
)
  
def transform(df, df_dicionario, df_municipios_ibge):
 
    # Remove registros completamente duplicados
    df = df.dropDuplicates()
 
    # Padroniza a chave do municipio antes do join, remove espaço e transforma para string
    df = df.withColumn(
        "id_municipio",
        trim(col("id_municipio").cast("string"))
    )
 
    # Garante tipos numéricos
    df = (
        df
        .withColumn("ano", col("ano").cast("integer"))
        .withColumn("serie", col("serie").cast("integer"))
        .withColumn("rede", col("rede").cast("integer"))
        .withColumn("taxa_alfabetizacao",col("taxa_alfabetizacao").cast("double"))
        .withColumn("media_portugues", col("media_portugues").cast("double"))
    )

    # Enriquece com o nome do municipio e a UF vindos do IBGE
    df = join_municipios_ibge(df, df_municipios_ibge)

    # Padroniza a sigla da UF, maiuscula
    df = df.withColumn("sigla_uf", upper(trim(col("sigla_uf")))
    )

    # Fazer o de para com o df dicionario
    for coluna, coluna_descricao in COLUNAS_DE_PARA_DICIONARIO.items():
        df = apply_dictionary_lookup(df, df_dicionario, coluna, coluna_descricao)

    # Mantem o ano dentro dos arquivos: o partitionBy grava o valor apenas no
    # caminho do S3, entao duplicamos a coluna para o parquet ficar
    # autocontido quando lido arquivo a arquivo.
    df = df.withColumn("ano_referencia", col("ano"))

    # Adiciona timestamp de processamento
    df = df.withColumn(
        "processed_at",
        current_timestamp()
    )
 
    return df
 
def join_municipios_ibge(df, df_municipios_ibge):

    df_ibge = (
        df_municipios_ibge
        .select(
            trim(col("id_municipio").cast("string")).alias("id_municipio"),
            col("nome_municipio"),
            col("sigla_uf")
        )
        .dropDuplicates(["id_municipio"])
    )

    df = df.join(
        broadcast(df_ibge),
        on="id_municipio",
        how="left"
    )

    return df


def apply_dictionary_lookup(df, df_dicionario, coluna, coluna_descricao, id_tabela="municipio"):

    df_de_para = (
        df_dicionario
        .filter(
            (col("id_tabela") == lit(id_tabela))
            & (col("nome_coluna") == lit(coluna))
        )
        .select(
            trim(col("chave").cast("string")).alias("_chave"),
            trim(col("valor").cast("string")).alias(coluna_descricao)
        )
        .dropDuplicates(["_chave"])
    )

    df = (
        df
        .withColumn("_chave_fato", trim(col(coluna).cast("string")))
        .join(
            broadcast(df_de_para),
            col("_chave_fato") == col("_chave"),
            how="left"
        )
        .withColumn(
            coluna_descricao,
            coalesce(col(coluna_descricao), lit(VALOR_NAO_MAPEADO))
        )
        .drop("_chave_fato", "_chave")
    )

    return df


def load(input_path, spark_session):

    df = spark_session.read.parquet(input_path)
    
    return df

 
def validate(df):
 
    print("========================================")
    print("VALIDAÇÃO DA SILVER - MUNICÍPIO")
    print("========================================")
 
    print("\nQuantidade de registros:")
    print(df.count())
 
    print("\nSchema:")
    df.printSchema()
 
    print("\nValores distintos de UF:")
    df.select("sigla_uf").distinct().orderBy("sigla_uf").show()

    print("\nMunicípios distintos:")
    print(df.select("id_municipio").distinct().count())

    sem_ibge = df.filter(col("nome_municipio").isNull()).count()
    print(f"\nRegistros sem correspondência no IBGE: {sem_ibge}")

 
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
    df_municipios_ibge = load(INPUT_MUNICIPIOS_IBGE, spark_session)
 
    print("\nSchema original:")
    df_bronze.printSchema()
 
    df_silver = transform(df_bronze, df_dicionario, 
                          df_municipios_ibge)
 
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
 