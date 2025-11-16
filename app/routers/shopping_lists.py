from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app import models, schemas
from app.database import get_db
from app.auth import get_current_active_user

router = APIRouter(prefix="/shopping-lists", tags=["shopping-lists"])


@router.get("/", response_model=List[schemas.ShoppingList])
def get_shopping_lists(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    month: str = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Retorna todas as listas de compras do usuário com filtros opcionais"""
    query = db.query(models.ShoppingList).filter(
        models.ShoppingList.user_id == current_user.id
    )
    
    if status:
        query = query.filter(models.ShoppingList.status == status)
    
    if month:
        query = query.filter(models.ShoppingList.month == month)
    
    lists = query.order_by(models.ShoppingList.created_at.desc()).offset(skip).limit(limit).all()
    return lists


@router.get("/{list_id}", response_model=schemas.ShoppingList)
def get_shopping_list(
    list_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Retorna uma lista de compras específica"""
    shopping_list = db.query(models.ShoppingList).filter(
        models.ShoppingList.id == list_id,
        models.ShoppingList.user_id == current_user.id
    ).first()
    
    if not shopping_list:
        raise HTTPException(status_code=404, detail="Lista de compras não encontrada")
    
    return shopping_list


@router.post("/", response_model=schemas.ShoppingList, status_code=status.HTTP_201_CREATED)
def create_shopping_list(
    shopping_list: schemas.ShoppingListCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Cria uma nova lista de compras"""
    db_list = models.ShoppingList(
        user_id=current_user.id,
        name=shopping_list.name,
        month=shopping_list.month,
        status=models.ShoppingListStatus(shopping_list.status) if shopping_list.status else models.ShoppingListStatus.active,
        total_estimated=shopping_list.total_estimated,
        total_spent=shopping_list.total_spent
    )
    
    db.add(db_list)
    db.flush()
    
    if shopping_list.items:
        for item_data in shopping_list.items:
            db_item = models.ShoppingItem(
                shopping_list_id=db_list.id,
                **item_data.model_dump()
            )
            db.add(db_item)
    
    db.commit()
    db.refresh(db_list)
    return db_list


@router.put("/{list_id}", response_model=schemas.ShoppingList)
def update_shopping_list(
    list_id: int,
    shopping_list: schemas.ShoppingListUpdate,
    create_transactions: bool = False,
    account_id: int = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Atualiza uma lista de compras e opcionalmente cria transações"""
    db_list = db.query(models.ShoppingList).filter(
        models.ShoppingList.id == list_id,
        models.ShoppingList.user_id == current_user.id
    ).first()
    
    if not db_list:
        raise HTTPException(status_code=404, detail="Lista de compras não encontrada")
    
    update_data = shopping_list.model_dump(exclude_unset=True)
    
    if update_data.get("status") == "completed" and db_list.status != "completed":
        update_data["completed_at"] = datetime.utcnow()
        
        if create_transactions and db_list.total_spent > 0:
            items_by_category = {}
            for item in db_list.items:
                if item.is_purchased:
                    category = item.category
                    actual_price = item.actual_price if item.actual_price else item.estimated_price
                    
                    if category not in items_by_category:
                        items_by_category[category] = {
                            "total": 0,
                            "items": []
                        }
                    
                    items_by_category[category]["total"] += actual_price
                    items_by_category[category]["items"].append(item.name)
            
            transaction_date = update_data.get("completed_at") or datetime.utcnow()
            
            for category, data in items_by_category.items():
                items_list = ", ".join(data["items"][:5])
                if len(data["items"]) > 5:
                    items_list += f" (+{len(data['items']) - 5} mais)"
                
                description = f"Compras - {db_list.name}: {items_list}"
                
                transaction = models.Transaction(
                    user_id=current_user.id,
                    account_id=account_id,
                    description=description,
                    amount=data["total"],
                    type=models.TransactionType.expense,
                    category=category,
                    date=transaction_date
                )
                db.add(transaction)
                
                if account_id:
                    account = db.query(models.Account).filter(
                        models.Account.id == account_id,
                        models.Account.user_id == current_user.id
                    ).first()
                    
                    if account:
                        account.balance -= data["total"]
    
    for key, value in update_data.items():
        setattr(db_list, key, value)
    
    db.commit()
    db.refresh(db_list)
    return db_list


@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_shopping_list(
    list_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Deleta uma lista de compras"""
    db_list = db.query(models.ShoppingList).filter(
        models.ShoppingList.id == list_id,
        models.ShoppingList.user_id == current_user.id
    ).first()
    
    if not db_list:
        raise HTTPException(status_code=404, detail="Lista de compras não encontrada")
    
    db.delete(db_list)
    db.commit()
    return None


# ==================== ROTAS DE ITENS ====================

@router.post("/{list_id}/items", response_model=schemas.ShoppingItem, status_code=status.HTTP_201_CREATED)
def create_shopping_item(
    list_id: int,
    item: schemas.ShoppingItemCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Adiciona um item à lista de compras"""
    shopping_list = db.query(models.ShoppingList).filter(
        models.ShoppingList.id == list_id,
        models.ShoppingList.user_id == current_user.id
    ).first()
    
    if not shopping_list:
        raise HTTPException(status_code=404, detail="Lista de compras não encontrada")
    
    db_item = models.ShoppingItem(
        shopping_list_id=list_id,
        **item.model_dump()
    )
    db.add(db_item)
    shopping_list.total_estimated += item.estimated_price
    
    db.commit()
    db.refresh(db_item)
    return db_item


@router.put("/{list_id}/items/{item_id}", response_model=schemas.ShoppingItem)
def update_shopping_item(
    list_id: int,
    item_id: int,
    item: schemas.ShoppingItemUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Atualiza um item da lista de compras"""
    shopping_list = db.query(models.ShoppingList).filter(
        models.ShoppingList.id == list_id,
        models.ShoppingList.user_id == current_user.id
    ).first()
    
    if not shopping_list:
        raise HTTPException(status_code=404, detail="Lista de compras não encontrada")
    
    db_item = db.query(models.ShoppingItem).filter(
        models.ShoppingItem.id == item_id,
        models.ShoppingItem.shopping_list_id == list_id
    ).first()
    
    if not db_item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    
    update_data = item.model_dump(exclude_unset=True)
    
    old_estimated = db_item.estimated_price
    old_actual = db_item.actual_price or 0
    old_is_purchased = db_item.is_purchased
    
    for key, value in update_data.items():
        setattr(db_item, key, value)
    
    new_estimated = db_item.estimated_price
    new_actual = db_item.actual_price or 0
    new_is_purchased = db_item.is_purchased
    
    shopping_list.total_estimated += (new_estimated - old_estimated)
    
    if new_is_purchased and not old_is_purchased:
        shopping_list.total_spent += new_actual
    elif not new_is_purchased and old_is_purchased:
        shopping_list.total_spent -= old_actual
    elif new_is_purchased and old_is_purchased:
        shopping_list.total_spent += (new_actual - old_actual)
    
    db.commit()
    db.refresh(db_item)
    db.refresh(shopping_list)
    return db_item


@router.delete("/{list_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_shopping_item(
    list_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Deleta um item da lista de compras"""
    # Verificar se a lista existe e pertence ao usuário
    shopping_list = db.query(models.ShoppingList).filter(
        models.ShoppingList.id == list_id,
        models.ShoppingList.user_id == current_user.id
    ).first()
    
    if not shopping_list:
        raise HTTPException(status_code=404, detail="Lista de compras não encontrada")
    
    db_item = db.query(models.ShoppingItem).filter(
        models.ShoppingItem.id == item_id,
        models.ShoppingItem.shopping_list_id == list_id
    ).first()
    
    if not db_item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    
    shopping_list.total_estimated -= db_item.estimated_price
    shopping_list.total_spent -= (db_item.actual_price or 0)
    
    db.delete(db_item)
    db.commit()
    return None


@router.post("/{list_id}/duplicate", response_model=schemas.ShoppingList, status_code=status.HTTP_201_CREATED)
def duplicate_shopping_list(
    list_id: int,
    new_name: str,
    new_month: str = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Duplica uma lista de compras existente (para reutilizar itens)"""
    original_list = db.query(models.ShoppingList).filter(
        models.ShoppingList.id == list_id,
        models.ShoppingList.user_id == current_user.id
    ).first()
    
    if not original_list:
        raise HTTPException(status_code=404, detail="Lista de compras não encontrada")
    
    new_list = models.ShoppingList(
        user_id=current_user.id,
        name=new_name,
        month=new_month,
        status="active",
        total_estimated=0.0,
        total_spent=0.0
    )
    db.add(new_list)
    db.flush()
    
    total_estimated = 0.0
    for original_item in original_list.items:
        new_item = models.ShoppingItem(
            shopping_list_id=new_list.id,
            name=original_item.name,
            category=original_item.category,
            quantity=original_item.quantity,
            estimated_price=original_item.estimated_price,
            actual_price=None,
            is_purchased=False,
            notes=original_item.notes,
            order=original_item.order
        )
        db.add(new_item)
        total_estimated += original_item.estimated_price
    
    new_list.total_estimated = total_estimated
    
    db.commit()
    db.refresh(new_list)
    return new_list

