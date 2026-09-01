# Step Functions no projeto

A state machine Standard executa cinco etapas:

1. carga BigQuery e municípios IBGE em paralelo;
2. quatro jobs Bronze-to-Silver em paralelo;
3. job Silver-to-Gold;
4. preparação da lista dos nove crawlers;
5. execução e acompanhamento dos crawlers em paralelo.

O primeiro estado `Parallel` executa simultaneamente as duas Lambdas de carga.
O segundo aguarda os quatro Glue Jobs Silver antes de iniciar a Gold.

Após a Gold, `PrepararCrawlers` cria uma lista com os nove nomes recebidos por
`DefinitionSubstitutions`. O estado `ExecutarCrawlers` usa um `Map` com
concorrência máxima nove. Para cada item, o fluxo:

1. chama `glue:startCrawler`;
2. aguarda 15 segundos;
3. consulta `glue:getCrawler`;
4. repete enquanto o estado for `RUNNING` ou `STOPPING`;
5. conclui apenas com `READY` e `LastCrawl.Status = SUCCEEDED`;
6. gera `GlueCrawlerFailed` para qualquer outro resultado.

Lambda e Glue Jobs recebem retries para falhas transitórias. A definição ASL
fica em `infra/aws/step-functions/pipeline-alfabetizacao.asl.json`; ARNs e nomes físicos não
são fixados nela, sendo fornecidos pelo CloudFormation.

Os logs registram somente erros, não incluem os dados de execução e possuem
retenção de sete dias.
