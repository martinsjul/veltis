# DEC-001 — Coordenadas das faculdades (locais de oferta presencial)

- **Estado:** aceita (atualizada em 2026-11-03)
- **Data:** 2026-10-28
- **Responsáveis pela decisão:** equipe do projeto (backend e frontend)
- **Relacionado a:** mapa do portal; tabela `ies_local_oferta`; migration `004_locais_ies_e_mapa.sql`; endereço `/mapa/instituicoes` da API

## Contexto

O mapa do site precisa de latitude e longitude para desenhar cada instituição. As escolas têm coordenada oficial (Catálogo de Escolas do INEP e Escolas Ativas da SEDUC-SP). Já o Censo da Educação Superior (INEP) **não traz coordenadas**: traz só o endereço da **sede** de cada instituição. Muitas sedes ficam fora da região; por exemplo, a sede da UNIP fica em São Paulo e o IFSP tem uma única sede para cinco campi. O microdado informa em qual município há curso presencial, mas não em qual prédio.

Sem coordenadas, as faculdades não apareciam no mapa.

## Alternativas consideradas

- **Centro do município:** rápido, mas o ponto não corresponde a nenhum prédio e confunde o usuário.
- **Geocodificar o endereço da sede do INEP:** errado para as faculdades cuja sede fica em outra cidade.
- **Google Geocoding:** boa precisão, mas os termos de uso não permitem guardar as coordenadas num banco próprio por mais de 30 dias nem usá-las num mapa que não seja do Google.
- **Levantar o endereço de cada campus e localizar no OpenStreetMap:** o universo é pequeno (33 instituições com curso presencial, 39 campi), as fontes são oficiais e a licença (ODbL) permite guardar os pontos citando a fonte.

## Decisão e justificativa

Levantar o endereço de cada campus presencial e localizar o ponto no OpenStreetMap, guardando tudo num arquivo versionado: `backend/data/referencia/ies_locais_oferta.csv`.

- **Endereço:** o do INEP quando a sede fica no próprio município (25 campi); nos demais, o endereço publicado pela instituição (site oficial ou edital do vestibular). A coluna `ds_fonte_endereco` registra a origem de cada linha.
- **Coordenada:** OpenStreetMap (consulta via Nominatim/Photon em 2026-10-28), aceita só se o ponto cai dentro do polígono do município. Em 2026-11-03, 4 pontos que estavam só na rua foram melhorados com o CNEFE do IBGE (geocodebr, ver DEC-002). A coluna `ds_precisao` registra o nível: `edificio` (28), `numero` (8) ou `rua` (3).
- **Carga:** o pipeline `locais_ies` valida o arquivo (município da RMS, coordenada dentro de SP e do município, instituição existente no Censo, sem duplicidade) e substitui a tabela inteira.

## Consequências e revisão

- A API entrega latitude e longitude de todas as faculdades presenciais (`/mapa/instituicoes` e `locais` em `/instituicoes`).
- Os 3 pontos com precisão `rua` (Faculdade de Boituva, IFSP Boituva e FAMO) podem estar a algumas quadras do prédio; o frontend pode mostrá-los com outro ícone. Correção: editar o CSV e rodar `python -m src.pipeline --apenas locais_ies`.
- Pontos a confirmar: UNIP Sorocaba (endereço obtido do OpenStreetMap, porque o site da UNIP não o exibe) e IFSP Sorocaba (há um segundo prédio na Av. Dr. José Bella Netto).
- O site deve exibir a atribuição "© OpenStreetMap contributors".
- Revisar quando sair um novo Censo da Educação Superior: a verificação do banco (`vw_faculdades_sem_local`) aponta as ofertas presenciais novas que ainda não têm campus no arquivo.
