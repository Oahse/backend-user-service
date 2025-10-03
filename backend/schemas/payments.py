from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum
from uuid import UUID

class PaymentMethod(str, Enum):
    CreditCard = "CreditCard"
    DebitCard = "DebitCard"
    BankTransfer = "BankTransfer"
    ACH = "ACH"                      # US
    SEPA = "SEPA"                    # EU
    Paypal = "Paypal"
    ApplePay = "ApplePay"
    GooglePay = "GooglePay"
    UPI = "UPI"                      # India
    Alipay = "Alipay"                # China
    WeChatPay = "WeChatPay"          # China
    MobileMoney = "MobileMoney"      # Africa (e.g. M-Pesa)
    CashOnDelivery = "CashOnDelivery"
    Crypto = "Crypto"
    GiftCard = "GiftCard"
    BuyNowPayLater = "BuyNowPayLater"  # Klarna, Affirm etc.
    StoreCredit = "StoreCredit"      # Internal credit or loyalty points
    Stripe = "Stripe"
    Other = "Other"



class PaymentStatus(str, Enum):
    Pending = "Pending"
    Completed = "Completed"
    Failed = "Failed"
    Refunded = "Refunded"
    Cancelled = "Cancelled"
    Authorized = "Authorized"
    Voided = "Voided"


class ParentPaymentSchema(BaseModel):
    id: UUID

    class Config:
        from_attributes = True


class PaymentSchema(BaseModel):
    id: UUID
    order_id: UUID
    user_id: Optional[UUID] = None
    method: PaymentMethod
    status: PaymentStatus = PaymentStatus.Pending
    amount: float
    currency: str
    transaction_id: Optional[str] = None
    gateway_response: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    refunded_amount: float = 0.0
    parent_payment_id: Optional[UUID] = None
    parent_payment: Optional[ParentPaymentSchema] = None
    stripe_customer_id: Optional[str] = None
    stripe_payment_intent_id: Optional[str] = None
    stripe_checkout_session_id: Optional[str] = None

    class Config:
        from_attributes = True

class PaymentCreate(BaseModel):
    order_id: UUID
    user_id: Optional[UUID] = None
    method: PaymentMethod
    amount: float
    currency: str
    stripe_customer_id: Optional[str] = None
    stripe_payment_intent_id: Optional[str] = None
    stripe_checkout_session_id: Optional[str] = None

class PaymentUpdate(BaseModel):
    status: Optional[PaymentStatus] = None
    transaction_id: Optional[str] = None
    gateway_response: Optional[str] = None
    refunded_amount: Optional[float] = None
    stripe_payment_intent_id: Optional[str] = None
    stripe_checkout_session_id: Optional[str] = None