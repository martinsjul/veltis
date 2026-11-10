# Passo a passo: ligar a API do Veltis no seu PC

Para: Daniel · Sistema: Windows · Tempo: uns 15 minutos

Siga na ordem. Não pule passos.
Cada passo diz o que digitar e o que deve aparecer.
Se aparecer outra coisa, pare e veja a seção **Problemas comuns**, no fim.

---

## Antes de começar: o que você precisa

1. **Python 3.11 ou mais novo.**
    - Baixe em https://www.python.org/downloads/
    - Na instalação, marque a caixa **"Add python.exe to PATH"**. É obrigatório.
2. **Git.**
    - Baixe em https://git-scm.com/download/win
    - Na instalação, pode deixar tudo no padrão.
3. **Acesso ao repositório.**
    - A Julia precisa te adicionar como colaborador no GitHub.
    - Aceite o convite que chega no seu e-mail.
4. **A senha do banco.**
    - A Julia te manda por mensagem privada.
    - Nunca coloque essa senha no GitHub nem em grupo.

---

## Passo 1: abrir o terminal

1. Clique no menu **Iniciar**.
2. Digite **cmd**.
3. Clique em **Prompt de Comando**.

Use o **Prompt de Comando** (cmd), não o PowerShell. Todos os comandos deste guia são para o cmd.

---

## Passo 2: conferir o Python e o Git

Digite e aperte **Enter**:

```
python --version
```

Deve aparecer algo como `Python 3.13.1`.

Digite e aperte **Enter**:

```
git --version
```

Deve aparecer algo como `git version 2.47.0`.

Se aparecer **"não é reconhecido como um comando"**, veja os Problemas comuns 1 e 2.

---

## Passo 3: baixar o projeto

Entre na pasta Documentos:

```
cd %USERPROFILE%\Documents
```

Baixe o projeto:

```
git clone https://github.com/martinsjul/veltis.git
```

- Vai abrir uma janela de login do GitHub. Entre com a sua conta.
- No fim, deve aparecer `done`.

**Já tinha o projeto baixado?** Então não clone de novo. Entre na pasta dele e atualize:

```
cd %USERPROFILE%\Documents\veltis
git pull
```

---

## Passo 4: entrar na pasta do backend

```
cd %USERPROFILE%\Documents\veltis\backend
```

Confira se a API está ali:

```
dir api
```

Devem aparecer `main.py`, `db.py` e a pasta `rotas`.

Se aparecer "Arquivo não encontrado", rode `git pull` e tente de novo.

---

## Passo 5: criar o ambiente do Python

O ambiente é uma pasta só do projeto, onde ficam os pacotes instalados.
Você faz isso **uma vez só**.

```
python -m venv .venv
```

Não aparece nada. É normal. Espere a linha voltar.

---

## Passo 6: ativar o ambiente

```
.venv\Scripts\activate
```

O começo da linha muda e fica com `(.venv)` na frente:

```
(.venv) C:\Users\Daniel\Documents\veltis\backend>
```

**Sempre** confira se o `(.venv)` está aparecendo antes de rodar a API.

---

## Passo 7: instalar os pacotes da API

Com o `(.venv)` aparecendo, digite (é uma linha só):

```
pip install fastapi==0.160.0 "uvicorn[standard]==0.53.0" SQLAlchemy==2.1.5 "psycopg[binary]==3.3.6" python-dotenv==1.2.3
```

- Leva de 30 segundos a 1 minuto.
- No fim deve aparecer `Successfully installed ...`.
- Aviso amarelo sobre "new release of pip" pode ser ignorado.

Você faz isso **uma vez só**.

Esses são só os pacotes da API. Os pipelines de dados usam outros, mas você não precisa deles.

---

## Passo 8: criar o arquivo .env (endereço do banco)

O `.env` guarda o endereço e a senha do banco.
Ele fica só no seu PC. O GitHub ignora esse arquivo.

Ainda na pasta `backend`, digite:

```
notepad .env
```

- O Bloco de Notas pergunta se quer criar o arquivo. Clique em **Sim**.
- Cole esta linha:

```
DATABASE_URL=postgresql+psycopg://postgres.caamhmbuepxwphedozfe:SENHA@aws-1-us-west-2.pooler.supabase.com:5432/postgres?sslmode=require
```

- Troque `SENHA` pela senha que a Julia te mandou.
- Sem espaços. Sem aspas. Tudo numa linha só.
- Salve com **Ctrl + S** e feche o Bloco de Notas.

Confira se o arquivo foi criado com o nome certo:

```
dir .env
```

Deve aparecer `.env`, e **não** `.env.txt`.

Se a senha tiver `@`, `#`, `/`, `%` ou `:`, fale com a Julia antes. Esses símbolos precisam ser escritos de outro jeito.

---

## Passo 9: ligar a API

```
uvicorn api.main:app --reload
```

Deve aparecer:

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

- Se aparecerem códigos estranhos como `←[32m`, são só cores. Ignore.
- **Deixe essa janela aberta.** Ela é a API funcionando. Se fechar, a API desliga.

---

## Passo 10: testar no navegador

1. Abra o navegador.
2. Entre em **http://127.0.0.1:8000/docs**
3. Vai aparecer a página **API Veltis**.
4. Desça até o grupo **Geral** e clique em **GET /saude**.
5. Clique em **Try it out**.
6. Clique em **Execute**.
7. Desça até **Response body**.

Deve aparecer:

```json
{"status": "ok", "banco": "ok"}
```

**Se apareceu isso, está tudo funcionando.** 🎉

Se apareceu **503**, olhe a janela preta. O motivo está lá. Veja os Problemas comuns 6 e 7.

Para testar com dados de verdade:

- **GET /municipios/{cd_mun}** com `3552205` mostra a ficha de Sorocaba.
- **GET /instituicoes** com `modalidade` = `presencial` mostra as faculdades.

---

## Passo 11: ligar o frontend na API

Na pasta do frontend (React), crie um arquivo `.env` com esta linha:

```
VITE_API_URL=http://127.0.0.1:8000
```

- Se o `npm run dev` já estava rodando, pare (**Ctrl + C**) e rode de novo. O Vite só lê o `.env` quando liga.
- No código, use `import.meta.env.VITE_API_URL` para montar os endereços.
- O jeito de chamar cada endereço está no `GUIA_API_PARA_O_FRONTEND.md`.

A API aceita chamadas de `http://localhost:5173` e `http://localhost:3000`.
Se o seu site rodar em outra porta, avise a Julia.

---

## Todo dia, para ligar de novo

Você **não** repete os passos 3, 5, 7 e 8. Só faz isto:

```
cd %USERPROFILE%\Documents\veltis\backend
git pull
.venv\Scripts\activate
uvicorn api.main:app --reload
```

Para **desligar**: na janela da API, aperte **Ctrl + C**.

---

## Problemas comuns

**1. `'python' não é reconhecido como um comando`**
- O Python não foi instalado com o PATH.
- Rode o instalador do Python de novo, escolha **Modify** e marque **"Add python.exe to PATH"**.
- Feche e abra o cmd de novo.
- Se ainda não funcionar, troque `python` por `py` nos comandos.

**2. `'git' não é reconhecido como um comando`**
- Instale o Git (veja "Antes de começar").
- Feche e abra o cmd de novo.

**3. `Repository not found` no git clone**
- Você ainda não tem acesso ao repositório.
- Peça para a Julia te adicionar e aceite o convite no e-mail.
- Confira se fez login com a conta certa do GitHub.

**4. `No module named 'api'` ou `Could not import module "api.main"`**
- Você não está na pasta `backend`.
- Rode: `cd %USERPROFILE%\Documents\veltis\backend`

**5. `DATABASE_URL não foi definida`**
- O arquivo `.env` não existe, está em outra pasta ou virou `.env.txt`.
- Ele tem que estar dentro de `backend`.
- Refaça o passo 8 e confira com `dir .env`.

**6. Erro 503 e no terminal: `password authentication failed`**
- A senha ou o usuário estão errados.
- O usuário tem que ser `postgres.caamhmbuepxwphedozfe` (com o ponto e o código), e não só `postgres`.
- A senha não leva colchetes `[ ]`.
- Confira a senha com a Julia.
- Depois de corrigir o `.env`, desligue a API (**Ctrl + C**) e ligue de novo.

**7. Erro 503 e no terminal: `timeout` ou `could not connect`**
- A sua internet ou a rede está bloqueando o banco.
- Teste em outra rede (por exemplo, o roteador do celular).

**8. `No module named 'fastapi'` ou `'uvicorn' não é reconhecido`**
- O ambiente não está ativo. Falta o `(.venv)` no começo da linha.
- Rode `.venv\Scripts\activate` e tente de novo.
- Se ainda der erro, refaça o passo 7.

**9. No PowerShell: `a execução de scripts foi desabilitada neste sistema`**
- Feche o PowerShell e use o **Prompt de Comando** (cmd). Comece do passo 1.

**10. `address already in use` ou erro com a porta 8000**
- A API já está ligada em outra janela. Feche a outra janela.
- Ou ligue em outra porta: `uvicorn api.main:app --reload --port 8001`
- Nesse caso, use `http://127.0.0.1:8001` no navegador e no `VITE_API_URL`.

**11. No console do navegador: `blocked by CORS policy`**
- O site está rodando numa porta que a API não libera.
- Use a porta 5173 (padrão do Vite) ou avise a Julia qual porta você usa.

**Nada disso resolveu?**
Tire um print da **janela preta da API** e mande para a Julia.
Antes de mandar, cubra a senha se ela aparecer.
