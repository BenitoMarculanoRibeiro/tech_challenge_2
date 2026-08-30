# CloudFormation no projeto

A infraestrutura AWS do projeto é definida por meio de dois templates
CloudFormation separados:

- `bootstrap.yaml`: cria o bucket utilizado para armazenar os artefatos da aplicação;
- `application.yaml`: cria os recursos necessários para execução do pipeline.

Essa separação permite preparar primeiro o armazenamento dos artefatos e depois
implantar a aplicação utilizando os arquivos gerados pelo processo de build.

O bucket de artefatos armazena somente recursos necessários ao deployment,
como pacotes das Lambdas, layers, definição da Step Function e scripts Glue.
Ele possui acesso público bloqueado, versionamento habilitado e exige conexões
HTTPS.

O `application.yaml` utiliza parâmetros para evitar dependências desnecessárias
do ambiente, incluindo nomes do projeto, ambiente, bucket de artefatos,
`LabRole`, parâmetro SSM das credenciais do BigQuery, quantidade de workers Glue
e configuração opcional do AWS Budget.

Os nomes físicos dos buckets Bronze, Silver e Gold são gerados pelo
CloudFormation. Os scripts recebem essas referências por parâmetros e variáveis
de ambiente, evitando nomes de buckets fixos no código.

Os templates não armazenam credenciais, valores de `SecureString`, IDs de conta
específicos da implantação ou dados analíticos.

Os scripts PowerShell de reprodução exibem o plano de execução por padrão.
Chamadas que alteram recursos na AWS exigem a opção `-Execute`.