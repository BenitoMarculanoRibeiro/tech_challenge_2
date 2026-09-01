# API Gateway no projeto

O **Amazon API Gateway** é utilizado na prova de conceito para disponibilizar
um endpoint HTTP capaz de receber novas metas de alfabetização e encaminhá-las
para processamento na AWS.

## Endpoint

A API disponibiliza a seguinte rota:

```http
POST /metas
```

O corpo da requisição é enviado em formato JSON e encaminhado para a Lambda
`metas`, responsável por processar a entrada e armazenar o dado na camada
Bronze.

```text
Cliente
   │
   │ POST /metas
   ▼
API Gateway
   │
   ▼
Lambda metas
   │
   ├──────────────► S3 Bronze
   │
   └──────────────► Step Functions
```

Após persistir o dado recebido no Amazon S3, a Lambda inicia a Step Function
utilizada pelo pipeline para dar continuidade ao processamento.

## Objetivo da prova de conceito

O endpoint demonstra uma alternativa de ingestão orientada a eventos, permitindo
que uma nova informação seja incorporada ao pipeline sem depender exclusivamente
da execução periódica do fluxo batch.

A API utiliza throttling para limitar a quantidade de requisições aceitas.

## Segurança

Para simplificar a demonstração acadêmica, a rota utiliza:

```text
AuthorizationType: NONE
```

Portanto, o endpoint não exige autenticação.

Essa configuração foi adotada exclusivamente para a prova de conceito e não é
recomendada para um ambiente de produção.

Em um cenário produtivo, a API deveria considerar mecanismos adicionais de
segurança, como:

- autenticação e autorização;
- validação do payload recebido;
- limites de requisição adequados ao cenário de uso;
- proteção contra abuso;
- monitoramento e auditoria das chamadas.

Nenhuma credencial ou segredo deve ser enviado no corpo das requisições.

## Infraestrutura

A API é criada pela infraestrutura CloudFormation do projeto.

O endpoint gerado durante o deployment é disponibilizado pelo Output:

```text
StreamingApiUrl
```

Dessa forma, não é necessário manter uma URL fixa no código ou na
documentação, permitindo que a infraestrutura seja reproduzida em diferentes
ambientes.