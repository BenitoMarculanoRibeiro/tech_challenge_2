# Infraestrutura AWS

- `templates/bootstrap.yaml`: bucket de artefatos.
- `templates/application.yaml`: aplicação.
- `step-functions/`: definição ASL.
- `config/`: parâmetros seguros de exemplo.

O código-fonte não é duplicado aqui: Lambdas ficam em `infra/lambda` e Glue em
`glue`. Consulte o [guia de implantação](../../docs/reproducao/README.md).