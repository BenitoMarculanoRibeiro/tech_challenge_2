# Configurações dos Glue Crawlers

Esta pasta mantém uma representação legível e auditável dos nove crawlers da
camada Gold. Cada arquivo registra somente a configuração necessária para
reproduzir o recurso: nome, database, role, destino S3 e políticas de catálogo.

Os campos operacionais exportados pela AWS (`State`, `LastCrawl`, datas, logs e
versão) foram omitidos porque são resultados de execução, não configuração.

## Fonte de implantação

O arquivo `infra/aws/templates/application.yaml` continua sendo a fonte oficial
de implantação. Estes JSONs servem para revisão acadêmica e são conferidos pelo
script `tools/validate-crawler-configs.ps1` para evitar divergência entre:

1. os nove arquivos desta pasta;
2. os recursos `AWS::Glue::Crawler` do CloudFormation;
3. a lista executada pela Step Function.

`$GOLD_BUCKET` representa o bucket Gold recebido por referência do
CloudFormation. Nenhum nome físico de bucket ou dado do ambiente foi copiado do
backup.

| Arquivo | Tabela/prefixo Gold |
| --- | --- |
| `evolucao_temporal_brasil.json` | `evolucao_temporal_brasil/` |
| `evolucao_temporal_municipio.json` | `evolucao_temporal_municipio/` |
| `evolucao_temporal_uf.json` | `evolucao_temporal_uf/` |
| `indicador_brasil.json` | `indicador_brasil/` |
| `indicador_municipio.json` | `indicador_municipio/` |
| `indicador_uf.json` | `indicador_uf/` |
| `metas_vs_resultado_brasil.json` | `metas_vs_resultado_brasil/` |
| `metas_vs_resultado_municipio.json` | `metas_vs_resultado_municipio/` |
| `metas_vs_resultado_uf.json` | `metas_vs_resultado_uf/` |
