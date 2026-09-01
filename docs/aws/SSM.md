# SSM Parameter Store e BigQuery

O projeto utiliza o AWS Systems Manager Parameter Store para armazenar a
credencial utilizada na integração com o Google BigQuery.

O parâmetro utilizado é:

`/tc2/google-bigquery-credentials`

O valor deve conter o JSON completo de uma Service Account do Google Cloud e
deve ser armazenado como `SecureString`.

O CloudFormation não recebe nem armazena o conteúdo dessa credencial.

## Configuração

Para configurar a integração:

1. Criar uma Service Account no Google Cloud.
2. Conceder somente as permissões necessárias para acesso ao BigQuery.
3. Gerar a chave da Service Account em formato JSON.
4. Armazenar o conteúdo integral do JSON no AWS Systems Manager Parameter Store
   como `SecureString`.
5. Informar o nome do parâmetro à infraestrutura por meio de `SsmGetParameter`.

A Lambda responsável pela carga consulta o parâmetro em tempo de execução com
descriptografia habilitada, evitando que a credencial seja armazenada no
código-fonte ou nos artefatos da aplicação.

## Segurança

Credenciais reais não devem ser versionadas no repositório.

O diretório `docs/reproducao/exemplos` contém apenas um arquivo de exemplo com
a estrutura esperada da credencial, sem dados reais.

Consulte também:

- [Guia de configuração](../reproducao/README.md)
- [Exemplo de credencial](../reproducao/exemplos/google-bigquery-credentials.example.json)
