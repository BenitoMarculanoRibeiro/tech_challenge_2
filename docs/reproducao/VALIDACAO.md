# Validação de baixo custo

Comece pelas verificações sem workload e só execute processamento com autorização
e créditos suficientes.

## 1. Infraestrutura sem processar dados

Antes de executar o pipeline, revise a infraestrutura pelo console da AWS e,
quando aplicável, com auxílio do Agent Toolkit for AWS.

Confirme:

- stack CloudFormation em estado `CREATE_COMPLETE`;
- existência do parâmetro SSM, sem descriptografar seu valor;
- três buckets de dados;
- três Lambdas;
- cinco jobs Glue;
- Glue Crawler e database;
- Step Function;
- regra EventBridge;
- HTTP API;
- CloudWatch Dashboard.

Não visualize nem exponha o valor do `SecureString` durante a validação.

Se `EnableBudget=true`, confirme o Budget no console de Billing. Falta de
permissão para AWS Budgets no Learner Lab é uma limitação possível do ambiente;
nesse caso, mantenha `EnableBudget=false`.

No S3, valide somente a configuração Lifecycle, sem listar nem baixar os dados:

- Bronze: transições em 30, 60 e 180 dias e multipart em 10 dias;
- Silver: transição em 60 dias e multipart em 10 dias;
- Gold: transição em 180 dias.

## 2. Smoke test controlado

1. Inicie a Step Function manualmente com `{}` apenas após estimar o custo.
2. Confirme objetos esperados na Bronze sem baixá-los integralmente.
3. Confirme as quatro execuções Glue Silver e a execução Gold.
4. Confirme prefixos `alunos`, `municipio`, `uf` e `meta_alfabetizacao` na Silver.
5. Confirme `indicador_uf` e demais saídas documentadas na Gold.
6. Execute o crawler e confirme a tabela no Data Catalog.
7. Faça uma consulta Athena limitada, por exemplo `SELECT * ... LIMIT 10`.

## 3. Prova de conceito HTTP

O endpoint é público. Use apenas dados fictícios:

```text
POST /metas
```

```json
{
  "version": "0",
  "detail-type": "metas",
  "source": "com.tc2",
  "detail": [
    {
      "ano": "2023",
      "rede": "Pública",
      "taxa_alfabetizacao": "61.0",
      "meta_alfabetizacao_2024": "60.0",
      "meta_alfabetizacao_2025": "65.0",
      "meta_alfabetizacao_2026": "70.0",
      "meta_alfabetizacao_2027": "75.0",
      "meta_alfabetizacao_2028": "80.0",
      "meta_alfabetizacao_2029": "85.0",
      "meta_alfabetizacao_2030": "90.0",
      "percentual_participacao": "86.0"
    },
    {
      "ano": "2024",
      "rede": "Pública",
      "taxa_alfabetizacao": "64.0",
      "meta_alfabetizacao_2025": "62.0",
      "meta_alfabetizacao_2026": "67.0",
      "meta_alfabetizacao_2027": "72.0",
      "meta_alfabetizacao_2028": "77.0",
      "meta_alfabetizacao_2029": "82.0",
      "meta_alfabetizacao_2030": "87.0",
      "meta_alfabetizacao_2031": "92.0",
      "percentual_participacao": "88.0"
    },
    {
      "ano": "2025",
      "rede": "Pública",
      "taxa_alfabetizacao": "67.0",
      "meta_alfabetizacao_2026": "64.0",
      "meta_alfabetizacao_2027": "69.0",
      "meta_alfabetizacao_2028": "74.0",
      "meta_alfabetizacao_2029": "79.0",
      "meta_alfabetizacao_2030": "84.0",
      "meta_alfabetizacao_2031": "89.0",
      "meta_alfabetizacao_2032": "94.0",
      "percentual_participacao": "90.0"
    },
    {
      "ano": "2026",
      "rede": "Pública",
      "taxa_alfabetizacao": "70.0",
      "meta_alfabetizacao_2027": "66.0",
      "meta_alfabetizacao_2028": "71.0",
      "meta_alfabetizacao_2029": "76.0",
      "meta_alfabetizacao_2030": "81.0",
      "meta_alfabetizacao_2031": "86.0",
      "meta_alfabetizacao_2032": "91.0",
      "meta_alfabetizacao_2033": "96.0",
      "percentual_participacao": "92.0"
    }
  ]
}
```

Confirme HTTP 200, objeto de metas na Bronze e nova execução da Step Function.

Não envie dados pessoais nem credenciais. O teste inicia o pipeline completo.

## Critério de sucesso

O pipeline termina sem falhas, cria objetos Bronze/Silver/Gold, cataloga
`indicador_uf` e não expõe o valor do SecureString em logs ou respostas.