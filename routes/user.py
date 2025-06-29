from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from core.database import get_db
from core.utils.response import Response
from models.user import UserRole, User
from services.user import UserService  # assuming your UserService is here
from schemas.user import UserCreate, UserRead, UserUpdate,UserLogin,ChangePasswordRequest  # your Pydantic schemas

router = APIRouter(prefix='/api/v1', tags=["Users"])

@router.post("/", response_model=Response[UserRead], status_code=status.HTTP_201_CREATED)
async def create_user(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    user, err = await service.create_user(
        firstname=user_in.firstname,
        lastname=user_in.lastname,
        email=user_in.email,
        password=user_in.password,
        role=UserRole(user_in.role),
        age=user_in.age,
        gender=user_in.gender,
        phone_number=user_in.phone_number,
        phone_number_pre=user_in.phone_number_pre,
        picture=user_in.picture,
    )
    if err:
        raise HTTPException(status_code=400, detail=err)
    return Response(data=user)

@router.get("/{user_id}", response_model=Response[UserRead])
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    user, err = await service.get_user_by_id(user_id)
    if err:
        raise HTTPException(status_code=400, detail=err)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return Response(data=user)

@router.put("/{user_id}", response_model=Response[UserRead])
async def update_user(user_id: int, user_in: UserUpdate, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    update_data = user_in.dict(exclude_unset=True)
    user, err = await service.update_user(user_id, **update_data)
    if err:
        raise HTTPException(status_code=400, detail=err)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return Response(data=user)

@router.delete("/{user_id}", response_model=Response[bool])
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    success, err = await service.delete_user(user_id)
    if err:
        raise HTTPException(status_code=400, detail=err)
    if not success:
        raise HTTPException(status_code=404, detail="User not found or could not be deleted")
    return Response(data=True)

@router.get("/", response_model=Response[List[UserRead]])
async def list_users(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    users, err = await service.list_users(skip=skip, limit=limit)
    if err:
        raise HTTPException(status_code=400, detail=err)
    return Response(data=users)


@router.post("/login", response_model=Response[UserRead])
async def login_user(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    user, err = await service.login(credentials.email, credentials.password)
    if err:
        raise HTTPException(status_code=400, detail=err)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    # Here you can generate and attach JWT tokens, etc.
    return Response(data=user)


@router.post("/{user_id}/change-password", response_model=Response[bool])
async def change_password(user_id: int, request: ChangePasswordRequest, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    success, err = await service.change_password(user_id, request.old_password, request.new_password)
    if err:
        raise HTTPException(status_code=400, detail=err)
    if not success:
        raise HTTPException(status_code=401, detail="Old password is incorrect or user not found")
    return Response(data=True)
