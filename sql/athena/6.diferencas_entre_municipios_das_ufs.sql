/*
    Pergunta: 6. Existem diferenças relevantes entre municípios das diferentes UFs?

    Fonte: indicador_municipio, onde o gold_job já deixou as duas comparações prontas na
    linha do município -- diferenca_pp_vs_uf e diferenca_pp_vs_brasil, casadas por ano,
    série e rede. Nenhum join necessário.

    A pergunta tem duas metades, e as duas colunas respondem uma cada:

    - ENTRE UFs, via diferenca_pp_vs_brasil: onde os municípios de cada estado estão em
      relação ao país. É a distância de um estado para outro.
    - DENTRO da UF, via diferenca_pp_vs_uf: o quanto os municípios se espalham em torno da
      própria média estadual. amplitude_p10_p90_pp usa percentis, não mínimo e máximo, que
      nas pontas costumam ser município pequeno -- ruído, não desigualdade.

    As duas últimas colunas fecham a resposta: se amplitude_entre_ufs_pp for muito maior
    que amplitude_interna_media_pp, a UF explica o desempenho do município. Se for da mesma
    ordem ou menor, a diferença que importa está dentro dos estados, não entre eles.

    Agrupa por série porque a comparação só vale dentro do mesmo recorte; com uma série só
    na gold, o resultado é o mesmo de não agrupar. Rede 3 (Municipal) para acompanhar as
    outras queries da pasta -- trocar para 5 (Pública) é uma linha.
*/

WITH por_uf AS (
    SELECT
        sigla_uf,
        serie,
        COUNT(*)                                            AS municipios,
        COUNT(diferenca_pp_vs_brasil)                       AS municipios_comparaveis,
        AVG(taxa_alfabetizacao)                             AS taxa_media_municipal,

        -- entre UFs
        AVG(diferenca_pp_vs_brasil)                         AS media_vs_brasil_pp,
        APPROX_PERCENTILE(diferenca_pp_vs_brasil, 0.5)      AS mediana_vs_brasil_pp,
        SUM(CASE WHEN diferenca_pp_vs_brasil > 0 THEN 1 ELSE 0 END)
                                                            AS municipios_acima_do_brasil,
        100.0 * SUM(CASE WHEN diferenca_pp_vs_brasil > 0 THEN 1 ELSE 0 END)
            / NULLIF(COUNT(diferenca_pp_vs_brasil), 0)      AS percentual_acima_do_brasil,

        -- dentro da UF
        STDDEV(diferenca_pp_vs_uf)                          AS desvio_interno_pp,
        APPROX_PERCENTILE(diferenca_pp_vs_uf, 0.1)          AS p10_vs_uf_pp,
        APPROX_PERCENTILE(diferenca_pp_vs_uf, 0.9)          AS p90_vs_uf_pp,
        APPROX_PERCENTILE(diferenca_pp_vs_uf, 0.9)
            - APPROX_PERCENTILE(diferenca_pp_vs_uf, 0.1)    AS amplitude_p10_p90_pp
    FROM
        "tc2-glue-database-table"."indicador_municipio"
    WHERE
        ano = '2024'
        AND rede_descricao = 'Municipal'
        AND taxa_alfabetizacao IS NOT NULL
    GROUP BY
        sigla_uf,
        serie,
        serie_descricao
)

SELECT
    sigla_uf,
    municipios,
    municipios_comparaveis,
    ROUND(taxa_media_municipal, 1)                          AS taxa_media_municipal,
    ROUND(media_vs_brasil_pp, 1)                            AS media_vs_brasil_pp,
    ROUND(mediana_vs_brasil_pp, 1)                          AS mediana_vs_brasil_pp,
    municipios_acima_do_brasil,
    ROUND(percentual_acima_do_brasil, 1)                    AS percentual_acima_do_brasil,
    ROUND(desvio_interno_pp, 1)                             AS desvio_interno_pp,
    ROUND(p10_vs_uf_pp, 1)                                  AS p10_vs_uf_pp,
    ROUND(p90_vs_uf_pp, 1)                                  AS p90_vs_uf_pp,
    ROUND(amplitude_p10_p90_pp, 1)                          AS amplitude_p10_p90_pp,

    -- constantes dentro da série: a resposta da pergunta em dois números
    ROUND(
        MAX(media_vs_brasil_pp) OVER (PARTITION BY serie)
        - MIN(media_vs_brasil_pp) OVER (PARTITION BY serie), 1)
                                                            AS amplitude_entre_ufs_pp,
    ROUND(AVG(amplitude_p10_p90_pp) OVER (PARTITION BY serie), 1)
                                                            AS amplitude_interna_media_pp
FROM
    por_uf
ORDER BY
    serie,
    media_vs_brasil_pp DESC,
    sigla_uf;
