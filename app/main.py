from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import accounts, credit_cards, transactions, investments, goals

app = FastAPI(title="Cash Plan API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

