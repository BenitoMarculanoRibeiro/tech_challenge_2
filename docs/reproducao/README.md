# Implantação do ambiente

Este guia descreve a implantação do projeto em uma conta/Learner Lab.

## Pré-requisitos

- Git e AWS CLI.
- PowerShell e Python com `pip`.
- Learner Lab ativo, credenciais temporárias configuradas e região `us-east-1`.
- `LabRole` disponível.
- Conta Google Cloud com acesso ao BigQuery/Base dos Dados.

## 1. Preparar parâmetros

Use `infra/aws/config/parameters.example.json` como referência para os parâmetros
necessários da infraestrutura. Consulte [PARAMETROS.md](PARAMETROS.md) para a
descrição de cada valor.

Não versione credenciais, e-mails pessoais ou outros valores sensíveis.

## 2. Preparar a credencial Google

1. Crie um projeto ou selecione um projeto próprio no Google Cloud.
2. Crie uma Service Account com o menor acesso necessário para consultar o
   BigQuery.
3. Gere uma chave JSON e salve-a fora do repositório.
4. No Systems Manager Parameter Store da sua conta AWS, crie um parâmetro
   `SecureString` chamado `/fiap/google-bigquery-credentials`.
5. Use como valor o conteúdo completo do JSON, não o caminho do arquivo.

O [exemplo falso](exemplos/google-bigquery-credentials.example.json) demonstra
o formato; ele é intencionalmente inválido e não autentica.

## 3. Criar o bucket de artefatos

No console do CloudFormation, crie uma stack usando:

- `infra/aws/templates/bootstrap.yaml`

Quando a stack terminar, copie o Output `ArtifactBucketName`.

## 4. Gerar e publicar os artefatos

Na raiz do repositório, primeiro execute em modo de simulação:

```powershell
.\infra\aws\publish-artifacts.ps1 -ArtifactBucketName <ARTIFACT_BUCKET_NAME>
```

O script gera em `.build/` os três pacotes Lambda, a layer Google, os cinco
scripts Glue, a definição da Step Function e um manifesto com hashes. Nesse modo
nenhum comando AWS é executado.

Depois de revisar o plano exibido, publique com:

```powershell
.\infra\aws\publish-artifacts.ps1 `
  -ArtifactBucketName <ARTIFACT_BUCKET_NAME> `
  -Execute
```

Copie os valores `ArtifactBucketName` e `ArtifactPrefix` mostrados ao final.
Se o executável Python não estiver disponível como `python`, informe-o com
`-PythonCommand <CAMINHO_DO_PYTHON>`.

## 5. Criar a aplicação

No console do CloudFormation, crie outra stack usando:

- `infra/aws/templates/application.yaml`

Informe o bucket e o prefixo produzidos nas etapas anteriores. Os demais valores
podem seguir `infra/aws/config/parameters.example.json`.

A definição da Step Function publicada pelo script vem de:

- `infra/aws/step-functions/tc2-steps.asl.json`

O bootstrap define o bucket utilizado pelos artefatos da aplicação. O template
principal define os recursos AWS do projeto, incluindo S3, Lambda, Glue,
Step Functions, EventBridge, API Gateway, CloudWatch e recursos opcionais de
controle de custo.

A infraestrutura foi desenvolvida e revisada com auxílio do Agent Toolkit for AWS.
O script publica somente arquivos e não cria nem atualiza stacks. Antes de cada
implantação manual, revise os recursos, permissões e custos apresentados.

## 6. Executar e validar

Após a implantação, use os Outputs da stack para identificar buckets, API,
Step Function, crawler e demais recursos.

Siga [VALIDACAO.md](VALIDACAO.md), começando pelas verificações que não executam
workload. Execuções de Lambda, Glue e Step Functions podem consumir créditos do Lab.

## 7. Encerramento

Buckets usam `DeletionPolicy: Retain`; excluir a stack não remove dados. Para
evitar perda acidental, a limpeza é manual. Confirme os nomes gerados, esvazie e
exclua buckets apenas quando os dados não forem mais necessários.
