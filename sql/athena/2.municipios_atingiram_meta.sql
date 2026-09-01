/*
    Pergunta: 2. Quais municípios atingiram/superaram as metas? 

    Buscou-se em metas_vs_resultado_municipio resultados específicos de 2024 da rede Municipal, filtrando cidades com "atingiu_meta" = TRUE. 
    Aqui ordedou-se os dados da cidade que mais superou a cidade para a que menos superou. 
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
    "tc2-alfabetizacao"."metas_vs_resultado_municipio"
WHERE
    ano = '2024'
    AND ano_meta = 2024
    AND ano_meta IS NOT NULL
    AND atingiu_meta = TRUE
    AND rede_descricao = 'Municipal'
ORDER BY 
    gap_pp DESC;
