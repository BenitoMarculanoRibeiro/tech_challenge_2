# Infraestrutura AWS

- `templates/bootstrap.yaml`: bucket de artefatos.
- `publish-artifacts.ps1`: empacotamento e publicação dos artefatos.
- `configure-athena-results.ps1`: configura a saída de consultas do Athena no
  prefixo `resultados-athena/` do bucket Gold publicado pelo stack.
- `templates/application.yaml`: aplicação.
- `step-functions/`: definição ASL.
- `crawlers/`: configurações legíveis e auditáveis dos nove Glue Crawlers.
- `config/`: parâmetros seguros de exemplo.

O código-fonte não é duplicado aqui: Lambdas ficam em `infra/lambda` e Glue em
`glue`. Consulte o [guia de implantação](../../docs/reproducao/README.md).
