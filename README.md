# Pipeline de Dados — Alfabetização

## Sobre o projeto

Este projeto tem como objetivo estruturar uma pipeline de dados para organização, tratamento e análise de informações relacionadas à alfabetização no Brasil.

A solução foi construída em ambiente AWS, utilizando uma arquitetura em camadas para organizar os dados desde sua origem até a disponibilização de estruturas analíticas para consultas e análises.

O projeto contempla o levantamento e análise das fontes, definição das perguntas de negócio, preparação das informações, materialização das camadas de dados e consulta das estruturas analíticas.

## Objetivo

Organizar e disponibilizar dados de alfabetização de forma estruturada, permitindo análises relacionadas ao desempenho dos municípios e Unidades da Federação, ao atingimento das metas e à evolução dos indicadores ao longo do período analisado.

A solução também foi estruturada de forma a permitir sua evolução futura para novas análises, relatórios e aplicações de Inteligência Artificial.

## Fontes de dados

### Base principal — Avaliação da Alfabetização

Fonte principal utilizada no projeto, contendo informações relacionadas aos resultados de alfabetização, municípios, Unidades da Federação e metas de alfabetização.

### API de Localidades — IBGE

Utilizada como fonte de apoio para identificação e relacionamento das informações municipais, incluindo códigos e nomes dos municípios e informações territoriais utilizadas nas análises.

> **Observação:** Censo Escolar 2023 e INSE 2023 foram analisados durante a etapa exploratória do projeto, mas não fazem parte das fontes utilizadas na versão final das análises.

## Estrutura do projeto

O projeto foi organizado em três notebooks complementares.

### Notebook 1 — Análise de Dados

Responsável pelo levantamento e análise das fontes de dados utilizadas no projeto.

Principais atividades:

- análise da Base de Avaliação da Alfabetização;
- identificação das tabelas e estruturas disponíveis;
- levantamento de variáveis;
- identificação dos tipos de dados;
- análise dos padrões de nomenclatura;
- consulta à API de Localidades do IBGE;
- identificação das informações necessárias para as etapas posteriores.

### Notebook 2 — Relacionamento e Análise das Bases

Responsável pela definição das perguntas de análise e pelo levantamento dos dados e relacionamentos necessários para respondê-las.

Principais atividades:

- definição das perguntas de análise;
- identificação dos dados necessários;
- definição das chaves de relacionamento;
- definição das variáveis necessárias;
- preparação das informações para as camadas Prata e Gold;
- definição das análises e visualizações possíveis.

### Notebook 3 — Consultas Camadas

Responsável pela leitura, conferência e consulta dos dados materializados nas camadas Bronze, Prata e Gold no ambiente AWS.

Principais atividades:

- configuração e acesso aos buckets;
- conferência das estruturas disponíveis;
- leitura das camadas Bronze e Prata;
- leitura e consulta das estruturas da Gold;
- conferência de dimensões e tipos;
- leitura por amostra para bases de grande volume;
- utilização de partições quando aplicável;
- consultas orientadas às perguntas de análise.

## Perguntas de análise

As análises do projeto foram orientadas pelas seguintes perguntas:

1. Qual é o indicador de alfabetização por município?
2. Quais municípios atingiram ou superaram as metas estabelecidas?
3. Como o indicador de alfabetização evoluiu entre 2019 e 2025?
4. Qual é a distância entre a meta estabelecida e o resultado observado por município?
5. Quais regiões concentram maior desigualdade nos resultados de alfabetização?
6. Qual porte de município apresenta melhor desempenho de alfabetização?

## Arquitetura de dados

A solução utiliza uma arquitetura em camadas:

```text
Fontes de dados
      ↓
   Bronze
      ↓
   Prata
      ↓
    Gold
      ↓
Consultas e análises