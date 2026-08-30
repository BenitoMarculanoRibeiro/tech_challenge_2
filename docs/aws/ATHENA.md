# Athena no projeto

O **Amazon Athena** é utilizado como camada de consulta analítica sobre os dados
processados e armazenados no Amazon S3.

Após a execução do pipeline Bronze → Silver → Gold, o AWS Glue Crawler atualiza
o catálogo de dados. A partir desse catálogo, o Athena permite executar consultas
SQL diretamente sobre os arquivos armazenados na camada Gold.

## Fluxo de consulta

```text
S3 Gold
   │
   ▼
AWS Glue Crawler
   │
   ▼
Glue Data Catalog
   │
   ▼
Amazon Athena
   │
   ▼
Consultas SQL
```

O Athena não movimenta os dados para outro banco. As consultas são executadas
diretamente sobre os arquivos armazenados no Amazon S3 utilizando os metadados
registrados no AWS Glue Data Catalog.

## Utilização no projeto

O Athena pode ser utilizado após a conclusão do pipeline para validar se os
dados consolidados na camada Gold foram corretamente catalogados e estão
disponíveis para consulta.

Uma consulta simples de validação pode ser executada no banco criado pelo
projeto:

```sql
SELECT *
FROM <database>.<tabela>
LIMIT 10;
```

Os nomes efetivos do database e da tabela devem ser consultados no AWS Glue
Data Catalog após a execução do crawler.

## Configuração dos resultados

Antes de executar consultas no Athena, é necessário configurar um local para
armazenamento dos resultados das queries.

Esse local deve apontar para um bucket ou prefixo S3 disponível no ambiente de
execução.

Exemplo:

```text
s3://<bucket-de-resultados-athena>/
```

Essa configuração pode ser realizada diretamente nas configurações do
workgroup utilizado para executar as consultas.

## Workgroup

O projeto pode utilizar o workgroup padrão:

```text
primary
```

Não é necessário criar um workgroup dedicado apenas para a demonstração
acadêmica, embora essa separação possa ser adotada em ambientes produtivos para
controle de permissões, custos e configurações específicas.

## Custos e boas práticas

O Athena cobra com base na quantidade de dados analisados pelas consultas.

Para reduzir processamento desnecessário durante os testes:

- utilizar `LIMIT` nas consultas de validação;
- selecionar somente as colunas necessárias;
- evitar consultas repetidas sobre grandes volumes;
- utilizar arquivos em formatos colunares, como Parquet;
- aproveitar particionamento quando aplicável.

Como os dados processados pelo projeto são armazenados em Parquet, o Athena pode
ler apenas as colunas necessárias para uma consulta, reduzindo o volume de dados
analisado quando comparado a formatos orientados a linha.

## Papel na arquitetura

O Athena representa a etapa de consumo e validação analítica do pipeline:

```text
Fontes
   │
   ▼
Bronze
   │
   ▼
Silver
   │
   ▼
Gold
   │
   ▼
Glue Data Catalog
   │
   ▼
Athena
```

Dessa forma, a solução mantém o processamento e o armazenamento desacoplados da
ferramenta utilizada para consulta dos dados.