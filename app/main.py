from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, accounts, credit_cards, transactions, investments, goals

app = FastAPI(title="Cash Plan API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique os domínios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth router (não requer autenticação)
app.include_router(auth.router)

# Routers protegidos (vamos adicionar autenticação depois)
app.include_router(accounts.router)
app.include_router(credit_cards.router)
app.include_router(transactions.router)
app.include_router(investments.router)
app.include_router(goals.router)


@app.get("/")
def read_root():
    return {"message": "Cash Plan API - Backend running successfully"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}

