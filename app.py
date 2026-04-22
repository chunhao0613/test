from __future__ import annotations

import os
from pathlib import Path
from contextlib import asynccontextmanager
from collections.abc import Generator
from calendar import monthrange
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response, status
from fastapi.responses import HTMLResponse
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, create_engine, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker
from prometheus_client import Counter, Histogram, generate_latest, REGISTRY
import time


SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080"))
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bookkeeping.db")


engine_kwargs: dict[str, object] = {}
if DATABASE_URL.startswith("sqlite"):
	engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@asynccontextmanager
async def lifespan(_: FastAPI):
	create_tables()
	yield


app = FastAPI(title="Simple Bookkeeping API", lifespan=lifespan)
FRONTEND_PATH = Path(__file__).with_name("frontend").joinpath("index.html")

# Prometheus 指標
try:
	request_count = Counter(
		'http_requests_total',
		'Total HTTP requests',
		['method', 'endpoint', 'status']
	)
	request_duration = Histogram(
		'http_request_duration_seconds',
		'HTTP request duration in seconds',
		['method', 'endpoint']
	)
except ValueError:
	# 指標已存在，從 REGISTRY 獲取
	request_count = REGISTRY._names_to_collectors['http_requests_total']
	request_duration = REGISTRY._names_to_collectors['http_request_duration_seconds']

# Prometheus 中間件
@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
	method = request.method
	path = request.url.path
	start_time = time.time()
	
	response = await call_next(request)
	
	duration = time.time() - start_time
	status_code = response.status_code
	
	request_count.labels(method=method, endpoint=path, status=status_code).inc()
	request_duration.labels(method=method, endpoint=path).observe(duration)
	
	return response


class Base(DeclarativeBase):
	pass


class User(Base):
	__tablename__ = "users"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
	email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
	password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
	transactions: Mapped[list["Transaction"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Transaction(Base):
	__tablename__ = "transactions"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
	user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
	type: Mapped[str] = mapped_column(String(20), nullable=False)
	amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
	category: Mapped[str | None] = mapped_column(String(100), nullable=True)
	note: Mapped[str | None] = mapped_column(Text, nullable=True)
	happened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
	user: Mapped[User] = relationship(back_populates="transactions")


class RegisterRequest(BaseModel):
	email: EmailStr
	password: str = Field(min_length=8)


class LoginRequest(BaseModel):
	email: EmailStr
	password: str


class TransactionCreate(BaseModel):
	type: str = Field(pattern="^(income|expense)$")
	amount: Decimal = Field(gt=0)
	category: str | None = Field(default=None, max_length=100)
	note: str | None = None
	happened_at: datetime | None = None


class TransactionUpdate(BaseModel):
	type: str | None = Field(default=None, pattern="^(income|expense)$")
	amount: Decimal | None = Field(default=None, gt=0)
	category: str | None = Field(default=None, max_length=100)
	note: str | None = None
	happened_at: datetime | None = None


class TransactionOut(BaseModel):
	id: int
	type: str
	amount: Decimal
	category: str | None
	note: str | None
	happened_at: datetime
	created_at: datetime


class SummaryOut(BaseModel):
	income_total: Decimal
	expense_total: Decimal
	balance: Decimal
	month: str


class UserOut(BaseModel):
	id: int
	email: EmailStr
	created_at: datetime


def get_db() -> Generator[Session, None, None]:
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()


def create_tables() -> None:
	Base.metadata.create_all(bind=engine)


def hash_password(password: str) -> str:
	return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
	return pwd_context.verify(plain_password, password_hash)


def create_access_token(subject: str) -> str:
	expires = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
	return jwt.encode({"sub": subject, "exp": expires}, SECRET_KEY, algorithm=ALGORITHM)


def set_auth_cookie(response: Response, token: str) -> None:
	response.set_cookie(
		key="access_token",
		value=token,
		httponly=True,
		samesite="lax",
		secure=False,
		path="/",
		max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
	)


def clear_auth_cookie(response: Response) -> None:
	response.delete_cookie(key="access_token", path="/")


def get_current_user(request: Request, db: Session) -> User:
	token = request.cookies.get("access_token")
	if not token:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
	try:
		payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
		email = payload.get("sub")
		if not email:
			raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
	except JWTError as exc:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated") from exc
	user = db.scalar(select(User).where(User.email == email))
	if user is None:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
	return user


def transaction_to_out(transaction: Transaction) -> TransactionOut:
	return TransactionOut(
		id=transaction.id,
		type=transaction.type,
		amount=transaction.amount,
		category=transaction.category,
		note=transaction.note,
		happened_at=transaction.happened_at,
		created_at=transaction.created_at,
	)


def resolve_month_range(month: str | None) -> tuple[datetime, datetime, str]:
	current = datetime.now(UTC)
	month_value = month or current.strftime("%Y-%m")
	try:
		start = datetime.strptime(f"{month_value}-01", "%Y-%m-%d").replace(tzinfo=UTC)
	except ValueError as exc:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="month must use YYYY-MM") from exc
	last_day = monthrange(start.year, start.month)[1]
	end = start.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)
	return start, end, month_value


def render_page() -> str:
	return FRONTEND_PATH.read_text(encoding="utf-8")


@app.get("/", response_class=HTMLResponse)
def root() -> str:
	return render_page()


@app.get("/health")
def health_check(db: Session = Depends(get_db)) -> dict[str, str]:
	db.execute(select(1))
	return {"status": "ok"}


@app.get("/metrics")
def metrics():
	from fastapi.responses import Response
	return Response(content=generate_latest(), media_type="text/plain; charset=utf-8")


@app.post("/auth/register", status_code=status.HTTP_201_CREATED)
def register_user(payload: RegisterRequest, db: Session = Depends(get_db)) -> dict[str, str]:
	if db.scalar(select(User).where(User.email == payload.email)) is not None:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
	user = User(email=payload.email, password_hash=hash_password(payload.password))
	db.add(user)
	db.commit()
	return {"message": "registered"}


@app.post("/auth/login")
def login_user(payload: LoginRequest, response: Response, db: Session = Depends(get_db)) -> dict[str, object]:
	user = db.scalar(select(User).where(User.email == payload.email))
	if user is None or not verify_password(payload.password, user.password_hash):
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
	token = create_access_token(user.email)
	set_auth_cookie(response, token)
	return {"message": "logged_in", "user": {"id": user.id, "email": user.email}}


@app.post("/auth/logout")
def logout_user(response: Response) -> dict[str, str]:
	clear_auth_cookie(response)
	return {"message": "logged_out"}


@app.get("/auth/me")
def read_current_user(request: Request, db: Session = Depends(get_db)) -> UserOut:
	user = get_current_user(request, db)
	return UserOut(id=user.id, email=user.email, created_at=user.created_at)


@app.get("/transactions", response_model=list[TransactionOut])
def list_transactions(
	request: Request,
	db: Session = Depends(get_db),
	tx_type: str | None = Query(default=None, pattern="^(income|expense)$"),
	category: str | None = None,
	month: str | None = None,
	limit: int = Query(default=100, ge=1, le=300),
	offset: int = Query(default=0, ge=0),
) -> list[TransactionOut]:
	user = get_current_user(request, db)
	query = select(Transaction).where(Transaction.user_id == user.id)
	if tx_type:
		query = query.where(Transaction.type == tx_type)
	if category:
		query = query.where(Transaction.category.ilike(f"%{category}%"))
	if month:
		start, end, _ = resolve_month_range(month)
		query = query.where(Transaction.happened_at >= start, Transaction.happened_at <= end)
	transactions = db.scalars(
		query.order_by(Transaction.happened_at.desc(), Transaction.id.desc()).limit(limit).offset(offset)
	).all()
	return [transaction_to_out(item) for item in transactions]


@app.post("/transactions", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
def create_transaction(payload: TransactionCreate, request: Request, db: Session = Depends(get_db)) -> TransactionOut:
	user = get_current_user(request, db)
	transaction = Transaction(
		user_id=user.id,
		type=payload.type,
		amount=payload.amount,
		category=payload.category,
		note=payload.note,
		happened_at=payload.happened_at or datetime.now(UTC),
	)
	db.add(transaction)
	db.commit()
	db.refresh(transaction)
	return transaction_to_out(transaction)


@app.patch("/transactions/{transaction_id}", response_model=TransactionOut)
def update_transaction(transaction_id: int, payload: TransactionUpdate, request: Request, db: Session = Depends(get_db)) -> TransactionOut:
	user = get_current_user(request, db)
	transaction = db.scalar(select(Transaction).where(Transaction.id == transaction_id, Transaction.user_id == user.id))
	if transaction is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
	for field, value in payload.model_dump(exclude_unset=True).items():
		setattr(transaction, field, value)
	db.commit()
	db.refresh(transaction)
	return transaction_to_out(transaction)


@app.delete("/transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(transaction_id: int, request: Request, db: Session = Depends(get_db)) -> Response:
	user = get_current_user(request, db)
	transaction = db.scalar(select(Transaction).where(Transaction.id == transaction_id, Transaction.user_id == user.id))
	if transaction is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
	db.delete(transaction)
	db.commit()
	return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/summary/monthly", response_model=SummaryOut)
def monthly_summary(request: Request, db: Session = Depends(get_db), month: str | None = None) -> SummaryOut:
	user = get_current_user(request, db)
	start, end, month_value = resolve_month_range(month)
	income_total = db.scalar(
		select(func.coalesce(func.sum(Transaction.amount), 0)).where(
			Transaction.user_id == user.id,
			Transaction.type == "income",
			Transaction.happened_at >= start,
			Transaction.happened_at <= end,
		)
	) or Decimal("0")
	expense_total = db.scalar(
		select(func.coalesce(func.sum(Transaction.amount), 0)).where(
			Transaction.user_id == user.id,
			Transaction.type == "expense",
			Transaction.happened_at >= start,
			Transaction.happened_at <= end,
		)
	) or Decimal("0")
	return SummaryOut(
		income_total=income_total,
		expense_total=expense_total,
		balance=Decimal(income_total) - Decimal(expense_total),
		month=month_value,
	)


if __name__ == "__main__":
	import uvicorn

	uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
