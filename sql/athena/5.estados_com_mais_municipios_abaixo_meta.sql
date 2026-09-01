/*
    Pergunta: 5. Quais estados concentram mais municípios abaixo da meta municipal?

    Abaixo da meta = NOT atingiu_meta, contra a meta vigente (ano_meta = 2024). Para a
    mesma pergunta contra o alvo final, troque ano_meta para 2030.

    A ordenação é por número absoluto, como a pergunta pede -- mas UF grande tende ao topo
    só por ter mais municípios. percentual_abaixo mostra a intensidade dentro do estado, e
    percentual_do_total / acumulado_nacional mostram a concentração de fato: quantas UFs
    respondem pela maior parte dos municípios atrasados do país.
*/

WITH meta_vigente AS (
    SELECT
        sigla_uf,
        gap_pp,
        atingiu_meta
    FROM
        "tc2-alfabetizacao"."metas_vs_resultado_municipio"
    WHERE
        ano = '2024'
        AND escopo_meta = 'municipio'
        AND ano_meta = 2024
),

por_uf AS (
    SELECT
        sigla_uf,
        COUNT(*)                                          AS municipios_com_meta,
        SUM(CASE WHEN NOT atingiu_meta THEN 1 ELSE 0 END) AS municipios_abaixo,
        100.0 * SUM(CASE WHEN NOT atingiu_meta THEN 1 ELSE 0 END) / COUNT(*)
                                                          AS percentual_abaixo,
        AVG(CASE WHEN NOT atingiu_meta THEN gap_pp END)   AS gap_medio_dos_abaixo,
        MIN(gap_pp)                                       AS pior_gap_pp
    FROM
        meta_vigente
    GROUP BY
        sigla_uf
)

SELECT
    sigla_uf,
    municipios_com_meta,
    municipios_abaixo,
    ROUND(percentual_abaixo, 1)                           AS percentual_abaixo,
    ROUND(100.0 * municipios_abaixo / SUM(municipios_abaixo) OVER (), 1)
                                                          AS percentual_do_total,
    ROUND(
        100.0 * SUM(municipios_abaixo) OVER (
            ORDER BY municipios_abaixo DESC, sigla_uf
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) / SUM(municipios_abaixo) OVER (), 1)            AS acumulado_nacional,
    ROUND(gap_medio_dos_abaixo, 1)                        AS gap_medio_dos_abaixo,
    ROUND(pior_gap_pp, 1)                                 AS pior_gap_pp
FROM
    por_uf
ORDER BY
    municipios_abaixo DESC,
    percentual_abaixo DESC,
    sigla_uf;
