from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models, schemas
from app.auth import get_current_active_user

router = APIRouter(prefix="/investments", tags=["investments"])


@router.get("/", response_model=List[schemas.Investment])
def get_investments(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Retorna todos os investimentos do usuário autenticado"""
    investments = db.query(models.Investment).filter(
        models.Investment.user_id == current_user.id
    ).all()
    return investments


@router.get("/{investment_id}", response_model=schemas.Investment)
def get_investment(
    investment_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Retorna um investimento específico do usuário"""
    investment = db.query(models.Investment).filter(
        models.Investment.id == investment_id,
        models.Investment.user_id == current_user.id
    ).first()
    
    if not investment:
        raise HTTPException(status_code=404, detail="Investment not found")
    return investment


@router.post("/", response_model=schemas.Investment, status_code=status.HTTP_201_CREATED)
def create_investment(
    investment: schemas.InvestmentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Cria um novo investimento para o usuário autenticado"""
    db_investment = models.Investment(
        **investment.model_dump(),
        user_id=current_user.id
    )
    db.add(db_investment)
    db.commit()
    db.refresh(db_investment)
    return db_investment


@router.put("/{investment_id}", response_model=schemas.Investment)
def update_investment(
    investment_id: int,
    investment: schemas.InvestmentUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Atualiza um investimento do usuário"""
    db_investment = db.query(models.Investment).filter(
        models.Investment.id == investment_id,
        models.Investment.user_id == current_user.id
    ).first()
    
    if not db_investment:
        raise HTTPException(status_code=404, detail="Investment not found")
    
    update_data = investment.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_investment, key, value)
    
    db.commit()
    db.refresh(db_investment)
    return db_investment


@router.delete("/{investment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_investment(
    investment_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Deleta um investimento do usuário"""
    db_investment = db.query(models.Investment).filter(
        models.Investment.id == investment_id,
        models.Investment.user_id == current_user.id
    ).first()
    
    if not db_investment:
        raise HTTPException(status_code=404, detail="Investment not found")
    
    db.delete(db_investment)
    db.commit()
    return None
