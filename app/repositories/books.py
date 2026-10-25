from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Book, Loan


def list_books(db: Session) -> list[Book]:
    query = select(Book).options(selectinload(Book.loans)).order_by(Book.title)
    return list(db.scalars(query).all())


def get_book(db: Session, book_id: int) -> Book | None:
    return db.get(Book, book_id)


def create_book(db: Session, title: str, author: str) -> Book:
    book = Book(title=title, author=author)
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


def get_user_loans(db: Session, user_id: int) -> list[Loan]:
    query = (
        select(Loan)
        .options(selectinload(Loan.book), selectinload(Loan.user))
        .where(Loan.user_id == user_id)
        .order_by(Loan.borrowed_at.desc())
    )
    return list(db.scalars(query).all())
