/*
    Pergunta: 3. Quais UFS apresentam melhores resultados em relação às metas?

*/

WITH trajetoria AS (
    SELECT
        sigla_uf,
        ano_meta,
        taxa_alfabetizacao,
        meta_alfabetizacao,
        gap_pp,
        percentual_da_meta,
        atingiu_meta,
        meta_ja_vencida
    FROM
        "tc2-glue-database-table"."metas_vs_resultado_uf"
    WHERE
        ano = '2024'
        AND escopo_meta = 'uf'
),

ranqueado AS (
    SELECT
        trajetoria.*,
        MAX(CASE WHEN ano_meta = 2030 THEN gap_pp END)
            OVER (PARTITION BY sigla_uf)              AS gap_2030_pp,
        SUM(CASE WHEN atingiu_meta THEN 1 ELSE 0 END)
            OVER (PARTITION BY sigla_uf)              AS degraus_alcancados
    FROM
        trajetoria
)

SELECT
    sigla_uf,
    ano_meta,
    ROUND(taxa_alfabetizacao, 1)                      AS taxa_alfabetizacao,
    ROUND(meta_alfabetizacao, 1)                      AS meta_alfabetizacao,
    ROUND(gap_pp, 1)                                  AS gap_pp,
    ROUND(percentual_da_meta, 1)                      AS percentual_da_meta,
    atingiu_meta,
    meta_ja_vencida,
    degraus_alcancados,
    ROUND(gap_2030_pp, 1)                             AS gap_2030_pp
FROM
    ranqueado
ORDER BY
    gap_2030_pp DESC,
    degraus_alcancados DESC,
    sigla_uf,
    ano_meta;
