from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app import crud, schemas
from app.api import deps

router = APIRouter()


@router.get("/users/", response_model=List[schemas.User])
def read_users(
    skip: int = 0, limit: int = 10, db: Session = Depends(deps.get_db)
):
    users = crud.user.get_multi(db, skip=skip, limit=limit)
    return users


@router.post("/users/", response_model=schemas.User)
def create_user(
    *, db: Session = Depends(deps.get_db), user_in: schemas.UserCreate
):
    user = crud.user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists in the system.",
        )
    user = crud.user.create(db, obj_in=user_in)
    return user


@router.get("/users/{user_id}", response_model=schemas.User)
def read_user(*, db: Session = Depends(deps.get_db), user_id: int):
    user = crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    return user


@router.put("/users/{user_id}", response_model=schemas.User)
def update_user(
    *, db: Session = Depends(deps.get_db), user_id: int, user_in: schemas.UserUpdate
):
    user = crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    user = crud.user.update(db, db_obj=user, obj_in=user_in)
    return user


@router.delete("/users/{user_id}", response_model=schemas.User)
def delete_user(*, db: Session = Depends(deps.get_db), user_id: int):
    user = crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    user = crud.user.remove(db, id=user_id)
    return user
