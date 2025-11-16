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
model = genai.GenerativeModel("gemini-2.5-flash")


class ChatRequest(BaseModel):
    prompt: str


def validate_sql_query(query: str) -> tuple[bool, str]:
    query_upper = query.upper().strip()
    
    query_clean = re.sub(r'```sql|```', '', query, flags=re.IGNORECASE)
    query_clean = re.sub(r'--.*$', '', query_clean, flags=re.MULTILINE)
    query_clean = query_clean.strip()
    
    dangerous_commands = [
        'DROP', 'DELETE', 'TRUNCATE', 'ALTER', 
        'CREATE', 'GRANT', 'REVOKE', 'EXEC',
        'EXECUTE', 'UPDATE', ';--', 'XP_'
    ]
    
    for cmd in dangerous_commands:
        if cmd in query_upper:
            return False, f"Comando SQL não permitido: {cmd}"
    
    if not query_upper.startswith('SELECT'):
        return False, "Apenas consultas SELECT são permitidas para leitura"
    
    return True, query_clean

@router.post("/genai/chat")
async def genai_chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise HTTPException(
            status_code=500, 
            detail="GEMINI_API_KEY não configurada no servidor. Adicione a chave no arquivo .env"
        )
    
    try:
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
        print(error_detail)
        raise HTTPException(status_code=500, detail=str(e))


async def identify_intent(prompt: str) -> str:
    prompt_lower = prompt.lower().strip()
    
    casual_keywords = [
        'oi', 'olá', 'ola', 'hey', 'ei', 'bom dia', 'boa tarde', 'boa noite',
        'tudo bem', 'como vai', 'e ai', 'e aí', 'beleza', 'opa',
        'obrigado', 'obrigada', 'valeu', 'vlw', 'ok', 'certo',
        'tchau', 'até logo', 'até mais', 'falou'
    ]
    
    if len(prompt_lower) < 20 and any(keyword in prompt_lower for keyword in casual_keywords):
        return "conversation"
    
    add_keywords = [
        'adicionar', 'adicione', 'criar', 'crie', 'novo', 'nova',
        'gastei', 'paguei', 'comprei', 'recebi', 'ganhei',
        'registrar', 'registre', 'lançar', 'lance',
        'insira', 'inserir', 'salvar', 'salve'
    ]
    
    query_keywords = [
        'quanto', 'qual', 'quais', 'mostre', 'mostra', 'liste', 'listar',
        'total', 'saldo', 'gastos', 'receitas', 'transações', 'transacoes',
        'contas', 'metas', 'investimentos', 'cartões', 'cartoes',
        'últimas', 'ultimas', 'esse mês', 'este mês', 'hoje', 'ontem'
    ]
    
    if any(keyword in prompt_lower for keyword in add_keywords):
        return "add_data"
    
    if any(keyword in prompt_lower for keyword in query_keywords):
        return "query"
    
    import re
    if re.search(r'\d+', prompt) and any(word in prompt_lower for word in ['reais', 'r$', 'de ', 'com ']):
        return "add_data"
    
    return "conversation"


async def handle_conversation(prompt: str, current_user: User):
    user_name = current_user.full_name or current_user.username
    
    system_prompt = f"""
    Você é um assistente financeiro do app Cash Plan. O usuário atual é {user_name}.
    
    Você está conversando de forma natural e amigável com o usuário. Sua função é:
    - Responder perguntas sobre finanças pessoais de forma educativa
    - Orientar sobre como usar o sistema
    - Manter uma conversa natural e empática
    - Quando apropriado, sugerir funcionalidades do sistema (consultar dados, adicionar transações, etc)
    
    IMPORTANTE:
    - Seja natural, conversacional e amigável
    - Use português brasileiro
    - Mantenha respostas concisas mas completas
    - Se o usuário fizer perguntas que requerem dados do banco, oriente-o a fazer perguntas específicas como "Quanto gastei este mês?" ou "Qual meu saldo total?"
    - Não invente dados ou informações que você não tem acesso
    """
    
    try:
        chat = model.start_chat(history=[])
        response = chat.send_message(f"{system_prompt}\n\nMensagem do usuário: {prompt}")
        
        return {
            "response": response.text
        }
    except Exception as e:
        return {
            "response": f"Desculpe, ocorreu um erro ao processar sua mensagem: {str(e)}",
            "error": True
        }


async def handle_query(prompt: str, db: Session, current_user: User):
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
    
    is_valid, clean_query = validate_sql_query(sql_query)
    if not is_valid:
        return {
            "response": f"Desculpe, não posso executar essa operação. {clean_query}",
            "error": True
        }
    
    try:
        result = db.execute(text(clean_query)).fetchall()
        result_list = [dict(row._mapping) for row in result] if result else []
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
    
    IMPORTANTE: Se o usuário mencionar MÚLTIPLAS transações na mesma mensagem, retorne um array de transações.
    
    Exemplos de pedidos e respostas:
    
    Pedido: "Gastei 50 com mercado"
    Resposta: {{"entity_type": "transaction", "data": {{"description": "Mercado", "category": "Alimentação", "date": "{today}", "amount": -50.0, "type": "expense"}}}}
    
    Pedido: "Gastei 35 reais com uber, 78 reais com hamburguer e 90 reais com video game"
    Resposta: {{"entity_type": "transaction", "data": [{{"description": "Uber", "category": "Transporte", "date": "{today}", "amount": -35.0, "type": "expense"}}, {{"description": "Hamburguer", "category": "Alimentação", "date": "{today}", "amount": -78.0, "type": "expense"}}, {{"description": "Video game", "category": "Lazer", "date": "{today}", "amount": -90.0, "type": "expense"}}]}}
    
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
    - category: categoria apropriada (Alimentação, Transporte, Salário, Lazer, etc)
    
    Para múltiplas transações:
    - Se o usuário mencionar várias transações, retorne "data" como um ARRAY de objetos
    - Cada objeto do array deve ter todos os campos obrigatórios
    
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
        
        if entity_type == "transaction":
            if isinstance(entity_data, list):
                created_items = []
                mensagens = []
                
                for trans_data in entity_data:
                    trans_data["user_id"] = current_user.id
                    
                    required_fields = ["description", "amount", "type"]
                    missing = [f for f in required_fields if f not in trans_data or not trans_data[f]]
                    if missing:
                        continue
                    
                    if "date" not in trans_data or not trans_data["date"]:
                        trans_data["date"] = date.today()
                    elif isinstance(trans_data["date"], str):
                        try:
                            trans_data["date"] = datetime.strptime(trans_data["date"], "%Y-%m-%d").date()
                        except ValueError:
                            trans_data["date"] = date.today()
                    
                    if trans_data.get("type") == "expense" and trans_data.get("amount", 0) > 0:
                        trans_data["amount"] = -abs(trans_data["amount"])
                    
                    if "category" not in trans_data or not trans_data["category"]:
                        trans_data["category"] = "Outros"
                    
                    new_item = Transaction(**trans_data)
                    db.add(new_item)
                    created_items.append(new_item)
                
                if not created_items:
                    return {
                        "response": "Não foi possível criar nenhuma transação. Verifique se forneceu todas as informações necessárias.",
                        "error": True
                    }
                
                db.commit()
                
                for item in created_items:
                    db.refresh(item)
                    valor_formatado = f"R$ {abs(item.amount):.2f}"
                    tipo_texto = "receita" if item.type == "income" else "despesa"
                    data_formatada = item.date.strftime("%d/%m/%Y")
                    mensagens.append(f"{item.description} - {valor_formatado} ({tipo_texto}) - {item.category} - {data_formatada}")
                
                mensagem = f"{len(created_items)} transação(ões) adicionada(s) com sucesso!\n\n"
                mensagem += "\n".join(mensagens)
                
                return {
                    "response": mensagem,
                    "entity_type": entity_type,
                    "created_ids": [item.id for item in created_items]
                }
            else:
                entity_data["user_id"] = current_user.id
                
                required_fields = ["description", "amount", "type"]
                missing = [f for f in required_fields if f not in entity_data or not entity_data[f]]
                if missing:
                    return {
                        "response": f"Faltam informações para criar a transação: {', '.join(missing)}. Tente descrever com mais detalhes.",
                        "error": True
                    }
                
                if "date" not in entity_data or not entity_data["date"]:
                    entity_data["date"] = date.today()
                elif isinstance(entity_data["date"], str):
                    try:
                        entity_data["date"] = datetime.strptime(entity_data["date"], "%Y-%m-%d").date()
                    except ValueError:
                        entity_data["date"] = date.today()
                
                if entity_data.get("type") == "expense" and entity_data.get("amount", 0) > 0:
                    entity_data["amount"] = -abs(entity_data["amount"])
                
                if "category" not in entity_data or not entity_data["category"]:
                    entity_data["category"] = "Outros"
                
                new_item = Transaction(**entity_data)
                db.add(new_item)
                db.commit()
                db.refresh(new_item)
                
                valor_formatado = f"R$ {abs(entity_data['amount']):.2f}"
                tipo_texto = "receita" if entity_data['type'] == "income" else "despesa"
                data_formatada = entity_data['date'].strftime("%d/%m/%Y")
                mensagem = f"Transação adicionada com sucesso!\n\n"
                mensagem += f"{entity_data['description']}\n"
                mensagem += f"{valor_formatado} ({tipo_texto})\n"
                mensagem += f"Categoria: {entity_data['category']}\n"
                mensagem += f"Data: {data_formatada}"
                
                return {
                    "response": mensagem,
                    "entity_type": entity_type,
                    "created_id": new_item.id
                }
        
        entity_data["user_id"] = current_user.id
        
        if entity_type == "account":
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
        
        db.add(new_item)
        db.commit()
        db.refresh(new_item)
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
