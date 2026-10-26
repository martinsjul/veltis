# Guia da API Veltis para o frontend

Para: Daniel (frontend) · De: Julia (backend) · Outubro de 2026

Este guia explica como a API funciona e como usá-la no React com o Leaflet. Os exemplos de resposta mostram o **formato** dos dados; os números são ilustrativos.

---

## 1. A ideia em uma frase

O banco (Supabase) guarda os dados. A **API** lê esses dados e entrega em JSON. O **site** (React) pede os dados para a API e mostra no mapa.

```text
Site (React + Leaflet)  →  pede  →  API (FastAPI)  →  lê  →  Banco (Supabase)
                        ←  JSON  ←
```

O site **nunca fala direto com o banco**. Ele só chama a API.

A API **só lê**: nenhum endereço grava, altera ou apaga dados.

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
| `/municipios` | Desenhar o contorno das 27 cidades | GeoJSON |
| `/municipios/indicadores` | Tabela ou mapa colorido por população, alfabetização etc. | Lista |
| `/municipios/{cd_mun}` | Painel lateral ao clicar numa cidade | Objeto |
| `/escolas` | Pontos das escolas no mapa (com filtros) | GeoJSON |
| `/escolas/{co_entidade}` | Painel ao clicar numa escola | Objeto |
| `/escolas/sem-localizacao` | Lista das escolas que não têm ponto no mapa | Página |
| `/cursos-tecnicos` | Lista e busca de cursos técnicos | Página |
| `/cursos-superiores` | Lista e busca de cursos de graduação | Página |
| `/instituicoes` | Faculdades de cada cidade | Página |
| `/filtros` | Opções prontas para os campos de seleção | Objeto |
| `/fontes` | Rodapé "dados atualizados em..." e página de fontes | Lista |
| `/saude` | Testar se a API está no ar | Objeto |

### Códigos que você vai usar

- **Município:** código IBGE com 7 dígitos. Exemplo: `3552205` = Sorocaba. A lista completa vem em `/filtros`.
- **Escola:** código INEP (`co_entidade`). Exemplo: `35016299`.

---

## 4. Os três formatos de resposta

### 4.1 GeoJSON (para o mapa)

`/municipios` e `/escolas` devolvem **GeoJSON**, o formato que o Leaflet desenha direto. As coordenadas já estão em WGS 84, o padrão do Leaflet; não precisa converter nada.

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

- Atenção: no GeoJSON a ordem é **[longitude, latitude]**, ao contrário do Leaflet, que usa `[lat, lng]`. O componente `GeoJSON` do react-leaflet já cuida disso sozinho.
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

### 6.2 Mapa com as cidades e as escolas

```jsx
import { useEffect, useState } from "react";
import { MapContainer, TileLayer, GeoJSON, CircleMarker, Popup } from "react-leaflet";
import { buscar } from "./api";

export default function Mapa({ filtros, aoClicarCidade, aoClicarEscola }) {
  const [cidades, setCidades] = useState(null);
  const [escolas, setEscolas] = useState(null);

  useEffect(() => { buscar("/municipios").then(setCidades); }, []);
  useEffect(() => { buscar("/escolas", filtros).then(setEscolas); }, [filtros]);

  return (
    <MapContainer center={[-23.5, -47.45]} zoom={9} style={{ height: "100vh" }}>
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution="&copy; OpenStreetMap"
      />

      {cidades && (
        <GeoJSON
          data={cidades}
          style={{ weight: 1, fillOpacity: 0.05 }}
          onEachFeature={(f, camada) =>
            camada.on("click", () => aoClicarCidade(f.properties.cd_mun))
          }
        />
      )}

      {escolas?.features.map((f) => (
        <CircleMarker
          key={f.id}
          center={[f.geometry.coordinates[1], f.geometry.coordinates[0]]}
          radius={4}
          eventHandlers={{ click: () => aoClicarEscola(f.id) }}
        >
          <Popup>{f.properties.no_entidade}</Popup>
        </CircleMarker>
      ))}
    </MapContainer>
  );
}
```

- **Importante:** o `GeoJSON` do react-leaflet **não redesenha** quando o `data` muda. Se for trocar os dados de uma camada `GeoJSON`, mude também a `key` dela (ex.: `key={JSON.stringify(filtros)}`). No exemplo acima as escolas usam `CircleMarker`, que não tem esse problema.
- Com todas as escolas (~1.600 pontos), se o mapa ficar lento, use agrupamento de marcadores (marker cluster) ou desenhe os pontos com `preferCanvas` no `MapContainer`.

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

- **Escolas sem ponto:** cerca de 13% das escolas não têm coordenada oficial e não aparecem em `/escolas`. Mostre-as numa lista à parte, usando `/escolas/sem-localizacao`, para o usuário não pensar que faltam escolas.
- **Ponto fora da cidade:** `ponto_confere_municipio = false` quer dizer que a coordenada oficial cai fora do contorno da cidade (são poucas). Vale mostrar um ícone de aviso.
- **Presencial × EAD:** um curso EAD aparece em **toda cidade onde tem aluno**. Para "faculdades que funcionam na cidade", use `modalidade=presencial`.
- **Vagas:** `qt_vagas` só existe no presencial; no EAD vem `null`.
- **Taxas não se somam:** campos terminados em `_pct` (porcentagens) não podem ser somados entre cidades.
- **Ano:** sem o filtro `ano`, a API usa a edição mais recente (Censo Escolar 2025, Censo Superior 2024).
- **Valores vazios:** campo `null` quer dizer "não informado pela fonte". Mostre "—", nunca 0.
- **Fontes:** o site precisa citar IBGE e INEP. `/fontes` traz a lista pronta.

---

## 9. Próximos passos sugeridos para o frontend

1. **Ligar a API e explorar o `/docs`**, para conhecer as respostas.
2. **Criar o `src/api.js`** (seção 6.1).
3. **Mapa base:** OpenStreetMap + contorno das 27 cidades (`/municipios`).
4. **Escolas no mapa** (`/escolas`), com a contagem de `metadados`.
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
