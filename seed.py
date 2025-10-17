"""
Script para popular o banco de dados com dados de exemplo
"""
from app.database import SessionLocal, engine
from app.models import Account, CreditCard, Transaction, Investment, Goal, TransactionType, InvestmentType
from datetime import date
import sys

def seed_database():
    """Popular banco de dados com dados de exemplo"""
    db = SessionLocal()
    
    try:
        print("Iniciando seed do banco de dados...")
        
        # Verificar se já existem dados
        if db.query(Account).count() > 0:
            print("⚠️  Banco de dados já possui dados. Deseja continuar? (s/n)")
            response = input().lower()
            if response != 's':
                print("Seed cancelado.")
                return
            
            print("Limpando dados existentes...")
            db.query(Transaction).delete()
            db.query(Account).delete()
            db.query(CreditCard).delete()
            db.query(Investment).delete()
            db.query(Goal).delete()
            db.commit()
        
        # Criar contas bancárias
        print("Criando contas bancárias...")
        accounts = [
            Account(
                name="Banco do Brasil",
                bank="Banco do Brasil",
                balance=1978.26,
                investments=0.00,
                color="#FCD34D"
            ),
            Account(
                name="Sicoob",
                bank="Sicoob",
                balance=460.75,
                investments=981.47,
                color="#10B981"
            ),
            Account(
                name="Nubank",
                bank="Nubank",
                balance=3250.00,
                investments=5000.00,
                color="#8B5CF6"
            ),
        ]
        db.add_all(accounts)
        db.commit()
        print(f"✓ {len(accounts)} contas criadas")
        
        # Criar cartões de crédito
        print("Criando cartões de crédito...")
        credit_cards = [
            CreditCard(
                name="Banco do Brasil GOLD4760",
                bank="OUROCARD VISA INTERNATIONAL",
                used=0,
                limit=80000,
                color="#FCD34D"
            ),
            CreditCard(
                name="Sicoob B620",
                bank="SICOOB MASTERCARD CLÁSSICO PRO",
                used=0,
                limit=815000,
                color="#3B82F6"
            ),
            CreditCard(
                name="Itaú BLACK2898",
                bank="ITAÚ MASTERCARD BLACK",
                used=15000,
                limit=50000,
                color="#F97316"
            ),
        ]
        db.add_all(credit_cards)
        db.commit()
        print(f"✓ {len(credit_cards)} cartões criados")
        
        # Criar transações
        print("Criando transações...")
        transactions = [
            Transaction(
                description="Salário Outubro",
                category="Renda",
                date=date(2025, 10, 1),
                amount=5000.00,
                type=TransactionType.income,
                account_id=accounts[0].id
            ),
            Transaction(
                description="Freelance",
                category="Renda Cliente",
                date=date(2025, 10, 15),
                amount=2500.00,
                type=TransactionType.income,
                account_id=accounts[2].id
            ),
            Transaction(
                description="Mercado",
                category="Despesas obrigatórias",
                date=date(2025, 10, 5),
                amount=-350.00,
                type=TransactionType.expense,
                account_id=accounts[0].id
            ),
            Transaction(
                description="Aluguel",
                category="Despesas obrigatórias",
                date=date(2025, 10, 10),
                amount=-1200.00,
                type=TransactionType.expense,
                account_id=accounts[1].id
            ),
            Transaction(
                description="Conta de Luz",
                category="Despesas obrigatórias",
                date=date(2025, 10, 8),
                amount=-180.00,
                type=TransactionType.expense,
                account_id=accounts[0].id
            ),
        ]
        db.add_all(transactions)
        db.commit()
        print(f"✓ {len(transactions)} transações criadas")
        
        # Criar investimentos
        print("Criando investimentos...")
        investments = [
            Investment(
                name="Tesouro Selic 2029",
                type=InvestmentType.renda_fixa,
                value=5000.00,
                return_rate=12.5,
                color="#10B981"
            ),
            Investment(
                name="CDB Banco X",
                type=InvestmentType.renda_fixa,
                value=3000.00,
                return_rate=10.2,
                color="#3B82F6"
            ),
            Investment(
                name="Ações PETR4",
                type=InvestmentType.renda_variavel,
                value=2500.00,
                return_rate=-5.3,
                color="#8B5CF6"
            ),
            Investment(
                name="Fundos Imobiliários",
                type=InvestmentType.renda_variavel,
                value=1500.00,
                return_rate=8.7,
                color="#F59E0B"
            ),
        ]
        db.add_all(investments)
        db.commit()
        print(f"✓ {len(investments)} investimentos criados")
        
        # Criar metas financeiras
        print("Criando metas financeiras...")
        goals = [
            Goal(
                name="Fundo de Emergência",
                target=30000.00,
                current=18500.00,
                color="#10B981"
            ),
            Goal(
                name="Viagem para Europa",
                target=15000.00,
                current=8200.00,
                color="#3B82F6"
            ),
            Goal(
                name="Curso de Especialização",
                target=5000.00,
                current=3800.00,
                color="#8B5CF6"
            ),
            Goal(
                name="Carro Novo",
                target=50000.00,
                current=12000.00,
                color="#F59E0B"
            ),
        ]
        db.add_all(goals)
        db.commit()
        print(f"✓ {len(goals)} metas criadas")
        
        print("\n✅ Seed concluído com sucesso!")
        print("\nResumo:")
        print(f"  - {len(accounts)} contas bancárias")
        print(f"  - {len(credit_cards)} cartões de crédito")
        print(f"  - {len(transactions)} transações")
        print(f"  - {len(investments)} investimentos")
        print(f"  - {len(goals)} metas financeiras")
        
    except Exception as e:
        print(f"\n❌ Erro ao fazer seed do banco de dados: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()

