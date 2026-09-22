# Veltis — Front Oficial

Front novo do projeto de mapeamento educacional da Região Metropolitana de Sorocaba.

## Stack

- React + Vite
- MapTiler SDK JS
- Lucide React
- CSS próprio, sem framework visual

## Identidade visual

O protótipo anterior foi usado como referência de fluxo, não como base visual. O front oficial usa:

- fundo verde-acinzentado claro;
- painéis claros e translúcidos;
- azul-petróleo como cor institucional;
- âmbar para informação secundária;
- DM Sans para texto e Manrope para títulos;
- bordas suaves, pouca sombra e elementos compactos.

## Rodando

1. Instale Node.js.
2. Copie `.env.example` para `.env`.
3. Coloque a chave do MapTiler em `VITE_MAPTILER_KEY`.
4. Ajuste `VITE_API_URL` para a URL do seu backend.
5. Execute:

```bash
npm install
npm run dev
```

O Vite abrirá em `http://localhost:5173`.

## Contrato esperado do backend

O front foi desacoplado dos nomes das colunas SQL. A API deve devolver instituições já normalizadas, por exemplo:

```json
{
  "id": "inep-123",
  "origem": "INEP_ESCOLA",
  "tipo": "ETEC",
  "nome": "ETEC Exemplo",
  "sigla": "ETEC",
  "municipio": "Sorocaba",
  "uf": "SP",
  "rede": "Estadual",
  "categoriaAdministrativa": null,
  "endereco": "Rua Exemplo, 100",
  "bairro": "Centro",
  "cep": "18000-000",
  "latitude": -23.5,
  "longitude": -47.45,
  "anoCenso": 2025,
  "situacaoFuncionamento": "Ativa",
  "possuiEnsinoMedio": true,
  "organizacaoAcademica": null,
  "cursos": []
}
```

Para `MEC_IES`, o backend precisa entregar latitude e longitude. A tabela enviada possui endereço, mas não possui campos geográficos da instituição.

`tipo` também deve ser normalizado no backend porque o esquema enviado não possui um campo específico para diferenciar diretamente Escola/ETEC/FATEC/Faculdade.

## Endpoint inicial

```http
GET /api/instituicoes
```

Filtros server-side podem ser adicionados depois sem alterar os componentes principais:

```http
GET /api/instituicoes?query=&municipio=&tipo=&rede=
```

## Banco recebido como fonte

O esquema de origem possui `INEP_ESCOLA`, `MEC_IES`, `MEC_CURSOS` e `IBGE_MUNICIPIOS`, com `MEC_CURSOS.CO_IES` referenciando `MEC_IES.CO_IES`.
