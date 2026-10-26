"""API do Veltis.

Rodar (dentro da pasta backend, com o ambiente virtual ativo):

    uvicorn api.main:app --reload

Documentação interativa: http://127.0.0.1:8000/docs
"""

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DBAPIError

from api.config import origens_cors
from api.rotas import cursos, escolas, gerais, municipios


log = logging.getLogger("veltis.api")

DESCRICAO = """
Dados públicos oficiais da **Região Metropolitana de Sorocaba** (27 municípios):
municípios e indicadores do IBGE, escolas do Censo Escolar, cursos técnicos e
cursos superiores do INEP.

- A API **só lê** o banco (as views `vw_*`); não grava nada.
- Endereços de mapa devolvem **GeoJSON** em WGS 84 (EPSG:4326), pronto para o Leaflet.
- Listas longas são paginadas: `?pagina=1&por_pagina=50`.
- Sem `ano`, cada endereço usa a edição mais recente carregada.
"""

TAGS = [
    {"name": "Municípios", "description": "Contornos, indicadores do IBGE e ficha de cada cidade."},
    {"name": "Escolas", "description": "Escolas do Censo Escolar (INEP) com a localização."},
    {"name": "Cursos", "description": "Cursos técnicos e de graduação, e as faculdades."},
    {"name": "Geral", "description": "Opções de filtro, fontes dos dados e situação da API."},
]

# Os dados mudam no máximo uma vez por ano: o navegador pode guardar por 5 min.
CACHE_SEGUNDOS = 300


app = FastAPI(
    title="API Veltis",
    description=DESCRICAO,
    version="1.0.0",
    openapi_tags=TAGS,
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origens_cors(),
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.middleware("http")
async def cache_de_leitura(request: Request, call_next):
    resposta = await call_next(request)
    if request.method == "GET" and resposta.status_code == 200:
        resposta.headers.setdefault("Cache-Control", f"public, max-age={CACHE_SEGUNDOS}")
    return resposta


@app.exception_handler(DBAPIError)
async def banco_indisponivel(request: Request, erro: DBAPIError):
    # O detalhe técnico fica no log do servidor; o usuário recebe uma mensagem simples.
    log.error("Erro no banco em %s: %s", request.url.path, erro.orig or erro)
    return JSONResponse(
        status_code=503,
        content={"detail": "Não foi possível consultar o banco de dados agora. Tente de novo."},
    )


@app.get("/", include_in_schema=False)
def inicio():
    return {"api": "Veltis", "documentacao": "/docs", "saude": "/saude"}


app.include_router(municipios.router)
app.include_router(escolas.router)
app.include_router(cursos.router)
app.include_router(gerais.router)
