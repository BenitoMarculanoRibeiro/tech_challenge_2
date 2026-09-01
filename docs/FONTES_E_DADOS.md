# Fontes e dados

## Fontes utilizadas pelo pipeline

O pipeline integra dados provenientes de diferentes fontes, que são ingeridos
na camada Bronze antes das etapas de transformação e consolidação.

| Fonte | Utilização | Destino na Bronze |
| --- | --- | --- |
| Base dos Dados / BigQuery | Dados de alfabetização utilizados pelo pipeline principal | Um prefixo por tabela |
| API de Localidades do IBGE | Nome, código e UF dos municípios | `municipio_ibge/` |
| API / EventBridge de metas | Entrada da prova de conceito orientada a eventos | `meta_alfabetizacao_brasil/metas/` |

Os dados provenientes da Base dos Dados são obtidos por meio do BigQuery e
carregados para o Amazon S3 pela Lambda `carga`.

Os dados de municípios são consultados na API de Localidades do IBGE pela
Lambda `carga_municipios`.

A prova de conceito permite ainda o recebimento de metas por meio da API HTTP
ou de eventos do Amazon EventBridge.

## Fontes complementares

O diretório `Fontes_Complementares` contém arquivos do **Censo Escolar** e do
**INSE** utilizados como fontes auxiliares do projeto.

Esses dados são utilizados nos notebooks de exploração e análise, permitindo
a apresentação e contextualização dos dados trabalhados no Tech Challenge.
Também podem ser utilizados como insumos durante a preparação e execução dos
processos na AWS.

Os arquivos são mantidos no repositório para permitir a reprodução das
análises e demonstrações realizadas pelo projeto.

A origem, o ano e os nomes originais dos arquivos são preservados na estrutura
de diretórios para facilitar sua identificação e rastreabilidade.

## Dados gerados durante a execução

Os dados armazenados nas camadas **Bronze**, **Silver** e **Gold** são gerados
durante a execução do pipeline e, portanto, não são versionados no repositório.

Também não são versionados:

- credenciais de acesso;
- valores armazenados como `SecureString`;
- logs de execução do CloudWatch;
- artefatos temporários de processamento;
- conteúdo gerado nos buckets S3.

A infraestrutura, o código e as fontes necessárias para reproduzir a solução
são mantidos no repositório.