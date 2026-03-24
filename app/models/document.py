"""Document model for AI Document Enhancement System."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class DocumentStatus(Enum):
    UPLOADED = "uploaded"
    PREPROCESSING = "preprocessing"
    OCR_PROCESSING = "ocr_processing"
    REVIEW = "review"
    ENHANCING = "enhancing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentType(Enum):
    ESSAY = "essay"
    REPORT = "report"
    LETTER = "letter"
    NOTES = "notes"
    RESEARCH_PAPER = "research_paper"


class PipelineStage(Enum):
    PREPROCESSING = "preprocessing"
    OCR = "ocr"
    GRAMMAR = "grammar"
    READABILITY = "readability"
    SUMMARIZATION = "summarization"
    FORMATTING = "formatting"
    PLAGIARISM_CHECK = "plagiarism_check"
    PARAPHRASING = "paraphrasing"


@dataclass
class GrammarCorrection:
    """A single grammar or spelling correction applied to the document."""
    original: str
    corrected: str
    rule_id: str
    message: str
    offset: int
    length: int
    category: str = ""


@dataclass
class ProcessingState:
    """Tracks the progress of a document through the AI pipeline."""
    completed_stages: List[PipelineStage] = field(default_factory=list)
    current_stage: Optional[PipelineStage] = None
    stage_results: Dict[str, Any] = field(default_factory=dict)
    errors: List[Dict[str, str]] = field(default_factory=list)
    progress_percent: float = 0.0
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    def begin_stage(self, stage: PipelineStage) -> None:
        self.current_stage = stage
        if self.started_at is None:
            self.started_at = datetime.now()

    def complete_stage(self, stage: PipelineStage, result: Any = None) -> None:
        if stage not in self.completed_stages:
            self.completed_stages.append(stage)
        if result is not None:
            self.stage_results[stage.value] = result
        self.current_stage = None
        total = len(PipelineStage)
        self.progress_percent = (len(self.completed_stages) / total) * 100

    def record_error(self, stage: PipelineStage, error_msg: str) -> None:
        self.errors.append({
            "stage": stage.value,
            "error": error_msg,
            "timestamp": datetime.now().isoformat(),
        })
        self.current_stage = None

    def mark_finished(self) -> None:
        self.finished_at = datetime.now()
        self.progress_percent = 100.0

    @property
    def is_running(self) -> bool:
        return self.started_at is not None and self.finished_at is None

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0


@dataclass
class Document:
    doc_id: int
    user_id: int
    filename: str
    file_path: str
    num_pages: int = 1
    status: DocumentStatus = DocumentStatus.UPLOADED
    doc_type: Optional[DocumentType] = None
    raw_text: str = ""
    enhanced_text: str = ""
    summary_text: str = ""
    readability_score: float = 0.0
    plagiarism_score: float = 0.0
    ocr_confidence: float = 0.0
    grammar_corrections: List[GrammarCorrection] = field(default_factory=list)
    processing_state: ProcessingState = field(default_factory=ProcessingState)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def update_status(self, new_status: DocumentStatus) -> None:
        valid_transitions = {
            DocumentStatus.UPLOADED: [DocumentStatus.PREPROCESSING, DocumentStatus.FAILED],
            DocumentStatus.PREPROCESSING: [DocumentStatus.OCR_PROCESSING, DocumentStatus.FAILED],
            DocumentStatus.OCR_PROCESSING: [DocumentStatus.REVIEW, DocumentStatus.ENHANCING, DocumentStatus.FAILED],
            DocumentStatus.REVIEW: [DocumentStatus.ENHANCING, DocumentStatus.FAILED],
            DocumentStatus.ENHANCING: [DocumentStatus.COMPLETED, DocumentStatus.FAILED],
            DocumentStatus.COMPLETED: [],
            DocumentStatus.FAILED: [DocumentStatus.UPLOADED],
        }
        if new_status not in valid_transitions.get(self.status, []):
            raise ValueError(
                f"Invalid transition from {self.status.value} to {new_status.value}"
            )
        self.status = new_status
        self.updated_at = datetime.now()

    def set_ocr_result(self, text: str, confidence: float) -> None:
        if confidence < 0 or confidence > 100:
            raise ValueError("Confidence must be between 0 and 100")
        self.raw_text = text
        self.ocr_confidence = confidence

    def set_enhanced_text(self, text: str) -> None:
        self.enhanced_text = text
        self.updated_at = datetime.now()

    def set_summary(self, summary: str) -> None:
        self.summary_text = summary
        self.updated_at = datetime.now()

    def add_grammar_correction(self, correction: GrammarCorrection) -> None:
        self.grammar_corrections.append(correction)

    def set_readability_score(self, score: float) -> None:
        if score < 0 or score > 100:
            raise ValueError("Readability score must be between 0 and 100")
        self.readability_score = score

    def set_plagiarism_score(self, score: float) -> None:
        if score < 0 or score > 100:
            raise ValueError("Plagiarism score must be between 0 and 100")
        self.plagiarism_score = score

    def is_processing_complete(self) -> bool:
        return self.status == DocumentStatus.COMPLETED

    def get_word_count(self) -> int:
        text = self.enhanced_text if self.enhanced_text else self.raw_text
        return len(text.split()) if text else 0

    def get_file_extension(self) -> str:
        return self.filename.rsplit(".", 1)[-1].lower() if "." in self.filename else ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "user_id": self.user_id,
            "filename": self.filename,
            "file_path": self.file_path,
            "num_pages": self.num_pages,
            "status": self.status.value,
            "doc_type": self.doc_type.value if self.doc_type else None,
            "raw_text": self.raw_text,
            "enhanced_text": self.enhanced_text,
            "summary_text": self.summary_text,
            "readability_score": self.readability_score,
            "plagiarism_score": self.plagiarism_score,
            "ocr_confidence": self.ocr_confidence,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Document":
        return cls(
            doc_id=data["doc_id"],
            user_id=data["user_id"],
            filename=data["filename"],
            file_path=data["file_path"],
            num_pages=data.get("num_pages", 1),
            status=DocumentStatus(data.get("status", "uploaded")),
            doc_type=DocumentType(data["doc_type"]) if data.get("doc_type") else None,
            raw_text=data.get("raw_text", ""),
            enhanced_text=data.get("enhanced_text", ""),
            summary_text=data.get("summary_text", ""),
            readability_score=data.get("readability_score", 0.0),
            plagiarism_score=data.get("plagiarism_score", 0.0),
            ocr_confidence=data.get("ocr_confidence", 0.0),
        )

    def __str__(self) -> str:
        return f"Document({self.filename}, status={self.status.value})"
