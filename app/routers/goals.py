from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/goals", tags=["goals"])


@router.get("/", response_model=List[schemas.Goal])
def get_goals(db: Session = Depends(get_db)):
    goals = db.query(models.Goal).all()
    return goals


@router.get("/{goal_id}", response_model=schemas.Goal)
def get_goal(goal_id: int, db: Session = Depends(get_db)):
    goal = db.query(models.Goal).filter(models.Goal.id == goal_id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return goal


@router.post("/", response_model=schemas.Goal, status_code=201)
def create_goal(goal: schemas.GoalCreate, db: Session = Depends(get_db)):
    db_goal = models.Goal(**goal.model_dump())
    db.add(db_goal)
    db.commit()
    db.refresh(db_goal)
    return db_goal


@router.put("/{goal_id}", response_model=schemas.Goal)
def update_goal(
    goal_id: int, goal: schemas.GoalUpdate, db: Session = Depends(get_db)
):
    db_goal = db.query(models.Goal).filter(models.Goal.id == goal_id).first()
    if not db_goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    update_data = goal.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_goal, key, value)

    db.commit()
    db.refresh(db_goal)
    return db_goal


@router.delete("/{goal_id}", status_code=204)
def delete_goal(goal_id: int, db: Session = Depends(get_db)):
    db_goal = db.query(models.Goal).filter(models.Goal.id == goal_id).first()
    if not db_goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    db.delete(db_goal)
    db.commit()
    return None

