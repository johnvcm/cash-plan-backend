import os
import re
import google.generativeai as genai
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.schemas import User
from app.auth import get_current_user
from app.db_schema import get_db_schema
from pydantic import BaseModel

router = APIRouter()

genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))
# Usando gemini-2.0-flash que é rápido e eficiente
model = genai.GenerativeModel("gemini-2.0-flash")


class ChatRequest(BaseModel):
    prompt: str


def validate_sql_query(query: str) -> tuple[bool, str]:
    """
    Valida se a query SQL é segura para execução.
    Retorna (is_valid, error_message)
    """
    query_upper = query.upper().strip()
    
    # Remove comentários SQL e código markdown
    query_clean = re.sub(r'```sql|```', '', query, flags=re.IGNORECASE)
    query_clean = re.sub(r'--.*$', '', query_clean, flags=re.MULTILINE)
    query_clean = query_clean.strip()
    
    # Lista de comandos perigosos
    dangerous_commands = [
        'DROP', 'DELETE', 'TRUNCATE', 'ALTER', 
        'CREATE', 'GRANT', 'REVOKE', 'EXEC',
        'EXECUTE', 'UPDATE', ';--', 'XP_'
    ]
    
    # Verifica se contém comandos perigosos para queries de leitura
    for cmd in dangerous_commands:
        if cmd in query_upper:
            return False, f"Comando SQL não permitido: {cmd}"
    
    # Deve começar com SELECT para queries de leitura
    if not query_upper.startswith('SELECT'):
        return False, "Apenas consultas SELECT são permitidas para leitura"
    
    return True, query_clean

@router.post("/genai/chat")
async def genai_chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Endpoint principal do assistente GenAI.
    Identifica automaticamente se é uma pergunta ou um comando.
    """
    # Verifica se a API key está configurada
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise HTTPException(
            status_code=500, 
            detail="GEMINI_API_KEY não configurada no servidor. Adicione a chave no arquivo .env"
        )
    
    try:
        # Identifica a intenção do usuário
        intent = await identify_intent(request.prompt)
        
        if intent == "conversation":
            return await handle_conversation(request.prompt, current_user)
        elif intent == "add_data":
            return await handle_insert(request.prompt, db, current_user)
        else:
            return await handle_query(request.prompt, db, current_user)
            
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"Erro no assistente GenAI: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)  # Log para o console
        raise HTTPException(status_code=500, detail=str(e))


async def identify_intent(prompt: str) -> str:
    """
    Identifica a intenção do usuário: 'conversation', 'add_data' ou 'query'
    """
    prompt_lower = prompt.lower().strip()
    
    # Cumprimentos e conversação casual (não precisa acessar BD)
    casual_keywords = [
        'oi', 'olá', 'ola', 'hey', 'ei', 'bom dia', 'boa tarde', 'boa noite',
        'tudo bem', 'como vai', 'e ai', 'e aí', 'beleza', 'opa',
        'obrigado', 'obrigada', 'valeu', 'vlw', 'ok', 'certo',
        'tchau', 'até logo', 'até mais', 'falou'
    ]
    
    # Se for uma frase muito curta e casual
    if len(prompt_lower) < 20 and any(keyword in prompt_lower for keyword in casual_keywords):
        return "conversation"
    
    # Palavras-chave que indicam adição de dados
    add_keywords = [
        'adicionar', 'adicione', 'criar', 'crie', 'novo', 'nova',
        'gastei', 'paguei', 'comprei', 'recebi', 'ganhei',
        'registrar', 'registre', 'lançar', 'lance',
        'insira', 'inserir', 'salvar', 'salve'
    ]
    
    # Palavras-chave que indicam consulta de dados
    query_keywords = [
        'quanto', 'qual', 'quais', 'mostre', 'mostra', 'liste', 'listar',
        'total', 'saldo', 'gastos', 'receitas', 'transações', 'transacoes',
        'contas', 'metas', 'investimentos', 'cartões', 'cartoes',
        'últimas', 'ultimas', 'esse mês', 'este mês', 'hoje', 'ontem'
    ]
    
    # Verifica adição de dados
    if any(keyword in prompt_lower for keyword in add_keywords):
        return "add_data"
    
    # Verifica consulta de dados
    if any(keyword in prompt_lower for keyword in query_keywords):
        return "query"
    
    # Se contém números e menciona valores (provavelmente é adição)
    import re
    if re.search(r'\d+', prompt) and any(word in prompt_lower for word in ['reais', 'r$', 'de ', 'com ']):
        return "add_data"
    
    # Por padrão, trata como conversação casual
    return "conversation"


async def handle_conversation(prompt: str, current_user: User):
    """
    Lida com conversação casual sem precisar acessar o banco de dados
    """
    user_name = current_user.full_name or current_user.username
    prompt_lower = prompt.lower()
    
    # Respostas naturais para cumprimentos
    if any(word in prompt_lower for word in ['oi', 'olá', 'ola', 'hey', 'ei']):
        if 'tudo bem' in prompt_lower or 'como vai' in prompt_lower:
            return {
                "response": f"Olá, {user_name}! Tudo ótimo por aqui! 😊\n\nComo posso te ajudar com suas finanças hoje?"
            }
        return {
            "response": f"Olá, {user_name}! 👋\n\nEstou aqui para te ajudar com suas finanças. Pode me perguntar sobre seus gastos, adicionar transações, ou o que precisar!"
        }
    
    if any(word in prompt_lower for word in ['bom dia', 'boa tarde', 'boa noite']):
        saudacao = 'Bom dia' if 'bom dia' in prompt_lower else 'Boa tarde' if 'boa tarde' in prompt_lower else 'Boa noite'
        return {
            "response": f"{saudacao}, {user_name}! ✨\n\nPronto para te ajudar com suas finanças. O que você precisa?"
        }
    
    if any(word in prompt_lower for word in ['obrigado', 'obrigada', 'valeu', 'vlw']):
        return {
            "response": "Por nada! 😊 Estou sempre aqui quando precisar. Conte comigo!"
        }
    
    if any(word in prompt_lower for word in ['tchau', 'até logo', 'até mais', 'falou']):
        return {
            "response": "Até logo! 👋 Qualquer coisa, é só me chamar!"
        }
    
    # Resposta genérica para outras conversas casuais
    return {
        "response": f"Entendo, {user_name}! Como posso te ajudar com suas finanças? Posso responder perguntas sobre seus dados ou adicionar novas transações. 💰"
    }


async def handle_query(prompt: str, db: Session, current_user: User):
    """
    Lida com perguntas do usuário (apenas leitura - SELECT)
    """
    try:
        db_schema = get_db_schema()
        user_name = current_user.full_name or current_user.username
        
        system_prompt = f"""
        Você é um assistente financeiro do app Cash Plan. O usuário atual é {user_name} (ID: {current_user.id}).
        Seu objetivo é responder a perguntas do usuário sobre seus dados financeiros, convertendo a pergunta em uma consulta SQL.
        
        Aqui está o esquema do banco de dados:
        {db_schema}
        
        Instruções IMPORTANTES:
        1. Analise a pergunta do usuário.
        2. Gere uma consulta SQL que responda à pergunta. A consulta deve SEMPRE incluir WHERE user_id = {current_user.id} para filtrar apenas os dados do usuário.
        3. Use APENAS comandos SELECT. NUNCA use INSERT, UPDATE, DELETE, DROP ou outros comandos.
        4. Retorne APENAS a consulta SQL pura, sem formatação markdown, sem ```sql, sem texto adicional.
        5. A consulta deve ser válida para PostgreSQL.
        6. Se precisar de agregações, use SUM, AVG, COUNT, etc.
        7. Para datas, use DATE_TRUNC ou EXTRACT conforme necessário.
        """
        
        chat = model.start_chat(history=[])
        sql_response = chat.send_message(f"{system_prompt}\n\nPergunta do usuário: {prompt}")
        
        sql_query = sql_response.text.strip()
    except Exception as e:
        return {
            "response": f"Erro ao gerar consulta SQL: {str(e)}. Verifique se a GEMINI_API_KEY está configurada corretamente.",
            "error": True
        }
    
    # Valida a query antes de executar
    is_valid, clean_query = validate_sql_query(sql_query)
    if not is_valid:
        return {
            "response": f"Desculpe, não posso executar essa operação. {clean_query}",
            "error": True
        }
    
    # Executa a query
    try:
        result = db.execute(text(clean_query)).fetchall()
        
        # Converte resultado para formato mais legível
        result_list = [dict(row._mapping) for row in result] if result else []
        
        # Pede ao Gemini para explicar os resultados
        explanation_prompt = f"""
        A consulta SQL foi executada com sucesso e retornou os seguintes dados:
        {result_list}
        
        Explique esses dados para o usuário de forma amigável, clara e em português.
        Se não houver dados, explique que não foram encontrados registros.
        Formate valores monetários em reais (R$) quando aplicável.
        """
        
        explanation_response = chat.send_message(explanation_prompt)
        return {
            "response": explanation_response.text,
            "sql_query": clean_query,
            "data": result_list
        }
        
    except Exception as e:
        return {
            "response": f"Desculpe, ocorreu um erro ao processar sua pergunta: {str(e)}",
            "error": True
        }


async def handle_insert(prompt: str, db: Session, current_user: User):
    """
    Lida com inserções de dados (transações, contas, metas, etc)
    """
    from app.models import Transaction, Account, CreditCard, Goal, Investment
    from datetime import datetime, date
    
    db_schema = get_db_schema()
    user_name = current_user.full_name or current_user.username
    
    from datetime import date as date_type
    today = date_type.today().strftime("%Y-%m-%d")
    
    system_prompt = f"""
    Você é um assistente financeiro do app Cash Plan. O usuário atual é {user_name} (ID: {current_user.id}).
    Seu objetivo é ajudar o usuário a adicionar dados financeiros ao sistema.
    
    Hoje é {today}.
    
    Aqui está o esquema do banco de dados:
    {db_schema}
    
    O usuário quer adicionar dados. Analise o pedido e retorne um JSON com as informações extraídas.
    
    Exemplos de pedidos e respostas:
    
    Pedido: "Gastei 50 com mercado"
    Resposta: {{"entity_type": "transaction", "data": {{"description": "Mercado", "category": "Alimentação", "date": "{today}", "amount": -50.0, "type": "expense"}}}}
    
    Pedido: "Adicionar uma transação de 50 reais no Mercado dia 15/10"
    Resposta: {{"entity_type": "transaction", "data": {{"description": "Mercado", "category": "Alimentação", "date": "2025-10-15", "amount": -50.0, "type": "expense"}}}}
    
    Pedido: "Recebi 1000 de salário"
    Resposta: {{"entity_type": "transaction", "data": {{"description": "Salário", "category": "Salário", "date": "{today}", "amount": 1000.0, "type": "income"}}}}
    
    Pedido: "Criar uma conta no Banco Inter com saldo de 1000"
    Resposta: {{"entity_type": "account", "data": {{"name": "Conta Inter", "bank": "Banco Inter", "balance": 1000.0}}}}
    
    Pedido: "Adicionar meta de 5000 reais para comprar um carro"
    Resposta: {{"entity_type": "goal", "data": {{"name": "Comprar um carro", "target": 5000.0, "current": 0.0}}}}
    
    REGRAS IMPORTANTES:
    
    Para transações (SEMPRE obrigatórios):
    - type: "income" (receita) ou "expense" (despesa)
    - amount: valor em float (NEGATIVO para despesas, POSITIVO para receitas)
    - date: formato YYYY-MM-DD (se não especificado, use {today})
    - description: descrição clara da transação
    - category: categoria apropriada (Alimentação, Transporte, Salário, etc)
    
    Para contas:
    - name: nome da conta
    - bank: nome do banco
    - balance: saldo inicial (float, padrão 0.0)
    
    Para metas:
    - name: nome da meta
    - target: valor alvo (float)
    - current: valor atual (float, padrão 0.0)
    
    Para investimentos:
    - name: nome do investimento
    - type: "Renda Fixa" ou "Renda Variável"
    - value: valor investido (float)
    - return_rate: taxa de retorno em % (float, padrão 0.0)
    
    Se faltar informação OBRIGATÓRIA, retorne:
    {{"error": "Mensagem explicando o que falta"}}
    
    Retorne APENAS o JSON, sem texto adicional, sem markdown.
    """
    
    chat = model.start_chat(history=[])
    response = chat.send_message(f"{system_prompt}\n\nPedido do usuário: {prompt}")
    
    try:
        import json
        # Remove markdown se houver
        response_text = response.text.strip()
        response_text = re.sub(r'```json\s*|\s*```', '', response_text)
        
        data = json.loads(response_text)
        
        if "error" in data:
            return {
                "response": f"Preciso de mais informações: {data['error']}",
                "error": True
            }
        
        entity_type = data.get("entity_type")
        entity_data = data.get("data", {})
        
        # Adiciona user_id automaticamente
        entity_data["user_id"] = current_user.id
        
        # Cria a entidade apropriada
        if entity_type == "transaction":
            # Validação: campos obrigatórios
            required_fields = ["description", "amount", "type"]
            missing = [f for f in required_fields if f not in entity_data or not entity_data[f]]
            if missing:
                return {
                    "response": f"Faltam informações para criar a transação: {', '.join(missing)}. Tente descrever com mais detalhes.",
                    "error": True
                }
            
            # Validação: data é obrigatória (usa hoje como fallback)
            if "date" not in entity_data or not entity_data["date"]:
                entity_data["date"] = date.today()
            elif isinstance(entity_data["date"], str):
                # Processa data em string
                try:
                    entity_data["date"] = datetime.strptime(entity_data["date"], "%Y-%m-%d").date()
                except ValueError:
                    entity_data["date"] = date.today()
            
            # Validação: garante que amount é negativo para despesas
            if entity_data.get("type") == "expense" and entity_data.get("amount", 0) > 0:
                entity_data["amount"] = -abs(entity_data["amount"])
            
            # Validação: category padrão se não fornecida
            if "category" not in entity_data or not entity_data["category"]:
                entity_data["category"] = "Outros"
            
            new_item = Transaction(**entity_data)
            item_name = "transação"
            
        elif entity_type == "account":
            new_item = Account(**entity_data)
            item_name = "conta"
            
        elif entity_type == "credit_card":
            new_item = CreditCard(**entity_data)
            item_name = "cartão de crédito"
            
        elif entity_type == "goal":
            new_item = Goal(**entity_data)
            item_name = "meta"
            
        elif entity_type == "investment":
            new_item = Investment(**entity_data)
            item_name = "investimento"
        else:
            return {
                "response": "Desculpe, não entendi que tipo de dado você quer adicionar.",
                "error": True
            }
        
        # Salva no banco
        db.add(new_item)
        db.commit()
        db.refresh(new_item)
        
        # Cria mensagem de confirmação personalizada
        if entity_type == "transaction":
            valor_formatado = f"R$ {abs(entity_data['amount']):.2f}"
            tipo_texto = "receita" if entity_data['type'] == "income" else "despesa"
            data_formatada = entity_data['date'].strftime("%d/%m/%Y")
            mensagem = f"Transação adicionada com sucesso!\n\n"
            mensagem += f"{entity_data['description']}\n"
            mensagem += f"{valor_formatado} ({tipo_texto})\n"
            mensagem += f"Categoria: {entity_data['category']}\n"
            mensagem += f"Data: {data_formatada}"
        else:
            mensagem = f"{item_name.capitalize()} adicionada com sucesso!"
        
        return {
            "response": mensagem,
            "entity_type": entity_type,
            "created_id": new_item.id
        }
        
    except json.JSONDecodeError:
        return {
            "response": "Desculpe, não consegui processar sua solicitação. Pode reformular?",
            "error": True
        }
    except Exception as e:
        db.rollback()
        return {
            "response": f"Ocorreu um erro ao adicionar os dados: {str(e)}",
            "error": True
        }
