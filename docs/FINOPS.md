# FinOps — escolhas e estimativa de custos

Esta análise explica as escolhas de custo do projeto. Os valores são preços
públicos de referência para **us-east-1**, consultados em **31/08/2026**, em
dólares e sem considerar créditos do AWS Academy, impostos ou descontos. A
cobrança real depende do tempo de execução e do volume processado.

## Decisões principais

### Parameter Store em vez de Secrets Manager

O projeto guarda uma credencial do BigQuery como `SecureString` no parâmetro
`/tc2/google-bigquery-credentials`.

| Opção | Preço de referência | Avaliação |
|---|---:|---|
| SSM Parameter Store Standard | **USD 0,00/mês** e chamadas com throughput padrão sem custo adicional | Escolhido: atende uma credencial estática de até 4 KB |
| SSM Parameter Store Advanced | **USD 0,05/parâmetro/mês** + **USD 0,05/10 mil chamadas** | Desnecessário para este trabalho |
| Secrets Manager | **USD 0,40/segredo/mês** + **USD 0,05/10 mil chamadas** | Não usado: acrescentaria pelo menos USD 0,40/mês |

O Parameter Store cumpre a função necessária de armazenar e recuperar o valor
criptografado, mas não substitui todas as capacidades do Secrets Manager. O
Secrets Manager oferece recursos próprios de rotação e gerenciamento do ciclo
de vida. Como a chave de teste é atualizada manualmente e o projeto não exige
rotação automática, o Parameter Store Standard é suficiente e mais econômico.

Fontes: [Systems Manager Pricing](https://aws.amazon.com/systems-manager/pricing/)
e [Secrets Manager Pricing](https://aws.amazon.com/secrets-manager/pricing/).

### Step Functions em vez de Apache Airflow/MWAA

O pipeline é linear, executado sob demanda e usa integrações nativas com Lambda
e Glue. A Step Function Standard cobra **USD 0,025 por 1.000 transições** e
oferece **4.000 transições gratuitas por mês**.

No caminho feliz atual, considerando uma única consulta de estado por crawler,
a estimativa é de aproximadamente **56 transições**, ou **USD 0,0014 por
execução antes da faixa gratuita**. Cada nova rodada de espera, consulta e
decisão dos nove crawlers acrescenta até 27 transições.

O Amazon MWAA com ambiente Airflow pequeno custa **USD 0,49/hora**. Mantido por
744 horas, o ambiente-base custa **USD 364,56/mês**, antes de workers extras e
armazenamento do banco de metadados. Embora Airflow seja adequado para centenas
de DAGs, plugins e orquestração multiplataforma, seria excesso de capacidade
para uma única máquina de estados acadêmica.

Fonte: [Step Functions Pricing](https://aws.amazon.com/step-functions/pricing/)
e [Amazon MWAA Pricing](https://aws.amazon.com/managed-workflows-for-apache-airflow/pricing/).

### Athena em vez de Redshift

O Athena consulta os arquivos Parquet diretamente no S3 e cobra **USD 5 por TB
verificado**, com mínimo de 10 MB por consulta. Uma consulta que alcance apenas
o mínimo custa aproximadamente **USD 0,00005**; as seis consultas SQL do
repositório custariam aproximadamente **USD 0,00029** nesse cenário mínimo.

O Redshift Serverless começa em aproximadamente **USD 1,50 por hora ativa** e
o Redshift provisionado começa em **USD 0,543/hora**, além do armazenamento.
Redshift faria sentido para maior concorrência, baixa latência contínua e um
data warehouse permanente. Para poucas consultas sobre uma Gold pequena,
Athena evita capacidade ociosa.

Fonte: [Athena Pricing](https://aws.amazon.com/athena/pricing/) e
[Redshift Pricing](https://aws.amazon.com/redshift/pricing/).

### Glue em vez de cluster Spark permanente

Os cinco jobs usam Glue 5.1, worker `G.1X` e 10 workers. O preço de referência é
**USD 0,44 por DPU-hora**, cobrado por segundo com mínimo de um minuto para jobs.
No exemplo de 3 minutos por job:

`5 jobs × 10 DPUs × 3/60 hora × USD 0,44 = USD 1,10 por pipeline`.

Os crawlers também custam **USD 0,44 por DPU-hora**, com mínimo de 10 minutos.
Assumindo 2 DPUs por crawler no exemplo:

`9 crawlers × 2 DPUs × 10/60 hora × USD 0,44 = USD 1,32 por pipeline`.

Um cluster EMR permanente exigiria capacidade provisionada e administração. O
EMR Serverless é uma alternativa válida para Spark mais complexo, mas cobra
separadamente vCPU, memória e armazenamento usados. Para cinco jobs curtos e
integrados ao Data Catalog, o Glue mantém a operação mais simples.

Fonte: [AWS Glue Pricing](https://aws.amazon.com/glue/pricing/) e
[Amazon EMR Pricing](https://aws.amazon.com/emr/pricing/).

### Power BI em vez de QuickSight

O grupo já utiliza Power BI Desktop, portanto não foi necessário contratar um
autor de BI adicional na AWS. O QuickSight/Quick Author custa **USD 24 por
autor/mês**; seria interessante para publicação totalmente gerenciada dentro
da AWS, mas não trouxe benefício suficiente para a demonstração local.

Fonte: [QuickSight Pricing](https://aws.amazon.com/quick/quicksight/pricing/).

## Preços unitários dos serviços utilizados

| Serviço | Quantidade/configuração no projeto | Preço de referência |
|---|---|---:|
| CloudFormation | 2 stacks: `tc2-artefatos` e `tc2-pipeline` | **USD 0,00** pelo uso normal de recursos AWS; os serviços criados são cobrados separadamente |
| IAM | 1 role existente, `LabRole` | **USD 0,00** pelo serviço IAM |
| S3 | 4 buckets: artefatos, Bronze, Silver e Gold | Standard: **USD 0,023/GB-mês**; PUT/COPY/POST/LIST: **USD 0,005/1.000**; GET: **USD 0,0004/1.000** |
| Lambda | 3 funções; 1.024 MB, 128 MB e 128 MB | **USD 0,20/milhão de solicitações** + **USD 0,0000166667/GB-s** |
| Lambda Layers | 1 layer própria e 1 layer pública AWS | Sem cobrança própria; armazenamento e execução entram nos custos de Lambda/S3 |
| Glue Jobs | 5 jobs `G.1X`, 10 workers cada | **USD 0,44/DPU-hora** |
| Glue Crawlers | 9 crawlers | **USD 0,44/DPU-hora**, mínimo de 10 minutos |
| Glue Data Catalog | 1 database e 9 tabelas | Primeiro milhão de objetos e acessos/mês sem custo |
| Step Functions Standard | 1 máquina de estado | **USD 0,025/1.000 transições**; 4.000/mês gratuitas |
| Athena | 6 consultas SQL documentadas | **USD 5/TB verificado**, mínimo de 10 MB/consulta |
| API Gateway HTTP API | 1 API, 1 rota `POST /metas` | Primeiro nível: **USD 1,00/milhão de chamadas** |
| EventBridge | 1 regra de evento de metas | Eventos customizados: **USD 1,00/milhão**; entrega na mesma conta sem custo adicional |
| CloudWatch Logs | 3 logs Lambda + 1 log da Step Function, retenção de 7 dias | Ingestão de referência: **USD 0,50/GB**; primeiros 5 GB/mês na faixa gratuita |
| CloudWatch Dashboard | 1 dashboard | **USD 3,00/dashboard-mês**; até 3 dashboards com 50 métricas na faixa gratuita |
| Parameter Store | 1 `SecureString` Standard | **USD 0,00** com throughput padrão |
| AWS Budget | 1 budget opcional | Os dois primeiros action-enabled budgets são gratuitos; verificar a conta antes de habilitar |

Fontes adicionais: [S3 Pricing](https://aws.amazon.com/s3/pricing/),
[Lambda Pricing](https://aws.amazon.com/lambda/pricing/),
[API Gateway Pricing](https://aws.amazon.com/api-gateway/pricing/),
[EventBridge Pricing](https://aws.amazon.com/eventbridge/pricing/) e
[CloudWatch Pricing](https://aws.amazon.com/cloudwatch/pricing/). Para o
controle de gastos, consulte também [AWS Budgets Pricing](https://aws.amazon.com/aws-cost-management/aws-budgets/pricing/).

## Exemplo consolidado

Premissas didáticas de uma execução completa:

- cinco jobs Glue com 10 DPUs durante 3 minutos cada;
- nove crawlers com 2 DPUs durante o mínimo faturável de 10 minutos;
- 56 transições na Step Function;
- seis consultas Athena no mínimo de 10 MB;
- Lambda BigQuery por 60 s em 1 GB, município por 10 s em 128 MB e streaming
  por 5 s em 128 MB;
- uma chamada HTTP API;
- 1 GB mantido no S3 durante o mês;
- faixas gratuitas desconsideradas para evidenciar o preço bruto.

| Componente | Valor estimado |
|---|---:|
| 5 Glue Jobs | USD 1,100000 por execução |
| 9 Glue Crawlers | USD 1,320000 por execução |
| Step Functions | USD 0,001400 por execução |
| 6 consultas Athena | USD 0,000286 por execução |
| Lambda — computação e solicitações | USD 0,001032 por execução |
| Uma chamada HTTP API | USD 0,000001 por execução |
| **Subtotal por execução** | **USD 2,422719** |
| S3 Standard — 1 GB por mês | USD 0,023000 por mês |
| **10 execuções + 1 GB no S3** | **USD 24,250190 por mês** |

O maior custo variável do cenário é o Glue: jobs e crawlers representam quase
todo o subtotal. A otimização mais efetiva é medir a duração real e reduzir
`GlueNumberOfWorkers` de 10 para 2 quando os testes demonstrarem que o volume
permite. Também é importante evitar executar todos os nove crawlers quando
nenhum prefixo Gold mudou.

## Controles FinOps adotados

- `EnableBudget=false` por padrão, evitando falha no Learner Lab; pode ser
  habilitado com limite de **USD 10** e alerta em **USD 8**.
- Logs com retenção de **7 dias**, em vez de retenção indefinida.
- S3 com Lifecycle: Bronze em Intelligent-Tiering após 30 dias, Glacier IR após
  60 e Deep Archive após 180; Silver em Intelligent-Tiering após 60; Gold após
  180 dias.
- Arquivos Parquet e consultas por colunas reduzem bytes verificados no Athena.
- `MaxConcurrentRuns=1` nos jobs evita execuções duplicadas simultâneas.
- Crawler e pipeline são acionados sob demanda; não há cluster ligado 24×7.

Para uma estimativa de implantação real, substitua as durações exemplificadas
pelas métricas do CloudWatch e use a
[AWS Pricing Calculator](https://calculator.aws/). Os valores desta página
devem ser revisados antes da apresentação, pois a AWS pode alterar preços e
faixas gratuitas.
