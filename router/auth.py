from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from database import get_db
from models import User
from schemas import ForgotPassword, UpdatePassword, UpdateUser, UserCreate, UserOut

router = APIRouter()
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
OAuth2_bearer = OAuth2PasswordBearer(tokenUrl='login')
SECRET_KEY = '86746eeb8285ca279c6251e0bd83cdd50c88027b934a93f19d8b9af782139516'
ALGORITHM = 'HS256'
DbDependency = Annotated[Session, Depends(get_db)]


def authenticate_user(username, password, db):
    user = db.query(User).filter(User.username == username).first()
    if user is None or not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user


def create_access_token(username: str, user_id: int, role: str, expires_delta: timedelta):
    payload = {'sub': username, 'id': user_id, 'role': role, 'exp': datetime.now(timezone.utc) + expires_delta}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: Annotated[str, Depends(OAuth2_bearer)], db: DbDependency):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get('sub')
        user_id = payload.get('id')
        role = payload.get('role')
        if username is None or user_id is None:
            raise HTTPException(status_code=401, detail='Failed Authentication')
    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail='Failed Authentication')
    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail='Failed Authentication')
    return {'username': username, 'id': user_id, 'role': role}


def current_user_model(user: Annotated[dict, Depends(get_current_user)], db: DbDependency):
    current = db.query(User).filter(User.id == user['id']).first()
    if current is None:
        raise HTTPException(status_code=404, detail='User not found')
    return current


@router.post('/createuser', response_model=UserOut, status_code=201)
def create_user(db: DbDependency, new_user: UserCreate):
    if db.query(User).filter(User.username == new_user.username).first():
        raise HTTPException(status_code=400, detail='Username already exists')
    if db.query(User).filter(User.email == new_user.email).first():
        raise HTTPException(status_code=400, detail='Email already exists')
    user_model = User(email=new_user.email, username=new_user.username, full_name=new_user.full_name, hashed_password=bcrypt_context.hash(new_user.password), role=new_user.role, is_active=True)
    db.add(user_model)
    db.commit()
    db.refresh(user_model)
    return user_model


@router.post('/login')
def login_user(db: DbDependency, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail='Failed authentication')
    token = create_access_token(user.username, user.id, user.role, timedelta(minutes=30))
    return {'access_token': token, 'token_type': 'bearer', 'user': UserOut.model_validate(user)}


@router.get('/user', response_model=UserOut)
def get_user_details(user: Annotated[dict, Depends(get_current_user)], db: DbDependency):
    return current_user_model(user, db)


@router.put('/edituser')
def update_user(user: Annotated[dict, Depends(get_current_user)], db: DbDependency, update_user: UpdateUser):
    current_user = current_user_model(user, db)
    for key, value in update_user.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(current_user, key, value)
    db.commit()
    return JSONResponse(status_code=200, content={'message': 'User updated successfully'})


@router.put('/passwordchange')
def update_password(user: Annotated[dict, Depends(get_current_user)], db: DbDependency, update_password: UpdatePassword):
    current_user = current_user_model(user, db)
    if not bcrypt_context.verify(update_password.current_password, current_user.hashed_password):
        raise HTTPException(status_code=401, detail='Wrong Password')
    current_user.hashed_password = bcrypt_context.hash(update_password.new_password)
    db.commit()
    return JSONResponse(status_code=200, content={'message': 'Password updated successfully'})


@router.post('/forgotpassword')
def forgot_password(data: ForgotPassword, db: DbDependency):
    if db.query(User).filter(User.email == data.email).first() is None:
        return {'message': 'If the account exists, reset instructions are available'}
    return {'message': 'Reset request accepted. Contact an administrator for the development reset flow.'}
