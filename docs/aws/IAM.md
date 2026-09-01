# IAM e AWS Academy

As Lambdas, os jobs Glue, os nove crawlers e a Step Function utilizam a `LabRole`
disponibilizada pelo AWS Academy Learner Lab.

O template constrói o ARN da `LabRole` utilizando a conta e a região do
ambiente atual e não cria roles IAM próprias.

Essa decisão mantém a infraestrutura compatível com as restrições do Learner
Lab, onde a criação e administração de roles pode ser limitada.

A `LabRole` deve possuir as permissões necessárias para os serviços utilizados
pelo projeto, incluindo Lambda, Glue, Step Functions, S3 e CloudWatch Logs.

Caso o projeto seja implantado em outro ambiente, as permissões associadas à
role utilizada devem ser revisadas de acordo com os recursos da infraestrutura.
