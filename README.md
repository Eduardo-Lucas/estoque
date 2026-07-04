
# Controle de Estoque — Angular + Django REST Framework

Projeto de estudo para entender, na prática, como o frontend (Angular) se
comunica com o backend (Django + DRF) via HTTP/REST.

## Estrutura

```
estoque/
├── backend/            Django + DRF
│   ├── estoque_backend/    settings, urls raiz
│   └── estoque/             app com models, serializers, views, urls
└── frontend/           Angular (standalone components)
    └── src/app/
        ├── models/          interfaces TypeScript (espelham os serializers)
        ├── services/        chamadas HTTP (HttpClient)
        └── components/      telas (produto-list, movimentacao-form)
```

## Como rodar

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser   # opcional, para acessar /admin
python manage.py runserver
```

API disponível em `http://localhost:8000/api/`:
- `GET/POST /api/produtos/`
- `GET/PUT/DELETE /api/produtos/{id}/`
- `GET/POST /api/movimentacoes/`

### Frontend

```bash
cd frontend
npm install
npm start
```

Acesse `http://localhost:4200`.

> O CORS já está liberado no backend para `localhost:4200` (ver
> `CORS_ALLOWED_ORIGINS` em `settings.py`).

## Onde está o "como o frontend faz requisições"

Esse é o objetivo do projeto, então vale destacar os arquivos certos:

1. **`src/app/services/produto.service.ts`** e **`movimentacao.service.ts`**
   — aqui é onde o `HttpClient` do Angular monta as chamadas (`get`, `post`,
   `put`, `delete`) para a API REST. Cada método retorna um `Observable`.

2. **`src/main.ts`** — registra `provideHttpClient()` na aplicação. Sem isso
   o `HttpClient` não pode ser injetado em nenhum service.

3. **Componentes** (`produto-list.component.ts`,
   `movimentacao-form.component.ts`) — chamam os services e usam
   `.subscribe({ next, error })` para tratar sucesso e erro da requisição,
   atualizando o estado do componente (que a template reflete
   automaticamente via data binding).

## Fluxo de uma requisição, ponta a ponta

Exemplo: registrar uma requisição de produto.

1. Usuário preenche o formulário em `movimentacao-form.component.html`
   (`[(ngModel)]` mantém o objeto `nova: Movimentacao` sincronizado).
2. Clique em "Registrar" chama `registrar()` no componente.
3. `registrar()` chama `movimentacaoService.criar(this.nova)`.
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
  (validado no serializer do backend).
- A cada requisição/devolução, a quantidade do produto é atualizada
  automaticamente (view do backend, dentro de uma transação atômica).

## Próximos passos sugeridos (para continuar estudando)

- Trocar `FormsModule`/`ngModel` por `ReactiveFormsModule` com validações.
- Adicionar autenticação (Token ou JWT) via DRF + interceptor HTTP no Angular.
- Adicionar paginação real na listagem (a API já retorna `count`/`next`/`previous`).
- Escrever testes (`pytest-django` no backend, `TestBed` no Angular).
