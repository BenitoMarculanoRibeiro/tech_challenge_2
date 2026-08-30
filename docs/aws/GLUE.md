# Glue no projeto

O projeto utiliza cinco jobs AWS Glue 5.1. Quatro realizam as transformações
Bronze-to-Silver e o quinto consolida os dados da camada Gold.

## Jobs

| Job | Etapa | Responsabilidade |
| --- | --- | --- |
| `bronze_to_silver_uf_job` | Bronze → Silver | Tratamento dos dados de UF |
| `bronze_to_silver_municipio_job` | Bronze → Silver | Tratamento dos dados de municípios |
| `bronze_to_silver_aluno_job` | Bronze → Silver | Tratamento dos dados de alunos |
| `bronze_to_silver_meta_job` | Bronze → Silver | Tratamento dos dados de metas |
| `gold_job` | Silver → Gold | Consolidação dos dados para consumo analítico |

Os scripts permanecem separados por etapa para evidenciar a responsabilidade
de cada transformação, mesmo sendo publicados juntos no bucket de artefatos.

## Configuração

Todos os jobs utilizam Glue 5.1 e workers G.1X. Por padrão, são utilizados
10 workers.

O parâmetro `GlueNumberOfWorkers` permite configurar de 2 a 10 workers,
possibilitando reduzir os recursos utilizados durante testes sem alterar os
scripts de transformação.

Os buckets são recebidos pelos argumentos:

- `--BRONZE_BUCKET`
- `--SILVER_BUCKET`
- `--GOLD_BUCKET`

Dessa forma, os scripts não dependem de nomes fixos de buckets e podem ser
utilizados em diferentes implantações da infraestrutura.

A sequência de execução e o paralelismo entre os jobs estão documentados em
`../ARQUITETURA.md`.

As decisões de dimensionamento e otimização dos jobs estão documentadas em
`otimizacao/glue_resumo.md`.