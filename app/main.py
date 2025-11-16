from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, accounts, credit_cards, transactions, investments, goals, shopping_lists, categories, genai

app = FastAPI(title="Cash Plan API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(accounts.router)
app.include_router(credit_cards.router)
app.include_router(transactions.router)
app.include_router(investments.router)
app.include_router(goals.router)
app.include_router(shopping_lists.router)
app.include_router(categories.router)
app.include_router(genai.router)


@app.get("/")
def read_root():
    return {"message": "Cash Plan API - Backend running successfully"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}

