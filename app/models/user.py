"""User model for AI Document Enhancement System."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class User:
    user_id: int
    username: str
    email: str
    password_hash: str
    is_premium: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    documents_processed: int = 0
    storage_used_mb: float = 0.0

    def upgrade_to_premium(self) -> bool:
        if self.is_premium:
            return False
        self.is_premium = True
        return True

    def downgrade_from_premium(self) -> bool:
        if not self.is_premium:
            return False
        self.is_premium = False
        return True

    def validate_email(self) -> bool:
        return "@" in self.email and "." in self.email.split("@")[-1]

    def increment_documents_processed(self, count: int = 1) -> None:
        if count <= 0:
            raise ValueError("Count must be positive")
        self.documents_processed += count

    def add_storage_usage(self, size_mb: float) -> None:
        if size_mb < 0:
            raise ValueError("Size cannot be negative")
        self.storage_used_mb += size_mb

    def get_storage_limit_mb(self) -> float:
        return 5000.0 if self.is_premium else 500.0

    def has_storage_space(self, required_mb: float) -> bool:
        return (self.storage_used_mb + required_mb) <= self.get_storage_limit_mb()

    def __str__(self) -> str:
        tier = "Premium" if self.is_premium else "Free"
        return f"User({self.username}, {tier}, docs={self.documents_processed})"
