# Notebooks — Análise e Relacionamento de Dados

## Sobre

Esta pasta reúne os notebooks desenvolvidos para o levantamento, análise, planejamento e consulta dos dados do projeto.

Os notebooks documentam as fontes disponíveis, as variáveis identificadas, as perguntas de análise, os relacionamentos necessários entre as bases e a leitura das estruturas materializadas nas camadas Bronze, Prata e Gold.

---

## Notebooks

### Análise de Dados

Realiza o levantamento e a análise das fontes de dados utilizadas no projeto.

O notebook contempla:

- análise da Base Principal — Avaliação da Alfabetização;
- análise do Censo Escolar 2023;
- análise do INSE 2023;
- identificação de tabelas e estruturas;
- levantamento de variáveis;
- identificação dos tipos de dados;
- análise dos padrões de nomenclatura;
- identificação das informações disponíveis para as etapas posteriores.

O notebook tem como objetivo responder:

> **Quais dados estão disponíveis nas fontes utilizadas no projeto?**

---

### Relacionamento e Análise das Bases

Utiliza o levantamento realizado no notebook **Análise de Dados** para definir as informações necessárias às análises do projeto.

O notebook contempla:

- definição das perguntas de análise;
- identificação dos dados necessários;
- matriz inicial de dados;
- definição dos relacionamentos entre as bases;
- definição das variáveis necessárias;
- preparação das informações para as camadas Prata e Gold;
- modelos de relatórios e visualizações.

O notebook tem como objetivo responder:

> **Quais informações são necessárias e como elas podem ser relacionadas para responder às perguntas de análise?**

---

### Consultas Camadas

Realiza a leitura, conferência e consulta dos dados materializados nas camadas Bronze, Prata e Gold no ambiente AWS.

O notebook contempla:

- configuração e acesso aos buckets;
- conferência das estruturas disponíveis;
- leitura das camadas Bronze e Prata;
- leitura e consulta das estruturas da Gold;
- conferência de dimensões e tipos;
- leitura por amostra para bases de grande volume;
- uso de partições quando aplicável;
- consultas orientadas às perguntas de análise.

Entre as principais estruturas consultadas na Gold estão `indicador_municipio`, `indicador_uf`, `indicador_brasil`, `metas_vs_resultado_municipio`, `metas_vs_resultado_uf`, `metas_vs_resultado_brasil`, `evolucao_temporal_municipio`, `evolucao_temporal_uf`, `evolucao_temporal_brasil` e `ml_aluno`.

O notebook tem como objetivo responder:

> **Os dados materializados nas camadas estão disponíveis e estruturados para responder às perguntas de análise?**

---

## Fluxo dos notebooks

```text
Análise de Dados
      ↓
Relacionamento e Análise das Bases
      ↓
Preparação das camadas
      ↓
Consultas Camadas
      ↓
Perguntas de análise e resultados
```

## Fontes de dados

Os notebooks consideram:

### Base Principal

**Avaliação da Alfabetização**

Contém as informações centrais utilizadas nas análises de alfabetização, incluindo resultados, municípios, Unidades da Federação e metas de alfabetização.

### Fonte Complementar 1

**Censo Escolar 2023**

Fonte utilizada para complementar o contexto educacional das análises, incluindo informações relacionadas às unidades escolares e à educação profissional técnica.

### Fonte Complementar 2

**INSE 2023 — Indicador de Nível Socioeconômico**

Fonte externa utilizada para incorporar informações relacionadas ao contexto socioeconômico em diferentes níveis de agregação.

### API IBGE

Consulta utilizada como apoio à identificação e ao relacionamento das informações municipais.

---

## Relação com as camadas de dados

Os notebooks fazem parte da etapa de levantamento e planejamento analítico do projeto.

```text
Fontes de dados
      ↓
Camada Bronze
      ↓
Análise e relacionamento
      ↓
Camada Prata
      ↓
Camada Gold
      ↓
Consultas e indicadores
      ↓
Relatórios e análises