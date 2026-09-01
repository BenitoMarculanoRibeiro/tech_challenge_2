# AWS Budgets no projeto

O **AWS Budgets** pode ser utilizado como mecanismo complementar de controle e
monitoramento dos custos gerados pela infraestrutura do projeto.

A configuração é opcional e foi projetada para não impedir a implantação do
pipeline em ambientes do **AWS Academy Learner Lab**, onde determinadas
permissões administrativas podem não estar disponíveis.

## Objetivo

O Budget permite acompanhar o consumo mensal da conta e definir um valor de
alerta antes que o limite planejado seja atingido.

A configuração padrão do projeto considera:

| Configuração | Valor padrão |
| --- | ---: |
| Limite mensal | USD 10 |
| Alerta de gasto | USD 8 |
| Budget habilitado | Não |

O alerta em USD 8 representa 80% do limite mensal configurado.

## Parâmetros

A criação do Budget é controlada pelos parâmetros da infraestrutura:

| Parâmetro | Padrão | Finalidade |
| --- | --- | --- |
| `EnableBudget` | `false` | Habilita ou desabilita a criação do Budget |
| `BudgetLimitUsd` | `10` | Define o limite mensal em dólares |
| `BudgetAlertThresholdUsd` | `8` | Define o valor de gasto que dispara o alerta |
| `BudgetNotificationEmail` | vazio | Define o destinatário opcional das notificações |

Por padrão:

```text
EnableBudget = false
```

Dessa forma, a ausência de permissão para criação de Budgets não impede o
deployment dos demais recursos do projeto.

## Exemplo de configuração

Para habilitar o recurso, os parâmetros podem ser definidos da seguinte forma:

```json
{
  "EnableBudget": "true",
  "BudgetLimitUsd": 10,
  "BudgetAlertThresholdUsd": 8,
  "BudgetNotificationEmail": "<BUDGET_NOTIFICATION_EMAIL>"
}
```

O endereço de e-mail deve ser informado apenas durante a configuração do
ambiente e não deve ser versionado no repositório.

## Comportamento do alerta

O AWS Budget utilizado pelo projeto possui finalidade de **monitoramento**.

Quando o valor configurado para alerta é atingido, o Budget pode emitir uma
notificação ao destinatário configurado. Ele não interrompe automaticamente:

- AWS Lambda;
- AWS Glue Jobs;
- AWS Step Functions;
- Amazon S3;
- Amazon API Gateway;
- ou outros recursos do pipeline.

Portanto, o limite configurado não deve ser interpretado como um bloqueio
automático de gastos.

Também pode existir um intervalo entre o consumo efetivo dos serviços, a
atualização das informações de custo e a emissão do alerta.

## Compatibilidade com AWS Academy

Ambientes do AWS Academy podem restringir ações administrativas, incluindo a
criação ou alteração de recursos do AWS Budgets.

Por esse motivo, o Budget é tratado como recurso opcional da infraestrutura.

```text
EnableBudget = false
        │
        └──► Pipeline implantado sem AWS Budget

EnableBudget = true
        │
        ├──► Permissão disponível ──► AWS Budget criado
        │
        └──► Requer permissão para criação do recurso
```

A indisponibilidade desse recurso não interfere no funcionamento do pipeline
Bronze → Silver → Gold.

## Boas práticas

O Budget complementa, mas não substitui, outras práticas de controle de custos.

Durante testes e demonstrações do projeto, recomenda-se:

- executar os jobs somente quando necessário;
- evitar execuções repetidas do pipeline sem necessidade;
- acompanhar o consumo disponibilizado pelo ambiente AWS Academy;
- utilizar consultas Athena pequenas durante validações;
- remover recursos temporários que não sejam mais necessários;
- manter limites e alertas compatíveis com o ambiente utilizado.

O objetivo do Budget é fornecer visibilidade adicional sobre o consumo sem
introduzir uma dependência obrigatória para execução da solução.