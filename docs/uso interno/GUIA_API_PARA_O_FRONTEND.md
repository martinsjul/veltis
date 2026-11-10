# Guia da API Veltis para o frontend

Para: Daniel (frontend) · De: Julia (backend) · Outubro de 2026

Este guia explica como a API funciona e como usá-la no React com o MapTiler. Os exemplos de resposta mostram o **formato** dos dados; os números são ilustrativos.

---

## 1. A ideia em uma frase

O banco (Supabase) guarda os dados. A **API** lê esses dados e entrega em JSON. O **site** (React) pede os dados para a API e mostra no mapa.

```text
Site (React + MapTiler) →  pede  →  API (FastAPI)  →  lê  →  Banco (Supabase)
                        ←  JSON  ←
```

O site **nunca fala direto com o banco**. Ele só chama a API.

A API **só lê**: nenhum endereço grava, altera ou apaga dados.

### O mais importante: os pinos do mapa

Use **`GET /mapa/instituicoes`**. Ele devolve **escolas e faculdades numa lista só**, cada uma com **`latitude` e `longitude`**, nos mesmos campos do `mockData` do site:

```json
[
  {
    "id": "ies-33-19",
    "origem": "MEC_IES",
    "tipo": "FATEC",
    "nome": "Fatec Sorocaba",
    "sigla": "FATEC SO",
    "municipio": "Sorocaba",
    "rede": "Pública",
    "endereco": "Avenida Engenheiro Carlos Reinaldo Mendes, 2015",
    "cep": "18013-280",
    "latitude": -23.480133,
    "longitude": -47.425939,
    "precisaoLocalizacao": "edificio",
    "anoCenso": 2024,
    "possuiEnsinoMedio": false,
    "organizacaoAcademica": "Faculdade",
    "cursos": [{ "codigo": 1, "nome": "Análise e Desenvolvimento de Sistemas", "grau": "Tecnológico", "vagas": 80, "matriculas": 300 }]
  }
]
```

- `tipo`: `Escola`, `ETEC`, `FATEC` ou `Faculdade/Universidade` (as mesmas chaves de `TIPO_COLORS`).
- Filtros: `?municipio=3552205`, `?tipo=etec&tipo=fatec` (valores: `escola`, `etec`, `fatec`, `faculdade`) e `?busca=texto`.
- Por padrão só vêm itens **com** coordenada. `?incluir_sem_coordenada=true` traz também as escolas sem ponto (com `latitude: null`).
- `precisaoLocalizacao` diz de onde veio o ponto:
  - escolas: `oficial` (INEP/SEDUC) ou, quando calculado pelo endereço (IBGE CNEFE), `numero`, `numero_aproximado` ou `logradouro`;
  - faculdades: `edificio`, `numero` ou `rua`.
  - `logradouro` e `rua` = rua certa, mas pode estar a algumas quadras; vale um ícone diferente.

No `src/services/institutionService.js`, troque:

```js
const response = await fetch(`${API_URL}/instituicoes`)
```

por:

```js
const response = await fetch(`${API_URL}/mapa/instituicoes`)
```

A resposta já é uma lista (`Array.isArray(data)` dá `true`), então o resto do código funciona igual.

---

## 2. Como ligar a API no seu computador

Faça uma vez:

```bash
git pull
cd backend
python -m venv .venv
.venv\Scripts\activate          # no Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
```

Crie o arquivo `backend/.env` com a linha `DATABASE_URL=...`. Peça para a Julia o endereço do banco **por mensagem privada**: ele tem senha e **nunca** vai para o GitHub.

Toda vez que for trabalhar:

```bash
cd backend
.venv\Scripts\activate
uvicorn api.main:app --reload
```

A API fica em **http://127.0.0.1:8000**. Deixe esse terminal aberto enquanto usa o site.

### A página /docs

Abra **http://127.0.0.1:8000/docs**. Ela lista todos os endereços. Em cada um:

1. Clique em **Try it out**.
2. Preencha os filtros.
3. Clique em **Execute**.

Você vê a resposta real na hora. Use essa página para descobrir o formato dos dados antes de escrever código.

---

## 3. Os endereços

Todos são `GET`.

| Endereço | Para que serve no site | Formato |
| --- | --- | --- |
| **`/mapa/instituicoes`** | **Pinos do mapa: escolas e faculdades com latitude e longitude** | **Lista** |
| `/municipios` | Desenhar o contorno das 27 cidades | GeoJSON |
| `/municipios/indicadores` | Tabela ou mapa colorido por população, alfabetização etc. | Lista |
| `/municipios/{cd_mun}` | Painel lateral ao clicar numa cidade | Objeto |
| `/escolas` | Pontos das escolas no mapa (com filtros) | GeoJSON |
| `/escolas/{co_entidade}` | Painel ao clicar numa escola | Objeto |
| `/escolas/sem-localizacao` | Lista das escolas que não têm ponto no mapa | Página |
| `/cursos-tecnicos` | Lista e busca de cursos técnicos | Página |
| `/cursos-superiores` | Lista e busca de cursos de graduação | Página |
| `/instituicoes` | Faculdades de cada cidade, com contagem de cursos e os campi (`locais`) | Página |
| `/filtros` | Opções prontas para os campos de seleção | Objeto |
| `/fontes` | Rodapé "dados atualizados em..." e página de fontes | Lista |
| `/saude` | Testar se a API está no ar | Objeto |

### Códigos que você vai usar

- **Município:** código IBGE com 7 dígitos. Exemplo: `3552205` = Sorocaba. A lista completa vem em `/filtros`.
- **Escola:** código INEP (`co_entidade`). Exemplo: `35016299`.

---

## 4. Os três formatos de resposta

### 4.1 GeoJSON (para o mapa)

`/municipios` e `/escolas` devolvem **GeoJSON**, que o MapTiler (MapLibre) desenha direto com `map.addSource(..., { type: 'geojson', data })`. As coordenadas já estão em WGS 84; não precisa converter nada. Em `/escolas`, cada ponto também traz `latitude` e `longitude` em `properties`.

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "id": 35016299,
      "geometry": { "type": "Point", "coordinates": [-47.44, -23.46] },
      "properties": {
        "co_entidade": 35016299,
        "no_entidade": "AGGEO PEREIRA DO AMARAL PROFESSOR",
        "no_municipio": "Sorocaba",
        "ds_dependencia": "Estadual",
        "oferece_ensino_medio": true,
        "educacao_profissional": true,
        "qt_cursos_tecnicos": 4,
        "ponto_confere_municipio": true
      }
    }
  ],
  "metadados": {
    "ano": 2025,
    "total_filtrado": 91,
    "no_mapa": 80,
    "sem_coordenada": 11,
    "ponto_fora_do_municipio": 0
  }
}
```

- Atenção: no GeoJSON e no MapTiler a ordem é **[longitude, latitude]** (ex.: `marker.setLngLat([longitude, latitude])`).
- Os dados de cada escola ficam em `feature.properties`.
- `metadados` só existe em `/escolas`. Use para mostrar algo como "80 escolas no mapa, 11 sem localização".

### 4.2 Página (para listas)

Listas longas vêm em páginas:

```json
{
  "total": 38,
  "pagina": 1,
  "por_pagina": 50,
  "itens": [
    {
      "co_ies": 150,
      "no_ies": "UNIVERSIDADE DE SOROCABA",
      "sg_ies": "UNISO",
      "no_municipio": "Sorocaba",
      "qt_cursos_presenciais": 67,
      "qt_cursos_ead": 0,
      "qt_matriculas": 7721
    }
  ]
}
```

- Para a próxima página, use `?pagina=2`. O tamanho padrão é 50 itens e o máximo é 500 (`?por_pagina=100`).
- Total de páginas = `Math.ceil(total / por_pagina)`.

### 4.3 Objeto (fichas)

`/municipios/{cd_mun}` e `/escolas/{co_entidade}` devolvem um objeto só, com tudo do item. Exemplo do município:

```text
{
  "cd_mun": "3552205",
  "nm_mun": "Sorocaba",
  "indicadores": { populacao_2022, homens, mulheres, densidade_hab_km2, ... },
  "educacao": {
    "escolas_ativas": 461,
    "escolas_ativas_ensino_medio": 84,
    "cursos_tecnicos": 155,
    "instituicoes_presenciais": 14,
    "cursos_superiores_presenciais": 215
  }
}
```

---

## 5. Filtros

Os filtros vão na URL, depois do `?`, separados por `&`:

```text
/escolas?municipio=3552205&dependencia=estadual&ensino_medio=true
```

| Filtro | Onde funciona | Valores |
| --- | --- | --- |
| `municipio` | quase todos | código IBGE, ex. `3552205` |
| `dependencia` | escolas | `federal`, `estadual`, `municipal`, `privada` (pode repetir) |
| `apenas_ativas` | escolas | `true` (padrão) ou `false` |
| `ensino_medio` | escolas | `true` / `false` |
| `educacao_profissional` | escolas | `true` = tem técnico, médio integrado ou itinerário técnico |
| `modalidade` | cursos superiores, instituições | `presencial`, `ead` |
| `grau` | cursos superiores | `bacharelado`, `licenciatura`, `tecnologico`, `bacharelado_e_licenciatura` |
| `rede` | cursos superiores, instituições | `publica`, `privada` |
| `gratuito` | cursos superiores | `true` / `false` |
| `area` | cursos técnicos e superiores | valor que vem em `/filtros` |
| `busca` | vários | texto livre; ignora maiúsculas e acentos |

**Dica:** não escreva essas listas à mão no React. Chame `/filtros` uma vez e monte os `<select>` com o que vier. Cada opção tem `valor` (o que vai na URL) e `rotulo` (o que aparece para o usuário):

```json
{ "dependencias": [ { "valor": "estadual", "rotulo": "Estadual" } ] }
```

---

## 6. Usando no React

### 6.1 Endereço da API num lugar só

Crie `frontend/.env`:

```text
VITE_API_URL=http://127.0.0.1:8000
```

E um arquivo `src/api.js`:

```js
const BASE = import.meta.env.VITE_API_URL;

export async function buscar(caminho, filtros = {}) {
  const url = new URL(caminho, BASE);
  for (const [chave, valor] of Object.entries(filtros)) {
    if (valor === undefined || valor === null || valor === "") continue;
    // listas (ex.: várias dependências) viram ?dependencia=a&dependencia=b
    [].concat(valor).forEach((v) => url.searchParams.append(chave, v));
  }
  const resposta = await fetch(url);
  if (!resposta.ok) {
    const erro = await resposta.json().catch(() => ({}));
    throw new Error(erro.detail ?? `Erro ${resposta.status}`);
  }
  return resposta.json();
}
```

### 6.2 Mapa (MapTiler) com o contorno das cidades e os pinos

O site já desenha os pinos a partir de `latitude`/`longitude` (componente `MapView`). Com `/mapa/instituicoes` (seção 1) isso passa a funcionar com dados reais. Para desenhar também o **contorno das cidades**, adicione uma camada GeoJSON depois que o mapa carregar:

```js
map.on("load", async () => {
  const cidades = await buscar("/municipios");
  map.addSource("municipios", { type: "geojson", data: cidades });
  map.addLayer({
    id: "municipios-contorno",
    type: "line",
    source: "municipios",
    paint: { "line-color": "#315B62", "line-width": 1 },
  });
  map.addLayer({
    id: "municipios-area",
    type: "fill",
    source: "municipios",
    paint: { "fill-color": "#315B62", "fill-opacity": 0.04 },
  });
  map.on("click", "municipios-area", (e) => aoClicarCidade(e.features[0].properties.cd_mun));
});
```

- Com ~1.500 pinos, os marcadores HTML (`new Marker`) podem deixar o mapa lento. Se acontecer, troque por uma camada `circle` de uma fonte GeoJSON com `cluster: true`.

### 6.3 Painel ao clicar

```js
const ficha = await buscar(`/municipios/${cdMun}`);        // cidade
const escola = await buscar(`/escolas/${coEntidade}`);     // escola, com escola.cursos_tecnicos
```

### 6.4 Lista paginada

```js
const [pagina, setPagina] = useState(1);
const dados = await buscar("/cursos-superiores", { municipio, modalidade: "presencial", pagina });
const totalPaginas = Math.ceil(dados.total / dados.por_pagina);
```

---

## 7. Erros que podem aparecer

| Código | Significa | O que mostrar no site |
| --- | --- | --- |
| 200 | Deu certo | os dados |
| 404 | Cidade ou escola não existe | "Não encontrado" |
| 422 | Filtro com valor errado (ex.: `dependencia=particular`) | Erro de programação: confira o valor enviado |
| 503 | A API não conseguiu falar com o banco | "Dados indisponíveis no momento, tente de novo" |
| erro de rede / CORS | A API está desligada, ou o site roda num endereço não liberado | Confira se o `uvicorn` está rodando |

A mensagem de erro sempre vem em `detail`.

**Sobre CORS:** a API aceita chamadas de `http://localhost:5173` (Vite) e `http://localhost:3000`. Se o site rodar em outro endereço, avise a Julia para incluir em `VELTIS_CORS_ORIGENS`.

---

## 8. Cuidados com os dados

- **Escolas sem ponto:** cerca de 13% das escolas não têm coordenada oficial e não aparecem em `/escolas` nem em `/mapa/instituicoes`. Mostre-as numa lista à parte, usando `/escolas/sem-localizacao`, para o usuário não pensar que faltam escolas.
- **Faculdades:** o INEP não publica coordenadas das faculdades. Os pontos dos campi foram levantados à mão (endereço oficial + OpenStreetMap) e estão em `backend/data/referencia/ies_locais_oferta.csv`. Achou um ponto errado? Corrija o CSV e rode `python -m src.pipeline --apenas locais_ies`.
- **Ponto fora da cidade:** `ponto_confere_municipio = false` quer dizer que a coordenada oficial cai fora do contorno da cidade (são poucas). Vale mostrar um ícone de aviso.
- **Presencial × EAD:** um curso EAD aparece em **toda cidade onde tem aluno**. Para "faculdades que funcionam na cidade", use `modalidade=presencial`.
- **Vagas:** `qt_vagas` só existe no presencial; no EAD vem `null`.
- **Taxas não se somam:** campos terminados em `_pct` (porcentagens) não podem ser somados entre cidades.
- **Ano:** sem o filtro `ano`, a API usa a edição mais recente (Censo Escolar 2025, Censo Superior 2024).
- **Valores vazios:** campo `null` quer dizer "não informado pela fonte". Mostre "—", nunca 0.
- **Fontes:** o site precisa citar IBGE (incluindo "CNEFE – Censo 2022" e "geocodebr/Ipea" para os pontos calculados), INEP, SEDUC-SP e "© OpenStreetMap contributors" (coordenadas das faculdades). `/fontes` traz a lista pronta.

---

## 9. Próximos passos sugeridos para o frontend

1. **Ligar a API e explorar o `/docs`**, para conhecer as respostas.
2. **Criar o `src/api.js`** (seção 6.1).
3. **Pinos reais:** trocar o `mockData` por `/mapa/instituicoes` (seção 1) e desenhar o contorno das 27 cidades (`/municipios`).
4. **Filtro por tipo** (Escola, ETEC, FATEC, Faculdade) e por cidade, usando os filtros de `/mapa/instituicoes`.
5. **Filtros:** cidade, rede, ensino médio, educação profissional e busca por nome, montados a partir de `/filtros`.
6. **Painel da cidade** ao clicar no contorno (`/municipios/{cd_mun}`): população, sexo, faixas de idade e resumo da educação.
7. **Painel da escola** ao clicar no ponto (`/escolas/{co_entidade}`): endereço, telefone e cursos técnicos.
8. **Aba "Faculdades e cursos":** `/instituicoes` e `/cursos-superiores`, com busca e paginação.
9. **Lista "Escolas sem localização"** (`/escolas/sem-localizacao`).
10. **Rodapé com as fontes** (`/fontes`).
11. **Estados de tela:** "carregando...", lista vazia e mensagem de erro em todas as chamadas.

Sugestão de ordem para mostrar ao professor: os passos 3, 4 e 6 já viram uma demonstração completa (mapa + escolas + ficha da cidade).

---

## 10. Dúvidas

- O formato exato de cada resposta está no `/docs`, na seção **Schemas**.
- O significado de cada campo (de onde vem cada dado) está no documento "Mapa das tabelas e views do banco".
- Faltou um campo ou um filtro? Fale com a Julia: é rápido adicionar na API.
