# Step Functions no projeto

A state machine Standard executa:

1. carga BigQuery e municípios IBGE em paralelo;
2. quatro jobs Bronze-to-Silver em paralelo;
3. job Gold após todas as branches Silver concluírem.

O primeiro estado `Parallel` executa simultaneamente as Lambdas `carga` e
`carga_municipios`. Após a conclusão das duas branches, o fluxo inicia um
segundo estado `Parallel`, responsável pelos quatro jobs de transformação:

- `bronze_to_silver_uf`;
- `bronze_to_silver_municipio`;
- `bronze_to_silver_aluno`;
- `bronze_to_silver_meta`.

A Step Function aguarda a conclusão de todas as branches Bronze-to-Silver antes
de iniciar o job `gold`.

Lambda e Glue recebem retries para falhas transitórias. A definição ASL fica em
`infra/aws/step-functions` e recebe ARNs/nomes por `DefinitionSubstitutions`.

Logs `ERROR` não incluem dados de execução e expiram em sete dias.