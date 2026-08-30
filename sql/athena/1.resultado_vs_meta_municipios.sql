/*
    Pergunta: 1. Qual a diferença entre resultado e meta para cada município/período? 

    Buscou-se em metas_vs_resultado_municipio resultados específicos de 2024 e rede municipal, comparando a taxa de alfabetização vs
meta_afbatetização do mesmo ano. Como é uma pergunta abrangente, não há ordenação na query. 

*/ 

SELECT
    ano,
    sigla_uf,
    nome_municipio,
    rede_descricao,
    taxa_alfabetizacao,
    meta_alfabetizacao,
    gap_pp,
    atingiu_meta,
    ano_meta
FROM
    "tc2-glue-database-table"."metas_vs_resultado_municipio"
WHERE
    ano = '2024'
    AND ano_meta = 2024
    AND ano_meta IS NOT NULL
    AND rede_descricao = 'Municipal';
