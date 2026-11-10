# Especificação de requisitos — Veltis

* **Projeto:** Veltis
* **Versão:** 0.4 (revisão de 2026-11-10: requisitos de consulta agrupados a pedido do orientador — de 14 para 8 requisitos funcionais; a versão 0.3 está no histórico do Git)
* **Data:** 2026-11-10
* **Escopo:** portal web para consultar escolas, faculdades, cursos e indicadores demográficos dos 27 municípios da Região Metropolitana de Sorocaba (RMS) e ver a localização das instituições no mapa. Dashboards em Power BI e Data Warehouse estão fora do escopo desta versão (ver `docs/decisoes/DEC-007`).

**Estados usados:** *Implementado* (feito e testado), *Em desenvolvimento*, *A validar* (feito, falta teste com usuários), *Planejado*.
A coluna **API** indica se o backend já entrega o que o requisito precisa; a coluna **Interface** indica o estado no frontend.

## 1. Requisitos funcionais (RF)

| ID | Nome | Descrição | Prioridade | Caso de uso | API | Interface |
| - | - | - | - | - | - | - |
| RF-01 | Visualizar o mapa da RMS | O sistema deve exibir, na abertura, o mapa com a malha dos 27 municípios da RMS e permitir mostrar ou ocultar as camadas (municípios, escolas, faculdades). | Alta | UC-01, UC-02 | Implementado (`/municipios`, GeoJSON) | Implementado; camadas planejadas |
| RF-02 | Selecionar município | O sistema deve permitir escolher um município para consultar as instituições e os dados relacionados a ele. | Alta | UC-02, UC-04, UC-07 | Implementado (`?municipio=`) | Implementado |
| RF-03 | Filtrar e pesquisar instituições | O sistema deve permitir filtrar as instituições por tipo (escola, ETEC, FATEC, faculdade/universidade) e por rede, e pesquisar pelo nome ou sigla, sem diferenciar maiúsculas e acentos. | Alta | UC-04, UC-07 | Implementado (`?tipo=`, `?dependencia=`, `?rede=`, `?busca=`) | Implementado |
| RF-04 | Exibir as instituições no mapa | O sistema deve exibir no mapa os pontos das escolas e faculdades que têm coordenada e listar à parte as escolas sem localização, para que não pareçam ausentes. | Alta | UC-04 | Implementado (`/mapa/instituicoes`, `/escolas/sem-localizacao`) | Implementado; lista "sem localização" planejada |
| RF-05 | Consultar instituição e cursos | O sistema deve permitir selecionar uma instituição e ver seus dados (endereço, telefone, rede) e os cursos oferecidos: cursos técnicos das escolas e cursos superiores das faculdades no município. | Alta | UC-05, UC-06 | Implementado (`/mapa/instituicoes`, `/escolas/{codigo}`, `/cursos-tecnicos`, `/cursos-superiores`) | Implementado |
| RF-06 | Consultar indicadores municipais | O sistema deve apresentar os indicadores do IBGE de cada município (população, sexo, faixas de idade, alfabetização, frequência escolar, escolaridade) e um resumo da educação. | Média | UC-03 | Implementado (`/municipios/{codigo}`) | Planejado |
| RF-07 | Exibir fontes e atualização | O sistema deve exibir as fontes oficiais dos dados e a data da última carga. | Média | UC-01 | Implementado (`/fontes`) | Planejado |
| RF-08 | Atualizar a base de dados | O administrador deve conseguir baixar, validar e carregar novamente os dados oficiais com um comando, sem duplicar registros. | Alta | UC-08 | Implementado (pipelines) | Não se aplica |

### Correspondência com a versão 0.3

| Versão 0.4 | Requisitos da versão 0.3 agrupados |
| - | - |
| RF-01 | RF-01 Consultar municípios, RF-02 Visualizar mapa, RF-11 Ativar ou desativar camadas |
| RF-02 | RF-03 Filtrar por município |
| RF-03 | RF-04 Filtrar por tipo, RF-05 Filtrar por rede, RF-06 Pesquisar instituições |
| RF-04 | RF-07 Exibir instituições no mapa, RF-12 Listar escolas sem localização |
| RF-05 | RF-08 Consultar detalhes, RF-09 Consultar cursos |
| RF-06 | RF-10 Consultar indicadores municipais |
| RF-07 | RF-13 Exibir fontes e atualização |
| RF-08 | RF-14 Atualizar a base de dados |

## 2. Requisitos não funcionais (RNF)

| ID | Atributo | Descrição | Critério de verificação | Prioridade / estado |
| - | - | - | - | - |
| RNF-01 | Usabilidade | A interface deve apresentar filtros, mapa e informações das instituições de forma clara e simples. | Selecionar um município, aplicar filtros e consultar uma instituição sem ajuda. | Alta / A validar |
| RNF-02 | Desempenho da interface | O mapa deve carregar rápido e continuar fluido com todas as instituições da região. | Abrir a aplicação e navegar no mapa sem travamentos. | Alta / A validar |
| RNF-03 | Desempenho das consultas | As consultas devem respeitar os filtros e devolver só o necessário; listas longas são paginadas (máx. 500 itens) e as respostas grandes são comprimidas. | Testar endereços com filtros diferentes; tempo de resposta local abaixo de 1 s. | Média / Implementado na API |
| RNF-04 | Integração | O frontend deve obter os dados pela API do projeto e exibi-los no serviço de mapas (MapTiler). | Dados da API aparecem corretamente no mapa e no painel. | Alta / Implementado |
| RNF-05 | Manutenibilidade | O código deve ser organizado em módulos (coletores, transformações, validações, cargas, rotas) para que uma mudança não afete as demais partes. | Testes automáticos passam após cada mudança. | Média / Implementado no backend |
| RNF-06 | Confiabilidade das informações | Os dados exibidos devem corresponder às fontes oficiais e aos registros da API. | Comparar interface, API e banco; verificação do banco sem erros. | Alta / A validar |
| RNF-07 | Segurança | A API só lê o banco (transação somente leitura, tempo limite de 10 s), valida todos os parâmetros e não expõe credenciais nem detalhes técnicos em erros. As tabelas têm RLS ligado. | Testes CT-11 a CT-13 (`docs/testes/`). | Alta / Implementado |
| RNF-08 | Integridade e rastreabilidade | O banco impede registros duplicados (chaves únicas) e cada linha guarda a carga que a gerou (`ID_INGESTAO`). | Testes CT-09 e CT-10; verificação do banco. | Alta / Implementado |
| RNF-09 | Reprodutibilidade | As edições das fontes e as versões das bibliotecas ficam fixas; rodar o pipeline de novo produz o mesmo banco. | Rodar o pipeline duas vezes: a segunda não recarrega nem duplica. | Média / Implementado |
| RNF-10 | Licenças e atribuição | O site deve citar IBGE, INEP, SEDUC-SP, MapTiler/OpenStreetMap e, para pontos calculados, "IBGE CNEFE 2022 / geocodebr (Ipea)". | Conferir o rodapé e a página de fontes. | Média / Planejado |

## 3. Regras de negócio (RN)

| ID | Regra | Origem / validação | Requisitos relacionados | Estado |
| - | - | - | - | - |
| RN-01 | Ao selecionar um município, a consulta considera apenas as instituições daquele município. | Comportamento dos filtros. | RF-02, RF-04 | Implementado |
| RN-02 | Os filtros podem ser combinados (município, tipo, rede e nome); sem filtro, o mapa mostra todas as instituições da RMS. | Comportamento do mapa (frontend). | RF-02, RF-03, RF-04 | Implementado |
| RN-03 | Uma instituição só aparece como ponto quando tem coordenada válida e dentro do próprio município. | Validação dos pipelines (`ponto_confere_municipio`). | RF-04, RNF-06 | Implementado |
| RN-04 | Falta de coordenada não exclui a instituição: ela continua contada e aparece na lista "sem localização". | Necessidade identificada nos testes. | RF-04 | Implementado na API |
| RN-05 | Ao remover a seleção do município, o mapa volta a mostrar a RMS inteira. | Comportamento do mapa. | RF-01, RF-02 | Implementado |
| RN-06 | No SIDRA, cada valor vale para uma combinação de município, período, variável e classificação (sexo, idade...); as categorias são pedidas uma a uma para não contar em dobro, e taxas (%) nunca são somadas entre municípios. | DEC-003. | RF-06 | Implementado |
| RN-07 | Coordenada oficial (Catálogo INEP, depois SEDUC-SP) tem prioridade. Sem ela, o ponto pode ser calculado pelo endereço (IBGE CNEFE) apenas com precisão de número ou de rua; centro de CEP, bairro ou município nunca é usado. A precisão de cada ponto é informada. | DEC-002, DEC-004. | RF-04, RNF-06 | Implementado |
| RN-08 | O recorte é a RMS com 27 municípios (Lei Complementar estadual 1.241/2014 e 1.289/2016, que incluiu Itapetininga). | Configuração `src/config/rms.py`. | RF-01 | Implementado |
| RN-09 | O município de um curso superior é o **local de oferta**, não a sede da instituição; só entram as ofertas presenciais e as EAD com alunos no município. | DEC-006. | RF-05 | Implementado |
| RN-10 | O Censo Escolar define quais escolas existem; Catálogo INEP e SEDUC-SP só complementam endereço e coordenada. | DEC-004. | RF-04, RF-05 | Implementado |

## 4. Critérios de aceite e validação

| Requisito | Cenário / condição | Resultado esperado | Método / evidência | Situação |
| - | - | - | - | - |
| RF-01 | A aplicação é aberta. | A malha dos 27 municípios aparece no mapa. | Teste visual no navegador; resposta de `/municipios`. | Implementado |
| RF-02 | O usuário seleciona um município. | Só as instituições do município aparecem. | Teste com municípios que têm registros. | Implementado |
| RF-03 | O usuário escolhe um tipo e uma rede e pesquisa "sao roque". | Os resultados respeitam os filtros e encontram "São Roque". | CT-15; `/mapa/instituicoes?tipo=`; interface. | Implementado |
| RF-04 | Há instituições com e sem coordenada no município. | As com coordenada aparecem nos pontos certos; as sem coordenada vão para a lista à parte. | CT-14; `/escolas/sem-localizacao`. | Implementado na API; lista a fazer na interface |
| RF-05 | O usuário seleciona uma instituição. | O painel mostra os dados e os cursos daquela instituição no município. | Conferência com `/escolas/{codigo}` e `/cursos-superiores`. | Implementado; validar |
| RF-06 | O usuário abre a ficha de um município. | Os indicadores batem com o IBGE. | `/municipios/{codigo}`. | API implementada |
| RF-08 | O administrador roda o pipeline duas vezes. | A segunda execução não duplica dados; a verificação termina sem erros. | `python -m src.pipeline`; `docs/testes/` §4.2 e §4.5. | Implementado |
| RNF-04 | O frontend consulta a API e mostra o mapa. | Os dados da API aparecem corretamente. | Teste de integração frontend + API. | Implementado |
| RNF-06 | Uma instituição é exibida no painel. | As informações batem com a API e com a fonte oficial. | Comparação interface × API × fonte. | A validar |
| RNF-07 | Filtro inválido, banco fora do ar, tentativa de escrita. | 422, 503 sem detalhe técnico, escrita recusada. | CT-11 a CT-13. | Implementado |
