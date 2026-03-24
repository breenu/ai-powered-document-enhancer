"""Processing Order model for AI Document Enhancement System."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class OrderStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


@dataclass
class Order:
    order_id: int
    user_id: int
    document_ids: List[int] = field(default_factory=list)
    status: OrderStatus = OrderStatus.PENDING
    num_pages: int = 0
    base_price: float = 0.0
    discount_amount: float = 0.0
    tax_amount: float = 0.0
    total_amount: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    def add_document(self, doc_id: int, pages: int) -> None:
        if doc_id in self.document_ids:
            raise ValueError(f"Document {doc_id} already in order")
        self.document_ids.append(doc_id)
        self.num_pages += pages

    def remove_document(self, doc_id: int, pages: int) -> None:
        if doc_id not in self.document_ids:
            raise ValueError(f"Document {doc_id} not in order")
        self.document_ids.remove(doc_id)
        self.num_pages = max(0, self.num_pages - pages)

    def set_pricing(self, base: float, discount: float, tax: float, total: float) -> None:
        self.base_price = base
        self.discount_amount = discount
        self.tax_amount = tax
        self.total_amount = total

    def mark_completed(self) -> None:
        if self.status != OrderStatus.PROCESSING:
            raise ValueError("Only processing orders can be completed")
        self.status = OrderStatus.COMPLETED
        self.completed_at = datetime.now()

    def mark_processing(self) -> None:
        if self.status != OrderStatus.PENDING:
            raise ValueError("Only pending orders can start processing")
        self.status = OrderStatus.PROCESSING

    def cancel(self) -> bool:
        if self.status in (OrderStatus.COMPLETED, OrderStatus.REFUNDED):
            return False
        self.status = OrderStatus.CANCELLED
        return True

    def get_document_count(self) -> int:
        return len(self.document_ids)

    def __str__(self) -> str:
        return f"Order(#{self.order_id}, {self.status.value}, total={self.total_amount})"
