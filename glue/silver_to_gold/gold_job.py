import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

from pyspark.sql.functions import (
    col,
    current_timestamp,
    lit,
    when,
    coalesce,
    array,
    struct,
    explode,
    broadcast,
    lag,
    first,
    count,
    sum as spark_sum,
    pmod,
    hash as spark_hash
)

from pyspark.sql.window import Window

def configure_paths(args):
    """Configura entradas e saídas sem depender dos nomes físicos dos buckets."""
    global INPUT_SILVER_UF, INPUT_SILVER_MUNICIPIO
    global INPUT_SILVER_ALUNOS, INPUT_SILVER_META
    global OUTPUT_GOLD_INDICADOR_MUNICIPIO, OUTPUT_GOLD_INDICADOR_UF
    global OUTPUT_GOLD_INDICADOR_BRASIL, OUTPUT_GOLD_METAS_MUNICIPIO
    global OUTPUT_GOLD_METAS_UF, OUTPUT_GOLD_METAS_BRASIL
    global OUTPUT_GOLD_EVOLUCAO_MUNICIPIO, OUTPUT_GOLD_EVOLUCAO_UF
    global OUTPUT_GOLD_EVOLUCAO_BRASIL, OUTPUT_GOLD_ML_ALUNO

    silver = args["SILVER_BUCKET"]
    gold = args["GOLD_BUCKET"]
    INPUT_SILVER_UF = f"s3://{silver}/uf/"
    INPUT_SILVER_MUNICIPIO = f"s3://{silver}/municipio/"
    INPUT_SILVER_ALUNOS = f"s3://{silver}/alunos/"
    INPUT_SILVER_META = f"s3://{silver}/meta_alfabetizacao/"
    OUTPUT_GOLD_INDICADOR_MUNICIPIO = f"s3://{gold}/indicador_municipio/"
    OUTPUT_GOLD_INDICADOR_UF = f"s3://{gold}/indicador_uf/"
    OUTPUT_GOLD_INDICADOR_BRASIL = f"s3://{gold}/indicador_brasil/"
    OUTPUT_GOLD_METAS_MUNICIPIO = f"s3://{gold}/metas_vs_resultado_municipio/"
    OUTPUT_GOLD_METAS_UF = f"s3://{gold}/metas_vs_resultado_uf/"
    OUTPUT_GOLD_METAS_BRASIL = f"s3://{gold}/metas_vs_resultado_brasil/"
    OUTPUT_GOLD_EVOLUCAO_MUNICIPIO = f"s3://{gold}/evolucao_temporal_municipio/"
    OUTPUT_GOLD_EVOLUCAO_UF = f"s3://{gold}/evolucao_temporal_uf/"
    OUTPUT_GOLD_EVOLUCAO_BRASIL = f"s3://{gold}/evolucao_temporal_brasil/"
    OUTPUT_GOLD_ML_ALUNO = f"s3://{gold}/ml_aluno/"


NIVEL_MUNICIPIO = "municipio"
NIVEL_UF = "uf"
NIVEL_BRASIL = "brasil"

# Procedencia do indicador, para nao misturar numero publicado com calculado
# sem deixar rastro.
ORIGEM_PUBLICADA = "inep_publicado"
ORIGEM_CALCULADA = "calculado_microdado"

# Codigo do dicionario para a rede publica, unica rede coberta pela meta
# nacional.
REDE_PUBLICA = 5

# O microdado de alunos tem uma linha por rede individual. As redes compostas
# do dicionario sao montadas somando as redes que as compoem.
#
# Atencao: o microdado nao traz a rede 1 (Federal), entao a rede 0 (Total) sai
# sem a parcela federal -- uma subcontagem pequena, mas real.
AGREGACOES_REDE = [
    (0, "Total (Federal, Estadual, Municipal e Privada)", [1, 2, 3, 4]),
    (REDE_PUBLICA, "Pública (Estadual e Municipal)", [2, 3]),
    (2, "Estadual", [2]),
    (3, "Municipal", [3]),
    (4, "Privada", [4]),
]

# Split deterministico para treino de modelo: derivado do hash do id_aluno,
# entao o mesmo aluno cai sempre na mesma parte, execucao apos execucao.
SPLITS_ML = [
    ("treino", 0, 70),
    ("validacao", 70, 85),
    ("teste", 85, 100),
]

CHAVE_BRASIL = "BR"

# Ano do alvo final do compromisso de alfabetizacao.
ANO_META_FINAL = 2030

# Componentes aditivos da media ponderada. Guardar as somas em vez da taxa e o
# que permite consolidar municipio -> UF -> Brasil sem reler o microdado.
COLUNAS_SOMA = [
    "soma_ponderada",
    "soma_pesos",
    "soma_alfabetizados",
    "qtd_alunos",
]

# Colunas que cada silver precisa entregar. Conferir na entrada troca um
# AnalysisException no meio do job por uma mensagem dizendo o que falta -- o
# caso tipico e a silver ter sido gravada por uma versao antiga do job de
# bronze_to_silver, sem as metas prefixadas por escopo.
COLUNAS_OBRIGATORIAS_UF = [
    "sigla_uf",
    "ano_referencia",
    "serie",
    "serie_descricao",
    "rede",
    "rede_descricao",
    "taxa_alfabetizacao",
    "media_portugues",
]

COLUNAS_OBRIGATORIAS_MUNICIPIO = [
    "id_municipio",
    "nome_municipio",
    "sigla_uf",
    "ano_referencia",
    "serie",
    "serie_descricao",
    "rede",
    "rede_descricao",
    "taxa_alfabetizacao",
    "media_portugues",
]

COLUNAS_OBRIGATORIAS_META = [
    "escopo",
    "chave",
    "rede",
    "ano_publicacao",
    "ano_meta",
    "meta_alfabetizacao",
]

COLUNAS_OBRIGATORIAS_ALUNOS = [
    "id_aluno",
    "id_escola",
    "id_municipio",
    "nome_municipio",
    "sigla_uf",
    "ano_referencia",
    "serie",
    "serie_descricao",
    "rede",
    "rede_descricao",
    "caderno",
    "presenca",
    "preenchimento_caderno",
    "alfabetizado",
    "proficiencia",
    "peso_aluno",
]


def load(input_path, spark_session):

    df = spark_session.read.parquet(input_path)

    return df


def valida_schema(nome, df, colunas_obrigatorias):
    """Falha cedo, e com mensagem util, se a silver estiver defasada."""

    faltando = [
        coluna for coluna in colunas_obrigatorias
        if coluna not in df.columns
    ]

    if faltando:
        raise ValueError(
            f"A silver de {nome} nao tem as colunas {faltando}. "
            f"Colunas encontradas: {sorted(df.columns)}. "
            "Reprocesse a silver com a versao atual do job bronze_to_silver "
            "antes de rodar a gold."
        )

    print(f"Schema da silver de {nome}: ok")


def finaliza(df, nivel):
    """Colunas comuns a todo dataset da gold: nivel, particao e carimbo."""

    return (
        df
        .withColumn("nivel_geografico", lit(nivel))
        .withColumn("ano", col("ano_referencia"))
        .withColumn("processed_at", current_timestamp())
    )


def agrega_alunos(df_alunos):
    """Agrega o microdado uma unica vez, no grao mais fino.

    Devolve uma linha por (sigla_uf, id_municipio, ano, serie, rede individual)
    com os componentes aditivos da taxa, nao a taxa. Guardar as somas e o que
    permite consolidar para UF e Brasil somando, sem reler os ~3,9M de linhas
    uma vez por nivel.
    """

    return (
        df_alunos
        .groupBy(
            "sigla_uf",
            "id_municipio",
            "ano_referencia",
            "serie",
            "serie_descricao",
            "rede"
        )
        .agg(
            spark_sum(col("alfabetizado") * col("peso_aluno"))
            .alias("soma_ponderada"),
            spark_sum(
                when(col("alfabetizado").isNotNull(), col("peso_aluno"))
            ).alias("soma_pesos"),
            spark_sum(col("alfabetizado").cast("double"))
            .alias("soma_alfabetizados"),
            count(col("alfabetizado")).alias("qtd_alunos")
        )
    )


def consolida_alunos(df_agregado, colunas_chave):
    """Consolida o agregado do microdado no nivel pedido, por rede.

    As redes compostas do dicionario sao montadas somando as individuais, e a
    taxa e recalculada ao final: media de alfabetizado ponderada por
    peso_aluno, com queda para media simples quando o peso nao esta preenchido.

    colunas_chave vazia consolida o Brasil inteiro.
    """

    consolidados = None

    for codigo_rede, descricao_rede, redes_incluidas in AGREGACOES_REDE:
        consolidado = (
            df_agregado
            .filter(col("rede").isin(redes_incluidas))
            .groupBy(
                *colunas_chave,
                "ano_referencia",
                "serie",
                "serie_descricao"
            )
            .agg(*[
                spark_sum(col(coluna)).alias(coluna)
                for coluna in COLUNAS_SOMA
            ])
            .withColumn("rede", lit(codigo_rede))
            .withColumn("rede_descricao", lit(descricao_rede))
            .withColumn(
                "taxa_alfabetizacao_calculada",
                coalesce(
                    100 * col("soma_ponderada") / col("soma_pesos"),
                    100 * col("soma_alfabetizados") / col("qtd_alunos")
                )
            )
            .drop("soma_ponderada", "soma_pesos", "soma_alfabetizados")
        )

        consolidados = (
            consolidado if consolidados is None
            else consolidados.unionByName(consolidado)
        )

    return consolidados


def volume_alunos(df_agregado, colunas_chave):
    """So a contagem de alunos, para anexar aos niveis que usam a taxa do INEP.

    Os nomes ganham sufixo `_vol` para nao colidirem com as colunas do fato no
    join; sao descartados logo depois.
    """

    df = consolida_alunos(df_agregado, colunas_chave)

    return df.select(
        *[col(coluna).alias(f"{coluna}_vol") for coluna in colunas_chave],
        col("ano_referencia").alias("ano_referencia_vol"),
        col("serie").alias("serie_vol"),
        col("rede").alias("rede_vol"),
        col("qtd_alunos")
    )


def anexa_volume(df, df_volume, colunas_chave):
    """Junta a contagem de alunos ao fato, por chave, ano, serie e rede."""

    condicao = (
        (col("ano_referencia") == col("ano_referencia_vol"))
        & (col("serie") == col("serie_vol"))
        & (col("rede") == col("rede_vol"))
    )

    for coluna in colunas_chave:
        condicao = condicao & (col(coluna) == col(f"{coluna}_vol"))

    return (
        df
        .join(broadcast(df_volume), condicao, how="left")
        .drop(
            "ano_referencia_vol",
            "serie_vol",
            "rede_vol",
            *[f"{coluna}_vol" for coluna in colunas_chave]
        )
    )


def referencia_uf(df_indicador_uf):
    """Taxa da UF, para desnormalizar na linha do municipio."""

    return df_indicador_uf.select(
        col("sigla_uf").alias("_sigla_uf_ref"),
        col("ano_referencia").alias("_ano_ref_uf"),
        col("serie").alias("_serie_ref_uf"),
        col("rede").alias("_rede_ref_uf"),
        col("taxa_alfabetizacao").alias("taxa_alfabetizacao_uf")
    )


def referencia_brasil(df_indicador_brasil):
    """Taxa nacional, para desnormalizar nas linhas de municipio e de UF."""

    return df_indicador_brasil.select(
        col("ano_referencia").alias("_ano_ref_br"),
        col("serie").alias("_serie_ref_br"),
        col("rede").alias("_rede_ref_br"),
        col("taxa_alfabetizacao").alias("taxa_alfabetizacao_brasil")
    )


def anexa_comparativos(df, df_ref_uf=None, df_ref_brasil=None):
    """Coloca na mesma linha as taxas de referencia e a diferenca contra elas.

    E o que justifica o indicador existir na gold: o dashboard responde "esse
    municipio esta acima ou abaixo do seu estado e do pais" lendo uma linha,
    sem join. A comparacao casa ano, serie e rede, para nunca cruzar recortes
    diferentes.
    """

    if df_ref_uf is not None:
        df = (
            df
            .join(
                broadcast(df_ref_uf),
                (col("sigla_uf") == col("_sigla_uf_ref"))
                & (col("ano_referencia") == col("_ano_ref_uf"))
                & (col("serie") == col("_serie_ref_uf"))
                & (col("rede") == col("_rede_ref_uf")),
                how="left"
            )
            .drop("_sigla_uf_ref", "_ano_ref_uf", "_serie_ref_uf",
                  "_rede_ref_uf")
            .withColumn(
                "diferenca_pp_vs_uf",
                col("taxa_alfabetizacao") - col("taxa_alfabetizacao_uf")
            )
        )

    if df_ref_brasil is not None:
        df = (
            df
            .join(
                broadcast(df_ref_brasil),
                (col("ano_referencia") == col("_ano_ref_br"))
                & (col("serie") == col("_serie_ref_br"))
                & (col("rede") == col("_rede_ref_br")),
                how="left"
            )
            .drop("_ano_ref_br", "_serie_ref_br", "_rede_ref_br")
            .withColumn(
                "diferenca_pp_vs_brasil",
                col("taxa_alfabetizacao") - col("taxa_alfabetizacao_brasil")
            )
        )

    return df


def indicador_municipio(df_municipio, df_agregado, df_meta,
                        df_ref_uf, df_ref_brasil):
    """Indicador no nivel municipio, com a taxa publicada pelo INEP.

    Recebe a contagem de alunos, a meta do proprio ano e as taxas de
    referencia da UF e do Brasil.
    """

    df = df_municipio.select(
        col("id_municipio"),
        col("nome_municipio"),
        col("sigla_uf"),
        col("ano_referencia"),
        col("serie"),
        col("serie_descricao"),
        col("rede"),
        col("rede_descricao"),
        col("taxa_alfabetizacao"),
        col("media_portugues"),
        lit(ORIGEM_PUBLICADA).alias("origem_indicador")
    )

    df = anexa_volume(
        df, volume_alunos(df_agregado, ["id_municipio"]), ["id_municipio"]
    )
    df = anexa_meta_do_ano(
        df, meta_do_ano(df_meta, NIVEL_MUNICIPIO), "id_municipio"
    )
    df = anexa_comparativos(df, df_ref_uf, df_ref_brasil)

    return finaliza(df, NIVEL_MUNICIPIO)


def indicador_uf(df_uf, df_agregado, df_meta, df_ref_brasil):
    """Indicador no nivel UF, com a taxa publicada pelo INEP."""

    df = df_uf.select(
        col("sigla_uf"),
        col("ano_referencia"),
        col("serie"),
        col("serie_descricao"),
        col("rede"),
        col("rede_descricao"),
        col("taxa_alfabetizacao"),
        col("media_portugues"),
        lit(ORIGEM_PUBLICADA).alias("origem_indicador")
    )

    df = anexa_volume(
        df, volume_alunos(df_agregado, ["sigla_uf"]), ["sigla_uf"]
    )
    df = anexa_meta_do_ano(df, meta_do_ano(df_meta, NIVEL_UF), "sigla_uf")
    df = anexa_comparativos(df, df_ref_brasil=df_ref_brasil)

    return finaliza(df, NIVEL_UF)


def meta_do_ano(df_meta, escopo):
    """Meta cujo ano coincide com o ano observado, para anexar ao indicador.

    E a leitura mais direta -- "estou acima ou abaixo da meta deste ano" -- e a
    unica que cabe numa coluna. A trajetoria completa fica no dataset de metas
    vs resultado, que consome a tabela longa inteira.

    A revisao usada e a publicada no proprio ano observado
    (ano_publicacao = ano_meta), evitando comparar o resultado de um ano com a
    meta revisada depois.
    """

    return (
        df_meta
        .filter(
            (col("escopo") == lit(escopo))
            & (col("ano_publicacao") == col("ano_meta"))
        )
        .select(
            col("chave").alias("_chave_meta"),
            col("ano_meta").alias("_ano_meta"),
            col("rede").alias("_rede_meta"),
            col("meta_alfabetizacao").alias("meta_alfabetizacao_do_ano")
        )
    )


def anexa_meta_do_ano(df, df_meta_ano, coluna_chave=None):
    """Junta a meta do ano ao fato, por geografia, ano e rede.

    A rede entra na chave do join: como a tabela de meta carrega a rede que ela
    cobre, a restricao por rede acontece sozinha -- linha de rede privada
    simplesmente nao encontra meta, em vez de depender de regra no codigo.
    """

    condicao = (
        (col("ano_referencia") == col("_ano_meta"))
        & (col("rede") == col("_rede_meta"))
    )

    if coluna_chave:
        condicao = condicao & (col(coluna_chave) == col("_chave_meta"))
    else:
        condicao = condicao & (col("_chave_meta") == lit(CHAVE_BRASIL))

    return (
        df
        .join(broadcast(df_meta_ano), condicao, how="left")
        .drop("_chave_meta", "_ano_meta", "_rede_meta")
        .withColumn(
            "gap_meta_do_ano_pp",
            col("taxa_alfabetizacao") - col("meta_alfabetizacao_do_ano")
        )
    )


def indicador_brasil(df_agregado, df_meta):
    """Indicador no nivel Brasil, calculado a partir do microdado de alunos.

    Nao existe silver agregada de Brasil, entao a taxa nacional e consolidada
    do microdado e sai marcada como ORIGEM_CALCULADA -- o numero precisa ser
    reconciliado com a taxa nacional publicada pelo INEP antes de virar
    indicador oficial.
    """

    df = consolida_alunos(df_agregado, [])

    df = df.select(
        col("ano_referencia"),
        col("serie"),
        col("serie_descricao"),
        col("rede"),
        col("rede_descricao"),
        col("taxa_alfabetizacao_calculada").alias("taxa_alfabetizacao"),
        col("qtd_alunos"),
        lit(ORIGEM_CALCULADA).alias("origem_indicador")
    )

    df = anexa_meta_do_ano(df, meta_do_ano(df_meta, NIVEL_BRASIL))

    return finaliza(df, NIVEL_BRASIL)


def build_metas_vs_resultado(
    df_indicador,
    df_meta,
    escopos_meta,
    coluna_chave,
    colunas_identificacao
):
    """Comparacao entre metas e resultados, em formato longo.

    A silver de meta ja e longa -- uma linha por escopo, geografia, revisao e
    ano de meta --, entao aqui e um join, nao mais um unpivot de 14 colunas.

    A revisao usada e a vigente no ano observado (ano_publicacao =
    ano_referencia): comparar o resultado de um ano com uma meta revisada
    depois seria anacronico.

    A rede entra na chave do join, entao a restricao por rede acontece sozinha:
    linha de rede privada nao encontra meta publica.
    """

    df_metas = (
        df_meta
        .filter(col("escopo").isin(escopos_meta))
        .select(
            col("escopo").alias("escopo_meta"),
            col("chave").alias("_chave_meta"),
            col("rede").alias("_rede_meta"),
            col("ano_publicacao").alias("_ano_publicacao"),
            col("ano_meta"),
            col("meta_alfabetizacao")
        )
    )

    # A meta nacional casa por chave fixa; a do proprio nivel, pela geografia.
    geografia = (
        (col("escopo_meta") == lit(NIVEL_BRASIL))
        & (col("_chave_meta") == lit(CHAVE_BRASIL))
    )

    if coluna_chave:
        geografia = geografia | (
            (col("escopo_meta") != lit(NIVEL_BRASIL))
            & (col("_chave_meta") == col(coluna_chave))
        )

    df = (
        df_indicador
        .join(
            broadcast(df_metas),
            geografia
            & (col("rede") == col("_rede_meta"))
            & (col("ano_referencia") == col("_ano_publicacao")),
            how="inner"
        )
        .select(
            "nivel_geografico",
            *colunas_identificacao,
            col("ano_referencia").alias("ano_observacao"),
            "serie",
            "serie_descricao",
            "rede",
            "rede_descricao",
            "taxa_alfabetizacao",
            "qtd_alunos",
            "origem_indicador",
            "escopo_meta",
            "ano_meta",
            "meta_alfabetizacao"
        )
        .filter(col("taxa_alfabetizacao").isNotNull())
    )

    df = (
        df
        .withColumn(
            "gap_pp",
            col("taxa_alfabetizacao") - col("meta_alfabetizacao")
        )
        .withColumn(
            "percentual_da_meta",
            100 * col("taxa_alfabetizacao") / col("meta_alfabetizacao")
        )
        .withColumn(
            "atingiu_meta",
            col("taxa_alfabetizacao") >= col("meta_alfabetizacao")
        )
        .withColumn(
            "meta_ja_vencida",
            col("ano_meta") <= col("ano_observacao")
        )
        .withColumn("ano", col("ano_observacao"))
        .withColumn("processed_at", current_timestamp())
    )

    return df


def anexa_meta_final(df, df_meta, escopo, coluna_chave=None):
    """Anexa a meta do ano final (2030), da revisao vigente no ano observado."""

    df_final = (
        df_meta
        .filter(
            (col("escopo") == lit(escopo))
            & (col("ano_meta") == lit(ANO_META_FINAL))
        )
        .select(
            col("chave").alias("_chave_final"),
            col("rede").alias("_rede_final"),
            col("ano_publicacao").alias("_ano_pub_final"),
            col("meta_alfabetizacao").alias("meta_alfabetizacao_final")
        )
    )

    condicao = (
        (col("rede") == col("_rede_final"))
        & (col("ano_referencia") == col("_ano_pub_final"))
    )

    if coluna_chave:
        condicao = condicao & (col(coluna_chave) == col("_chave_final"))
    else:
        condicao = condicao & (col("_chave_final") == lit(CHAVE_BRASIL))

    return (
        df
        .join(broadcast(df_final), condicao, how="left")
        .drop("_chave_final", "_rede_final", "_ano_pub_final")
        .withColumn(
            "gap_para_meta_final_pp",
            col("meta_alfabetizacao_final") - col("taxa_alfabetizacao")
        )
    )


def build_evolucao_temporal(
    df_indicador,
    df_meta,
    escopo,
    colunas_chave,
    coluna_chave
):
    """Evolucao temporal do indicador.

    A serie e por geografia, rede e serie escolar; as janelas comparam cada ano
    com o anterior observado e com o primeiro ano da serie. No nivel Brasil
    colunas_chave vem vazia, e a particao fica so em rede e serie.
    """

    particao = [*colunas_chave, "rede", "serie"]

    janela = Window.partitionBy(*particao).orderBy("ano_referencia")

    janela_completa = (
        Window
        .partitionBy(*particao)
        .orderBy("ano_referencia")
        .rowsBetween(Window.unboundedPreceding, Window.unboundedFollowing)
    )

    df = (
        df_indicador
        .withColumn("ano_anterior", lag("ano_referencia").over(janela))
        .withColumn(
            "taxa_ano_anterior",
            lag("taxa_alfabetizacao").over(janela)
        )
        .withColumn(
            "taxa_primeiro_ano",
            first("taxa_alfabetizacao", ignorenulls=True)
            .over(janela_completa)
        )
    )

    df = (
        df
        .withColumn(
            "variacao_pp",
            col("taxa_alfabetizacao") - col("taxa_ano_anterior")
        )
        .withColumn(
            "variacao_percentual",
            when(
                col("taxa_ano_anterior") > 0,
                100
                * (col("taxa_alfabetizacao") - col("taxa_ano_anterior"))
                / col("taxa_ano_anterior")
            )
        )
        .withColumn(
            "variacao_acumulada_pp",
            col("taxa_alfabetizacao") - col("taxa_primeiro_ano")
        )
        .withColumn("processed_at", current_timestamp())
    )

    return anexa_meta_final(df, df_meta, escopo, coluna_chave)


def contexto_municipio_ano_anterior(df_municipio):
    """Taxa do municipio no ano anterior, para usar como feature sem leakage.

    A taxa do proprio ano e calculada a partir dos mesmos alunos que compoem o
    target, entao usar o ano anterior evita vazar o alvo para o modelo.
    """

    return df_municipio.select(
        col("id_municipio").alias("_id_municipio_ctx"),
        (col("ano_referencia") + 1).alias("_ano_ctx"),
        col("rede").alias("_rede_ctx"),
        col("taxa_alfabetizacao").alias(
            "taxa_alfabetizacao_municipio_ano_anterior"
        ),
        col("media_portugues").alias(
            "media_portugues_municipio_ano_anterior"
        )
    )


def build_ml_aluno(df_alunos, df_municipio):
    """Feature table no grao de aluno, para classificacao.

    Target binario alfabetizado, features do proprio aluno mais contexto do
    municipio no ano anterior, e um split deterministico por hash do id_aluno
    para o treino ser reproduzivel entre execucoes.
    """

    df_contexto = contexto_municipio_ano_anterior(df_municipio)

    df = (
        df_alunos
        .filter(col("alfabetizado").isNotNull())
        .join(
            df_contexto,
            (col("id_municipio") == col("_id_municipio_ctx"))
            & (col("ano_referencia") == col("_ano_ctx"))
            & (col("rede") == col("_rede_ctx")),
            how="left"
        )
        .drop("_id_municipio_ctx", "_ano_ctx", "_rede_ctx")
    )

    # 0..99 estavel por aluno: mesmo id cai sempre na mesma faixa.
    df = df.withColumn(
        "_faixa_split",
        pmod(spark_hash(col("id_aluno")), lit(100))
    )

    split = None

    for nome, inicio, fim in SPLITS_ML:
        condicao = (
            (col("_faixa_split") >= lit(inicio))
            & (col("_faixa_split") < lit(fim))
        )
        split = (
            when(condicao, lit(nome)) if split is None
            else split.when(condicao, lit(nome))
        )

    df = df.withColumn("dataset_split", split).drop("_faixa_split")

    df = df.select(
        col("id_aluno"),
        col("id_escola"),
        col("id_municipio"),
        col("nome_municipio"),
        col("sigla_uf"),
        col("ano_referencia"),
        col("serie"),
        col("rede"),
        col("rede_descricao"),
        col("caderno"),
        col("presenca"),
        col("preenchimento_caderno"),
        col("proficiencia"),
        col("peso_aluno"),
        col("taxa_alfabetizacao_municipio_ano_anterior"),
        col("media_portugues_municipio_ano_anterior"),
        col("dataset_split"),
        col("alfabetizado")
    )

    df = df.withColumn("ano", col("ano_referencia"))
    df = df.withColumn("processed_at", current_timestamp())

    return df


def validate(nome, df, colunas_chave):

    print("========================================")
    print(f"VALIDAÇÃO DA GOLD - {nome}")
    print("========================================")

    print("\nQuantidade de registros:")
    print(df.count())

    print("\nSchema:")
    df.printSchema()

    print("\nRegistros por chave:")
    df.groupBy(*colunas_chave).count().orderBy(*colunas_chave).show(
        50, truncate=False
    )

    print("\nPrimeiros registros:")
    df.show(10, truncate=False)


def write(df, output_path, particoes, arquivo_unico=False):

    print(f"\nGravando: {output_path}")

    writer = df.coalesce(1).write if arquivo_unico else df.write

    (
        writer
        .mode("overwrite")
        .partitionBy(*particoes)
        .option("compression", "snappy")
        .parquet(output_path)
    )


def processa_nivel(
    nome,
    df_indicador,
    df_meta,
    escopo,
    escopos_meta,
    colunas_identificacao,
    colunas_chave,
    coluna_chave,
    output_indicador,
    output_metas,
    output_evolucao
):
    """Gera e grava os tres datasets analiticos de um nivel geografico."""

    validate(f"INDICADOR - {nome}", df_indicador, ["ano"])
    write(df_indicador, output_indicador, ["ano"], arquivo_unico=True)

    df_metas = build_metas_vs_resultado(
        df_indicador, df_meta, escopos_meta, coluna_chave,
        colunas_identificacao
    )

    validate(f"METAS VS RESULTADO - {nome}", df_metas, ["escopo_meta"])
    write(df_metas, output_metas, ["ano"], arquivo_unico=True)

    df_evolucao = build_evolucao_temporal(
        df_indicador, df_meta, escopo, colunas_chave, coluna_chave
    )

    validate(f"EVOLUÇÃO TEMPORAL - {nome}", df_evolucao, ["ano"])
    write(df_evolucao, output_evolucao, ["ano"], arquivo_unico=True)


def main():

    args = getResolvedOptions(
        sys.argv, ['JOB_NAME', 'SILVER_BUCKET', 'GOLD_BUCKET']
    )
    configure_paths(args)

    sc = SparkContext()
    glueContext = GlueContext(sc)
    spark_session = glueContext.spark_session
    job = Job(glueContext)
    job.init(args['JOB_NAME'], args)

    print("========================================")
    print("INICIANDO PROCESSAMENTO GOLD")
    print("========================================")

    df_uf = load(INPUT_SILVER_UF, spark_session)
    df_municipio = load(INPUT_SILVER_MUNICIPIO, spark_session)
    df_alunos = load(INPUT_SILVER_ALUNOS, spark_session)
    df_meta = load(INPUT_SILVER_META, spark_session)

    valida_schema("UF", df_uf, COLUNAS_OBRIGATORIAS_UF)
    valida_schema("MUNICÍPIO", df_municipio, COLUNAS_OBRIGATORIAS_MUNICIPIO)
    valida_schema("ALUNOS", df_alunos, COLUNAS_OBRIGATORIAS_ALUNOS)
    valida_schema("META", df_meta, COLUNAS_OBRIGATORIAS_META)

    # Pequena e usada em todos os niveis: vale materializar.
    df_meta = df_meta.cache()

    # Uma unica passada pelo microdado alimenta a contagem de alunos dos tres
    # niveis e a taxa calculada do Brasil.
    df_agregado = agrega_alunos(df_alunos).cache()

    # O Brasil e a UF viram referencia dos niveis abaixo, entao sao construidos
    # antes e materializados: sem cache, cada comparativo os recomputaria.
    df_indicador_brasil = indicador_brasil(df_agregado, df_meta).cache()

    df_ref_brasil = referencia_brasil(df_indicador_brasil)

    df_indicador_uf = indicador_uf(
        df_uf, df_agregado, df_meta, df_ref_brasil
    ).cache()

    df_ref_uf = referencia_uf(df_indicador_uf)

    df_indicador_municipio = indicador_municipio(
        df_municipio, df_agregado, df_meta, df_ref_uf, df_ref_brasil
    ).cache()

    processa_nivel(
        nome="MUNICÍPIO",
        df_meta=df_meta,
        escopo=NIVEL_MUNICIPIO,
        df_indicador=df_indicador_municipio,
        escopos_meta=[NIVEL_MUNICIPIO, NIVEL_BRASIL],
        colunas_identificacao=["id_municipio", "nome_municipio", "sigla_uf"],
        colunas_chave=["id_municipio"],
        coluna_chave="id_municipio",
        output_indicador=OUTPUT_GOLD_INDICADOR_MUNICIPIO,
        output_metas=OUTPUT_GOLD_METAS_MUNICIPIO,
        output_evolucao=OUTPUT_GOLD_EVOLUCAO_MUNICIPIO
    )

    processa_nivel(
        nome="UF",
        df_meta=df_meta,
        escopo=NIVEL_UF,
        df_indicador=df_indicador_uf,
        escopos_meta=[NIVEL_UF, NIVEL_BRASIL],
        colunas_identificacao=["sigla_uf"],
        colunas_chave=["sigla_uf"],
        coluna_chave="sigla_uf",
        output_indicador=OUTPUT_GOLD_INDICADOR_UF,
        output_metas=OUTPUT_GOLD_METAS_UF,
        output_evolucao=OUTPUT_GOLD_EVOLUCAO_UF
    )

    processa_nivel(
        nome="BRASIL",
        df_meta=df_meta,
        escopo=NIVEL_BRASIL,
        df_indicador=df_indicador_brasil,
        escopos_meta=[NIVEL_BRASIL],
        colunas_identificacao=[],
        colunas_chave=[],
        coluna_chave=None,
        output_indicador=OUTPUT_GOLD_INDICADOR_BRASIL,
        output_metas=OUTPUT_GOLD_METAS_BRASIL,
        output_evolucao=OUTPUT_GOLD_EVOLUCAO_BRASIL
    )

    df_indicador_municipio.unpersist()
    df_indicador_uf.unpersist()
    df_indicador_brasil.unpersist()
    df_agregado.unpersist()
    df_meta.unpersist()

    df_ml = build_ml_aluno(df_alunos, df_municipio)

    validate("ML ALUNO", df_ml, ["dataset_split", "ano"])
    write(df_ml, OUTPUT_GOLD_ML_ALUNO, ["ano"])

    print("\n========================================")
    print("GOLD CONCLUÍDA COM SUCESSO")
    print("========================================")

    job.commit()


if __name__ == "__main__":
    main()
