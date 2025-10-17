from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Enum, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class TransactionType(str, enum.Enum):
    income = "income"
    expense = "expense"


class InvestmentType(str, enum.Enum):
    renda_fixa = "Renda Fixa"
    renda_variavel = "Renda Variável"


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    bank = Column(String(255), nullable=False)
    balance = Column(Float, nullable=False, default=0.0)
    investments = Column(Float, nullable=False, default=0.0)
    color = Column(String(7), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    transactions = relationship("Transaction", back_populates="account")


class CreditCard(Base):
    __tablename__ = "credit_cards"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    bank = Column(String(255), nullable=False)
    used = Column(Integer, nullable=False, default=0)
    limit = Column(Integer, nullable=False)
    color = Column(String(7), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String(500), nullable=False)
    category = Column(String(255), nullable=False)
    date = Column(Date, nullable=False)
    amount = Column(Float, nullable=False)
    type = Column(Enum(TransactionType), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    account = relationship("Account", back_populates="transactions")


class Investment(Base):
    __tablename__ = "investments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    type = Column(Enum(InvestmentType), nullable=False)
    value = Column(Float, nullable=False)
    return_rate = Column(Float, nullable=False, default=0.0)
    color = Column(String(7), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Goal(Base):
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    target = Column(Float, nullable=False)
    current = Column(Float, nullable=False, default=0.0)
    color = Column(String(7), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
