from app.database import SessionLocal
from app.models import Category, TransactionType, User
from sqlalchemy import select

INCOME_CATEGORIES = [
    "Salário",
    "Freelance",
    "Investimentos",
    "Bônus",
    "Presente",
    "Venda",
    "Outros",
]

EXPENSE_CATEGORIES = [
    "Alimentação",
    "Transporte",
    "Moradia",
    "Saúde",
    "Educação",
    "Lazer",
    "Compras",
    "Contas",
    "Vestuário",
    "Outros",
]


def seed_categories():
    db = SessionLocal()
    
    try:
        users = db.execute(select(User)).scalars().all()
        
        if not users:
            print("Nenhum usuário encontrado no banco de dados")
            return
        
        print(f"Encontrados {len(users)} usuário(s)")
        
        categories_created = 0
        categories_skipped = 0
        
        for user in users:
            print(f"\nProcessando usuário: {user.username} (ID: {user.id})")
            
            for cat_name in INCOME_CATEGORIES:
                existing = db.query(Category).filter(
                    Category.user_id == user.id,
                    Category.name == cat_name,
                    Category.type == TransactionType.income
                ).first()
                
                if not existing:
                    category = Category(
                        user_id=user.id,
                        name=cat_name,
                        type=TransactionType.income,
                        is_default=True
                    )
                    db.add(category)
                    categories_created += 1
                    print(f"  Criada: {cat_name} (Receita)")
                else:
                    categories_skipped += 1
                    print(f"  Já existe: {cat_name} (Receita)")
            
            for cat_name in EXPENSE_CATEGORIES:
                existing = db.query(Category).filter(
                    Category.user_id == user.id,
                    Category.name == cat_name,
                    Category.type == TransactionType.expense
                ).first()
                
                if not existing:
                    category = Category(
                        user_id=user.id,
                        name=cat_name,
                        type=TransactionType.expense,
                        is_default=True
                    )
                    db.add(category)
                    categories_created += 1
                    print(f"  Criada: {cat_name} (Despesa)")
                else:
                    categories_skipped += 1
                    print(f"  Já existe: {cat_name} (Despesa)")
        
        db.commit()
        
        print(f"\n{'='*60}")
        print(f"Seed concluído com sucesso!")
        print(f"Categorias criadas: {categories_created}")
        print(f"Categorias já existentes: {categories_skipped}")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"\nErro ao popular categorias: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("\nIniciando seed de categorias padrão...\n")
    seed_categories()






