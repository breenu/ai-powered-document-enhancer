"""Shared test fixtures for AI Document Enhancement System."""

import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.order_calculation import OrderCalculator
from app.models.user import User
from app.models.document import Document, DocumentStatus
from app.models.order import Order, OrderStatus
from app.models.payment import Payment, PaymentMethod, PaymentStatus
from app.database.db_manager import DatabaseManager


@pytest.fixture
def calculator():
    return OrderCalculator()


@pytest.fixture
def sample_user():
    return User(
        user_id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hashed_password_123",
    )


@pytest.fixture
def premium_user():
    return User(
        user_id=2,
        username="premiumuser",
        email="premium@example.com",
        password_hash="hashed_password_456",
        is_premium=True,
    )


@pytest.fixture
def sample_document():
    return Document(
        doc_id=1,
        user_id=1,
        filename="test_document.pdf",
        file_path="/uploads/test_document.pdf",
        num_pages=5,
    )


@pytest.fixture
def sample_order():
    return Order(order_id=1, user_id=1)


@pytest.fixture
def sample_payment():
    return Payment(
        payment_id=1,
        order_id=1,
        user_id=1,
        amount=125.50,
        method=PaymentMethod.UPI,
    )


@pytest.fixture
def db_manager(tmp_path):
    db = DatabaseManager(str(tmp_path / "test.db"))
    db.connect()
    yield db
    db.disconnect()
