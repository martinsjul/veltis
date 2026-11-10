# DEC-005 — API somente de leitura sobre views

- **Estado:** aceita
- **Data:** 2026-10-26
- **Responsáveis pela decisão:** equipe do projeto
- **Relacionado a:** `backend/api/`; migrations 003 a 005 (views); RNF de segurança

## Contexto

O frontend precisa de dados prontos (nomes em vez de códigos, coordenadas em WGS 84, uma linha por item). O banco está no Supabase, que também oferece uma API automática por tabela.

## Alternativas consideradas

- **API automática do Supabase (PostgREST):** sem código, mas expõe as tabelas como estão, com códigos crus, e exigiria abrir políticas de acesso (RLS) para o público.
- **Backend próprio lendo as tabelas:** flexível, mas repetiria em Python a lógica de tradução e de junção.
- **Backend próprio (FastAPI) lendo views:** a tradução de códigos e a escolha da melhor localização ficam no banco (views), e a API só filtra, pagina e formata.

## Decisão e justificativa

FastAPI lendo as views `vw_*`. Cada requisição roda numa transação `READ ONLY` com tempo limite de 10 s; todos os filtros são parâmetros SQL (nunca texto concatenado). O RLS fica ligado em todas as tabelas, sem políticas, e as views usam `security_invoker = true`: a API automática do Supabase (chave anônima) não lê nada.

## Consequências e revisão

- A API não grava, altera nem apaga dados; as cargas são feitas só pelos pipelines.
- Erros de banco aparecem ao usuário como mensagem simples (HTTP 503), sem detalhes técnicos.
- O frontend recebe GeoJSON e listas no formato que usa (`/mapa/instituicoes`).
- Revisar se o site precisar de dados gravados por usuários (por exemplo, favoritos).
