from jose import JWTError, jwt
from fastapi import Depends, HTTPException, FastAPI, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import (
    User, MutualFund, SessionLocal, Base, engine,
    MutualFundCreate, MutualFundResponse, TokenResponse
)
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone

app = FastAPI()
Base.metadata.create_all(bind=engine)

SECRET_KEY = "f3e5cd2d4d60aceafb73f4c69c876db3104b85ea28483bb251a6cfa49c5b2c36"
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
ACCESS_TOKEN_EXPIRE_MINUTES = 30   

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------------------
# JWT helpers
# ---------------------------
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username != "admin":
            raise HTTPException(status_code=401, detail="Unauthorized")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"username": "admin"}

# ---------------------------
# Custom error handlers
# ---------------------------
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"error": "Validation Error", "details": str(exc)}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "HTTP Error", "details": exc.detail}
    )

# ---------------------------
# Endpoints
# ---------------------------
@app.post("/token", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username != "admin" or form_data.password != "admin":
        raise HTTPException(status_code=400, detail="Invalid admin credentials")

    access_token = create_access_token(data={"sub": "admin"})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/create_mutual_fund/", response_model=MutualFundResponse)
def create_mutualfund(
    fund: MutualFundCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # Check for duplicates
    existing = db.query(MutualFund).filter(MutualFund.name == fund.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Mutual fund already exists")

    new_mutualfund = MutualFund(name=fund.name, type=fund.type)
    db.add(new_mutualfund)
    db.commit()
    db.refresh(new_mutualfund)
    return new_mutualfund

@app.get("/mutual_funds/", response_model=list[MutualFundResponse])
def get_mutualfunds(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    mutualfunds = db.query(MutualFund).all()
    return mutualfunds
