from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.users import create_user, get_user_by_username
from app.security import hash_password, verify_password

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
DbSession = Annotated[Session, Depends(get_db)]


@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(
        request=request, name="login.html", context={"error": None}
    )


@router.post("/login")
def login(
    request: Request,
    db: DbSession,
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
):
    user = get_user_by_username(db, username.strip())
    if user is None or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"error": "아이디 또는 비밀번호가 올바르지 않습니다."},
            status_code=400,
        )
    request.session.clear()
    request.session["user_id"] = user.id
    return RedirectResponse("/library/books", status_code=303)


@router.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse(
        request=request, name="register.html", context={"error": None}
    )


@router.post("/register")
def register(
    request: Request,
    db: DbSession,
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
):
    username = username.strip()
    if len(username) < 3 or len(username) > 50 or len(password) < 8:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={"error": "아이디는 3~50자, 비밀번호는 8자 이상이어야 합니다."},
            status_code=400,
        )
    if get_user_by_username(db, username) is not None:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={"error": "이미 사용 중인 아이디입니다."},
            status_code=400,
        )
    user = create_user(db, username, hash_password(password))
    request.session.clear()
    request.session["user_id"] = user.id
    return RedirectResponse("/library/books", status_code=303)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)
