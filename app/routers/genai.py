import os
import google.generativeai as genai
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.schemas import User
from app.auth import get_current_user
from app.db_schema import get_db_schema

router = APIRouter()

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-pro")

@router.post("/genai/chat")
async def genai_chat(
    prompt: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        db_schema = get_db_schema()
        
        # System prompt for text-to-sql
        system_prompt = f"""
        Você é um assistente financeiro do app Cash Plan. O usuário atual é {current_user.name} (ID: {current_user.id}).
        Seu objetivo é responder a perguntas do usuário sobre seus dados financeiros, convertendo a pergunta em uma consulta SQL e, em seguida, explicando o resultado em linguagem natural.
        
        Aqui está o esquema do banco de dados:
        {db_schema}
        
        Instruções:
        1. Analise a pergunta do usuário.
        2. Gere uma consulta SQL que responda à pergunta. A consulta deve sempre filtrar os dados pelo `user_id` do usuário atual, que é `{current_user.id}`.
        3. Retorne APENAS a consulta SQL, sem nenhuma formatação ou texto adicional.
        """
        
        chat = model.start_chat(history=[])
        sql_response = chat.send_message(f"{system_prompt}\n\nPergunta do usuário: {prompt}")
        
        sql_query = sql_response.text.strip()
        
        # Execute the query
        try:
            result = db.execute(text(sql_query)).fetchall()
            
            # Follow-up prompt to explain the results
            explanation_prompt = f"""
            A consulta SQL `{sql_query}` foi executada e retornou os seguintes dados:
            {result}
            
            Explique esses dados para o usuário em uma linguagem amigável e natural.
            """
            
            explanation_response = chat.send_message(explanation_prompt)
            return {"response": explanation_response.text}
            
        except Exception as e:
            return {"response": f"Desculpe, não consegui executar a consulta para responder à sua pergunta. Detalhes do erro: {str(e)}"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
