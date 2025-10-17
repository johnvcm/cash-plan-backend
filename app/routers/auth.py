from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app import schemas
from app.models import User
from app.database import get_db
from app.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_active_user
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    """Registra um novo usuário"""
    
    # Verifica se o email já existe
    db_user = db.query(User).filter(User.email == user_data.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Verifica se o username já existe
    db_user = db.query(User).filter(User.username == user_data.username).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Cria o novo usuário
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        is_active=1
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Realiza login e retorna token JWT"""
    
    # Busca o usuário pelo username
    user = db.query(User).filter(User.username == form_data.username).first()
    
    # Verifica se o usuário existe e a senha está correta
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verifica se o usuário está ativo
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Cria o token JWT
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=schemas.User)
def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Retorna informações do usuário autenticado"""
    return current_user


@router.post("/logout")
def logout():
    """Endpoint de logout (client-side deve descartar o token)"""
    return {"message": "Successfully logged out"}

