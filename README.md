
# Controle de Estoque — Angular + Django REST Framework

![CI](https://github.com/Eduardo-Lucas/estoque/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-4.2-092E20?logo=django&logoColor=white)
![DRF](https://img.shields.io/badge/DRF-3.14+-a30000)
![Angular](https://img.shields.io/badge/Angular-21-DD0031?logo=angular&logoColor=white)

Projeto de estudo para entender, na prática, como o frontend (Angular) se
comunica com o backend (Django + DRF) via HTTP/REST.

## Estrutura

```
estoque/
├── backend/            Django + DRF
│   ├── estoque_backend/    settings, urls raiz
│   └── estoque/             app com models, serializers, views, urls, admin
│       └── nfe.py               parsing puro do XML de NF-e (sem acesso a banco)
└── frontend/           Angular (standalone components)
    └── src/app/
        ├── models/          interfaces TypeScript (espelham os serializers)
        ├── services/        chamadas HTTP (HttpClient)
        ├── guards/          authGuard (protege rotas autenticadas)
        ├── interceptors/    injeta o token e trata erros de HTTP
        └── components/      telas (produto, categoria, fornecedor,
                              movimentação, importações, login)
```

## Funcionalidades

- **Autenticação por token** (DRF Token Auth): tela de login, guard de rotas
  e interceptor HTTP que anexa o token e trata 401.
- **Produtos**: cadastro completo — nome, SKU, código de barras, categoria,
  fornecedor, unidade de medida, quantidade, estoque mínimo, preço de custo,
  preço de venda e status ativo/inativo.
- **Categorias** e **Fornecedores**: CRUD completo, usados como referência
  no cadastro de produtos.
- **Requisição / Devolução de estoque**: registra movimentações e ajusta a
  quantidade do produto automaticamente, dentro de uma transação atômica.
  Bloqueia requisições que excedam o estoque disponível.
- **Histórico de movimentações por produto**: tela de detalhe
  (`/produtos/:id/historico`, acessível pelo botão "Histórico" na lista)
  mostrando os dados do produto e só as movimentações daquele produto
  (`GET /api/movimentacoes/?produto=<id>`).
- **Importações** (tela própria em `/importacoes`, um item no menu principal):
  - **CSV** de Produtos, Categorias e Fornecedores: upsert por nome (atualiza
    o que já existe, cria o que não existe), células vazias não sobrescrevem
    valores já cadastrados, e categoria/fornecedor referenciados por nome são
    criados automaticamente se não existirem.
  - **NF-e (XML)** de compra: dá entrada em estoque casando cada item da nota
    com um produto existente por SKU (código do fornecedor) ou nome. Itens
    sem correspondência **não criam produto automaticamente** — ficam
    pendentes até o produto ser cadastrado manualmente e o mesmo arquivo ser
    reimportado (reimportar é idempotente: itens já processados não duplicam
    estoque).
- **Paginação** nas listagens (a API aceita `?page=` e `?page_size=`).
- **Filtros de busca na listagem de produtos**: por nome (busca parcial,
  sem diferenciar maiúsculas/minúsculas, com debounce de 300ms no campo de
  texto) e por categoria/fornecedor (selects), combináveis entre si
  (`GET /api/produtos/?nome=&categoria=<id>&fornecedor=<id>`).

### Padrão de telas

Toda entidade (Produto, Categoria, Fornecedor) segue o mesmo padrão de UI:
a lista tem um botão **"+ Criar"** no topo e um botão **"Editar"** por linha;
ambos levam a uma tela de formulário separada (`.../novo` ou `.../:id/editar`),
que decide entre criar e atualizar conforme a presença do `id` na rota. As
listas em si só mostram dados e ações de CRUD — import/export de arquivo
(CSV/NF-e) fica centralizado na tela **Importações**, não em cada lista.

## Como rodar

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser   # necessário para logar no frontend e acessar /admin
python manage.py runserver
```

API disponível em `http://localhost:8000/api/` (autenticação por token
obrigatória, exceto `POST /api/auth/token/`):
- `GET/POST /api/produtos/`, `GET/PUT/DELETE /api/produtos/{id}/`
  (`GET` aceita `?nome=`, `?categoria=<id>`, `?fornecedor=<id>` para filtrar)
- `POST /api/produtos/importar_csv/`, `GET /api/produtos/exportar_csv/`
- `POST /api/produtos/importar_nfe/` — dá entrada em estoque a partir do XML de uma NF-e de compra
- `GET/POST /api/categorias/`, `GET/PUT/DELETE /api/categorias/{id}/`
- `POST /api/categorias/importar_csv/`, `GET /api/categorias/exportar_csv/`
- `GET/POST /api/fornecedores/`, `GET/PUT/DELETE /api/fornecedores/{id}/`
- `POST /api/fornecedores/importar_csv/`, `GET /api/fornecedores/exportar_csv/`
- `GET/POST /api/movimentacoes/`, `?produto=<id>` filtra o histórico de um produto
- `POST /api/auth/token/` — login, retorna o token do usuário

### Frontend

```bash
cd frontend
npm install
npm start
```

Acesse `http://localhost:4200` e faça login com o usuário criado via
`createsuperuser` (ou outro usuário Django existente).

> O CORS já está liberado no backend para `localhost:4200` (ver
> `CORS_ALLOWED_ORIGINS` em `settings.py`).

## Testes

### Backend (pytest-django)

```bash
cd backend
source venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest                              # roda a suíte
python -m pytest --cov=estoque --cov-report=term-missing   # com cobertura
```

Testes em `estoque/tests/`: models (unicidade, defaults, `__str__`), API
(CRUD, autenticação obrigatória, upsert de CSV, criação automática de
categoria/fornecedor por nome, filtros de busca por nome/categoria/
fornecedor) e a regra de negócio de estoque insuficiente em `Movimentacao`.
`test_api_nfe.py` cobre o import de NF-e: matching por SKU/nome,
reimportação idempotente (mesmo arquivo não duplica estoque), item
pendente resolvido após cadastro manual + reimportação, quantidade
fracionária rejeitada, e matching de fornecedor por CNPJ normalizado.

### Frontend (Jest + TestBed)

```bash
cd frontend
npm install
npm test
```

Testes em arquivos `*.spec.ts` ao lado de cada arquivo testado: services
(via `HttpClientTestingModule`), guard/interceptors de autenticação e os
componentes mais representativos (`produto-list`, `produto-form`,
`produto-historico`, `importacoes`, `login`, `movimentacao-form`,
incluindo o `AsyncValidator` de estoque).

### CI

`.github/workflows/ci.yml` roda as duas suítes a cada push/PR para `main`:
o job `backend-tests` (pytest-django) e o job `frontend-tests` (Jest +
TestBed), em jobs separados e paralelos. O badge no topo do README reflete
o status da última execução na `main`.

## Onde está o "como o frontend faz requisições"

Esse é o objetivo do projeto, então vale destacar os arquivos certos:

1. **`src/app/services/*.service.ts`** (`produto`, `categoria`, `fornecedor`,
   `movimentacao`, `auth`) — aqui é onde o `HttpClient` do Angular monta as
   chamadas (`get`, `post`, `put`, `delete`) para a API REST. Cada método
   retorna um `Observable`.

2. **`src/app/interceptors/auth.interceptor.ts`** — anexa o header
   `Authorization: Token <...>` em toda requisição. **`error.interceptor.ts`**
   trata erros HTTP: em 401 faz logout e redireciona para `/login`; nos
   demais casos, normaliza a mensagem de erro vinda do DRF.

3. **`src/main.ts`** — registra `provideHttpClient()` na aplicação. Sem isso
   o `HttpClient` não pode ser injetado em nenhum service.

4. **Componentes `*-list`** (listagem + CRUD) e **`*-form`** (criação/edição)
   — chamam os services e usam `.subscribe({ next, error })` para tratar
   sucesso e erro da requisição, atualizando o estado do componente (que a
   template reflete automaticamente via data binding). O componente
   **`importacoes`** segue o mesmo padrão para os uploads de CSV/NF-e.

## Fluxo de uma requisição, ponta a ponta

Exemplo: registrar uma requisição de produto.

1. Usuário preenche o formulário em `movimentacao-form.component.html`
   (`ReactiveFormsModule`, com `AsyncValidator` que consulta o estoque
   disponível do produto selecionado).
2. Submit do form chama `registrar()` no componente.
3. `registrar()` chama `movimentacaoService.criar(this.form.getRawValue())`.
4. O service faz `POST http://localhost:8000/api/movimentacoes/` com o
   corpo em JSON.
5. No backend, `MovimentacaoViewSet.create()` valida os dados
   (`MovimentacaoSerializer.validate`, que barra requisição maior que o
   estoque disponível), salva a movimentação e **dentro da mesma transação**
   ajusta a quantidade do produto.
6. A resposta (201 Created ou 400 com erro) volta pro Angular via
   `Observable`. `next` atualiza a UI com sucesso; `error` mostra a
   mensagem de validação vinda do DRF.

## Regras de negócio implementadas

- Requisição não pode exceder a quantidade disponível em estoque
  (validado no serializer do backend, e também via `AsyncValidator` no
  formulário do Angular).
- A cada requisição/devolução, a quantidade do produto é atualizada
  automaticamente (view do backend, dentro de uma transação atômica).
- CSV de produtos: categoria e fornecedor podem ser referenciados pelo nome;
  se não existirem, são criados automaticamente na importação.
- Import de NF-e: **não cria produto automaticamente** quando um item não
  casa com nenhum SKU/nome existente (ao contrário do CSV) — fica pendente
  até cadastro manual. O rastreamento é por item da nota (não pela nota
  inteira), então reimportar o mesmo arquivo depois de cadastrar o produto
  processa só o que faltava, sem duplicar o que já foi aplicado.

## Próximos passos sugeridos (para continuar estudando)

- Persistir os filtros de produtos na URL (query params), pra permitir compartilhar/recarregar a busca.
