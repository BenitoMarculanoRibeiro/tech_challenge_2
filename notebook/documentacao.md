
## DOCUMENTAÇÃO.md

# Documentação Técnica — Pipeline de Dados de Alfabetização

## 1. Visão geral

O projeto consiste na construção de uma pipeline de dados destinada à organização, tratamento e análise de informações relacionadas à alfabetização no Brasil.

A solução utiliza uma arquitetura em camadas no ambiente AWS, permitindo organizar os dados desde sua origem até a disponibilização de estruturas analíticas para consultas.

O desenvolvimento foi estruturado em três notebooks complementares:

1. Análise de Dados;
2. Relacionamento e Análise das Bases;
3. Consultas Camadas.

Os dois primeiros notebooks são responsáveis pelo levantamento e planejamento analítico, enquanto o terceiro realiza a leitura, conferência e consulta das estruturas materializadas nas camadas de dados.

## 2. Fontes de dados

### 2.1 Base principal — Avaliação da Alfabetização

A Base de Avaliação da Alfabetização constitui a principal fonte de dados utilizada no projeto.

Entre as informações disponíveis estão:

- resultados de alfabetização;
- identificação dos municípios;
- identificação das Unidades da Federação;
- metas de alfabetização;
- informações relacionadas aos alunos;
- informações utilizadas para análises temporais.

A base constitui a principal fonte para os indicadores e comparações realizados no projeto.

### 2.2 API de Localidades — IBGE

A API de Localidades do IBGE é utilizada como fonte de apoio para identificação e relacionamento das informações municipais.

A consulta permite obter informações de identificação dos municípios, incluindo seus códigos e nomes, utilizadas no relacionamento com os dados da avaliação.

As informações territoriais obtidas por meio da API também apoiam as análises que envolvem Unidades da Federação, regiões e características municipais.

### 2.3 Fontes analisadas na etapa exploratória

Durante o levantamento inicial foram avaliadas outras fontes que poderiam complementar as análises, incluindo:

- Censo Escolar 2023;
- INSE 2023 — Indicador de Nível Socioeconômico.

Após a avaliação das fontes e considerando o escopo final do projeto, essas bases não foram incorporadas às análises finais.

Dessa forma, a versão final da solução utiliza a Base de Avaliação da Alfabetização e a API de Localidades do IBGE como fontes consideradas no fluxo analítico.

## 3. Notebook 1 — Análise de Dados

### 3.1 Objetivo

O notebook Análise de Dados tem como objetivo identificar as fontes, estruturas e variáveis disponíveis para o desenvolvimento do projeto.

A análise permite compreender:

- quais dados estão disponíveis;
- como as tabelas estão estruturadas;
- quais variáveis podem ser utilizadas;
- quais chaves podem ser utilizadas nos relacionamentos;
- quais informações são necessárias para as análises posteriores.

### 3.2 Principais atividades

O notebook contempla:

- análise da Base de Avaliação da Alfabetização;
- identificação das tabelas disponíveis;
- levantamento de variáveis;
- identificação dos tipos de dados;
- análise dos padrões de nomenclatura;
- consulta à API de Localidades do IBGE;
- identificação das informações necessárias para as etapas seguintes.

### 3.3 API de Localidades do IBGE

A consulta à API do IBGE é utilizada para complementar a identificação municipal.

O relacionamento utiliza o identificador municipal como chave para associar as informações territoriais aos dados da avaliação.

Essa etapa permite padronizar a identificação dos municípios e apoiar análises por município, UF e região.

### 3.4 Resultado do levantamento

O levantamento realizado no Notebook 1 fornece a base necessária para a definição das perguntas de análise e dos relacionamentos tratados no Notebook 2.

## 4. Notebook 2 — Relacionamento e Análise das Bases

### 4.1 Objetivo

O notebook Relacionamento e Análise das Bases tem como objetivo definir as perguntas que orientarão as análises e identificar os dados necessários para respondê-las.

A partir do levantamento realizado no Notebook 1, são avaliadas as variáveis, chaves e possibilidades de relacionamento necessárias para as análises.

### 4.2 Perguntas de análise

As análises do projeto foram organizadas a partir das seguintes perguntas:

1. Qual é o indicador de alfabetização por município?
2. Quais municípios atingiram ou superaram as metas estabelecidas?
3. Como o indicador de alfabetização evoluiu entre 2019 e 2025?
4. Qual é a distância entre a meta estabelecida e o resultado observado por município?
5. Quais regiões concentram maior desigualdade nos resultados de alfabetização?
6. Qual porte de município apresenta melhor desempenho de alfabetização?

### 4.3 Dados necessários

A definição dos dados necessários considera as informações disponíveis na Base de Avaliação da Alfabetização e os dados de identificação e caracterização municipal obtidos por meio da API do IBGE.

Entre as principais informações necessárias estão:

- ano;
- município;
- UF;
- região;
- porte municipal;
- resultado de alfabetização;
- metas de alfabetização;
- identificadores utilizados nos relacionamentos.

### 4.4 Relacionamentos

Os relacionamentos são definidos a partir das chaves disponíveis nas fontes utilizadas.

O principal relacionamento municipal utiliza:
id_municipio