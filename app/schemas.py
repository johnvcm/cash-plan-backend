from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date, datetime


# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class User(UserBase):
    id: int
    is_active: int
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[int] = None


# Account Schemas
class AccountBase(BaseModel):
    name: str
    bank: str
    balance: float
    investments: float = 0.0
    color: Optional[str] = None


class AccountCreate(AccountBase):
    pass


class AccountUpdate(BaseModel):
    name: Optional[str] = None
    bank: Optional[str] = None
    balance: Optional[float] = None
    investments: Optional[float] = None
    color: Optional[str] = None


class Account(AccountBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CreditCardBase(BaseModel):
    name: str
    bank: str
    used: int = 0
    limit: int
    color: Optional[str] = None


class CreditCardCreate(CreditCardBase):
    pass


class CreditCardUpdate(BaseModel):
    name: Optional[str] = None
    bank: Optional[str] = None
    used: Optional[int] = None
    limit: Optional[int] = None
    color: Optional[str] = None


class CreditCard(CreditCardBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TransactionBase(BaseModel):
    description: str
    category: str
    date: date
    amount: float
    type: str
    account_id: Optional[int] = None


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    description: Optional[str] = None
    category: Optional[str] = None
    date: Optional[date] = None
    amount: Optional[float] = None
    type: Optional[str] = None
    account_id: Optional[int] = None


class Transaction(TransactionBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class InvestmentBase(BaseModel):
    name: str
    type: str
    value: float
    return_rate: float = 0.0
    color: Optional[str] = None


class InvestmentCreate(InvestmentBase):
    pass


class InvestmentUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    value: Optional[float] = None
    return_rate: Optional[float] = None
    color: Optional[str] = None


class Investment(InvestmentBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class GoalBase(BaseModel):
    name: str
    target: float
    current: float = 0.0
    color: Optional[str] = None


class GoalCreate(GoalBase):
    pass


class GoalUpdate(BaseModel):
    name: Optional[str] = None
    target: Optional[float] = None
    current: Optional[float] = None
    color: Optional[str] = None


class Goal(GoalBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

