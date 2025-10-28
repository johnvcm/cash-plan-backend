from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models, schemas
from app.auth import get_current_active_user

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("/", response_model=List[schemas.Category])
def get_categories(
    type: str = None,  # Filtrar por tipo: "income" ou "expense"
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Retorna todas as categorias do usuário autenticado (padrão + customizadas)
    Opcionalmente filtra por tipo (income/expense)
    """
    query = db.query(models.Category).filter(
        models.Category.user_id == current_user.id
    )
    
    if type:
        query = query.filter(models.Category.type == type)
    
    categories = query.all()
    return categories


@router.get("/{category_id}", response_model=schemas.Category)
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Retorna uma categoria específica do usuário"""
    category = db.query(models.Category).filter(
        models.Category.id == category_id,
        models.Category.user_id == current_user.id
    ).first()
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.post("/", response_model=schemas.Category, status_code=status.HTTP_201_CREATED)
def create_category(
    category: schemas.CategoryCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Cria uma nova categoria customizada para o usuário"""
    # Verificar se já existe uma categoria com esse nome para o usuário
    existing = db.query(models.Category).filter(
        models.Category.user_id == current_user.id,
        models.Category.name == category.name,
        models.Category.type == category.type
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Você já possui uma categoria com este nome"
        )
    
    db_category = models.Category(
        **category.model_dump(),
        user_id=current_user.id,
        is_default=False  # Categorias criadas pelo usuário nunca são padrão
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


@router.put("/{category_id}", response_model=schemas.Category)
def update_category(
    category_id: int,
    category: schemas.CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Atualiza uma categoria customizada do usuário"""
    db_category = db.query(models.Category).filter(
        models.Category.id == category_id,
        models.Category.user_id == current_user.id
    ).first()
    
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Não permitir editar categorias padrão
    if db_category.is_default:
        raise HTTPException(
            status_code=403,
            detail="Não é possível editar categorias padrão do sistema"
        )
    
    update_data = category.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_category, key, value)
    
    db.commit()
    db.refresh(db_category)
    return db_category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Deleta uma categoria customizada do usuário"""
    db_category = db.query(models.Category).filter(
        models.Category.id == category_id,
        models.Category.user_id == current_user.id
    ).first()
    
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Não permitir deletar categorias padrão
    if db_category.is_default:
        raise HTTPException(
            status_code=403,
            detail="Não é possível deletar categorias padrão do sistema"
        )
    
    db.delete(db_category)
    db.commit()
    return None




