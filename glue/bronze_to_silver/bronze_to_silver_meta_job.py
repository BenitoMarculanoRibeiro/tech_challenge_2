import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

from pyspark.sql.functions import (
    col,
    current_timestamp,
    upper,
    trim,
    lit,
    when,
    array,
    struct,
    explode
)

INPUT_META_UF = (
    "s3://tc2-bronze/"
    "meta_alfabetizacao_uf/"
)

INPUT_META_MUNICIPIO = (
    "s3://tc2-bronze/"
    "meta_alfabetizacao_municipio/"
)

INPUT_META_BRASIL = (
    "s3://tc2-bronze/"
    "meta_alfabetizacao_brasil/"
)

OUTPUT_PATH_SILVER = (
    "s3://tc2-silver/"
    "meta_alfabetizacao/"
)

ESCOPO_UF = "uf"
ESCOPO_MUNICIPIO = "municipio"
ESCOPO_BRASIL = "brasil"

# O Brasil nao tem recorte geografico, mas a tabela e unica para os tres
# escopos, entao ele recebe uma chave fixa.
CHAVE_BRASIL = "BR"

# Anos de meta publicados pelo INEP. Sao colunas na bronze e viram linhas aqui.
ANOS_META = [2024, 2025, 2026, 2027, 2028, 2029, 2030]

# A rede vem como texto na origem. Traduzir para o codigo do dicionario e o que
# permite juntar a meta ao fato pela rede, em vez de espalhar regra de
# restricao por rede pelos jobs que consomem.
DE_PARA_REDE = {
    "Pública": 5,
    "Municipal": 3,
}

# Chave natural da tabela. Deduplicar por ela garante que o join no consumidor
# nunca multiplique registros do fato.
CHAVE_NATURAL = ["escopo", "chave", "ano_publicacao", "ano_meta"]


def load(input_path, spark_session):

    df = spark_session.read.parquet(input_path)

    return df


def codigo_rede():
    """Expressao que traduz a rede textual da origem para o codigo."""

    expressao = None

    for texto, codigo in DE_PARA_REDE.items():
        condicao = trim(col("rede")) == lit(texto)
        expressao = (
            when(condicao, lit(codigo)) if expressao is None
            else expressao.when(condicao, lit(codigo))
        )

    return expressao


def normaliza(df, escopo, coluna_chave=None):
    """Transforma um bloco de metas da bronze em formato longo.

    Na bronze cada ano de meta e uma coluna (meta_alfabetizacao_2024 ..
    _2030); aqui cada um vira uma linha, o que deixa a tabela no grao natural
    da meta: uma linha por escopo, geografia, revisao e ano de meta.

    `ano_publicacao` e o ano da revisao -- a mesma meta de 2030 aparece em mais
    de uma revisao, com valores levemente diferentes. Manter as duas datas
    separadas permite ao consumidor escolher a revisao vigente no ano que ele
    esta analisando.

    coluna_chave ausente significa escopo nacional, sem recorte geografico.
    """

    if coluna_chave == "sigla_uf":
        chave = upper(trim(col("sigla_uf")))
    elif coluna_chave:
        chave = trim(col(coluna_chave).cast("string"))
    else:
        chave = lit(CHAVE_BRASIL)

    metas = array(*[
        struct(
            lit(ano).alias("ano_meta"),
            col(f"meta_alfabetizacao_{ano}").cast("double").alias(
                "meta_alfabetizacao"
            )
        )
        for ano in ANOS_META
    ])

    return (
        df
        .withColumn("_meta", explode(metas))
        .select(
            lit(escopo).alias("escopo"),
            chave.alias("chave"),
            codigo_rede().alias("rede"),
            trim(col("rede").cast("string")).alias("rede_descricao"),
            col("ano").cast("integer").alias("ano_publicacao"),
            col("_meta.ano_meta").alias("ano_meta"),
            col("_meta.meta_alfabetizacao").alias("meta_alfabetizacao")
        )
        # Ausencia de meta e ausencia de linha: nao guardamos nulo em tabela
        # longa, senao o consumidor precisa filtrar depois do join.
        .filter(col("meta_alfabetizacao").isNotNull())
    )


def transform(df_meta_uf, df_meta_municipio, df_meta_brasil):

    df = (
        normaliza(df_meta_uf, ESCOPO_UF, "sigla_uf")
        .unionByName(
            normaliza(df_meta_municipio, ESCOPO_MUNICIPIO, "id_municipio")
        )
        .unionByName(normaliza(df_meta_brasil, ESCOPO_BRASIL))
    )

    df = df.dropDuplicates(CHAVE_NATURAL)

    df = df.withColumn("processed_at", current_timestamp())

    return df


def validate(df):

    print("========================================")
    print("VALIDAÇÃO DA SILVER - META DE ALFABETIZAÇÃO")
    print("========================================")

    print("\nQuantidade de registros:")
    print(df.count())

    print("\nSchema:")
    df.printSchema()

    print("\nLinhas por escopo e ano de publicação:")
    (
        df
        .groupBy("escopo", "ano_publicacao")
        .count()
        .orderBy("escopo", "ano_publicacao")
        .show()
    )

    print("\nRede de cada escopo:")
    (
        df
        .select("escopo", "rede", "rede_descricao")
        .distinct()
        .orderBy("escopo", "rede")
        .show(truncate=False)
    )

    sem_rede = df.filter(col("rede").isNull()).count()
    print(f"\nRegistros com rede não mapeada: {sem_rede}")

    if sem_rede:
        print("Redes textuais sem de-para em DE_PARA_REDE:")
        (
            df
            .filter(col("rede").isNull())
            .select("rede_descricao")
            .distinct()
            .show(truncate=False)
        )

    print("\nAnos de meta disponíveis:")
    df.select("ano_meta").distinct().orderBy("ano_meta").show()

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
    print("INICIANDO PROCESSAMENTO SILVER - META")
    print("========================================")

    df_meta_uf = load(INPUT_META_UF, spark_session)
    df_meta_municipio = load(INPUT_META_MUNICIPIO, spark_session)
    df_meta_brasil = load(INPUT_META_BRASIL, spark_session)

    df_silver = transform(df_meta_uf, df_meta_municipio, df_meta_brasil)

    validate(df_silver)

    print("\nGravando Silver:")
    print(OUTPUT_PATH_SILVER)

    (
        df_silver
        .write
        .mode("overwrite")
        .partitionBy('escopo')
        .option("compression", "snappy")
        .parquet(OUTPUT_PATH_SILVER)
    )

    print("\n========================================")
    print("SILVER CONCLUÍDA COM SUCESSO")
    print("========================================")

    job.commit()


if __name__ == "__main__":
    main()
