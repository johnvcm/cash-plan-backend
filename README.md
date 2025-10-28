# Cash Plan Backend

Backend da aplicação Cash Plan desenvolvido com FastAPI, SQLAlchemy e PostgreSQL.

## Tecnologias

- **FastAPI**: Framework web moderno e rápido
- **SQLAlchemy**: ORM para Python
- **Alembic**: Gerenciamento de migrations
- **PostgreSQL**: Banco de dados relacional
- **UV**: Gerenciador de pacotes Python

## Estrutura do Banco de Dados (MER)

O banco de dados possui as seguintes tabelas:

### 1. accounts (Contas Bancárias)

- `id`: Integer (PK)
- `name`: String(255) - Nome da conta
- `bank`: String(255) - Nome do banco
- `balance`: Float - Saldo atual
- `investments`: Float - Total em investimentos
- `color`: String(7) - Cor hexadecimal para identificação visual
- `created_at`: DateTime
- `updated_at`: DateTime

### 2. credit_cards (Cartões de Crédito)

- `id`: Integer (PK)
- `name`: String(255) - Nome do cartão
- `bank`: String(255) - Bandeira/Banco
- `used`: Integer - Valor utilizado (em centavos)
- `limit`: Integer - Limite total (em centavos)
- `color`: String(7) - Cor hexadecimal
- `created_at`: DateTime
- `updated_at`: DateTime

### 3. transactions (Lançamentos/Transações)

- `id`: Integer (PK)
- `description`: String(500) - Descrição da transação
- `category`: String(255) - Categoria
- `date`: Date - Data da transação
- `amount`: Float - Valor (positivo para receitas, negativo para despesas)
- `type`: Enum('income', 'expense') - Tipo da transação
- `account_id`: Integer (FK -> accounts.id) - Conta relacionada (opcional)
- `created_at`: DateTime
- `updated_at`: DateTime

### 4. investments (Investimentos)

- `id`: Integer (PK)
- `name`: String(255) - Nome do investimento
- `type`: Enum('Renda Fixa', 'Renda Variável') - Tipo
- `value`: Float - Valor investido
- `return_rate`: Float - Taxa de retorno (%)
- `color`: String(7) - Cor hexadecimal
- `created_at`: DateTime
- `updated_at`: DateTime

### 5. goals (Metas Financeiras)

- `id`: Integer (PK)
- `name`: String(255) - Nome da meta
- `target`: Float - Valor alvo
- `current`: Float - Valor atual acumulado
- `color`: String(7) - Cor hexadecimal
- `created_at`: DateTime
- `updated_at`: DateTime

## Configuração

### 1. Criar arquivo .env

Crie um arquivo `.env` na raiz do projeto backend:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost/cash_plan
```

### 2. Instalar dependências

```bash
uv sync
```

### 3. Criar banco de dados

```sql
CREATE DATABASE cash_plan;
```

### 4. Aplicar migrations

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

## Executar o servidor

```bash
# Método 1: Usando o arquivo main.py na raiz (recomendado)
uv run main.py

# Método 2: Usando uvicorn diretamente
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

O servidor estará disponível em: http://localhost:8080

- API docs (Swagger): http://localhost:8080/docs
- API docs (ReDoc): http://localhost:8080/redoc

## Criar novas migrations

Sempre que modificar os modelos em `app/models.py`, crie uma nova migration:

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
│   ├── database.py          # Configuração do banco
│   ├── main.py             # Entrada da aplicação FastAPI
│   └── models.py           # Modelos SQLAlchemy
├── alembic.ini              # Configuração do Alembic
├── pyproject.toml           # Dependências e configuração do projeto
├── .env                     # Variáveis de ambiente (não versionar)
└── README.md               # Este arquivo
```

## Assistente GenAI (Gemini)

O backend inclui um assistente financeiro inteligente baseado no Gemini AI da Google.

### Configuração da API Key

Adicione a chave da API do Gemini no arquivo `.env`:

```env
GEMINI_API_KEY=sua_chave_aqui
```

Para obter uma chave gratuita, acesse: https://makersuite.google.com/app/apikey

### Funcionalidades do Assistente

1. **Consultas Inteligentes (Text-to-SQL)**

   - Converte perguntas em linguagem natural para SQL
   - Executa consultas seguras no banco de dados
   - Retorna explicações em português
   - Exemplo: "Quanto gastei este mês?" ou "Qual meu saldo total?"

2. **Inserção de Dados por IA**

   - Adiciona transações, contas, metas e investimentos usando linguagem natural
   - Exemplo: "Adicionar transação de 50 reais no mercado"
   - Exemplo: "Criar conta no Banco Inter com saldo de 1000"

3. **Segurança**
   - Todas as queries são filtradas automaticamente por `user_id`
   - Validação de SQL para prevenir injection
   - Apenas comandos SELECT para consultas
   - Auditoria de comandos perigosos

### Endpoints

- `POST /genai/chat` - Endpoint principal
  - Parâmetros:
    - `prompt`: pergunta ou comando do usuário
    - `action_type`: "query" (consulta) ou "insert" (inserção)
  - Requer autenticação (token JWT)

## Próximos passos

1. ~~Criar schemas Pydantic para validação~~ ✅
2. ~~Implementar rotas CRUD para cada entidade~~ ✅
3. ~~Adicionar autenticação e autorização~~ ✅
4. Implementar testes automatizados
5. ~~Adicionar validações de negócio~~ ✅
6. ~~Integrar assistente GenAI~~ ✅
