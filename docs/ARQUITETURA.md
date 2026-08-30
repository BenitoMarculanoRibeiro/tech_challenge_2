# Arquitetura

A solução implementa um pipeline de dados baseado na arquitetura **Medallion**,
organizado nas camadas **Bronze**, **Silver** e **Gold**. A orquestração do
processamento é realizada por uma **AWS Step Functions Standard**.

## Fluxo principal

```text
                              START
                                │
                                ▼
                    ┌─────────────────────┐
                    │ PARALLEL — INGESTÃO │
                    └──────────┬──────────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
                    ▼                     ▼
             Lambda carga        Lambda carga_municipios
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
                 Glue Crawler / Data Catalog
                            │
                            ▼
                          Athena
```

A **Step Function Standard** orquestra o pipeline em três estágios.

Primeiro, executa em paralelo as Lambdas `carga` e `carga_municipios`,
responsáveis pela ingestão dos dados na camada Bronze.

Após a conclusão de ambas, são iniciados em paralelo os quatro AWS Glue Jobs
responsáveis pelas transformações Bronze → Silver:

- `bronze_to_silver_uf`;
- `bronze_to_silver_municipio`;
- `bronze_to_silver_aluno`;
- `bronze_to_silver_meta`.

A etapa Gold somente é iniciada após a conclusão das quatro transformações
Silver. O job `gold` consolida os dados tratados e grava o resultado na camada
Gold.

Por fim, o **AWS Glue Crawler** cataloga os dados disponibilizados, permitindo
sua consulta por meio do **Amazon Athena**.

## Fluxo de prova de conceito

Além do fluxo principal, a arquitetura possui um mecanismo simplificado para
demonstrar processamento orientado a eventos.

```text
POST /metas
     │
     ▼
API Gateway
     │
     ▼
Lambda metas ──────────────┐
     │                     │
     ▼                     │
 S3 Bronze                 │
                           │
                           ▼
                    Step Functions


EventBridge
source = com.tc2
detail-type = metas
     │
     ▼
Lambda metas
```

A Lambda `metas` pode ser acionada pelo endpoint HTTP ou por eventos do
EventBridge. Ela grava os dados recebidos em formato Parquet na camada Bronze
e inicia o pipeline de processamento.

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
- Nomes dos buckets de dados gerados automaticamente pela infraestrutura.
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
- **1 Glue Crawler**;
- **1 database/tabela no Glue Data Catalog**;
- **1 Step Function**;
- **1 API HTTP**;
- **1 regra EventBridge**.

Recursos administrativos do **AWS Academy Learner Lab** não integram a
arquitetura da aplicação e não devem ser reproduzidos pelo projeto.
