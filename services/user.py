from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from models.user import User, UserRole  # your models
from core.utils.encryption import PasswordManager
from typing import List, Optional
from core.utils.generator import generator
import uuid
from datetime import datetime, timedelta

def generate_activation_token():
    return str(uuid.uuid4())  # or another secure token generator

def generate_activation_expiry(hours=24):
    return datetime.utcnow() + timedelta(hours=hours)

class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, *, firstname: str, lastname: str, email: str, password: str, role: UserRole,
                          age: int, gender: str, phone_number: Optional[str] = None,
                          phone_number_pre: Optional[str] = None, picture: Optional[str] = None
                          ) -> tuple[Optional[User], Optional[str]]:
        password_manager = PasswordManager()
        hashed_password = password_manager.hash_password(password)
        userid = str(generator.get_id())
        new_user = User(
            id = userid,
            firstname=firstname,
            lastname=lastname,
            email=email,
            password=hashed_password,
            role=role,
            age=age,
            gender=gender,
            phone_number=phone_number,
            phone_number_pre=phone_number_pre,
            picture=picture,
            activation_token = generate_activation_token(),
            activation_token_expires = generate_activation_expiry()
        )
        
        try:
            self.db.add(new_user)
            await self.db.commit()
            await self.db.refresh(new_user)
            # print(new_user.activation_token,'newuser',new_user.activation_token_expires)
            
            return new_user, None
        except SQLAlchemyError as e:
            await self.db.rollback()
            return None, f"DB error during user creation: {str(e)}"

    async def get_user_by_id(self, user_id: str) -> tuple[Optional[User], Optional[str]]:
        try:
            result = await self.db.execute(select(User).where(User.id == user_id))
            user = result.unique().scalar_one_or_none()
            if not user:
                return None, "User not found"
            return user, None
        except SQLAlchemyError as e:
            return None, f"DB error during get_user_by_id: {str(e)}"

    async def get_user_by_email(self, email: str) -> tuple[Optional[User], Optional[str]]:
        try:
            result = await self.db.execute(select(User).where(User.email == email))
            user = result.unique().scalar_one_or_none()
            if not user:
                return None, "User not found"
            return user, None
        except SQLAlchemyError as e:
            return None, f"DB error during get_user_by_email: {str(e)}"

    async def update_user(self, user_id: str, **kwargs) -> tuple[Optional[User], Optional[str]]:
        user, err = await self.get_user_by_id(user_id)
        if err:
            return None, err
        if not user:
            return None, "User not found"

        for key, value in kwargs.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)
        try:
            await self.db.commit()
            await self.db.refresh(user)
            return user, None
        except SQLAlchemyError as e:
            await self.db.rollback()
            return None, f"DB error during update_user: {str(e)}"

    async def delete_user(self, user_id: str) -> tuple[bool, Optional[str]]:
        user, err = await self.get_user_by_id(user_id)
        if err:
            return False, err
        if not user:
            return False, "User not found"
        try:
            await self.db.delete(user)
            await self.db.commit()
            return True, None
        except SQLAlchemyError as e:
            await self.db.rollback()
            return False, f"DB error during delete_user: {str(e)}"

    async def verify_user_password(self, email: str, password: str) -> tuple[bool, Optional[str]]:
        user, err = await self.get_user_by_email(email)
        if err:
            return False, err
        if not user:
            return False, "User not found"

        password_manager = PasswordManager()
        valid = password_manager.verify_password(password, user.password)
        return valid, None

    async def list_users(self, skip: int = 0, limit: int = 100) -> tuple[List[User], Optional[str]]:
        try:
            result = await self.db.execute(select(User).offset(skip).limit(limit))
            users = result.unique().scalars().all()
            return [user.to_dict() for user in users], None
        except SQLAlchemyError as e:
            return [], f"DB error during list_users: {str(e)}"

    async def login(self, email: str, password: str) -> tuple[Optional[User], Optional[str]]:
        user, err = await self.get_user_by_email(email)
        if err:
            return None, err
        if not user:
            return None, "User not found"

        password_manager = PasswordManager()
        if password_manager.verify_password(password, user.password):
            return user, None
        else:
            return None, "Invalid credentials"
        
    async def activate(self, token: str) -> tuple[Optional[User], Optional[str]]:
        # Query user by activation token
        result = await self.db.execute(select(User).where(User.activation_token == token))
        user = result.unique().scalar_one_or_none()

        if not user:
            return None, "User not found"

        if not user.activation_token_expires or user.activation_token_expires < datetime.utcnow():
            return None, "Activation token expired"

        user.active = True
        user.activation_token = None
        user.activation_token_expires = None

        await self.db.commit()
        await self.db.refresh(user)

        return user, None

    async def change_password(self, user_id: str, old_password: str, new_password: str) -> tuple[bool, Optional[str]]:
        user, err = await self.get_user_by_id(user_id)
        if err:
            return False, err
        if not user:
            return False, "User not found"

        password_manager = PasswordManager()
        if not password_manager.verify_password(old_password, user.password):
            return False, "Old password does not match"

        try:
            user.password = password_manager.hash_password(new_password)
            await self.db.commit()
            return True, None
        except SQLAlchemyError as e:
            await self.db.rollback()
            return False, f"DB error during change_password: {str(e)}"
