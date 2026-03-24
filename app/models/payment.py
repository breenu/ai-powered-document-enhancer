"""Payment model for AI Document Enhancement System."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class PaymentMethod(Enum):
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    UPI = "upi"
    NET_BANKING = "net_banking"
    WALLET = "wallet"


class PaymentStatus(Enum):
    INITIATED = "initiated"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    REFUNDED = "refunded"


@dataclass
class Payment:
    payment_id: int
    order_id: int
    user_id: int
    amount: float
    method: PaymentMethod
    status: PaymentStatus = PaymentStatus.INITIATED
    transaction_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None

    def validate_amount(self) -> bool:
        return self.amount > 0

    def process_payment(self) -> bool:
        if self.status != PaymentStatus.INITIATED:
            raise ValueError("Payment already processed or in invalid state")
        if not self.validate_amount():
            self.status = PaymentStatus.FAILED
            return False
        self.status = PaymentStatus.PROCESSING
        return True

    def complete_payment(self, transaction_id: str) -> None:
        if self.status != PaymentStatus.PROCESSING:
            raise ValueError("Payment must be processing to complete")
        self.transaction_id = transaction_id
        self.status = PaymentStatus.SUCCESS
        self.processed_at = datetime.now()

    def fail_payment(self, reason: str = "") -> None:
        self.status = PaymentStatus.FAILED
        self.processed_at = datetime.now()

    def refund(self) -> bool:
        if self.status != PaymentStatus.SUCCESS:
            return False
        self.status = PaymentStatus.REFUNDED
        self.processed_at = datetime.now()
        return True

    def is_successful(self) -> bool:
        return self.status == PaymentStatus.SUCCESS

    def get_payment_summary(self) -> dict:
        return {
            "payment_id": self.payment_id,
            "order_id": self.order_id,
            "amount": self.amount,
            "method": self.method.value,
            "status": self.status.value,
            "transaction_id": self.transaction_id,
        }

    def __str__(self) -> str:
        return f"Payment(#{self.payment_id}, {self.amount}, {self.status.value})"
