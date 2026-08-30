# Lambda no projeto

O projeto utiliza três funções AWS Lambda para realizar as etapas de ingestão
de dados e a prova de conceito orientada a eventos.

| Função | Papel | Memória | Timeout |
| --- | --- | ---: | ---: |
| `carga` | Sete tabelas BigQuery para Bronze | 1024 MB | 900 s |
| `carga_municipios` | API IBGE para Bronze | 128 MB | 60 s |
| `metas` | API/EventBridge para Bronze e inicia Step Functions | 128 MB | 63 s |

Todas utilizam Python 3.12 em arquitetura x86_64 e recebem os nomes dos buckets
por variáveis de ambiente, evitando dependência de nomes fixos.

A função `carga` lê as credenciais do Google BigQuery no AWS Systems Manager
Parameter Store como `SecureString`, com descriptografia durante a execução.

O código-fonte das funções fica em `infra/lambda/`. Os pacotes ZIP utilizados
na implantação são gerados em `.build/` e não são versionados no repositório.