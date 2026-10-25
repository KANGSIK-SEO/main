from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Loan, User
from app.repositories import books as book_repository


class LibraryError(Exception):
    pass


def borrow_book(db: Session, user: User, book_id: int) -> Loan:
    book = book_repository.get_book(db, book_id)
    if book is None:
        raise LibraryError("도서를 찾을 수 없습니다.")
    active_loan = db.scalar(
        select(Loan).where(Loan.book_id == book_id, Loan.status == "borrowed")
    )
    if active_loan is not None:
        raise LibraryError("이미 대여 중인 도서입니다.")
    loan = Loan(user_id=user.id, book_id=book.id, status="borrowed")
    db.add(loan)
    db.commit()
    db.refresh(loan)
    return loan


def return_book(db: Session, user: User, loan_id: int) -> Loan:
    loan = db.get(Loan, loan_id)
    if loan is None or loan.user_id != user.id:
        raise LibraryError("대여 내역을 찾을 수 없습니다.")
    if loan.status != "borrowed":
        raise LibraryError("이미 반납 완료된 대여입니다.")
    loan.status = "returned"
    loan.returned_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(loan)
    return loan
