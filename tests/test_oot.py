"""
Q6 - OBJECT-ORIENTED TESTING (OOT) for AI Document Enhancement System.

Tool Used: pytest (Python testing framework)

OOT focuses on testing OOP constructs:
  1. Class-level testing (state + behavior of individual classes)
  2. Encapsulation testing (data hiding, access control)
  3. Inheritance testing (subclass behavior, method overriding)
  4. Polymorphism testing (method dispatch, interface consistency)
  5. Inter-class (integration) testing (object interactions)
  6. State-based testing (object state transitions)

Classes Tested: User, Document (adapted from Order), Payment
"""

import pytest
from datetime import datetime

from app.models.user import User
from app.models.document import Document, DocumentStatus, DocumentType
from app.models.order import Order, OrderStatus
from app.models.payment import Payment, PaymentMethod, PaymentStatus


# ═══════════════════════════════════════════════════════════════════════
# SECTION A: CLASS-LEVEL TESTING (User Class)
# ═══════════════════════════════════════════════════════════════════════

class TestUserClass:
    """OOT: Testing state and behavior of the User class."""

    def test_user_initialization(self, sample_user):
        """TC-OOT-001: User object initializes with correct default state."""
        assert sample_user.user_id == 1
        assert sample_user.username == "testuser"
        assert sample_user.email == "test@example.com"
        assert sample_user.is_premium is False
        assert sample_user.documents_processed == 0
        assert sample_user.storage_used_mb == 0.0

    def test_user_string_representation(self, sample_user):
        """TC-OOT-002: __str__ returns meaningful representation."""
        result = str(sample_user)
        assert "testuser" in result
        assert "Free" in result

    def test_premium_user_string(self, premium_user):
        """TC-OOT-003: Premium user __str__ shows correct tier."""
        result = str(premium_user)
        assert "Premium" in result

    def test_email_validation_valid(self, sample_user):
        """TC-OOT-004: Valid email passes validation."""
        assert sample_user.validate_email() is True

    def test_email_validation_invalid(self):
        """TC-OOT-005: Invalid email fails validation."""
        user = User(1, "test", "invalidemail", "hash")
        assert user.validate_email() is False

    def test_upgrade_to_premium(self, sample_user):
        """TC-OOT-006: Free user can upgrade to premium."""
        result = sample_user.upgrade_to_premium()
        assert result is True
        assert sample_user.is_premium is True

    def test_upgrade_already_premium(self, premium_user):
        """TC-OOT-007: Already premium user cannot upgrade again."""
        result = premium_user.upgrade_to_premium()
        assert result is False

    def test_downgrade_from_premium(self, premium_user):
        """TC-OOT-008: Premium user can downgrade."""
        result = premium_user.downgrade_from_premium()
        assert result is True
        assert premium_user.is_premium is False

    def test_downgrade_free_user(self, sample_user):
        """TC-OOT-009: Free user cannot downgrade further."""
        result = sample_user.downgrade_from_premium()
        assert result is False

    def test_increment_documents(self, sample_user):
        """TC-OOT-010: Document count increments correctly."""
        sample_user.increment_documents_processed(5)
        assert sample_user.documents_processed == 5

    def test_increment_documents_invalid(self, sample_user):
        """TC-OOT-011: Negative increment raises ValueError."""
        with pytest.raises(ValueError, match="positive"):
            sample_user.increment_documents_processed(-1)

    def test_storage_limit_free_user(self, sample_user):
        """TC-OOT-012: Free user has 500MB storage limit."""
        assert sample_user.get_storage_limit_mb() == 500.0

    def test_storage_limit_premium_user(self, premium_user):
        """TC-OOT-013: Premium user has 5000MB storage limit."""
        assert premium_user.get_storage_limit_mb() == 5000.0

    def test_has_storage_space(self, sample_user):
        """TC-OOT-014: Storage space check works correctly."""
        assert sample_user.has_storage_space(100.0) is True
        assert sample_user.has_storage_space(600.0) is False


# ═══════════════════════════════════════════════════════════════════════
# SECTION B: STATE-BASED TESTING (Document Class)
# ═══════════════════════════════════════════════════════════════════════

class TestDocumentClass:
    """OOT: Testing state transitions and behavior of Document class."""

    def test_document_initialization(self, sample_document):
        """TC-OOT-015: Document initializes in UPLOADED state."""
        assert sample_document.status == DocumentStatus.UPLOADED
        assert sample_document.raw_text == ""
        assert sample_document.enhanced_text == ""

    def test_valid_state_transition(self, sample_document):
        """TC-OOT-016: Valid state transition from UPLOADED to PREPROCESSING."""
        sample_document.update_status(DocumentStatus.PREPROCESSING)
        assert sample_document.status == DocumentStatus.PREPROCESSING

    def test_full_processing_pipeline(self, sample_document):
        """TC-OOT-017: Document goes through complete state machine."""
        transitions = [
            DocumentStatus.PREPROCESSING,
            DocumentStatus.OCR_PROCESSING,
            DocumentStatus.REVIEW,
            DocumentStatus.ENHANCING,
            DocumentStatus.COMPLETED,
        ]
        for state in transitions:
            sample_document.update_status(state)
        assert sample_document.is_processing_complete() is True

    def test_invalid_state_transition(self, sample_document):
        """TC-OOT-018: Invalid state transition raises ValueError."""
        with pytest.raises(ValueError, match="Invalid transition"):
            sample_document.update_status(DocumentStatus.COMPLETED)

    def test_failure_from_any_processing_state(self, sample_document):
        """TC-OOT-019: Any processing state can transition to FAILED."""
        sample_document.update_status(DocumentStatus.PREPROCESSING)
        sample_document.update_status(DocumentStatus.FAILED)
        assert sample_document.status == DocumentStatus.FAILED

    def test_retry_after_failure(self, sample_document):
        """TC-OOT-020: Failed document can be retried (back to UPLOADED)."""
        sample_document.update_status(DocumentStatus.PREPROCESSING)
        sample_document.update_status(DocumentStatus.FAILED)
        sample_document.update_status(DocumentStatus.UPLOADED)
        assert sample_document.status == DocumentStatus.UPLOADED

    def test_set_ocr_result(self, sample_document):
        """TC-OOT-021: OCR results are stored correctly."""
        sample_document.set_ocr_result("Hello World", 85.5)
        assert sample_document.raw_text == "Hello World"
        assert sample_document.ocr_confidence == 85.5

    def test_set_ocr_invalid_confidence(self, sample_document):
        """TC-OOT-022: Invalid OCR confidence raises ValueError."""
        with pytest.raises(ValueError):
            sample_document.set_ocr_result("text", 150.0)

    def test_word_count_raw_text(self, sample_document):
        """TC-OOT-023: Word count works on raw text."""
        sample_document.raw_text = "This is a test document with seven words"
        assert sample_document.get_word_count() == 8

    def test_word_count_enhanced_text(self, sample_document):
        """TC-OOT-024: Word count prefers enhanced text when available."""
        sample_document.raw_text = "raw"
        sample_document.enhanced_text = "enhanced text here"
        assert sample_document.get_word_count() == 3

    def test_file_extension_extraction(self, sample_document):
        """TC-OOT-025: File extension extracted correctly."""
        assert sample_document.get_file_extension() == "pdf"

    def test_readability_score_bounds(self, sample_document):
        """TC-OOT-026: Readability score rejects out-of-range values."""
        sample_document.set_readability_score(75.0)
        assert sample_document.readability_score == 75.0
        with pytest.raises(ValueError):
            sample_document.set_readability_score(150.0)

    def test_plagiarism_score_bounds(self, sample_document):
        """TC-OOT-027: Plagiarism score rejects out-of-range values."""
        sample_document.set_plagiarism_score(12.5)
        assert sample_document.plagiarism_score == 12.5
        with pytest.raises(ValueError):
            sample_document.set_plagiarism_score(-5.0)


# ═══════════════════════════════════════════════════════════════════════
# SECTION C: ENCAPSULATION & BEHAVIOR TESTING (Order Class)
# ═══════════════════════════════════════════════════════════════════════

class TestOrderClass:
    """OOT: Testing encapsulation and method behavior of Order class."""

    def test_order_initialization(self, sample_order):
        """TC-OOT-028: Order initializes with PENDING status."""
        assert sample_order.status == OrderStatus.PENDING
        assert sample_order.document_ids == []
        assert sample_order.total_amount == 0.0

    def test_add_document_to_order(self, sample_order):
        """TC-OOT-029: Documents can be added to order."""
        sample_order.add_document(101, 5)
        assert 101 in sample_order.document_ids
        assert sample_order.num_pages == 5

    def test_add_duplicate_document_raises(self, sample_order):
        """TC-OOT-030: Duplicate document addition raises ValueError."""
        sample_order.add_document(101, 5)
        with pytest.raises(ValueError, match="already in order"):
            sample_order.add_document(101, 5)

    def test_remove_document(self, sample_order):
        """TC-OOT-031: Documents can be removed from order."""
        sample_order.add_document(101, 5)
        sample_order.remove_document(101, 5)
        assert 101 not in sample_order.document_ids
        assert sample_order.num_pages == 0

    def test_order_lifecycle(self, sample_order):
        """TC-OOT-032: Order follows valid lifecycle: PENDING -> PROCESSING -> COMPLETED."""
        sample_order.mark_processing()
        assert sample_order.status == OrderStatus.PROCESSING

        sample_order.mark_completed()
        assert sample_order.status == OrderStatus.COMPLETED
        assert sample_order.completed_at is not None

    def test_complete_non_processing_raises(self, sample_order):
        """TC-OOT-033: Cannot complete a non-processing order."""
        with pytest.raises(ValueError, match="processing"):
            sample_order.mark_completed()

    def test_cancel_pending_order(self, sample_order):
        """TC-OOT-034: Pending order can be cancelled."""
        result = sample_order.cancel()
        assert result is True
        assert sample_order.status == OrderStatus.CANCELLED

    def test_cancel_completed_order(self, sample_order):
        """TC-OOT-035: Completed order cannot be cancelled."""
        sample_order.mark_processing()
        sample_order.mark_completed()
        result = sample_order.cancel()
        assert result is False

    def test_document_count(self, sample_order):
        """TC-OOT-036: Document count returns correct value."""
        sample_order.add_document(1, 3)
        sample_order.add_document(2, 5)
        assert sample_order.get_document_count() == 2


# ═══════════════════════════════════════════════════════════════════════
# SECTION D: POLYMORPHISM & METHOD TESTING (Payment Class)
# ═══════════════════════════════════════════════════════════════════════

class TestPaymentClass:
    """OOT: Testing polymorphic behavior and method correctness of Payment."""

    def test_payment_initialization(self, sample_payment):
        """TC-OOT-037: Payment initializes in INITIATED state."""
        assert sample_payment.status == PaymentStatus.INITIATED
        assert sample_payment.amount == 125.50
        assert sample_payment.method == PaymentMethod.UPI

    def test_validate_positive_amount(self, sample_payment):
        """TC-OOT-038: Positive amount passes validation."""
        assert sample_payment.validate_amount() is True

    def test_validate_zero_amount(self):
        """TC-OOT-039: Zero amount fails validation."""
        payment = Payment(1, 1, 1, 0.0, PaymentMethod.CREDIT_CARD)
        assert payment.validate_amount() is False

    def test_validate_negative_amount(self):
        """TC-OOT-040: Negative amount fails validation."""
        payment = Payment(1, 1, 1, -50.0, PaymentMethod.CREDIT_CARD)
        assert payment.validate_amount() is False

    def test_process_payment(self, sample_payment):
        """TC-OOT-041: Valid payment can be processed."""
        result = sample_payment.process_payment()
        assert result is True
        assert sample_payment.status == PaymentStatus.PROCESSING

    def test_process_already_processed(self, sample_payment):
        """TC-OOT-042: Already processed payment raises error."""
        sample_payment.process_payment()
        with pytest.raises(ValueError, match="already processed"):
            sample_payment.process_payment()

    def test_complete_payment(self, sample_payment):
        """TC-OOT-043: Processing payment can be completed with transaction ID."""
        sample_payment.process_payment()
        sample_payment.complete_payment("TXN_ABC123")
        assert sample_payment.status == PaymentStatus.SUCCESS
        assert sample_payment.transaction_id == "TXN_ABC123"
        assert sample_payment.processed_at is not None

    def test_complete_non_processing_raises(self, sample_payment):
        """TC-OOT-044: Cannot complete a non-processing payment."""
        with pytest.raises(ValueError):
            sample_payment.complete_payment("TXN_ABC")

    def test_fail_payment(self, sample_payment):
        """TC-OOT-045: Payment can be marked as failed."""
        sample_payment.fail_payment("Insufficient funds")
        assert sample_payment.status == PaymentStatus.FAILED

    def test_refund_successful_payment(self, sample_payment):
        """TC-OOT-046: Successful payment can be refunded."""
        sample_payment.process_payment()
        sample_payment.complete_payment("TXN_REF001")
        result = sample_payment.refund()
        assert result is True
        assert sample_payment.status == PaymentStatus.REFUNDED

    def test_refund_non_successful_payment(self, sample_payment):
        """TC-OOT-047: Non-successful payment cannot be refunded."""
        result = sample_payment.refund()
        assert result is False

    def test_payment_summary_dict(self, sample_payment):
        """TC-OOT-048: Payment summary returns correct dict structure."""
        summary = sample_payment.get_payment_summary()
        assert summary["payment_id"] == 1
        assert summary["amount"] == 125.50
        assert summary["method"] == "upi"
        assert summary["status"] == "initiated"

    @pytest.mark.parametrize("method", list(PaymentMethod))
    def test_all_payment_methods_accepted(self, method):
        """TC-OOT-049: All payment method enum values work correctly (polymorphism)."""
        payment = Payment(1, 1, 1, 100.0, method)
        assert payment.method == method
        summary = payment.get_payment_summary()
        assert summary["method"] == method.value

    def test_is_successful_check(self, sample_payment):
        """TC-OOT-050: is_successful returns correct boolean."""
        assert sample_payment.is_successful() is False
        sample_payment.process_payment()
        sample_payment.complete_payment("TXN_123")
        assert sample_payment.is_successful() is True


# ═══════════════════════════════════════════════════════════════════════
# SECTION E: INTER-CLASS INTEGRATION TESTING
# ═══════════════════════════════════════════════════════════════════════

class TestInterClassIntegration:
    """OOT: Testing interactions between User, Document, Order, and Payment objects."""

    def test_user_creates_document_and_order(self):
        """TC-OOT-051: Full workflow - user uploads doc, creates order, makes payment."""
        user = User(1, "john", "john@test.com", "hash123")
        doc = Document(1, user.user_id, "essay.pdf", "/uploads/essay.pdf", num_pages=10)
        order = Order(order_id=1, user_id=user.user_id)

        order.add_document(doc.doc_id, doc.num_pages)
        assert order.num_pages == 10

        user.increment_documents_processed(1)
        assert user.documents_processed == 1

    def test_premium_user_higher_storage(self):
        """TC-OOT-052: Premium user has more storage than free user."""
        free_user = User(1, "free", "free@test.com", "hash")
        premium_user = User(2, "premium", "prem@test.com", "hash", is_premium=True)

        assert premium_user.get_storage_limit_mb() > free_user.get_storage_limit_mb()

    def test_payment_linked_to_order(self):
        """TC-OOT-053: Payment is correctly linked to an order."""
        order = Order(order_id=1, user_id=1)
        order.set_pricing(100.0, 10.0, 16.2, 106.2)

        payment = Payment(1, order.order_id, order.user_id, order.total_amount, PaymentMethod.UPI)
        assert payment.amount == order.total_amount
        assert payment.order_id == order.order_id

    def test_document_processing_updates_status(self):
        """TC-OOT-054: Document status updates reflect processing pipeline."""
        doc = Document(1, 1, "notes.jpg", "/uploads/notes.jpg")

        doc.update_status(DocumentStatus.PREPROCESSING)
        doc.update_status(DocumentStatus.OCR_PROCESSING)
        doc.set_ocr_result("Extracted text from handwritten notes", 78.5)
        doc.update_status(DocumentStatus.REVIEW)
        doc.set_enhanced_text("Enhanced and corrected text from notes")
        doc.update_status(DocumentStatus.ENHANCING)
        doc.set_readability_score(82.0)
        doc.set_plagiarism_score(5.2)
        doc.update_status(DocumentStatus.COMPLETED)

        assert doc.is_processing_complete()
        assert doc.ocr_confidence == 78.5
        assert doc.readability_score == 82.0
        assert doc.plagiarism_score == 5.2
        assert doc.get_word_count() > 0


# ═══════════════════════════════════════════════════════════════════════
# SECTION F: DATABASE INTEGRATION TESTING
# ═══════════════════════════════════════════════════════════════════════

class TestDatabaseOOT:
    """OOT: Testing persistence of objects through DatabaseManager."""

    def test_create_and_retrieve_user(self, db_manager):
        """TC-OOT-055: User persisted and retrieved from database."""
        user_id = db_manager.insert_user("testuser", "test@test.com", "hash123")
        assert user_id is not None

        user = db_manager.get_user(user_id)
        assert user["username"] == "testuser"
        assert user["email"] == "test@test.com"

    def test_create_and_retrieve_document(self, db_manager):
        """TC-OOT-056: Document persisted and retrieved from database."""
        user_id = db_manager.insert_user("docuser", "doc@test.com", "hash")
        doc_id = db_manager.insert_document(user_id, "test.pdf", "/path/test.pdf", 5)

        doc = db_manager.get_document(doc_id)
        assert doc["filename"] == "test.pdf"
        assert doc["num_pages"] == 5

    def test_update_document_status(self, db_manager):
        """TC-OOT-057: Document status update persists in database."""
        user_id = db_manager.insert_user("statuser", "stat@test.com", "hash")
        doc_id = db_manager.insert_document(user_id, "doc.pdf", "/path/doc.pdf")

        db_manager.update_document_status(doc_id, "preprocessing")
        doc = db_manager.get_document(doc_id)
        assert doc["status"] == "preprocessing"

    def test_user_documents_relationship(self, db_manager):
        """TC-OOT-058: User-document relationship works correctly."""
        user_id = db_manager.insert_user("multiuser", "multi@test.com", "hash")
        db_manager.insert_document(user_id, "doc1.pdf", "/path/doc1.pdf")
        db_manager.insert_document(user_id, "doc2.pdf", "/path/doc2.pdf")

        docs = db_manager.get_user_documents(user_id)
        assert len(docs) == 2

    def test_order_and_payment_persistence(self, db_manager):
        """TC-OOT-059: Order and payment data persist correctly."""
        user_id = db_manager.insert_user("orderuser", "order@test.com", "hash")
        order_id = db_manager.insert_order(user_id, 10, 25.0, 2.5, 4.05, 26.55)
        payment_id = db_manager.insert_payment(order_id, user_id, 26.55, "upi")

        assert order_id is not None
        assert payment_id is not None
