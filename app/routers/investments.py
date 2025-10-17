from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/investments", tags=["investments"])


@router.get("/", response_model=List[schemas.Investment])
def get_investments(db: Session = Depends(get_db)):
    investments = db.query(models.Investment).all()
    return investments


@router.get("/{investment_id}", response_model=schemas.Investment)
def get_investment(investment_id: int, db: Session = Depends(get_db)):
    investment = (
        db.query(models.Investment)
        .filter(models.Investment.id == investment_id)
        .first()
    )
    if not investment:
        raise HTTPException(status_code=404, detail="Investment not found")
    return investment


@router.post("/", response_model=schemas.Investment, status_code=201)
def create_investment(
    investment: schemas.InvestmentCreate, db: Session = Depends(get_db)
):
    db_investment = models.Investment(**investment.model_dump())
    db.add(db_investment)
    db.commit()
    db.refresh(db_investment)
    return db_investment


@router.put("/{investment_id}", response_model=schemas.Investment)
def update_investment(
    investment_id: int,
    investment: schemas.InvestmentUpdate,
    db: Session = Depends(get_db),
):
    db_investment = (
        db.query(models.Investment)
        .filter(models.Investment.id == investment_id)
        .first()
    )
    if not db_investment:
        raise HTTPException(status_code=404, detail="Investment not found")

    update_data = investment.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_investment, key, value)

    db.commit()
    db.refresh(db_investment)
    return db_investment


@router.delete("/{investment_id}", status_code=204)
def delete_investment(investment_id: int, db: Session = Depends(get_db)):
    db_investment = (
        db.query(models.Investment)
        .filter(models.Investment.id == investment_id)
        .first()
    )
    if not db_investment:
        raise HTTPException(status_code=404, detail="Investment not found")

    db.delete(db_investment)
    db.commit()
    return None

