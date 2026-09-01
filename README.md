# Tech Challenge - Alfabetização no Brasil

Pipeline híbrido batch e streaming para organizar dados públicos de alfabetização
em camadas Bronze, Silver e Gold na AWS. Trabalho acadêmico da FIAP, Fase 2.

## Navegação

- [Arquitetura](docs/ARQUITETURA.md)
- [FinOps e estimativa de custos](docs/FINOPS.md)
- [Documentação técnica](docs/README.md)
- [Implantação do ambiente](docs/reproducao/README.md)
- [Parâmetros necessários](docs/reproducao/PARAMETROS.md)
- [Validação de baixo custo](docs/reproducao/VALIDACAO.md)
- [Serviços AWS](docs/aws/README.md)

## Problema e objetivo

O projeto organiza resultados, metas e microdados relacionados à alfabetização
para permitir comparações entre Brasil, unidades da Federação e municípios. O
objetivo técnico é demonstrar ingestão, transformação, orquestração e catálogo
de dados com componentes gerenciados da AWS.

## Fontes

- Base dos Dados/BigQuery: sete tabelas do conjunto
  `br_inep_avaliacao_alfabetizacao`.
- API de Localidades do IBGE: identificação e UF dos municípios.
- API HTTP de prova de conceito: atualização pontual de metas.
- Censo Escolar e INSE: fontes complementares mantidas para exploração, ainda
  fora do pipeline implantado.

Consulte [Fontes e dados](docs/FONTES_E_DADOS.md) para origem e limitações.

## Metodologia e processamento

1. Lambdas gravam dados de origem em Parquet na Bronze.
2. Quatro jobs Glue normalizam alunos, municípios, UF e metas na Silver.
3. O job Gold produz indicadores geográficos, comparação com metas, evolução
   temporal e um conjunto preparado para análises futuras.
4. Step Functions mantém a ordem e o paralelismo do pipeline.
5. Nove Glue Crawlers catalogam as tabelas Gold para consulta no Athena e uso
   pelo Power BI.

Os buckets usam os prefixos `bucket-bronze`, `bucket-silver` e `bucket-gold`,
com conta e região acrescentadas pelo CloudFormation para garantir unicidade.
As referências são propagadas para Lambdas e jobs Glue sem nomes hardcoded.

## Análises demonstradas

Os notebooks documentam o inventário das fontes, relacionamentos possíveis e
perguntas analíticas, incluindo distância para metas, comparação territorial e
contextos educacional e socioeconômico. Eles não comprovam ainda conclusões
quantitativas finais; por isso este README não apresenta rankings ou resultados
que não estejam materializados e validados.

## Segurança e implantação

A credencial Google é fornecida pelo próprio usuário como `SecureString` no
Parameter Store. Nenhuma credencial real é versionada. O endpoint `POST /metas`
é público exclusivamente como prova de conceito acadêmica, com throttling baixo;
não deve ser usado dessa forma em produção.

O ambiente suportado é o Learner Lab em `us-east-1`, utilizando a `LabRole` já
fornecida.

## Limitações conhecidas

- Censo Escolar e INSE ainda não entram nas transformações AWS.
- A validação completa executa Lambda/Glue e pode consumir créditos do Lab.
- O repositório não contém o valor da credencial Google nem ZIPs de deployment.

## Repositório

- `glue/`: scripts organizados por etapa.
- `infra/lambda/`: fonte única das Lambdas.
- `infra/aws/`: CloudFormation, ASL, configuração e publicação de artefatos.
- `notebook/`: exploração e leitura das camadas.
- `Fontes_Complementares/`: arquivos acadêmicos mantidos fora do pipeline AWS.
