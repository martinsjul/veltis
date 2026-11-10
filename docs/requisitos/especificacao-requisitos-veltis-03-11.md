# Especificação de requisitos — Veltis

* **Projeto:** Veltis
* **Versão:** 0.3 (revisão de 2026-11-03: numeração alinhada aos casos de uso, requisitos do backend e regras de dados)
* **Data:** 2026-11-03
* **Escopo:** portal web para consultar escolas, faculdades, cursos e indicadores demográficos dos 27 municípios da Região Metropolitana de Sorocaba (RMS) e ver a localização das instituições no mapa. Dashboards em Power BI e Data Warehouse estão fora do escopo desta versão (ver `docs/decisoes/DEC-007`).

**Estados usados:** *Implementado* (feito e testado), *Em desenvolvimento*, *A validar* (feito, falta teste com a interface real), *Planejado*.
A coluna **API** indica se o backend já entrega o que o requisito precisa; a coluna **Interface** indica o estado no frontend.

## 1. Requisitos funcionais (RF)

| ID | Nome | Descrição | Prioridade | Caso de uso | API | Interface |
| - | - | - | - | - | - | - |
| RF-01 | Consultar municípios | O sistema deve apresentar os 27 municípios da RMS para seleção. | Alta | UC-02 | Implementado (`/filtros`, `/municipios`) | Implementado |
| RF-02 | Visualizar mapa | O sistema deve exibir a malha geográfica dos municípios na abertura da aplicação. | Alta | UC-01 | Implementado (`/municipios`, GeoJSON) | Implementado |
| RF-03 | Filtrar por município | O sistema deve permitir selecionar um município para consultar as instituições relacionadas a ele. | Alta | UC-02, UC-10 | Implementado (`?municipio=`) | Implementado |
| RF-04 | Filtrar por tipo de instituição | O sistema deve permitir filtrar por tipo: escola, ETEC, FATEC e faculdade/universidade. | Alta | UC-10 | Implementado (`?tipo=`) | Implementado |
| RF-05 | Filtrar por rede | O sistema deve permitir filtrar por rede (escolas: federal, estadual, municipal, privada; faculdades: pública, privada). | Média | UC-10 | Implementado (`?dependencia=`, `?rede=`) | Implementado; validar |
| RF-06 | Pesquisar instituições | O sistema deve permitir pesquisar instituições pelo nome ou sigla, sem diferenciar maiúsculas e acentos. | Média | UC-10 | Implementado (`?busca=`) | Em desenvolvimento |
| RF-07 | Exibir instituições no mapa | O sistema deve exibir no mapa os pontos das escolas e faculdades que possuam coordenadas. | Alta | UC-04, UC-07 | Implementado (`/mapa/instituicoes`) | Implementado; validar com a API |
| RF-08 | Consultar detalhes | O sistema deve permitir selecionar uma instituição e ver seus dados (endereço, telefone, rede, ofertas) num painel. | Alta | UC-05, UC-08 | Implementado (`/escolas/{codigo}`, `/mapa/instituicoes`) | Em desenvolvimento |
| RF-09 | Consultar cursos | O sistema deve apresentar os cursos técnicos de cada escola e os cursos superiores de cada faculdade no município. | Média | UC-06, UC-09 | Implementado (`/cursos-tecnicos`, `/cursos-superiores`) | A validar |
| RF-10 | Consultar indicadores municipais | O sistema deve apresentar os indicadores do IBGE de cada município (população, sexo, faixas de idade, alfabetização, frequência escolar, escolaridade) e um resumo da educação. | Média | UC-03 | Implementado (`/municipios/{codigo}`) | Planejado |
| RF-11 | Ativar ou desativar camadas | O sistema deve permitir mostrar ou ocultar as camadas do mapa (municípios, escolas, faculdades). | Baixa | UC-11 | Não se aplica | Planejado |
| RF-12 | Listar escolas sem localização | O sistema deve listar à parte as escolas que não têm ponto no mapa, para que não pareçam ausentes. | Média | UC-04 | Implementado (`/escolas/sem-localizacao`) | Planejado |
| RF-13 | Exibir fontes e atualização | O sistema deve exibir as fontes oficiais dos dados e a data da última carga. | Média | UC-01 | Implementado (`/fontes`) | Planejado |
| RF-14 | Atualizar a base de dados | O administrador deve conseguir baixar, validar e carregar novamente os dados oficiais com um comando, sem duplicar registros. | Alta | UC-12 | Implementado (pipelines) | Não se aplica |

## 2. Requisitos não funcionais (RNF)

| ID | Atributo | Descrição | Critério de verificação | Prioridade / estado |
| - | - | - | - | - |
| RNF-01 | Usabilidade | A interface deve apresentar filtros, mapa e informações das instituições de forma clara e simples. | Selecionar um município, aplicar filtros e consultar uma instituição sem ajuda. | Alta / A validar |
| RNF-02 | Desempenho da interface | O mapa não deve carregar os pontos das instituições antes da seleção de um município. | Abrir a aplicação e verificar que só as malhas aparecem. | Alta / Em desenvolvimento |
| RNF-03 | Desempenho das consultas | As consultas devem respeitar os filtros e devolver só o necessário; listas longas são paginadas (máx. 500 itens) e as respostas grandes são comprimidas. | Testar endereços com filtros diferentes; tempo de resposta local abaixo de 1 s. | Média / Implementado na API |
| RNF-04 | Integração | O frontend deve obter os dados pela API do projeto e exibi-los no serviço de mapas (MapTiler). | Dados da API aparecem corretamente no mapa e no painel. | Alta / Em desenvolvimento |
| RNF-05 | Manutenibilidade | O código deve ser organizado em módulos (coletores, transformações, validações, cargas, rotas) para que uma mudança não afete as demais partes. | Testes automáticos passam após cada mudança. | Média / Implementado no backend |
| RNF-06 | Confiabilidade das informações | Os dados exibidos devem corresponder às fontes oficiais e aos registros da API. | Comparar interface, API e banco; verificação do banco sem erros. | Alta / A validar |
| RNF-07 | Segurança | A API só lê o banco (transação somente leitura, tempo limite de 10 s), valida todos os parâmetros e não expõe credenciais nem detalhes técnicos em erros. As tabelas têm RLS ligado. | Testes CT-11 a CT-13 (`docs/testes/`). | Alta / Implementado |
| RNF-08 | Integridade e rastreabilidade | O banco impede registros duplicados (chaves únicas) e cada linha guarda a carga que a gerou (`ID_INGESTAO`). | Testes CT-09 e CT-10; verificação do banco. | Alta / Implementado |
| RNF-09 | Reprodutibilidade | As edições das fontes e as versões das bibliotecas ficam fixas; rodar o pipeline de novo produz o mesmo banco. | Rodar o pipeline duas vezes: a segunda não recarrega nem duplica. | Média / Implementado |
| RNF-10 | Licenças e atribuição | O site deve citar IBGE, INEP, SEDUC-SP, MapTiler/OpenStreetMap e, para pontos calculados, "IBGE CNEFE 2022 / geocodebr (Ipea)". | Conferir o rodapé e a página de fontes. | Média / Planejado |

## 3. Regras de negócio (RN)

| ID | Regra | Origem / validação | Requisitos relacionados | Estado |
| - | - | - | - | - |
| RN-01 | Ao selecionar um município, a consulta considera apenas as instituições daquele município. | Comportamento dos filtros. | RF-03, RF-07 | Implementado na API |
| RN-02 | Os pontos das instituições só aparecem quando um município está selecionado. | Comportamento do mapa (frontend). | RF-02, RF-03, RF-07 | Em desenvolvimento |
| RN-03 | Uma instituição só aparece como ponto quando tem coordenada válida e dentro do próprio município. | Validação dos pipelines (`ponto_confere_municipio`). | RF-07, RNF-06 | Implementado |
| RN-04 | Falta de coordenada não exclui a instituição: ela continua contada e aparece na lista "sem localização". | Necessidade identificada nos testes. | RF-07, RF-12 | Implementado na API |
| RN-05 | Ao remover a seleção do município, os pontos somem e a malha permanece. | Comportamento do mapa. | RF-02, RF-03, RF-07 | Em desenvolvimento |
| RN-06 | No SIDRA, cada valor vale para uma combinação de município, período, variável e classificação (sexo, idade...); as categorias são pedidas uma a uma para não contar em dobro, e taxas (%) nunca são somadas entre municípios. | DEC-003. | RF-10 | Implementado |
| RN-07 | Coordenada oficial (Catálogo INEP, depois SEDUC-SP) tem prioridade. Sem ela, o ponto pode ser calculado pelo endereço (IBGE CNEFE) apenas com precisão de número ou de rua; centro de CEP, bairro ou município nunca é usado. A precisão de cada ponto é informada. | DEC-002, DEC-004. | RF-07, RNF-06 | Implementado |
| RN-08 | O recorte é a RMS com 27 municípios (Lei Complementar estadual 1.241/2014 e 1.289/2016, que incluiu Itapetininga). | Configuração `src/config/rms.py`. | RF-01 | Implementado |
| RN-09 | O município de um curso superior é o **local de oferta**, não a sede da instituição; só entram as ofertas presenciais e as EAD com alunos no município. | DEC-006. | RF-09 | Implementado |
| RN-10 | O Censo Escolar define quais escolas existem; Catálogo INEP e SEDUC-SP só complementam endereço e coordenada. | DEC-004. | RF-07, RF-08 | Implementado |

## 4. Critérios de aceite e validação

| Requisito | Cenário / condição | Resultado esperado | Método / evidência | Situação |
| - | - | - | - | - |
| RF-01 | A aplicação consulta os municípios à API. | Os 27 municípios ficam disponíveis para seleção. | Interface + resposta de `/filtros`. | Implementado |
| RF-02 | A aplicação é aberta sem município selecionado. | A malha aparece sem pontos de instituições. | Teste visual no navegador. | Implementado |
| RF-03 | O usuário seleciona um município. | Só as instituições do município aparecem. | Teste com municípios que têm registros. | Implementado |
| RF-04 | O usuário seleciona um tipo. | Os resultados respeitam o tipo (Escola, ETEC, FATEC, Faculdade/Universidade). | `/mapa/instituicoes?tipo=` e interface. | Implementado |
| RF-05 | O usuário seleciona uma rede. | Só os registros da rede escolhida aparecem. | Teste com registros públicos e privados. | Implementado; validar |
| RF-06 | O usuário pesquisa "sao roque". | Aparecem os resultados com "São Roque". | CT-15; interface. | A validar na interface |
| RF-07 | Há município selecionado e instituições com coordenada. | Os pontos aparecem nas posições corretas. | CT-14; comparação dos pontos com a API. | Implementado; validar |
| RF-08 | O usuário seleciona uma instituição. | O painel mostra os dados daquela instituição. | Teste com instituições cadastradas. | Em desenvolvimento |
| RF-09 | O usuário consulta uma faculdade com cursos. | Os cursos presenciais do município aparecem. | Conferência com `/cursos-superiores`. | A validar |
| RF-12 | Município com escolas sem coordenada. | Elas aparecem na lista "sem localização" e não no mapa. | `/escolas/sem-localizacao`. | API implementada |
| RF-14 | O administrador roda o pipeline duas vezes. | A segunda execução não duplica dados; a verificação termina sem erros. | `python -m src.pipeline`; `docs/testes/` §4.2. | Implementado |
| RNF-02 | A aplicação é aberta sem filtro de município. | O mapa carrega as malhas sem pontos. | Inspeção visual. | Implementado; validar |
| RNF-04 | O frontend consulta a API e mostra o mapa. | Os dados da API aparecem corretamente. | Teste de integração frontend + API. | A validar |
| RNF-06 | Uma instituição é exibida no painel. | As informações batem com a API e com a fonte oficial. | Comparação interface × API × fonte. | A validar |
| RNF-07 | Filtro inválido, banco fora do ar, tentativa de escrita. | 422, 503 sem detalhe técnico, escrita recusada. | CT-11 a CT-13. | Implementado |
