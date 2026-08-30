# Parâmetros de configuração

Os parâmetros abaixo permitem configurar a implantação do projeto sem manter
nomes físicos de recursos, credenciais ou valores específicos de uma conta AWS
no código-fonte.

| Nome | Finalidade | Obrigatório | Sensível | Como obter/configurar |
|---|---|---:|---:|---|
| `Region` | região suportada | sim | não | `us-east-1` |
| `ProjectName` | prefixo lógico | sim | não | padrão `tc2` |
| `Environment` | separação de stack | sim | não | `dev` ou `test` |
| `LabRoleName` | role fornecida pelo Lab | sim | não | padrão `LabRole` |
| `GoogleCredentialsParameterName` | nome do SecureString | sim | não | `/fiap/google-bigquery-credentials` |
| `AwsSdkPandasLayerArn` | pandas/pyarrow Python 3.12 | sim | não | layer compatível disponível na região |
| `GlueNumberOfWorkers` | capacidade dos jobs | sim | não | 10 reproduz a configuração original; 2 reduz custo |
| `EnableBudget` | cria o Budget mensal opcional | não | não | padrão `false`; use `true` se a conta permitir |
| `BudgetLimitUsd` | limite mensal do Budget | quando habilitado | não | padrão `10` |
| `BudgetAlertThresholdUsd` | gasto real que dispara alerta | quando habilitado | não | padrão `8`; deve ser menor ou igual ao limite |
| `BudgetNotificationEmail` | destinatário opcional do alerta | não | sim | informar no deployment; nunca versionar endereço real |
| `ArtifactBucketName` | pacotes gerados pelo build | automático | não | Output do bootstrap |
| `ArtifactPrefix` | versão por hash | automático | não | calculado por `deploy.ps1` |
| `BRONZE_BUCKET` | destino de ingestão | automático | não | `Ref` CloudFormation |
| `SILVER_BUCKET` | dados normalizados | automático | não | `Ref` CloudFormation |
| `GOLD_BUCKET` | dados analíticos | automático | não | `Ref` CloudFormation |
| `STATE_MACHINE_ARN` | orquestração da Lambda de metas | automático | não | `Ref` CloudFormation |
| `TC2_BRONZE_BUCKET` | notebook de leitura | após deploy | não | Output `BronzeBucketName` |
| `TC2_SILVER_BUCKET` | notebook de leitura | após deploy | não | Output `SilverBucketName` |
| `TC2_GOLD_BUCKET` | notebook de leitura | após deploy | não | Output `GoldBucketName` |
| `GOOGLE_BIGQUERY_CREDENTIALS_JSON` | JSON real da Service Account | sim | **sim** | valor armazenado manualmente como SecureString; nunca versionar |

## Valores sensíveis

Os placeholders `<AWS_PROFILE>`, `<GOLD_BUCKET>` e
`<GOOGLE_BIGQUERY_CREDENTIALS_JSON>` aparecem somente na documentação e nos
arquivos de exemplo e devem ser substituídos pelo usuário quando aplicável.

O valor `<INVALID_PRIVATE_KEY_EXAMPLE_DO_NOT_USE>` é deliberadamente inválido
e existe apenas para demonstrar a estrutura esperada do arquivo de credenciais.
Nunca substitua esse valor por uma chave privada real dentro de um arquivo
versionado.

`<BUDGET_NOTIFICATION_EMAIL>` também é apenas um placeholder. Caso seja
utilizado, o endereço real deve ser informado durante a implantação e não deve
ser versionado.

## Recursos gerados automaticamente

Os nomes físicos dos buckets Bronze, Silver e Gold não precisam ser definidos
manualmente. Eles são criados pelo CloudFormation e propagados para Lambdas,
jobs Glue e demais recursos por referências da própria stack.

Da mesma forma, o ARN da Step Function é obtido automaticamente pela
infraestrutura, evitando dependência de IDs de conta ou ARNs fixos.

## Credencial do BigQuery

A credencial real do Google BigQuery não deve existir no repositório.

O JSON da Service Account deve ser armazenado no AWS Systems Manager Parameter
Store como `SecureString`. O projeto referencia somente o nome do parâmetro,
por padrão:

`/fiap/google-bigquery-credentials`

Consulte `docs/aws/SSM.md` para os detalhes da configuração.