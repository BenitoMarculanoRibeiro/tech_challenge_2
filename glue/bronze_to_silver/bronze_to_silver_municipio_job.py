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
COLUNAS_DE_PARA = {
    "rede": "rede_descricao",
    "serie": "serie_descricao",
}

VALOR_NAO_MAPEADO = "Nao informado"


# A meta_alfabetizacao_municipio cobre apenas a rede "Municipal" (codigo 3 do
# dicionario) e a meta_alfabetizacao_brasil apenas a rede "Pública" (codigo 5,
# "Pública (Estadual e Municipal)"). Nas demais redes as metas ficam nulas,
# para nao comparar a taxa de uma rede com a meta de outra.
REDES_COM_META_MUNICIPIO = [3]
REDES_COM_META_BRASIL = [5]

# Nomes das colunas de meta na bronze. As tres bases de meta (uf, municipio,
# brasil) usam os mesmos nomes, por isso na silver cada uma recebe o prefixo do
# seu escopo: meta_alfabetizacao_2030 -> meta_alfabetizacao_municipio_2030.
COLUNAS_META_ORIGEM = [
    "meta_alfabetizacao_2024",
    "meta_alfabetizacao_2025",
    "meta_alfabetizacao_2026",
    "meta_alfabetizacao_2027",
    "meta_alfabetizacao_2028",
    "meta_alfabetizacao_2029",
    "meta_alfabetizacao_2030",
]

INPUT_DICIONARIO = (
    "s3://tc2-bronze/"
    "dicionario/"
)

INPUT_MUNICIPIOS_IBGE = (
    "s3://tc2-bronze/"
    "municipio_ibge/"
)

INPUT_META_ALFABETIZACAO_MUNICIPIO = (
    "s3://tc2-bronze/"
    "meta_alfabetizacao_municipio/"
)

INPUT_META_ALFABETIZACAO_BRASIL = (
    "s3://tc2-bronze/"
    "meta_alfabetizacao_brasil/"
)

INPUT_PATH_BRONZE = (
    "s3://tc2-bronze/"
    "municipio/"
)
 
OUTPUT_PATH_SILVER = (
    "s3://tc2-silver/"
    "municipio/"
)
  
def transform(df, df_dicionario, df_municipios_ibge, df_meta_municipio,
              df_meta_brasil):
 
    # Remove registros completamente duplicados
    df = df.dropDuplicates()
 
    # Padroniza a chave do municipio antes do join
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
        .withColumn(
            "taxa_alfabetizacao",
            col("taxa_alfabetizacao").cast("double")
        )
        .withColumn(
            "media_portugues",
            col("media_portugues").cast("double")
        )
    )

    # Enriquece com o nome do municipio e a UF vindos do IBGE
    df = join_municipios_ibge(df, df_municipios_ibge)

    # Padroniza a sigla da UF (que vem do IBGE)
    df = df.withColumn(
        "sigla_uf",
        upper(trim(col("sigla_uf")))
    )

    # Fazer o de para com o df dicionario
    for coluna, coluna_descricao in COLUNAS_DE_PARA.items():
        df = apply_dictionary_lookup(df, df_dicionario, coluna, coluna_descricao)

    # Mantem o ano dentro dos arquivos: o partitionBy grava o valor apenas no
    # caminho do S3, entao duplicamos a coluna para o parquet ficar
    # autocontido quando lido arquivo a arquivo.
    df = df.withColumn("ano_referencia", col("ano"))

    # Traz as metas de alfabetizacao do municipio e do Brasil
    df = join_meta_alfabetizacao(
        df, df_meta_municipio, "municipio", REDES_COM_META_MUNICIPIO,
        chave_geografica="id_municipio"
    )
    df = join_meta_alfabetizacao(
        df, df_meta_brasil, "brasil", REDES_COM_META_BRASIL
    )

    # Adiciona timestamp de processamento
    df = df.withColumn(
        "processed_at",
        current_timestamp()
    )
 
    return df
 
def join_meta_alfabetizacao(df, df_meta, escopo, redes_com_meta,
                            chave_geografica=None):
    """Traz as metas de alfabetizacao (2024..2030) de uma das bases de meta.

    As bases de meta usam os mesmos nomes de coluna na bronze, entao aqui cada
    uma recebe o prefixo do seu escopo, evitando colisao e deixando explicito
    de onde a meta vem.

    O join sempre casa o ano_referencia do fato com o ano da meta e, quando a
    base tem recorte geografico, tambem a chave informada. Cada base tem uma
    unica linha por (chave, ano), logo o join nao multiplica registros do fato.

    - normaliza chave e ano nos dois lados, para nao perder match por espaco,
      caixa ou tipo;
    - usa broadcast, porque as metas sao pequenas e assim evitamos o shuffle;
    - left join para nunca descartar registro do fato sem meta;
    - preenche a meta apenas nas redes de redes_com_meta: cada base cobre uma
      unica rede, e colar meta de rede publica em rede privada/federal
      induziria a comparacoes erradas na gold.
    """

    colunas_meta = [
        coluna.replace(
            "meta_alfabetizacao_",
            f"meta_alfabetizacao_{escopo}_"
        )
        for coluna in COLUNAS_META_ORIGEM
    ]

    selecao = [col("ano").cast("integer").alias("_ano_meta")]

    if chave_geografica:
        selecao.append(
            upper(trim(col(chave_geografica).cast("string")))
            .alias("_chave_meta")
        )

    selecao += [
        col(origem).cast("double").alias(destino)
        for origem, destino in zip(COLUNAS_META_ORIGEM, colunas_meta)
    ]

    df_meta = df_meta.select(*selecao)

    condicao = col("ano_referencia") == col("_ano_meta")

    if chave_geografica:
        condicao = condicao & (
            upper(trim(col(chave_geografica).cast("string")))
            == col("_chave_meta")
        )

    df = (
        df
        .join(
            broadcast(df_meta),
            condicao,
            how="left"
        )
        .drop("_ano_meta", "_chave_meta")
    )

    rede_com_meta = col("rede").isin(redes_com_meta)

    for coluna in colunas_meta:
        df = df.withColumn(
            coluna,
            when(rede_com_meta, col(coluna))
        )

    return df


def join_municipios_ibge(df, df_municipios_ibge):
    """Traz nome_municipio e sigla_uf do IBGE para o fato, via id_municipio.

    - deduplica o lado do IBGE pela chave, para que o join nao multiplique
      registros do fato;
    - normaliza a chave como string aparada nos dois lados, evitando perda de
      match por espaco ou por diferenca de tipo;
    - usa broadcast, porque sao ~5,6 mil municipios e assim evitamos o shuffle;
    - left join para nunca descartar registro do fato sem correspondencia.
    """

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
    """Traduz uma coluna codificada usando o dicionario da bronze.

    - filtra o dicionario pela tabela/coluna e deduplica as chaves, para que o
      join nao multiplique registros do fato;
    - normaliza os dois lados da chave como string aparada, evitando o cast
      implicito entre a coluna numerica do fato e a chave textual do dicionario;
    - usa broadcast, porque o dicionario e pequeno o suficiente para caber em
      memoria e assim evitamos o shuffle;
    - preserva apenas a coluna descritiva, descartando as colunas auxiliares do
      dicionario (chave/valor).
    """

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

    for escopo, redes in (
        ("municipio", REDES_COM_META_MUNICIPIO),
        ("brasil", REDES_COM_META_BRASIL),
    ):
        sem_meta = df.filter(
            col("rede").isin(redes)
            & col(f"meta_alfabetizacao_{escopo}_2030").isNull()
        ).count()
        print(
            f"\nRegistros da rede com meta de {escopo}, porém sem meta: "
            f"{sem_meta}"
        )
 
    print("\nAnos disponíveis:")
    df.select("ano").distinct().orderBy("ano").show()

    for coluna, coluna_descricao in COLUNAS_DE_PARA.items():
        print(f"\nDe-para de {coluna}:")
        (
            df
            .select(coluna, coluna_descricao)
            .distinct()
            .orderBy(coluna)
            .show(truncate=False)
        )

        nao_mapeados = df.filter(
            col(coluna_descricao) == VALOR_NAO_MAPEADO
        ).count()
        print(f"Registros sem de-para em {coluna}: {nao_mapeados}")
 
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
    df_meta_municipio = load(
        INPUT_META_ALFABETIZACAO_MUNICIPIO, spark_session
    )
    df_meta_brasil = load(INPUT_META_ALFABETIZACAO_BRASIL, spark_session)
 
    print("\nSchema original:")
    df_bronze.printSchema()
 
    df_silver = transform(df_bronze, df_dicionario, df_municipios_ibge,
                          df_meta_municipio, df_meta_brasil)
 
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
 