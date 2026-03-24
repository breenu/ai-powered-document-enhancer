"""Database Manager for AI Document Enhancement System using SQLite."""

import json
import sqlite3
from typing import Any, Dict, List, Optional


class DatabaseManager:
    def __init__(self, db_path: str = "document_enhancer.db"):
        self.db_path = db_path
        self.connection = None

    def connect(self) -> None:
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self._create_tables()

    def disconnect(self) -> None:
        if self.connection:
            self.connection.close()
            self.connection = None

    def _ensure_connected(self) -> None:
        if self.connection is None:
            raise RuntimeError("Database not connected. Call connect() first.")

    def _create_tables(self) -> None:
        cursor = self.connection.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_premium INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                documents_processed INTEGER DEFAULT 0,
                storage_used_mb REAL DEFAULT 0.0
            );

            CREATE TABLE IF NOT EXISTS documents (
                doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                num_pages INTEGER DEFAULT 1,
                status TEXT DEFAULT 'uploaded',
                doc_type TEXT,
                raw_text TEXT DEFAULT '',
                enhanced_text TEXT DEFAULT '',
                summary_text TEXT DEFAULT '',
                readability_score REAL DEFAULT 0.0,
                plagiarism_score REAL DEFAULT 0.0,
                ocr_confidence REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );

            CREATE TABLE IF NOT EXISTS processing_history (
                history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id INTEGER NOT NULL,
                stage TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'started',
                input_preview TEXT DEFAULT '',
                output_preview TEXT DEFAULT '',
                details TEXT DEFAULT '{}',
                error_message TEXT,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (doc_id) REFERENCES documents(doc_id)
            );

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                num_pages INTEGER DEFAULT 0,
                base_price REAL DEFAULT 0.0,
                discount_amount REAL DEFAULT 0.0,
                tax_amount REAL DEFAULT 0.0,
                total_amount REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );

            CREATE TABLE IF NOT EXISTS payments (
                payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                method TEXT NOT NULL,
                status TEXT DEFAULT 'initiated',
                transaction_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES orders(order_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );
        """)
        self.connection.commit()

    # ── User CRUD ──

    def insert_user(self, username: str, email: str, password_hash: str) -> int:
        self._ensure_connected()
        cursor = self.connection.cursor()
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, password_hash),
        )
        self.connection.commit()
        return cursor.lastrowid

    def get_user(self, user_id: int) -> Optional[dict]:
        self._ensure_connected()
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    # ── Document CRUD ──

    def insert_document(self, user_id: int, filename: str, file_path: str,
                        num_pages: int = 1) -> int:
        self._ensure_connected()
        cursor = self.connection.cursor()
        cursor.execute(
            "INSERT INTO documents (user_id, filename, file_path, num_pages) "
            "VALUES (?, ?, ?, ?)",
            (user_id, filename, file_path, num_pages),
        )
        self.connection.commit()
        return cursor.lastrowid

    def get_document(self, doc_id: int) -> Optional[dict]:
        self._ensure_connected()
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM documents WHERE doc_id = ?", (doc_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def update_document_status(self, doc_id: int, status: str) -> None:
        self._ensure_connected()
        cursor = self.connection.cursor()
        cursor.execute(
            "UPDATE documents SET status = ?, updated_at = CURRENT_TIMESTAMP "
            "WHERE doc_id = ?",
            (status, doc_id),
        )
        self.connection.commit()

    def update_document_text(self, doc_id: int, *, raw_text: str = None,
                             enhanced_text: str = None,
                             summary_text: str = None) -> None:
        self._ensure_connected()
        fields: List[str] = []
        values: list = []
        if raw_text is not None:
            fields.append("raw_text = ?")
            values.append(raw_text)
        if enhanced_text is not None:
            fields.append("enhanced_text = ?")
            values.append(enhanced_text)
        if summary_text is not None:
            fields.append("summary_text = ?")
            values.append(summary_text)
        if not fields:
            return
        fields.append("updated_at = CURRENT_TIMESTAMP")
        values.append(doc_id)
        cursor = self.connection.cursor()
        cursor.execute(
            f"UPDATE documents SET {', '.join(fields)} WHERE doc_id = ?",
            tuple(values),
        )
        self.connection.commit()

    def update_document_scores(self, doc_id: int, *, readability_score: float = None,
                               plagiarism_score: float = None,
                               ocr_confidence: float = None) -> None:
        self._ensure_connected()
        fields: List[str] = []
        values: list = []
        if readability_score is not None:
            fields.append("readability_score = ?")
            values.append(readability_score)
        if plagiarism_score is not None:
            fields.append("plagiarism_score = ?")
            values.append(plagiarism_score)
        if ocr_confidence is not None:
            fields.append("ocr_confidence = ?")
            values.append(ocr_confidence)
        if not fields:
            return
        fields.append("updated_at = CURRENT_TIMESTAMP")
        values.append(doc_id)
        cursor = self.connection.cursor()
        cursor.execute(
            f"UPDATE documents SET {', '.join(fields)} WHERE doc_id = ?",
            tuple(values),
        )
        self.connection.commit()

    def update_document_type(self, doc_id: int, doc_type: str) -> None:
        self._ensure_connected()
        cursor = self.connection.cursor()
        cursor.execute(
            "UPDATE documents SET doc_type = ?, updated_at = CURRENT_TIMESTAMP "
            "WHERE doc_id = ?",
            (doc_type, doc_id),
        )
        self.connection.commit()

    def get_user_documents(self, user_id: int) -> List[dict]:
        self._ensure_connected()
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT * FROM documents WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def delete_document(self, doc_id: int) -> None:
        self._ensure_connected()
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM processing_history WHERE doc_id = ?", (doc_id,))
        cursor.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
        self.connection.commit()

    # ── Processing History CRUD ──

    def insert_history_entry(self, doc_id: int, stage: str,
                             status: str = "started",
                             input_preview: str = "",
                             details: dict = None) -> int:
        self._ensure_connected()
        cursor = self.connection.cursor()
        cursor.execute(
            "INSERT INTO processing_history "
            "(doc_id, stage, status, input_preview, details) "
            "VALUES (?, ?, ?, ?, ?)",
            (doc_id, stage, status, input_preview, json.dumps(details or {})),
        )
        self.connection.commit()
        return cursor.lastrowid

    def complete_history_entry(self, history_id: int, status: str = "completed",
                               output_preview: str = "",
                               error_message: str = None) -> None:
        self._ensure_connected()
        cursor = self.connection.cursor()
        cursor.execute(
            "UPDATE processing_history "
            "SET status = ?, output_preview = ?, error_message = ?, "
            "    completed_at = CURRENT_TIMESTAMP "
            "WHERE history_id = ?",
            (status, output_preview, error_message, history_id),
        )
        self.connection.commit()

    def get_document_history(self, doc_id: int) -> List[dict]:
        self._ensure_connected()
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT * FROM processing_history WHERE doc_id = ? "
            "ORDER BY started_at ASC",
            (doc_id,),
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            entry = dict(row)
            if entry.get("details"):
                try:
                    entry["details"] = json.loads(entry["details"])
                except (json.JSONDecodeError, TypeError):
                    pass
            result.append(entry)
        return result

    # ── Settings CRUD ──

    def set_setting(self, key: str, value: Any, category: str = "general") -> None:
        self._ensure_connected()
        serialized = json.dumps(value) if not isinstance(value, str) else value
        cursor = self.connection.cursor()
        cursor.execute(
            "INSERT INTO settings (key, value, category, updated_at) "
            "VALUES (?, ?, ?, CURRENT_TIMESTAMP) "
            "ON CONFLICT(key) DO UPDATE SET "
            "  value = excluded.value, "
            "  category = excluded.category, "
            "  updated_at = CURRENT_TIMESTAMP",
            (key, serialized, category),
        )
        self.connection.commit()

    def get_setting(self, key: str, default: Any = None) -> Any:
        self._ensure_connected()
        cursor = self.connection.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        if row is None:
            return default
        raw = row["value"]
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return raw

    def get_settings_by_category(self, category: str) -> Dict[str, Any]:
        self._ensure_connected()
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT key, value FROM settings WHERE category = ?", (category,),
        )
        result: Dict[str, Any] = {}
        for row in cursor.fetchall():
            try:
                result[row["key"]] = json.loads(row["value"])
            except (json.JSONDecodeError, TypeError):
                result[row["key"]] = row["value"]
        return result

    def delete_setting(self, key: str) -> None:
        self._ensure_connected()
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM settings WHERE key = ?", (key,))
        self.connection.commit()

    # ── Order & Payment CRUD (unchanged) ──

    def insert_order(self, user_id: int, num_pages: int, base_price: float,
                     discount: float, tax: float, total: float) -> int:
        self._ensure_connected()
        cursor = self.connection.cursor()
        cursor.execute(
            "INSERT INTO orders (user_id, num_pages, base_price, discount_amount, "
            "tax_amount, total_amount) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, num_pages, base_price, discount, tax, total),
        )
        self.connection.commit()
        return cursor.lastrowid

    def insert_payment(self, order_id: int, user_id: int, amount: float,
                       method: str) -> int:
        self._ensure_connected()
        cursor = self.connection.cursor()
        cursor.execute(
            "INSERT INTO payments (order_id, user_id, amount, method) "
            "VALUES (?, ?, ?, ?)",
            (order_id, user_id, amount, method),
        )
        self.connection.commit()
        return cursor.lastrowid
