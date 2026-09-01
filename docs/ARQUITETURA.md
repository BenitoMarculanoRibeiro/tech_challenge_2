# Arquitetura

A solução implementa um pipeline de dados baseado na arquitetura **Medallion**,
organizado nas camadas **Bronze**, **Silver** e **Gold**. A orquestração do
processamento é realizada por uma **AWS Step Functions Standard**.

## Fluxo principal

```text
 EXECUÇÃO DIRETA                         POST /metas
        │                                    │
        │                                    ▼
        │                              API `api-metas`
        │                                    │
        │                                    ▼
        │                    `streamMetaAlfabetizacaoBrasil`
        │                              │             │
        │                              ▼             │
        │                    S3 Bronze — metas       │
        │                                            │
        └──────────────────────┬─────────────────────┘
                               ▼
                 START `pipeline-alfabetizacao`
                               │
                               ▼
                    ┌─────────────────────┐
                    │ PARALLEL — INGESTÃO │
                    └──────────┬──────────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
                    ▼                     ▼
 batchCargaBaseDadosIndicador    batchCargaTabelaMunicipioIBGE
       Alfabetizacao
                    │                     │
                    └──────────┬──────────┘
                               │
                               ▼
                        ┌─────────────┐
                        │  S3 BRONZE  │
                        └──────┬──────┘
                               │
                               ▼
                ┌─────────────────────────────┐
                │ PARALLEL — BRONZE → SILVER │
                └──────────────┬──────────────┘
                               │
             ┌─────────────────┼─────────────────┐
             │                 │                 │
       ┌─────┴─────┐     ┌─────┴─────┐     ┌─────┴─────┐
       │           │     │           │     │           │
       ▼           ▼     ▼           ▼     │           │
   Glue UF   Glue Município      Glue Aluno       Glue Meta
       │           │                 │                 │
       └───────────┴────────┬────────┴─────────────────┘
                            │
                            ▼
                     ┌─────────────┐
                     │  S3 SILVER  │
                     └──────┬──────┘
                            │
                            ▼
                       Glue Gold
                            │
                            ▼
                     ┌─────────────┐
                     │   S3 GOLD   │
                     └──────┬──────┘
                            │
                            ▼
                  ┌─────────────────────┐
                  │  PREPARAR CRAWLERS  │
                  │      9 nomes        │
                  └──────────┬──────────┘
                            │
                            ▼
              ┌───────────────────────────┐
              │ MAP — 9 CRAWLERS EM       │
              │ PARALELO                   │
              └─────────────┬─────────────┘
                            │
       ┌────────────────────┼────────────────────┐
       │                    │                    │
       ▼                    ▼                    ▼
  3 Indicadores       3 Evoluções          3 Metas ×
 Brasil/Município/UF Brasil/Município/UF Resultado
       │                    │                    │
       └────────────────────┼────────────────────┘
                            │
                            ▼
             iniciar → aguardar → consultar
                            │
                            ▼
             READY + último crawl SUCCEEDED?
                    │               │
                   sim             não
                    │               │
                    ▼               ▼
             Glue Data Catalog   Falha explícita
                    │
                    ▼
                  Athena
```

A **Step Function Standard** orquestra o pipeline em quatro estágios: ingestão,
Silver, Gold e catalogação.

Primeiro, executa em paralelo as Lambdas
`batchCargaBaseDadosIndicadorAlfabetizacao` e
`batchCargaTabelaMunicipioIBGE`, responsáveis pela ingestão na Bronze.

Após a conclusão de ambas, são iniciados em paralelo os quatro AWS Glue Jobs
responsáveis pelas transformações Bronze → Silver:

- `bronze-to-silver-uf`;
- `bronze-to-silver-municipios`;
- `bronze-to-silver-alunos`;
- `bronze-to-silver-metas`.

A etapa Gold somente é iniciada após a conclusão das quatro transformações
Silver. O job `silver-to-gold` consolida os dados tratados e grava o resultado na camada
Gold.

Por fim, os **nove AWS Glue Crawlers** catalogam em paralelo os indicadores,
evoluções temporais e comparações entre metas e resultados, permitindo sua
consulta por meio do **Amazon Athena**.

## Fluxo de prova de conceito

Além do fluxo principal, a arquitetura possui um mecanismo simplificado para
demonstrar processamento orientado a eventos.

```text
 POST /metas                         EventBridge
      │                        source = com.tc2
      ▼                        detail-type = metas
 API `api-metas`                         │
      │                                  │
      └───────────────┬──────────────────┘
                      ▼
      `streamMetaAlfabetizacaoBrasil`
                  │          │
                  ▼          │ start_execution
        S3 Bronze — metas     │
                             ▼
              `pipeline-alfabetizacao`
                             │
                             ▼
              Bronze → Silver → Gold
                             │
                             ▼
                       9 crawlers
```

A Lambda `streamMetaAlfabetizacaoBrasil` pode ser acionada pelo `POST /metas`
da API `api-metas` ou por eventos do EventBridge. Ela grava os dados recebidos
em formato Parquet na Bronze e chama `StartExecution` da Step Function
`pipeline-alfabetizacao`. Portanto, o POST não encerra na ingestão: ele aciona
o processamento Bronze → Silver → Gold e a catalogação pelos nove crawlers.

O endpoint foi mantido sem autenticação exclusivamente para simplificar a
demonstração acadêmica. Há throttling baixo para limitar seu uso, mas essa
configuração **não é adequada para um ambiente de produção**.

## Arquitetura Medallion

| Camada | Responsabilidade |
| --- | --- |
| **Bronze** | Persistência dos dados ingeridos com mínima transformação |
| **Silver** | Limpeza, padronização e organização dos dados |
| **Gold** | Dados consolidados e preparados para consumo analítico |

A separação em camadas permite preservar os dados originalmente ingeridos,
aplicar transformações de forma controlada e disponibilizar uma representação
final adequada para análise.

## Decisões de reprodução

- Infraestrutura definida em **CloudFormation YAML**, sem dependência de CDK,
  SAM ou Terraform.
- Bootstrap separado para criação do bucket utilizado pelos artefatos.
- Buckets com prefixos fixos e namespace automático de conta/região, por
  exemplo `bucket-gold-<conta>-<região>-an`.
- Utilização da `LabRole` disponibilizada pelo AWS Academy, evitando a criação
  de roles incompatíveis com as restrições do Learner Lab.
- Código-fonte mantido em `glue/` e `infra/lambda/`.
- Artefatos derivados — ZIPs, layers e cópias destinadas ao S3 — gerados em
  `.build/`, mantendo-os separados do código-fonte.

## Escopo da entrega

A entrega reproduz os recursos funcionais utilizados pelo grupo no ambiente do
Learner Lab:

- **3 Lambdas** da aplicação;
- **5 AWS Glue Jobs 5.1**;
- **9 Glue Crawlers**;
- **1 database e 9 tabelas no Glue Data Catalog**;
- **1 Step Function**;
- **1 API HTTP**;
- **1 regra EventBridge**.

Recursos administrativos do **AWS Academy Learner Lab** não integram a
arquitetura da aplicação e não devem ser reproduzidos pelo projeto.
