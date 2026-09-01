# Glue Crawlers e Data Catalog

O database `tc2-alfabetizacao` reúne as nove tabelas produzidas na camada Gold.
Cada crawler aponta para um único prefixo, evitando que estruturas diferentes
sejam combinadas na mesma tabela.

| Crawler | Prefixo Gold | Tabela esperada |
| --- | --- | --- |
| `tc2-crawler-indicador-brasil` | `indicador_brasil/` | `indicador_brasil` |
| `tc2-crawler-indicador-municipio` | `indicador_municipio/` | `indicador_municipio` |
| `tc2-crawler-indicador-uf` | `indicador_uf/` | `indicador_uf` |
| `tc2-crawler-evolucao-brasil` | `evolucao_temporal_brasil/` | `evolucao_temporal_brasil` |
| `tc2-crawler-evolucao-municipio` | `evolucao_temporal_municipio/` | `evolucao_temporal_municipio` |
| `tc2-crawler-evolucao-uf` | `evolucao_temporal_uf/` | `evolucao_temporal_uf` |
| `tc2-crawler-metas-brasil` | `metas_vs_resultado_brasil/` | `metas_vs_resultado_brasil` |
| `tc2-crawler-metas-municipio` | `metas_vs_resultado_municipio/` | `metas_vs_resultado_municipio` |
| `tc2-crawler-metas-uf` | `metas_vs_resultado_uf/` | `metas_vs_resultado_uf` |

Todos usam a `LabRole`, executam `CRAWL_EVERYTHING`, atualizam o schema no
Data Catalog e apenas registram exclusões (`DeleteBehavior: LOG`). O lineage do
crawler fica desabilitado, reproduzindo a configuração validada no ambiente.

As configurações legíveis ficam em `infra/aws/crawlers/`. A fonte oficial de
implantação continua sendo `infra/aws/templates/application.yaml`.

Depois da etapa Gold, a Step Function inicia os nove crawlers em paralelo,
aguarda cada execução e só conclui quando todos retornam `READY` com o último
crawl em `SUCCEEDED`.
