# CloudWatch no projeto

O CloudFormation cria log groups para as três Lambdas e para a Step Function,
com retenção de sete dias. Os jobs Glue utilizam logs contínuos e métricas
habilitadas pelos argumentos dos jobs.

O projeto também cria o dashboard `tc2-cloudwatch-dashboard`,
utilizando referências automáticas aos recursos da stack, sem fixar account ID,
nomes físicos de buckets ou ID da API.

O dashboard reúne:

- invocações, erros e duração das três Lambdas;
- tamanho e quantidade de objetos dos buckets Bronze, Silver e Gold;
- métricas dos jobs Glue Silver Aluno e Gold;
- volume, erros e latência da HTTP API;
- cobrança estimada total publicada na região `us-east-1`.

O dashboard não executa o pipeline e não substitui os logs. Para validação,
devem ser observados os erros das Lambdas, falhas de execução da Step Function
e logs dos jobs Glue.

Algumas métricas podem aparecer somente após a primeira execução ou após o
período de publicação do serviço, como as métricas diárias do S3.
