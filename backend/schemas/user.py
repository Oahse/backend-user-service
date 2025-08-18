from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
from typing import List, Optional
from enum import Enum
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID

# --- Enums ---
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

# --- Address Schemas ---
class AddressBase(BaseModel):
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    post_code: Optional[str] = None
    kind: AddressType

class AddressCreate(AddressBase):
    user_id: str

class AddressRead(AddressBase):
    id: UUID
    user_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AddressUpdate(AddressBase):
    id: Optional[UUID]  # For updates/deletes
    pass

# --- User Schemas ---
class UserBase(BaseModel):
    firstname: str
    lastname: str
    email: EmailStr
    role: UserRole
    verified: bool = False
    active: bool = False
    phone: Optional[str] = None
    age: int
    gender: UserGender
    picture: Optional[str] = None
    telegram: Optional[str] = None
    whatsapp: Optional[str] = None
    addresses: Optional[List[AddressCreate]] = []

class UserCreate(UserBase):
    password: str

    @field_validator('password', mode='before')
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

    @field_validator('phone', mode='before')
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v and not v.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            raise ValueError('Phone number must contain only digits, spaces, hyphens, and plus sign')
        return v

class UserRead(UserBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UserUpdate(BaseModel):
    firstname: Optional[str]
    lastname: Optional[str]
    telegram: Optional[str]
    whatsapp: Optional[str]
    email: Optional[EmailStr]
    role: Optional[UserRole]
    verified: Optional[bool]
    active: Optional[bool]
    phone: Optional[str]
    age: Optional[int]
    gender: Optional[UserGender]
    picture: Optional[str]
    addresses: Optional[List[AddressUpdate]] = []

    @field_validator('phone', mode='before')
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v and not v.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            raise ValueError('Phone number must contain only digits, spaces, hyphens, and plus sign')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password_hash: str

class PasswordReset(BaseModel):
    email: EmailStr

class PasswordResetConfirm(PasswordReset):
    otp: str
    new_password: str

    @field_validator('new_password', mode='before')
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

class EmailVerification(BaseModel):
    email: EmailStr
    otp: str

class EmailChangeRequest(BaseModel):
    new_email: EmailStr

class EmailChangeConfirm(BaseModel):
    token: str
    
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserRead

class RefreshTokenRequest(BaseModel):
    refresh_token: str
