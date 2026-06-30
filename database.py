from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel, Field, field_validator

# ---------------------------
# Database connection
# ---------------------------
database_url = "sqlite:///./mutualfunds.db"
engine = create_engine(database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ---------------------------
# SQLAlchemy Models
# ---------------------------
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    email = Column(String, unique=True, index=True)

class MutualFund(Base):
    __tablename__ = "mutualfunds"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    type = Column(String)

Base.metadata.create_all(bind=engine)

# ---------------------------
# Pydantic Schemas
# ---------------------------

# Request schema for creating a mutual fund
class MutualFundCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=50)
    type: str

    @field_validator("type")
    def validate_type(cls, v):
        allowed_types = ["equity", "debt", "hybrid"]
        if v.lower() not in allowed_types:
            raise ValueError(f"Type must be one of {allowed_types}")
        return v.lower()

    @field_validator("name")
    def validate_name(cls, v):
        if not v.isalnum():
            raise ValueError("Name must be alphanumeric (no special characters)")
        return v

# Response schema for mutual fund
class MutualFundResponse(BaseModel):
    id: int
    name: str
    type: str

    class Config:
        orm_mode = True   # allows SQLAlchemy objects to be returned directly

# Request schema for login
class TokenRequest(BaseModel):
    username: str
    password: str

# Response schema for token
class TokenResponse(BaseModel):
    access_token: str
    token_type: str
