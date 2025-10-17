from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models, schemas
from app.auth import get_current_active_user

router = APIRouter(prefix="/credit-cards", tags=["credit_cards"])


@router.get("/", response_model=List[schemas.CreditCard])
def get_credit_cards(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Retorna todos os cartões do usuário autenticado"""
    cards = db.query(models.CreditCard).filter(
        models.CreditCard.user_id == current_user.id
    ).all()
    return cards


@router.get("/{card_id}", response_model=schemas.CreditCard)
def get_credit_card(
    card_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Retorna um cartão específico do usuário"""
    card = db.query(models.CreditCard).filter(
        models.CreditCard.id == card_id,
        models.CreditCard.user_id == current_user.id
    ).first()
    
    if not card:
        raise HTTPException(status_code=404, detail="Credit card not found")
    return card


@router.post("/", response_model=schemas.CreditCard, status_code=status.HTTP_201_CREATED)
def create_credit_card(
    card: schemas.CreditCardCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Cria um novo cartão para o usuário autenticado"""
    db_card = models.CreditCard(
        **card.model_dump(),
        user_id=current_user.id
    )
    db.add(db_card)
    db.commit()
    db.refresh(db_card)
    return db_card


@router.put("/{card_id}", response_model=schemas.CreditCard)
def update_credit_card(
    card_id: int,
    card: schemas.CreditCardUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Atualiza um cartão do usuário"""
    db_card = db.query(models.CreditCard).filter(
        models.CreditCard.id == card_id,
        models.CreditCard.user_id == current_user.id
    ).first()
    
    if not db_card:
        raise HTTPException(status_code=404, detail="Credit card not found")
    
    update_data = card.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_card, key, value)
    
    db.commit()
    db.refresh(db_card)
    return db_card


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_credit_card(
    card_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Deleta um cartão do usuário"""
    db_card = db.query(models.CreditCard).filter(
        models.CreditCard.id == card_id,
        models.CreditCard.user_id == current_user.id
    ).first()
    
    if not db_card:
        raise HTTPException(status_code=404, detail="Credit card not found")
    
    db.delete(db_card)
    db.commit()
    return None
