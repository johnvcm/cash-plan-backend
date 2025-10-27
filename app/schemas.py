from pydantic import BaseModel, EmailStr, field_serializer, ConfigDict, model_serializer
from typing import Optional, List, Any, Dict
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
    date: str  # Aceitar string (YYYY-MM-DD) ao invés de date
    amount: float
    type: str
    account_id: Optional[int] = None


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    description: Optional[str] = None
    category: Optional[str] = None
    date: Optional[str] = None  # Aceitar string ao invés de date
    amount: Optional[float] = None
    type: Optional[str] = None
    account_id: Optional[int] = None


class Transaction(TransactionBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    @model_serializer(mode='wrap')
    def serialize_model(self, serializer) -> Dict[str, Any]:
        """Serializa o modelo completo, convertendo date para string"""
        data = serializer(self)
        
        # Converter date para string se necessário
        if 'date' in data:
            date_value = data['date']
            if isinstance(date_value, date) and not isinstance(date_value, datetime):
                data['date'] = date_value.isoformat()
        
        return data


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


# Shopping List Schemas
class ShoppingItemBase(BaseModel):
    name: str
    category: str
    quantity: str
    estimated_price: float = 0.0
    actual_price: Optional[float] = None
    is_purchased: bool = False
    notes: Optional[str] = None
    order: int = 0


class ShoppingItemCreate(ShoppingItemBase):
    pass


class ShoppingItemUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    quantity: Optional[str] = None
    estimated_price: Optional[float] = None
    actual_price: Optional[float] = None
    is_purchased: Optional[bool] = None
    notes: Optional[str] = None
    order: Optional[int] = None


class ShoppingItem(ShoppingItemBase):
    id: int
    shopping_list_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ShoppingListBase(BaseModel):
    name: str
    month: Optional[str] = None
    status: str = "active"
    total_estimated: float = 0.0
    total_spent: float = 0.0


class ShoppingListCreate(ShoppingListBase):
    items: Optional[List[ShoppingItemCreate]] = []


class ShoppingListUpdate(BaseModel):
    name: Optional[str] = None
    month: Optional[str] = None
    status: Optional[str] = None
    total_estimated: Optional[float] = None
    total_spent: Optional[float] = None


class ShoppingList(ShoppingListBase):
    id: int
    items: List[ShoppingItem] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== CATEGORIES ====================

class CategoryBase(BaseModel):
    name: str
    type: str  # "income" ou "expense"


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None


class Category(CategoryBase):
    id: int
    user_id: int
    is_default: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

