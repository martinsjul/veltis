# Especificação de requisitos — Veltis

* **Projeto:** Veltis 
* **Versão:** 0.2
* **Data:** 2026-11-03
* **Escopo:** aplicação web para consultar instituições de ensino e visualizar sua localização nos municípios da Região Metropolitana de Sorocaba.

## 1\. Requisitos funcionais (RF)

|ID|Nome|Descrição|Prioridade|Caso de uso|Estado|
|-|-|-|-|-|-|
|RF-01|Consultar municípios|O sistema deve apresentar os municípios disponíveis para consulta.|Alta|UC-01 — Consultar municípios|Implementado|
|RF-02|Visualizar mapa|O sistema deve exibir a malha geográfica dos municípios na abertura da aplicação.|Alta|UC-02 — Visualizar mapa|Implementado|
|RF-03|Filtrar por município|O sistema deve permitir selecionar um município para consultar as instituições relacionadas a ele.|Alta|UC-03 — Filtrar instituições|Implementado|
|RF-04|Filtrar por tipo de ensino|O sistema deve permitir filtrar as instituições por tipo de ensino, incluindo educação básica e ensino superior.|Alta|UC-04 — Filtrar por tipo de ensino|Implementado|
|RF-05|Filtrar por rede|O sistema deve permitir filtrar as instituições por rede pública ou privada, conforme os dados disponíveis.|Média|UC-05 — Filtrar por rede|Implementado|
|RF-06|Pesquisar instituições|O sistema deve permitir pesquisar instituições pelo nome ou por outros campos definidos na interface.|Média|UC-06 — Pesquisar instituições|Em desenvolvimento|
|RF-07|Exibir instituições no mapa|O sistema deve exibir no mapa os pontos das instituições do município selecionado que possuam coordenadas disponíveis.|Alta|UC-07 — Visualizar instituições|Implementado|
|RF-08|Consultar detalhes|O sistema deve permitir selecionar uma instituição e visualizar seus dados em um painel de detalhes.|Alta|UC-08 — Consultar detalhes|Em desenvolvimento|
|RF-09|Consultar cursos superiores|O sistema deve apresentar os cursos associados às instituições de ensino superior, conforme os dados disponíveis na base.|Média|UC-09 — Consultar cursos|A confirmar|
|RF-10|Consultar indicadores municipais|O sistema deve permitir consultar os indicadores disponíveis para cada município.|Média|UC-10 — Consultar indicadores|A confirmar|

## 2\. Requisitos não funcionais (RNF)

|ID|Atributo|Descrição|Critério de verificação|Prioridade/estado|
|-|-|-|-|-|
|RNF-01|Usabilidade|A interface deve apresentar filtros, mapa e informações das instituições de forma clara e simples.|Verificar se é possível selecionar um município, aplicar filtros e consultar uma instituição sem dificuldade.|Alta / A validar|
|RNF-02|Desempenho|O sistema deve evitar carregar pontos de instituições antes da seleção de um município.|Abrir a aplicação e verificar se as malhas aparecem sem os pontos das instituições.|Alta / Em desenvolvimento|
|RNF-03|Desempenho das consultas|As consultas devem considerar os filtros selecionados e evitar carregar resultados que não serão exibidos.|Testar consultas com diferentes municípios e filtros.|Média / A validar|
|RNF-04|Integração|O sistema deve utilizar a API do projeto para obter os dados e o serviço de mapas configurado para exibi-los.|Verificar se os dados são recebidos pela API e apresentados corretamente no mapa e na interface.|Alta / Em desenvolvimento|
|RNF-05|Manutenibilidade|O código deve ser organizado de forma que alterações em filtros, consultas e mapa possam ser feitas sem comprometer as demais funcionalidades.|Verificar se alterações em um componente não impedem o funcionamento das outras partes do sistema.|Média / A validar|
|RNF-06|Confiabilidade das informações|Os dados apresentados devem corresponder aos registros recebidos da API.|Comparar as informações exibidas com os dados retornados pelos endpoints.|Alta / A validar|

## 3\. Regras de negócio (RN)

|ID|Regra|Origem/validação|Requisitos relacionados|Estado|
|-|-|-|-|-|
|RN-01|Ao selecionar um município, a consulta deve considerar apenas as instituições relacionadas a ele.|Comportamento definido para os filtros do sistema.|RF-03, RF-07|Em desenvolvimento|
|RN-02|Os pontos das instituições devem ser exibidos somente quando um município estiver selecionado.|Comportamento definido para o carregamento do mapa.|RF-02, RF-03, RF-07|Em desenvolvimento|
|RN-03|Uma instituição só deve aparecer como ponto no mapa quando possuir coordenadas válidas.|Limitação dos dados geográficos utilizados pelo mapa.|RF-07, RNF-06|A validar|
|RN-04|A falta de coordenadas não deve impedir que uma instituição seja contabilizada ou apresentada nos resultados da consulta.|Necessidade identificada durante os testes do sistema.|RF-03, RF-07|A validar|
|RN-05|Ao remover a seleção do município, os pontos das instituições devem deixar de ser exibidos, mantendo a malha geográfica.|Comportamento definido para o mapa.|RF-02, RF-03, RF-07|Em desenvolvimento|

## 4\. Critérios de aceite e validação

|Requisito|Cenário/condição|Resultado esperado|Método/evidência|Situação|
|-|-|-|-|-|
|RF-01|A aplicação é iniciada e consulta os municípios à API.|Os municípios retornados ficam disponíveis para seleção.|Teste da interface e conferência da resposta da API.|Implementado|
|RF-02|A aplicação é aberta sem município selecionado.|A malha geográfica aparece sem pontos de instituições.|Teste visual no navegador.|Implementado|
|RF-03|O usuário seleciona um município.|A consulta considera as instituições relacionadas ao município escolhido.|Teste com municípios que possuam registros.|Implementado|
|RF-04|O usuário seleciona um tipo de ensino.|Os resultados são filtrados conforme o tipo selecionado.|Teste com registros de educação básica e ensino superior.|Implementado|
|RF-05|O usuário seleciona uma rede administrativa.|São apresentados os registros correspondentes à rede escolhida.|Teste com registros públicos e privados.|Implementado; validar|
|RF-06|O usuário pesquisa pelo nome de uma instituição.|O sistema apresenta os resultados correspondentes ao termo informado.|Teste com nomes de instituições cadastradas.|A confirmar|
|RF-07|Há um município selecionado e instituições com coordenadas válidas.|Os pontos dessas instituições aparecem nas posições correspondentes no mapa.|Comparação dos pontos com as coordenadas recebidas da API.|Implementado; validar|
|RF-08|O usuário seleciona uma instituição.|O painel apresenta os dados disponíveis daquela instituição.|Teste com instituições cadastradas.|Implementado|
|RF-09|O usuário consulta uma instituição de ensino superior com cursos associados.|Os cursos disponíveis são apresentados relacionados à instituição.|Conferência com os dados retornados pela API.|A validar|
|RNF-01|O usuário realiza uma consulta utilizando os filtros.|Os controles e resultados podem ser identificados e utilizados com clareza.|Teste de uso da interface.|A validar|
|RNF-02|A aplicação é aberta sem filtro de município.|O mapa carrega as malhas sem criar pontos de instituições.|Inspeção visual e verificação do mapa.|Implementado; validar|
|RNF-04|A aplicação consulta os dados e apresenta o mapa.|Os dados da API são exibidos corretamente na interface.|Teste de integração com a API e o serviço de mapas.|A validar|
|RNF-06|Uma instituição é exibida na lista ou no painel de detalhes.|As informações apresentadas correspondem ao registro recebido da API.|Comparação entre a interface e a resposta da API.|A validar|



