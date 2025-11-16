# Cash Plan Backend

API REST desenvolvida em Python para gestão financeira pessoal. Implementa operações CRUD sobre entidades financeiras e um agente conversacional baseado em linguagem natural para consultas e inserções de dados.

## Tecnologias e Dependências

- **FastAPI** 0.104.1: Framework web assíncrono
- **SQLAlchemy** 2.0.23: ORM para mapeamento objeto-relacional
- **Alembic** 1.12.1: Sistema de versionamento de schema de banco de dados
- **PostgreSQL**: Sistema gerenciador de banco de dados relacional
- **Pydantic** 2.5.0: Validação de dados e serialização
- **python-jose** 3.3.0: Implementação de JWT para autenticação
- **passlib** 1.7.4: Criptografia de senhas com bcrypt
- **google-generativeai** 0.3.2: Cliente para API Gemini 2.5 Flash
- **UV**: Gerenciador de pacotes e ambientes virtuais

## Estrutura do Banco de Dados

O schema relacional contém as seguintes entidades principais:

### users

- `id`: Integer (PK)
- `email`: String(255), unique, not null
- `username`: String(100), unique, not null
- `hashed_password`: String(255), not null
- `full_name`: String(255), nullable
- `is_active`: Integer, default 1
- `created_at`: DateTime(timezone=True)
- `updated_at`: DateTime(timezone=True)

### accounts

- `id`: Integer (PK)
- `user_id`: Integer (FK -> users.id), not null
- `name`: String(255), not null
- `bank`: String(255), not null
- `balance`: Float, default 0.0
- `investments`: Float, default 0.0
- `color`: String(7), nullable
- `created_at`: DateTime(timezone=True)
- `updated_at`: DateTime(timezone=True)

### credit_cards

- `id`: Integer (PK)
- `user_id`: Integer (FK -> users.id), not null
- `name`: String(255), not null
- `bank`: String(255), not null
- `used`: Integer, default 0 (valor em centavos)
- `limit`: Integer, not null (valor em centavos)
- `color`: String(7), nullable
- `created_at`: DateTime(timezone=True)
- `updated_at`: DateTime(timezone=True)

### transactions

- `id`: Integer (PK)
- `user_id`: Integer (FK -> users.id), not null
- `description`: String(500), not null
- `category`: String(255), not null
- `date`: Date, not null
- `amount`: Float, not null (positivo para receitas, negativo para despesas)
- `type`: Enum('income', 'expense'), not null
- `account_id`: Integer (FK -> accounts.id), nullable
- `created_at`: DateTime(timezone=True)
- `updated_at`: DateTime(timezone=True)

### investments

- `id`: Integer (PK)
- `user_id`: Integer (FK -> users.id), not null
- `name`: String(255), not null
- `type`: Enum('Renda Fixa', 'Renda Variável'), not null
- `value`: Float, not null
- `return_rate`: Float, default 0.0
- `color`: String(7), nullable
- `created_at`: DateTime(timezone=True)
- `updated_at`: DateTime(timezone=True)

### goals

- `id`: Integer (PK)
- `user_id`: Integer (FK -> users.id), not null
- `name`: String(255), not null
- `target`: Float, not null
- `current`: Float, default 0.0
- `color`: String(7), nullable
- `created_at`: DateTime(timezone=True)
- `updated_at`: DateTime(timezone=True)

### shopping_lists

- `id`: Integer (PK)
- `user_id`: Integer (FK -> users.id), not null
- `name`: String(255), not null
- `month`: String(7), nullable (formato YYYY-MM)
- `status`: Enum('active', 'completed', 'archived'), default 'active'
- `total_estimated`: Float, default 0.0
- `total_spent`: Float, default 0.0
- `created_at`: DateTime(timezone=True)
- `updated_at`: DateTime(timezone=True)
- `completed_at`: DateTime(timezone=True), nullable

### shopping_items

- `id`: Integer (PK)
- `shopping_list_id`: Integer (FK -> shopping_lists.id), not null
- `name`: String(255), not null
- `category`: String(100), not null
- `quantity`: String(50), not null
- `estimated_price`: Float, default 0.0
- `actual_price`: Float, nullable
- `is_purchased`: Boolean, default False
- `notes`: Text, nullable
- `order`: Integer, default 0
- `created_at`: DateTime(timezone=True)
- `updated_at`: DateTime(timezone=True)

### categories

- `id`: Integer (PK)
- `user_id`: Integer (FK -> users.id), not null
- `name`: String(100), not null
- `type`: Enum('income', 'expense'), not null
- `is_default`: Boolean, default False
- `created_at`: DateTime(timezone=True)
- `updated_at`: DateTime(timezone=True)

Todas as entidades relacionadas a dados financeiros possuem `user_id` como chave estrangeira, garantindo isolamento de dados por usuário. Relacionamentos configurados com cascade delete para remoção em cascata.

## Configuração e Instalação

### Variáveis de Ambiente

Criar arquivo `.env` na raiz do projeto:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost/cash_plan
GEMINI_API_KEY=sua_chave_api_gemini
```

### Instalação de Dependências

```bash
uv sync
```

### Criação do Banco de Dados

```sql
CREATE DATABASE cash_plan;
```

### Aplicação de Migrations

```bash
# Aplicar todas as migrations
uv run alembic upgrade head

# Ver histórico de migrations
uv run alembic history

# Reverter última migration
uv run alembic downgrade -1

# Reverter todas as migrations
uv run alembic downgrade base
```

### Execução do Servidor

```bash
# Método 1: Script principal
uv run main.py

# Método 2: Uvicorn direto
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

Servidor disponível em `http://localhost:8080`. Documentação interativa:

- Swagger UI: `http://localhost:8080/docs`
- ReDoc: `http://localhost:8080/redoc`

### Criação de Novas Migrations

Após modificar modelos em `app/models.py`:

```bash
uv run alembic revision --autogenerate -m "Descrição da alteração"
uv run alembic upgrade head
```

## Estrutura do Projeto

```
cash-plan-backend/
├── alembic/                  # Migrations do Alembic
│   ├── versions/            # Arquivos de migration
│   ├── env.py              # Configuração do Alembic
│   └── script.py.mako      # Template para migrations
├── app/                      # Código da aplicação
│   ├── __init__.py
│   ├── database.py          # Configuração do banco de dados
│   ├── db_schema.py         # Geração dinâmica do schema
│   ├── main.py             # Entrada da aplicação FastAPI
│   ├── models.py           # Modelos SQLAlchemy
│   ├── schemas.py          # Schemas Pydantic para validação
│   ├── auth.py             # Autenticação JWT e criptografia
│   └── routers/            # Endpoints da API
│       ├── accounts.py
│       ├── auth.py
│       ├── categories.py
│       ├── credit_cards.py
│       ├── genai.py
│       ├── goals.py
│       ├── investments.py
│       ├── shopping_lists.py
│       └── transactions.py
├── alembic.ini              # Configuração do Alembic
├── pyproject.toml           # Dependências e configuração
├── main.py                 # Script de inicialização
├── seed_categories.py      # Script de seed de categorias
├── test_genai.py           # Testes do agente GenAI
└── README.md
```

## Endpoints da API

### Autenticação

- `POST /auth/register`: Registro de novo usuário
- `POST /auth/login`: Autenticação e obtenção de token JWT

### Contas Bancárias

- `GET /accounts`: Lista contas do usuário autenticado
- `GET /accounts/{id}`: Obtém conta específica
- `POST /accounts`: Cria nova conta
- `PUT /accounts/{id}`: Atualiza conta
- `DELETE /accounts/{id}`: Remove conta

### Cartões de Crédito

- `GET /credit_cards`: Lista cartões do usuário
- `GET /credit_cards/{id}`: Obtém cartão específico
- `POST /credit_cards`: Cria novo cartão
- `PUT /credit_cards/{id}`: Atualiza cartão
- `DELETE /credit_cards/{id}`: Remove cartão

### Transações

- `GET /transactions`: Lista transações do usuário
- `GET /transactions/{id}`: Obtém transação específica
- `POST /transactions`: Cria nova transação (atualiza saldo da conta se `account_id` fornecido)
- `PUT /transactions/{id}`: Atualiza transação (reverte e reaplica saldo)
- `DELETE /transactions/{id}`: Remove transação (reverte saldo)

### Investimentos

- `GET /investments`: Lista investimentos do usuário
- `GET /investments/{id}`: Obtém investimento específico
- `POST /investments`: Cria novo investimento
- `PUT /investments/{id}`: Atualiza investimento
- `DELETE /investments/{id}`: Remove investimento

### Metas

- `GET /goals`: Lista metas do usuário
- `GET /goals/{id}`: Obtém meta específica
- `POST /goals`: Cria nova meta
- `PUT /goals/{id}`: Atualiza meta
- `DELETE /goals/{id}`: Remove meta

### Listas de Compras

- `GET /shopping_lists`: Lista listas do usuário
- `GET /shopping_lists/{id}`: Obtém lista específica
- `POST /shopping_lists`: Cria nova lista
- `PUT /shopping_lists/{id}`: Atualiza lista
- `DELETE /shopping_lists/{id}`: Remove lista

### Categorias

- `GET /categories`: Lista categorias do usuário
- `GET /categories/{id}`: Obtém categoria específica
- `POST /categories`: Cria nova categoria
- `PUT /categories/{id}`: Atualiza categoria
- `DELETE /categories/{id}`: Remove categoria

### Assistente GenAI

- `POST /genai/chat`: Endpoint conversacional para consultas e inserções

Todos os endpoints, exceto `/auth/register` e `/auth/login`, requerem autenticação via token JWT no header `Authorization: Bearer <token>`.

## Autenticação

Implementação baseada em JWT (JSON Web Tokens) com OAuth2 Password Bearer.

### Fluxo de Autenticação

1. Cliente envia credenciais (`username` e `password`) para `/auth/login`
2. Servidor valida credenciais e gera token JWT contendo `user_id` no campo `sub`
3. Token expira em 7 dias (configurável via `ACCESS_TOKEN_EXPIRE_MINUTES`)
4. Cliente envia token em requisições subsequentes no header `Authorization: Bearer <token>`
5. Middleware `get_current_user` valida token e recupera usuário do banco

### Segurança

- Senhas armazenadas como hash bcrypt (truncadas para 72 bytes, limite do bcrypt)
- Tokens assinados com algoritmo HS256
- Validação de usuário ativo em cada requisição autenticada
- Isolamento de dados por `user_id` em todas as consultas

## Agente Text2SQL: Arquitetura e Implementação

O sistema implementa um agente conversacional que converte linguagem natural em operações SQL e inserções de dados. Utiliza o modelo Gemini 2.5 Flash da Google para processamento de linguagem natural.

### Arquitetura Geral

O agente opera em três modos distintos baseados na identificação de intenção:

1. **Conversação**: Respostas casuais sem acesso ao banco de dados
2. **Consulta (Query)**: Geração e execução de queries SELECT
3. **Inserção (Insert)**: Extração de dados e criação de entidades

### Fluxo de Processamento

```
Prompt do Usuário
    ↓
identify_intent()
    ↓
┌─────────────────┬──────────────────┬─────────────────┐
│ conversation    │ query            │ add_data        │
│                 │                  │                 │
│ handle_         │ handle_query()   │ handle_insert() │
│ conversation()  │                  │                 │
│                 │                  │                 │
│ Geração LLM     │ Geração SQL      │ Extração JSON   │
│ → Resposta      │ → Validação      │ → Validação     │
│ orgânica        │ → Execução       │ → Criação       │
│                 │ → Explicação     │ → Confirmação   │
└─────────────────┴──────────────────┴─────────────────┘
```

### Identificação de Intenção

A função `identify_intent()` implementa heurísticas baseadas em palavras-chave e padrões:

**Conversação:**

- Frases curtas (< 20 caracteres) contendo cumprimentos: "oi", "olá", "tudo bem", "obrigado", "tchau"
- Perguntas gerais sobre finanças pessoais ou uso do sistema
- Não requer acesso ao banco de dados
- Respostas geradas organicamente pelo LLM com contexto de assistente financeiro

**Inserção de Dados:**

- Palavras-chave: "adicionar", "criar", "novo", "gastei", "paguei", "recebi", "registrar", "inserir"
- Presença de números combinados com palavras como "reais", "R$", "de", "com"
- Prioridade sobre consultas quando detectado

**Consulta:**

- Palavras-chave: "quanto", "qual", "quais", "mostre", "liste", "total", "saldo", "gastos", "receitas"
- Referências temporais: "este mês", "hoje", "ontem", "últimas"
- Referências a entidades: "transações", "contas", "metas", "investimentos"

**Ordem de Avaliação:**

1. Verificação de conversação casual
2. Verificação de inserção
3. Verificação de consulta
4. Padrão: conversação

### Processamento de Conversação

A função `handle_conversation()` processa interações que não requerem acesso ao banco de dados através de geração orgânica pelo LLM.

#### Prompt de Sistema para Conversação

O prompt instrui o modelo a:

- Atuar como assistente financeiro do Cash Plan
- Manter conversação natural e amigável
- Responder perguntas educativas sobre finanças pessoais
- Orientar sobre uso do sistema
- Sugerir funcionalidades quando apropriado
- Não inventar dados ou informações sem acesso ao banco

#### Características

- Respostas geradas dinamicamente pelo Gemini 2.5 Flash
- Contexto personalizado com nome do usuário
- Linguagem natural em português brasileiro
- Respostas concisas mas completas
- Orientação para consultas específicas quando necessário

#### Fluxo de Processamento

```python
# 1. Construção do prompt com contexto do usuário
system_prompt = f"Você é um assistente financeiro... {user_name}"

# 2. Geração de resposta pelo LLM
chat = model.start_chat(history=[])
response = chat.send_message(system_prompt + user_message)

# 3. Retorno da resposta gerada
return {"response": response.text}
```

### Geração de SQL (Text2SQL)

#### Prompt de Sistema

O prompt enviado ao Gemini contém:

1. **Contexto do Usuário**: Nome e ID do usuário autenticado
2. **Schema do Banco**: Geração dinâmica via `get_db_schema()` usando SQLAlchemy Inspector
3. **Instruções Específicas**:
   - Análise da pergunta em linguagem natural
   - Geração de SQL SELECT válido para PostgreSQL
   - Inclusão obrigatória de `WHERE user_id = {current_user.id}` em todas as queries
   - Uso exclusivo de comandos SELECT
   - Retorno apenas da query SQL pura, sem markdown ou formatação
   - Suporte a agregações (SUM, AVG, COUNT) e funções de data (DATE_TRUNC, EXTRACT)

#### Processamento da Query

```python
# 1. Geração do SQL pelo modelo
sql_response = chat.send_message(system_prompt + user_prompt)
sql_query = sql_response.text.strip()

# 2. Validação de segurança
is_valid, clean_query = validate_sql_query(sql_query)

# 3. Execução no banco
result = db.execute(text(clean_query)).fetchall()

# 4. Explicação dos resultados
explanation = chat.send_message(explanation_prompt)
```

#### Validação de Segurança

A função `validate_sql_query()` implementa múltiplas camadas de proteção:

**Limpeza:**

- Remoção de blocos markdown (`sql, `)
- Remoção de comentários SQL (--)

**Lista de Comandos Bloqueados:**

- `DROP`, `DELETE`, `TRUNCATE`, `ALTER`, `CREATE`, `GRANT`, `REVOKE`, `EXEC`, `EXECUTE`, `UPDATE`
- Padrões de injeção: `;--`, `XP_`

**Validação de Tipo:**

- Query deve iniciar com `SELECT` (case-insensitive)
- Rejeição de qualquer outro comando SQL

**Resultado:**

- Retorna tupla `(is_valid: bool, clean_query: str)`
- Se inválida, retorna mensagem de erro específica

#### Explicação dos Resultados

Após execução bem-sucedida, o modelo recebe:

- Resultados da query em formato de lista de dicionários
- Instrução para explicar de forma amigável em português
- Formatação de valores monetários em reais (R$)
- Tratamento de casos sem resultados

### Inserção de Dados

#### Prompt de Sistema para Inserção

O prompt contém:

1. **Contexto Temporal**: Data atual no formato YYYY-MM-DD
2. **Schema do Banco**: Estrutura completa das tabelas
3. **Exemplos de Extração**: Casos de uso para cada tipo de entidade
4. **Regras de Validação**:
   - Campos obrigatórios por tipo de entidade
   - Formato de dados esperado
   - Valores padrão quando não especificados
   - Tratamento de erros quando informações faltam

#### Tipos de Entidades Suportadas

**Transações:**

- Campos obrigatórios: `description`, `amount`, `type`
- Campos opcionais: `date` (padrão: hoje), `category` (padrão: "Outros"), `account_id`
- Lógica: `amount` negativo para despesas (`type: "expense"`), positivo para receitas (`type: "income"`)

**Contas:**

- Campos obrigatórios: `name`, `bank`
- Campos opcionais: `balance` (padrão: 0.0), `color`

**Metas:**

- Campos obrigatórios: `name`, `target`
- Campos opcionais: `current` (padrão: 0.0), `color`

**Investimentos:**

- Campos obrigatórios: `name`, `type` ("Renda Fixa" ou "Renda Variável"), `value`
- Campos opcionais: `return_rate` (padrão: 0.0), `color`

**Cartões de Crédito:**

- Campos obrigatórios: `name`, `bank`, `limit`
- Campos opcionais: `used` (padrão: 0), `color`

#### Processamento de Inserção

```python
# 1. Extração de dados via LLM
response = chat.send_message(system_prompt + user_prompt)
data = json.loads(response_text)

# 2. Validação de campos obrigatórios
if "error" in data:
    return error_response

# 3. Adição automática de user_id
entity_data["user_id"] = current_user.id

# 4. Validações específicas por tipo
# - Transações: normalização de data, sinal de amount
# - Outros: valores padrão

# 5. Criação da entidade
new_item = EntityClass(**entity_data)
db.add(new_item)
db.commit()

# 6. Mensagem de confirmação personalizada
```

#### Validações Específicas

**Transações:**

- Data: parsing de strings em formato YYYY-MM-DD, fallback para hoje
- Amount: garantia de valor negativo para despesas
- Category: atribuição de "Outros" se não fornecida

**Tratamento de Erros:**

- JSON inválido: solicitação de reformulação
- Campos faltantes: mensagem específica listando campos obrigatórios
- Erro de banco: rollback da transação e mensagem de erro

### Premissas e Lógicas Implementadas

#### Isolamento de Dados

- Todas as queries geradas incluem `WHERE user_id = {current_user.id}`
- Inserções recebem `user_id` automaticamente
- Validação de propriedade em operações de atualização e exclusão

#### Segurança SQL

- Whitelist de comandos permitidos (apenas SELECT para consultas)
- Blacklist de comandos perigosos
- Sanitização de entrada (remoção de markdown e comentários)
- Execução via SQLAlchemy `text()` com parâmetros seguros

#### Robustez

- Tratamento de erros em cada etapa do pipeline
- Mensagens de erro descritivas para o usuário
- Logging de erros no console para debugging
- Rollback automático em caso de falha de inserção

#### Experiência do Usuário

- Respostas em português brasileiro
- Formatação de valores monetários
- Mensagens de confirmação detalhadas após inserções
- Explicações contextuais dos resultados de consultas

#### Limitações Conhecidas

- Modelo Gemini pode gerar SQL incorreto em casos complexos
- Identificação de intenção baseada em heurísticas simples (pode falhar em casos ambíguos)
- Não há histórico de conversação persistente entre requisições
- Validação de SQL não cobre todos os casos de injeção possíveis (depende do modelo gerar SQL válido)

### Configuração do Modelo

- Modelo utilizado: `gemini-2.5-flash`
- API Key configurada via variável de ambiente `GEMINI_API_KEY`
- Sessão de chat iniciada sem histórico (stateless)
- Timeout e retry não configurados explicitamente (dependem da biblioteca)

### Exemplos de Uso

**Consulta:**

```
Prompt: "Quanto gastei este mês?"
→ SQL: SELECT SUM(amount) FROM transactions WHERE user_id = 1 AND type = 'expense' AND DATE_TRUNC('month', date) = DATE_TRUNC('month', CURRENT_DATE)
→ Resposta: "Em outubro de 2025, você gastou R$ 2.350,00 no total."
```

**Inserção:**

```
Prompt: "Gastei 50 com mercado"
→ JSON: {"entity_type": "transaction", "data": {"description": "Mercado", "category": "Alimentação", "date": "2025-10-28", "amount": -50.0, "type": "expense"}}
→ Resposta: "Transação adicionada com sucesso! Mercado - R$ 50.00 (despesa) - Categoria: Alimentação - Data: 28/10/2025"
```
