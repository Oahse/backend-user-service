from pydantic import BaseModel, EmailStr
from typing import List, Optional
from enum import Enum
from datetime import datetime


class AddressType(str, Enum):
    Billing = "Billing"
    Shipping = "Shipping"


class UserRole(str, Enum):
    Guest = 'Guest'
    Customer = "Customer"
    Supplier = "Supplier"
    Admin = "Admin"
    Moderator = "Moderator"
    Support = "Support"
    Manager = "Manager"
    SuperAdmin = "SuperAdmin"
    GodAdmin = "GodAdmin"


class UserGender(str, Enum):
    Male = 'Male'
    Female = "Female"


class AddressBase(BaseModel):
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    post_code: Optional[str] = None
    kind: AddressType


class AddressCreate(AddressBase):
    user_id: str  # Required when creating, link to User


class AddressRead(AddressBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class AddressUpdate(AddressBase):
    pass

class UserBase(BaseModel):
    firstname: str
    lastname: str
    email: EmailStr
    role: UserRole
    active: bool = False
    phone_number: Optional[str] = None
    phone_number_pre: Optional[str] = None
    age: int
    gender: UserGender
    picture: Optional[str] = None


class UserCreate(UserBase):
    password: str  # Password required on creation


class UserRead(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime
    addresses: List[AddressRead] = []

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    firstname: Optional[str]
    lastname: Optional[str]
    email: Optional[EmailStr]
    role: Optional[UserRole]
    active: Optional[bool]
    phone_number: Optional[str]
    phone_number_pre: Optional[str]
    age: Optional[int]
    gender: Optional[UserGender]
    picture: Optional[str]

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str