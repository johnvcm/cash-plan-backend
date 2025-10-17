from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models, schemas
from app.auth import get_current_active_user

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("/", response_model=List[schemas.Account])
def get_accounts(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Retorna todas as contas do usuário autenticado"""
    accounts = db.query(models.Account).filter(
        models.Account.user_id == current_user.id
    ).all()
    return accounts


@router.get("/{account_id}", response_model=schemas.Account)
def get_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Retorna uma conta específica do usuário"""
    account = db.query(models.Account).filter(
        models.Account.id == account_id,
        models.Account.user_id == current_user.id
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.post("/", response_model=schemas.Account, status_code=status.HTTP_201_CREATED)
def create_account(
    account: schemas.AccountCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Cria uma nova conta para o usuário autenticado"""
    db_account = models.Account(
        **account.model_dump(),
        user_id=current_user.id
    )
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account


@router.put("/{account_id}", response_model=schemas.Account)
def update_account(
    account_id: int,
    account: schemas.AccountUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Atualiza uma conta do usuário"""
    db_account = db.query(models.Account).filter(
        models.Account.id == account_id,
        models.Account.user_id == current_user.id
    ).first()
    
    if not db_account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    update_data = account.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_account, key, value)
    
    db.commit()
    db.refresh(db_account)
    return db_account


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Deleta uma conta do usuário"""
    db_account = db.query(models.Account).filter(
        models.Account.id == account_id,
        models.Account.user_id == current_user.id
    ).first()
    
    if not db_account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    db.delete(db_account)
    db.commit()
    return None

