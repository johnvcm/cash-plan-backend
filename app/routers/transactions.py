from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models, schemas
from app.auth import get_current_active_user

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("/", response_model=List[schemas.Transaction])
def get_transactions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Retorna todas as transações do usuário autenticado"""
    transactions = db.query(models.Transaction).filter(
        models.Transaction.user_id == current_user.id
    ).all()
    return transactions


@router.get("/{transaction_id}", response_model=schemas.Transaction)
def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Retorna uma transação específica do usuário"""
    transaction = db.query(models.Transaction).filter(
        models.Transaction.id == transaction_id,
        models.Transaction.user_id == current_user.id
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction


@router.post("/", response_model=schemas.Transaction, status_code=status.HTTP_201_CREATED)
def create_transaction(
    transaction: schemas.TransactionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Cria uma nova transação para o usuário autenticado"""
    db_transaction = models.Transaction(
        **transaction.model_dump(),
        user_id=current_user.id
    )
    db.add(db_transaction)
    
    # Atualizar saldo da conta se account_id foi fornecido
    if transaction.account_id:
        account = db.query(models.Account).filter(
            models.Account.id == transaction.account_id,
            models.Account.user_id == current_user.id
        ).first()
        
        if account:
            if transaction.type == "income":
                account.balance += transaction.amount
            else:  # expense
                account.balance -= transaction.amount
    
    db.commit()
    db.refresh(db_transaction)
    return db_transaction


@router.put("/{transaction_id}", response_model=schemas.Transaction)
def update_transaction(
    transaction_id: int,
    transaction: schemas.TransactionUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Atualiza uma transação do usuário"""
    db_transaction = db.query(models.Transaction).filter(
        models.Transaction.id == transaction_id,
        models.Transaction.user_id == current_user.id
    ).first()
    
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Guardar valores antigos para reverter o saldo
    old_account_id = db_transaction.account_id
    old_amount = db_transaction.amount
    old_type = db_transaction.type
    
    # Reverter saldo da conta antiga se houver
    if old_account_id:
        old_account = db.query(models.Account).filter(
            models.Account.id == old_account_id,
            models.Account.user_id == current_user.id
        ).first()
        
        if old_account:
            if old_type == "income":
                old_account.balance -= old_amount
            else:  # expense
                old_account.balance += old_amount
    
    # Atualizar a transação
    update_data = transaction.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_transaction, key, value)
    
    # Aplicar novo saldo na conta (pode ser a mesma ou diferente)
    if db_transaction.account_id:
        new_account = db.query(models.Account).filter(
            models.Account.id == db_transaction.account_id,
            models.Account.user_id == current_user.id
        ).first()
        
        if new_account:
            if db_transaction.type == "income":
                new_account.balance += db_transaction.amount
            else:  # expense
                new_account.balance -= db_transaction.amount
    
    db.commit()
    db.refresh(db_transaction)
    return db_transaction


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Deleta uma transação do usuário"""
    db_transaction = db.query(models.Transaction).filter(
        models.Transaction.id == transaction_id,
        models.Transaction.user_id == current_user.id
    ).first()
    
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Reverter saldo da conta antes de deletar
    if db_transaction.account_id:
        account = db.query(models.Account).filter(
            models.Account.id == db_transaction.account_id,
            models.Account.user_id == current_user.id
        ).first()
        
        if account:
            if db_transaction.type == "income":
                account.balance -= db_transaction.amount
            else:  # expense
                account.balance += db_transaction.amount
    
    db.delete(db_transaction)
    db.commit()
    return None
