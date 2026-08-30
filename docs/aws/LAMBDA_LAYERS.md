# Lambda Layers no projeto

As Lambdas utilizam layers para disponibilizar dependências que não fazem parte
do runtime padrão do Python.

A layer gerenciada `AWSSDKPandas-Python312:31` fornece bibliotecas como
`pandas` e `pyarrow`.

Uma layer própria adiciona as dependências necessárias para integração com o
Google BigQuery, incluindo:

- `google-cloud-bigquery==3.43.0`;
- `google-auth==2.56.3`;
- dependências transitivas definidas durante o build.

A layer própria é gerada a partir de `infra/lambda/requirements.txt`.

O script `build.ps1` monta os artefatos utilizados pela infraestrutura. Para a
layer Google, ele instala wheels Linux x86_64 compatíveis com Python 3.12 em uma
estrutura `python/` e gera o arquivo `google-dependencies.zip`.

O mesmo processo de build também:

- gera os pacotes ZIP das três Lambdas;
- copia os scripts AWS Glue;
- copia a definição da Step Function;
- gera um `manifest.json` com hash SHA-256 e tamanho dos artefatos.

Os artefatos gerados são armazenados em `.build/` e não são versionados no
repositório.

Para implantação em outra região ou utilização de outra versão da layer
gerenciada, o parâmetro `AwsSdkPandasLayerArn` deve ser ajustado conforme o
ambiente.