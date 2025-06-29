from sqlalchemy.orm import mapped_column, Mapped, relationship, validates
from sqlalchemy import Enum, Integer, String, DateTime, ForeignKey, Boolean, Text, BigInteger
from core.database import Base, CHAR_LENGTH
from core.utils.encryption import PasswordManager
from core.utils.generator import generator
from datetime import datetime
from enum import Enum as PyEnum
from typing import List, Optional
from uuid import UUID


class AddressType(PyEnum):
    Billing = "Billing"
    Shipping = "Shipping"

class Address(Base):
    __tablename__ = "addresses"

    id: Mapped[str] = mapped_column(String(CHAR_LENGTH), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    user: Mapped["User"] = relationship("User", back_populates="addresses", uselist=False)
    
    street: Mapped[str] = mapped_column(String(CHAR_LENGTH), nullable=True)
    city: Mapped[str] = mapped_column(String(CHAR_LENGTH), nullable=True)
    state: Mapped[str] = mapped_column(String(CHAR_LENGTH), nullable=True)
    country: Mapped[str] = mapped_column(String(CHAR_LENGTH), nullable=True)
    post_code: Mapped[str] = mapped_column(String(CHAR_LENGTH), nullable=True)
    kind: Mapped[AddressType] = mapped_column(Enum(AddressType), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "street": self.street,
            "city": self.city,
            "state": self.state,
            "country": self.country,
            "post_code": self.post_code,
            "kind": self.kind.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self):
        return f"Address(id={self.id!r}, kind={self.kind!r})"


class UserRole(PyEnum):
    Guest = 'Guest'
    Customer = "Customer"
    Supplier = "Supplier"
    Admin = "Admin"
    Moderator = "Moderator"
    Support = "Support"
    Manager = "Manager"
    SuperAdmin = "SuperAdmin"
    GodAdmin = "GodAdmin"

class UserGender(PyEnum):
    Male = 'Male'
    Female = "Female"

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(String(CHAR_LENGTH), primary_key=True)
    
    firstname: Mapped[str] = mapped_column(String(CHAR_LENGTH))
    lastname: Mapped[str] = mapped_column(String(CHAR_LENGTH))
    password: Mapped[str] = mapped_column(Text, nullable=True)
    email: Mapped[str] = mapped_column(String(CHAR_LENGTH), unique=True, index=True)
    picture: Mapped[str] = mapped_column(Text, nullable=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    active: Mapped[bool] = mapped_column(Boolean, default=False)
    phone_number: Mapped[str] = mapped_column(String(CHAR_LENGTH), nullable=True)
    phone_number_pre: Mapped[str] = mapped_column(String(CHAR_LENGTH), nullable=True)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    gender: Mapped[UserGender] = mapped_column(Enum(UserGender), nullable=False)
    
    addresses: Mapped[List[Address]] = relationship(
        "Address", back_populates="user", cascade="all, delete-orphan", uselist=True, lazy="joined", passive_deletes=True
    )

    access_token: Mapped[str] = mapped_column(Text, nullable=True)
    refresh_token: Mapped[str] = mapped_column(Text, nullable=True)
    activation_token: Mapped[Optional[str]] = mapped_column(String(CHAR_LENGTH), nullable=True)
    activation_token_expires: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    @property
    def full_name(self):
        return f"{self.firstname} {self.lastname}"

    @validates("role")
    def validate_role(self, key, role):
        if not isinstance(role, UserRole):
            raise ValueError(f"Invalid role: {role}")
        return role

    def verify_password(self, password):
        password_manager = PasswordManager()
        return password_manager.verify_password(password, hashed_password=self.password)

    def to_dict(self):
        return {
            "id": self.id,
            "firstname": self.firstname,
            "lastname": self.lastname,
            "email": self.email,
            "picture": self.picture,
            "role": self.role.value,
            "active": self.active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "phone_number": self.phone_number,
            "phone_number_pre": self.phone_number_pre,
            "gender": self.gender.value,
            "age": self.age,
            "addresses": [address.to_dict() for address in self.addresses],
            "access_token": self.access_token,
            "refresh_token": self.refresh_token
        }

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, firstname={self.firstname!r}, lastname={self.lastname!r}, role={self.role!r})"
