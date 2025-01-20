# ----------------------------------------
# Imports
# ----------------------------------------
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from sqlalchemy import create_engine, Column, Integer, String, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# ----------------------------------------
# Database Configuration
# ----------------------------------------
DATABASE_URL = "sqlite:///./dating_app.db"

# Create database engine and session factory
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models
Base = declarative_base()

# ----------------------------------------
# Database Models
# ----------------------------------------
class UserDB(Base):
    __tablename__ = "users"  # Table name in the database
    user_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    age = Column(Integer)
    location = Column(String)
    gender = Column(String)
    preferences = Column(JSON)
    video_clip = Column(String)

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

# ----------------------------------------
# Pydantic Models
# ----------------------------------------
class User(BaseModel):
    user_id: int
    name: str
    age: int
    location: str
    gender: str
    preferences: dict
    video_clip: str

# ----------------------------------------
# Dependency Injection
# ----------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ----------------------------------------
# FastAPI Initialization
# ----------------------------------------
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins; restrict in production
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all HTTP headers
)

# ----------------------------------------
# API Endpoints
# ----------------------------------------

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}


@app.get("/users", response_model=List[User])
def get_users(db: Session = Depends(get_db)):
    return db.query(UserDB).all()


@app.get("/users/{user_id}", response_model=User)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.user_id == user_id).first()
    print(f"Queried user: {user}")  # Add this line
    if user:
        return user
    raise HTTPException(status_code=404, detail="User not found")



@app.post("/users", response_model=User)
def create_user(user: User, db: Session = Depends(get_db)):
    # Check if a user with the same ID already exists
    db_user = db.query(UserDB).filter(UserDB.user_id == user.user_id).first()
    if db_user:
        raise HTTPException(status_code=400, detail="User with this ID already exists")
    
    # Add the new user to the database
    db_user = UserDB(**user.dict())  # Convert Pydantic model to SQLAlchemy model
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.put("/users/{user_id}", response_model=User)
def update_user(user_id: int, updated_user: User, db: Session = Depends(get_db)):
    # Find the user in the database
    db_user = db.query(UserDB).filter(UserDB.user_id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update the user's fields
    for key, value in updated_user.dict().items():
        setattr(db_user, key, value)
    
    # Commit changes to the database
    db.commit()
    db.refresh(db_user)
    return db_user


@app.delete("/users/{user_id}", response_model=dict)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    # Find the user in the database
    db_user = db.query(UserDB).filter(UserDB.user_id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Delete the user
    db.delete(db_user)
    db.commit()
    return {"message": f"User {user_id} deleted successfully"}

@app.delete("/users/{user_id}", response_model=dict)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    # Find the user in the database
    db_user = db.query(UserDB).filter(UserDB.user_id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Delete the user
    db.delete(db_user)
    db.commit()
    return {"message": f"User {user_id} deleted successfully"}

@app.get("/users", response_model=List[User])
def get_users(
    location: str = None,
    min_age: int = None,
    max_age: int = None,
    gender: str = None,
    db: Session = Depends(get_db),
):
    query = db.query(UserDB)
    
    # Apply filters if provided
    if location:
        query = query.filter(UserDB.location == location)
    if min_age:
        query = query.filter(UserDB.age >= min_age)
    if max_age:
        query = query.filter(UserDB.age <= max_age)
    if gender:
        query = query.filter(UserDB.gender == gender)
    
    return query.all()

