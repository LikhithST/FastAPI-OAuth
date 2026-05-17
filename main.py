# Fast API
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

# SQL ORM
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import sessionmaker, Session, declarative_base

# for API models
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
import jwt
import bcrypt
from datetime import datetime, timedelta

# Sequrity Config
SECRET_KEY = "secret"
ALGORITHM = "HS256"
TOKEN_EXPIRES = 30

oauth2_schema = OAuth2PasswordBearer(tokenUrl="token") # for token generation

app = FastAPI(title="FastAPI with SQLAlchemy Example")

# database setup
DATABASE_URL = "sqlite:///sql_db.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False, unique=True)
    role = Column(String(100), nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    
Base.metadata.create_all(bind=engine)

# Pydantic models
class UserCreate(BaseModel):
    name: str
    email: str
    role: str
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)
    
# New Pydantic Model
class UserLogin(BaseModel):
    email: str
    password: str
    
class Token(BaseModel):
    access_token: str
    token_type: str
    
class TokenData(BaseModel):
    email: Optional[str] = None
    
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
    
# Security functions
def verify_password(plain_password:str, hash_password:str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hash_password.encode('utf-8'))

def get_password_hash(password:str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_access_token(data:dict, expires_delta: Optional[timedelta]=None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp":expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt



def verify_token(token:str) -> TokenData:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Could not verify credentials",
                headers={"WWW-Authenticate":"Bearer"}
                )
        return TokenData(email=email)
    except jwt.PyJWTError:
        raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Could not verify credentials",
                headers={"WWW-Authenticate":"Bearer"}
                )

# Auth Dependencies
def get_current_user(token:str = Depends(oauth2_schema), db:Session=Depends(get_db)):
    token_data = verify_token(token)
    user = db.query(User).filter(User.email == token_data.email).first()
    if user is None:
        raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="User does not exist",
                headers={"WWW-Authenticate":"Bearer"}
                )
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user["is_active"]:
        raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Invalid User",
                headers={"WWW-Authenticate":"Bearer"}
                )
    return current_user

# Auth Endpoints
@app.post("/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user.email).first():
        raise  HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="User already exists",
                )
    hashed_password = get_password_hash(user.password)
    db_user = User(
        name = user.name,
        email = user.email,
        role = user.role,
        hashed_password = hashed_password
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
    
@app.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email==form_data.username).first()
    
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=404,
            detail="Wrong Info!"
        )
        
    if not user["is_active"]:
        raise HTTPException(
            status_code=404,
            detail="Inactive User!"
        ) 
    access_token_expire = timedelta(minutes=TOKEN_EXPIRES)
    access_token = create_access_token(
        data={"sub": user.email}, 
        expires_delta=access_token_expire
        )
    return {"access_token": access_token, "token_type": "bearer"}



#routes 
@app.get("/")
def root():
    return {"message": "Welcome to the FastAPI with SQLAlchemy Example!"}

@app.get("/profile", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user

@app.get("/verify-token")
def verify_token_endpoint(current_user:User = Depends(get_current_active_user)):
    return{
        "valid": True,
        "user": {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "role": current_user.role
        }
    }

@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id:int, current_user:User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.post("/users/", response_model=UserResponse)
def create_user(user: UserCreate,current_user:User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if db.query(User).filter(User.email==user.email).first():
        raise HTTPException(status_code=404, detail="User already exists!")
    
    hashed_password = get_password_hash(user.password)
    # create user
    db_user = User(
        name=user.name,
        email=user.email,
        role=user.role,
        hashed_password=hashed_password
    )
        
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id:int, user:UserCreate, current_user:User = Depends(get_current_active_user), db:Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User does not exist!")
    
    db_user["name"] = user.name
    db_user["email"] = user.email
    db_user["role"] = user.role
    
    db.commit()
    db.refresh(db_user)
    return db_user

@app.delete("/user/{user_id}")
def delete_user(user_id:int, current_user:User = Depends(get_current_active_user), db:Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found!")
    
    if user_id == current_user.id:
        raise HTTPException(
            status_code=404,
            detail="You can not delete yourself!"
        )
    
    db.delete(db_user)
    db.commit()
    return {"message":"User Delete!"}

@app.get("/users/", response_model=List[UserResponse])
def get_all_users(current_user:User = Depends(get_current_active_user), db:Session=Depends(get_db)):
    return db.query(User).all()