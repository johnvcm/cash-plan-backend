from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/credit-cards", tags=["credit-cards"])


@router.get("/", response_model=List[schemas.CreditCard])
def get_credit_cards(db: Session = Depends(get_db)):
    cards = db.query(models.CreditCard).all()
    return cards


@router.get("/{card_id}", response_model=schemas.CreditCard)
def get_credit_card(card_id: int, db: Session = Depends(get_db)):
    card = db.query(models.CreditCard).filter(models.CreditCard.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Credit card not found")
    return card


@router.post("/", response_model=schemas.CreditCard, status_code=201)
def create_credit_card(card: schemas.CreditCardCreate, db: Session = Depends(get_db)):
    db_card = models.CreditCard(**card.model_dump())
    db.add(db_card)
    db.commit()
    db.refresh(db_card)
    return db_card


@router.put("/{card_id}", response_model=schemas.CreditCard)
def update_credit_card(
    card_id: int, card: schemas.CreditCardUpdate, db: Session = Depends(get_db)
):
    db_card = db.query(models.CreditCard).filter(models.CreditCard.id == card_id).first()
    if not db_card:
        raise HTTPException(status_code=404, detail="Credit card not found")
    
    update_data = card.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_card, key, value)
    
    db.commit()
    db.refresh(db_card)
    return db_card


@router.delete("/{card_id}", status_code=204)
def delete_credit_card(card_id: int, db: Session = Depends(get_db)):
    db_card = db.query(models.CreditCard).filter(models.CreditCard.id == card_id).first()
    if not db_card:
        raise HTTPException(status_code=404, detail="Credit card not found")
    
    db.delete(db_card)
    db.commit()
    return None

