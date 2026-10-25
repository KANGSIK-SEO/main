import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import select
from starlette.middleware.sessions import SessionMiddleware

from app.database import Base, SessionLocal, engine
from app.models import Book
from app.repositories.books import create_book
from app.repositories.users import create_user, get_user_by_username
from app.routers import auth, library, pages
from app.security import hash_password


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if get_user_by_username(db, "demo") is None:
            create_user(db, "demo", hash_password("demo1234"))
        if db.scalar(select(Book.id).limit(1)) is None:
            create_book(db, "어린 왕자", "앙투안 드 생텍쥐페리")
            create_book(db, "데미안", "헤르만 헤세")
    yield


app = FastAPI(title="책마루 도서 대여 서비스", lifespan=lifespan)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET", "development-only-change-this-secret"),
    same_site="lax",
    https_only=os.getenv("COOKIE_SECURE", "false").lower() == "true",
)
app.include_router(pages.router)
app.include_router(auth.router)
app.include_router(library.router)
