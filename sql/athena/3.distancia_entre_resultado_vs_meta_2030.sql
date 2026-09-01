/*
    Pergunta: 3. Como a distância entre resultado e meta evolui até 2030?

    Em vez de uma linha por município e ano de meta, resume o país em sete linhas: uma
    por degrau até 2030, mostrando quantos municípios ainda o alcançam com o resultado
    de hoje e o quanto a distância média cresce a cada ano.

*/

SELECT
    ano_meta,
    COUNT(*)                                          AS municipios,    
    SUM(CASE WHEN atingiu_meta THEN 1 ELSE 0 END)     AS ja_alcancam_a_meta,
    ROUND(100.0 * SUM(CASE WHEN atingiu_meta THEN 1 ELSE 0 END) / COUNT(*), 1)
                                                      AS percentual_que_alcanca,
    ROUND(AVG(meta_alfabetizacao), 1)                 AS meta_media,
    ROUND(AVG(taxa_alfabetizacao), 1)                 AS taxa_media_observada,
    ROUND(AVG(gap_pp), 1)                             AS gap_medio_pp,
    ROUND(APPROX_PERCENTILE(gap_pp, 0.5), 1)          AS gap_mediano_pp
FROM
    "tc2-alfabetizacao"."metas_vs_resultado_municipio"
WHERE
    ano = '2024'
    AND escopo_meta = 'municipio'
    AND rede_descricao = 'Municipal'
GROUP BY
    ano_meta
ORDER BY
    ano_meta;
