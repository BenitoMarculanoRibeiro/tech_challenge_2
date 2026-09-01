# Documentação dos Notebooks

## 1. Visão geral

Os notebooks foram desenvolvidos como etapa de levantamento e planejamento analítico do projeto, apoiando a preparação dos dados para as camadas Prata e Gold.

O notebook **Análise de Dados** é responsável pelo levantamento e análise das fontes de dados, enquanto o notebook **Relacionamento e Análise das Bases** utiliza essas informações para definir as perguntas de análise, os dados necessários e os possíveis relacionamentos entre as bases.

Os notebooks 1 e 2 documentam o levantamento, a análise e o planejamento que orientam a preparação das camadas Prata e Gold. O Notebook 3 complementa esse processo realizando a leitura, conferência e consulta dos dados materializados nessas camadas.

---

## 2. Análise de Dados

### 2.1 Objetivo

O notebook tem como objetivo realizar o levantamento e a análise das fontes de dados consideradas no projeto, identificando sua estrutura, tabelas, arquivos, variáveis e tipos de dados.

O levantamento permite conhecer as informações disponíveis antes da definição das análises e da preparação dos dados para as camadas posteriores.

### 2.2 Base Principal — Avaliação da Alfabetização

A Base Principal do projeto é composta pelos dados da Avaliação da Alfabetização disponibilizados pela Base dos Dados.

Foram analisadas as principais tabelas relacionadas ao projeto:

- `alunos`;
- `municipio`;
- `uf`;
- `meta_alfabetizacao_brasil`;
- `meta_alfabetizacao_municipio`;
- `meta_alfabetizacao_uf`;
- `dicionario`.

O levantamento contemplou a identificação da estrutura das tabelas, suas variáveis e respectivos tipos de dados, além das informações necessárias para compreender as possibilidades de relacionamento entre os dados.

Também foi utilizada a consulta de municípios da API do IBGE como apoio à identificação e ao relacionamento das informações municipais.

### 2.3 Fonte Complementar 1 — Censo Escolar 2023

O Censo Escolar 2023 foi analisado como fonte complementar para ampliar o contexto educacional das análises.

Foram identificadas duas estruturas principais:

- `microdados_unidade_coleta`;
- `suplemento_cursos_tecnicos`.

O levantamento resultou na documentação de 487 variáveis, sendo:

- 458 da estrutura `microdados_unidade_coleta`;
- 29 da estrutura `suplemento_cursos_tecnicos`.

A análise contemplou a identificação das variáveis, seus tipos e as características das informações disponibilizadas.

### 2.4 Fonte Complementar 2 — INSE 2023

O INSE 2023 foi incorporado como fonte externa complementar para representar o contexto socioeconômico.

Foram analisados arquivos nos seguintes níveis de agregação:

- Brasil;
- Unidades da Federação;
- municípios;
- escolas.

O levantamento identificou as estruturas e variáveis disponíveis para subsidiar os cruzamentos definidos nas etapas posteriores.

### 2.5 Resultado do levantamento

O notebook consolida as informações necessárias para que a equipe conheça as fontes disponíveis e possa selecionar as variáveis relevantes para as etapas seguintes.

A seleção definitiva das variáveis para utilização nas camadas posteriores não é realizada neste notebook.

---

## 3. Relacionamento e Análise das Bases

### 3.1 Objetivo

O notebook tem como objetivo definir as perguntas que orientarão as análises e identificar os dados necessários para respondê-las.

A partir do levantamento realizado no notebook **Análise de Dados**, são avaliadas as fontes, variáveis e possibilidades de relacionamento necessárias para as análises.

### 3.2 Perguntas de análise

As análises foram organizadas considerando:

- alcance e evolução das metas;
- comparação entre municípios e Unidades da Federação;
- desempenho e contexto educacional;
- contexto socioeconômico;
- análise integrada dos resultados.

O horizonte das análises considera a evolução das metas até 2030.

### 3.3 Dados e relacionamentos

Para cada análise foram identificadas as fontes e informações necessárias, considerando principalmente:

- identificação dos municípios;
- identificação das Unidades da Federação;
- identificação das escolas, quando aplicável;
- resultados de alfabetização;
- metas estabelecidas;
- características educacionais;
- indicadores socioeconômicos.

As possibilidades de relacionamento entre as bases foram definidas a partir das chaves e dos níveis de agregação disponíveis em cada fonte.

### 3.4 Variáveis selecionadas

Foram identificadas as principais variáveis necessárias para:

- identificar as unidades analisadas;
- relacionar as diferentes fontes;
- comparar resultados e metas;
- incorporar informações educacionais;
- incorporar informações socioeconômicas.

A seleção definitiva dos campos utilizados na implementação será realizada durante a preparação dos dados.

### 3.5 Indicadores e análises previstas

Entre as análises previstas estão:

- distância para a meta;
- atingimento da meta;
- evolução dos resultados;
- evolução em relação às metas até 2030;
- comparação de desempenho entre UFs;
- relação entre desempenho e contexto educacional;
- relação entre desempenho e contexto socioeconômico;
- análise integrada por município.

### 3.6 Modelos de relatórios e visualizações

Foram definidos modelos de análises e visualizações que poderão ser implementados posteriormente a partir da Camada Gold, incluindo:

- acompanhamento das metas de alfabetização;
- comparação entre Unidades da Federação;
- análise do contexto educacional;
- análise do contexto socioeconômico;
- visão integrada por município.

---

## 4. Leitura e validação das camadas — Notebook 3

### 4.1 Objetivo

O notebook **Consultas Camadas** realiza a leitura e a conferência dos dados materializados nas camadas Bronze, Prata e Gold no ambiente AWS.

Ele complementa os notebooks anteriores, permitindo verificar as estruturas disponíveis no S3 e utilizar os datasets analíticos preparados para as consultas de negócio.

### 4.2 Principais atividades

O notebook contempla:

- configuração da sessão AWS e dos buckets utilizados;
- verificação das estruturas disponíveis nas camadas;
- leitura dos datasets da Camada Bronze;
- leitura dos datasets tratados da Camada Prata;
- leitura dos datasets analíticos da Camada Gold;
- conferência de dimensões e tipos dos dados;
- utilização de amostras para bases de grande volume;
- leitura por partição quando aplicável;
- preparação e execução das consultas analíticas.

### 4.3 Estruturas consultadas na Camada Gold

Entre as principais estruturas utilizadas estão:

- `indicador_municipio`;
- `indicador_uf`;
- `indicador_brasil`;
- `metas_vs_resultado_municipio`;
- `metas_vs_resultado_uf`;
- `metas_vs_resultado_brasil`;
- `evolucao_temporal_municipio`;
- `evolucao_temporal_uf`;
- `evolucao_temporal_brasil`;
- `ml_aluno`.

Essas estruturas permitem realizar análises de resultados, metas, evolução temporal e preparação para análises de Machine Learning.

### 4.4 Leitura de bases de grande volume

A tabela `alunos` possui grande volume de registros. Por isso, o notebook utiliza leitura por blocos/amostras durante as etapas de conferência, evitando a necessidade de carregar integralmente a base quando a análise não exige todos os registros.

Para análises que dependem da totalidade dos dados, devem ser utilizados o dataset completo ou filtros de partição adequados.

### 4.5 Papel do Notebook 3 no projeto

O Notebook 3 representa a etapa de **consumo e validação analítica** dos dados já disponibilizados nas camadas, conectando a preparação realizada nos notebooks anteriores às consultas que respondem às perguntas de negócio.

---

## 5. Relação com as camadas de dados

Os notebooks cobrem etapas complementares do fluxo: levantamento e análise das fontes, definição dos relacionamentos e, no Notebook 3, leitura, validação e consulta dos dados materializados.

### 4.1 Camada Bronze

As fontes de dados são disponibilizadas na Camada Bronze, preservando as informações de origem para utilização nas etapas posteriores.

### 4.2 Camada Prata

As definições realizadas nos notebooks apoiam:

- seleção das variáveis;
- padronização;
- tratamento dos dados;
- normalização das chaves;
- validação dos relacionamentos;
- integração das fontes.

### 4.3 Camada Gold

As perguntas e análises definidas no notebook **Relacionamento e Análise das Bases**, e posteriormente consultadas no **Notebook 3**, orientam a construção e o consumo de:

- indicadores;
- tabelas analíticas;
- estruturas para comparação de metas e resultados;
- análises temporais;
- informações destinadas aos relatórios e visualizações.

---

### 5.4 Fluxo entre os notebooks

```text
Análise de Dados
      ↓
Relacionamento e Análise das Bases
      ↓
Preparação das camadas
      ↓
Consultas Camadas — Notebook 3
      ↓
Perguntas de análise e resultados
```

## 6. Resultado esperado

Os três notebooks formam uma sequência complementar: o **Análise de Dados** apresenta quais dados estão disponíveis; o **Relacionamento e Análise das Bases** define quais informações e relacionamentos são necessários; e o **Notebook 3 — Consultas Camadas** lê, confere e consulta as estruturas materializadas nas camadas, especialmente na Gold, para responder às perguntas de análise.