from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser, require_user
from app.database import get_db
from app.repositories.books import create_book, get_user_loans, list_books
from app.services.library import LibraryError, borrow_book, return_book

router = APIRouter(prefix="/library", dependencies=[Depends(require_user)])
templates = Jinja2Templates(directory="app/templates")
DbSession = Annotated[Session, Depends(get_db)]


@router.get("/books")
def books_page(request: Request, db: DbSession, user: CurrentUser):
    return templates.TemplateResponse(
        request=request,
        name="books.html",
        context={"user": user, "books": list_books(db)},
    )


@router.post("/books")
def add_book(
    db: DbSession,
    title: Annotated[str, Form()],
    author: Annotated[str, Form()],
):
    title, author = title.strip(), author.strip()
    if title and author:
        create_book(db, title[:200], author[:120])
    return RedirectResponse("/library/books", status_code=303)


@router.post("/books/{book_id}/borrow")
def borrow(
    book_id: int,
    db: DbSession,
    user: CurrentUser,
    request: Request,
):
    try:
        borrow_book(db, user, book_id)
    except LibraryError as error:
        return templates.TemplateResponse(
            request=request,
            name="books.html",
            context={"user": user, "books": list_books(db), "error": str(error)},
            status_code=400,
        )
    return RedirectResponse("/library/loans", status_code=303)


@router.get("/loans")
def loans_page(request: Request, db: DbSession, user: CurrentUser):
    return templates.TemplateResponse(
        request=request,
        name="loans.html",
        context={"user": user, "loans": get_user_loans(db, user.id)},
    )


@router.post("/loans/{loan_id}/return")
def return_loan(
    loan_id: int,
    db: DbSession,
    user: CurrentUser,
    request: Request,
):
    try:
        return_book(db, user, loan_id)
    except LibraryError as error:
        return templates.TemplateResponse(
            request=request,
            name="loans.html",
            context={
                "user": user,
                "loans": get_user_loans(db, user.id),
                "error": str(error),
            },
            status_code=400,
        )
    return RedirectResponse("/library/loans", status_code=303)
