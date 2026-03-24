"""Pipeline orchestrator for the full document enhancement workflow.

Chains preprocessing -> OCR -> grammar -> readability -> summarization ->
plagiarism -> paraphrasing -> formatting, with progress callbacks and
cancellation support.
"""

import logging
from dataclasses import dataclass
from typing import Callable, List, Optional

import numpy as np

from app.core.document_formatter import DocumentFormatter
from app.core.grammar_enhancer import GrammarEnhancer
from app.core.ocr_engine import OCREngine
from app.core.paraphraser import Paraphraser
from app.core.plagiarism_checker import PlagiarismChecker
from app.core.preprocessing import ImagePreprocessor
from app.core.readability_optimizer import ReadabilityOptimizer
from app.core.summarizer import Summarizer
from app.models.document import (
    Document,
    DocumentStatus,
    DocumentType,
    PipelineStage,
    ProcessingState,
)

logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    enable_grammar: bool = True
    enable_readability: bool = True
    enable_summarization: bool = True
    enable_plagiarism: bool = True
    enable_paraphrasing: bool = True
    enable_formatting: bool = True
    summarization_method: str = "extractive"
    summary_sentences: int = 5
    target_readability_grade: float = 10.0
    similarity_threshold: float = 0.7
    apply_threshold: bool = False
    ocr_language: str = "eng"
    tesseract_path: Optional[str] = None
    num_paraphrase_suggestions: int = 3


ProgressCallback = Callable[[PipelineStage, float, str], None]


class Pipeline:
    """Orchestrates the full document enhancement pipeline end-to-end."""

    def __init__(self, config: PipelineConfig = None):
        self.config = config or PipelineConfig()
        self.preprocessor = ImagePreprocessor()
        self.ocr_engine = OCREngine(
            tesseract_path=self.config.tesseract_path,
            language=self.config.ocr_language,
        )
        self.grammar_enhancer = GrammarEnhancer()
        self.readability_optimizer = ReadabilityOptimizer()
        self.summarizer = Summarizer()
        self.formatter = DocumentFormatter()
        self.plagiarism_checker = PlagiarismChecker(
            similarity_threshold=self.config.similarity_threshold,
        )
        self.paraphraser = Paraphraser()
        self._progress_callback: Optional[ProgressCallback] = None
        self._cancelled = False

    def set_progress_callback(self, callback: ProgressCallback) -> None:
        self._progress_callback = callback

    def cancel(self) -> None:
        self._cancelled = True

    def _notify(self, stage: PipelineStage, progress: float,
                message: str = "") -> None:
        if self._progress_callback:
            self._progress_callback(stage, progress, message)

    def _check_cancelled(self) -> None:
        if self._cancelled:
            raise InterruptedError("Pipeline cancelled by user")

    # ── Enhancement stages (shared between single- and multi-page) ──

    def _enhance_text(self, text: str,
                      document: Document) -> str:
        """Run grammar, readability, summarization, plagiarism, paraphrasing,
        and formatting stages on extracted text. Returns the enhanced text.

        Each stage is wrapped in its own try/except so that a failure in one
        stage (e.g. LanguageTool not available) does not prevent the remaining
        stages from running.
        """
        current_text = text

        if self.config.enable_grammar:
            self._check_cancelled()
            document.processing_state.begin_stage(PipelineStage.GRAMMAR)
            if document.status == DocumentStatus.OCR_PROCESSING:
                document.update_status(DocumentStatus.ENHANCING)
            self._notify(PipelineStage.GRAMMAR, 0, "Checking grammar...")
            try:
                grammar_result = self.grammar_enhancer.enhance(current_text)
                current_text = grammar_result.corrected_text

                from app.models.document import GrammarCorrection
                for c in grammar_result.corrections:
                    document.add_grammar_correction(GrammarCorrection(
                        original=c.original,
                        corrected=c.corrected,
                        rule_id=c.rule_id,
                        message=c.message,
                        offset=c.offset,
                        length=c.length,
                        category=c.category,
                    ))

                document.processing_state.complete_stage(PipelineStage.GRAMMAR, {
                    "corrections": grammar_result.total_errors,
                    "categories": grammar_result.categories,
                    "correction_details": [
                        {
                            "original": c.original,
                            "corrected": c.corrected,
                            "message": c.message,
                            "category": c.category,
                            "context": c.context,
                        }
                        for c in grammar_result.corrections
                    ],
                })
                self._notify(
                    PipelineStage.GRAMMAR, 100,
                    f"Grammar: {grammar_result.total_errors} corrections",
                )
            except InterruptedError:
                raise
            except Exception as e:
                logger.error("Grammar stage failed: %s", e)
                document.processing_state.record_error(
                    PipelineStage.GRAMMAR, str(e),
                )
                self._notify(PipelineStage.GRAMMAR, 100, "Grammar check failed")

        if document.status == DocumentStatus.OCR_PROCESSING:
            document.update_status(DocumentStatus.ENHANCING)

        if self.config.enable_readability:
            self._check_cancelled()
            document.processing_state.begin_stage(PipelineStage.READABILITY)
            self._notify(
                PipelineStage.READABILITY, 0, "Optimizing readability...",
            )
            try:
                readability_result = self.readability_optimizer.optimize(
                    current_text,
                    target_grade=self.config.target_readability_grade,
                )
                current_text = readability_result.optimized_text
                document.set_readability_score(
                    max(0, min(
                        100,
                        readability_result.optimized_metrics.flesch_reading_ease,
                    )),
                )
                document.processing_state.complete_stage(
                    PipelineStage.READABILITY, {
                        "flesch_kincaid_grade": (
                            readability_result.optimized_metrics.flesch_kincaid_grade
                        ),
                        "changes": len(readability_result.changes_made),
                    },
                )
                self._notify(
                    PipelineStage.READABILITY, 100, "Readability optimized",
                )
            except InterruptedError:
                raise
            except Exception as e:
                logger.error("Readability stage failed: %s", e)
                document.processing_state.record_error(
                    PipelineStage.READABILITY, str(e),
                )
                self._notify(PipelineStage.READABILITY, 100, "Readability failed")

        document.set_enhanced_text(current_text)

        if self.config.enable_summarization:
            self._check_cancelled()
            document.processing_state.begin_stage(PipelineStage.SUMMARIZATION)
            self._notify(PipelineStage.SUMMARIZATION, 0, "Summarizing...")
            try:
                summary_result = self.summarizer.summarize(
                    current_text,
                    method=self.config.summarization_method,
                    sentence_count=self.config.summary_sentences,
                )
                document.set_summary(summary_result.summary)
                document.processing_state.complete_stage(
                    PipelineStage.SUMMARIZATION, {
                        "method": summary_result.method,
                        "compression_ratio": summary_result.compression_ratio,
                    },
                )
                self._notify(
                    PipelineStage.SUMMARIZATION, 100, "Summarization complete",
                )
            except InterruptedError:
                raise
            except Exception as e:
                logger.error("Summarization stage failed: %s", e)
                document.processing_state.record_error(
                    PipelineStage.SUMMARIZATION, str(e),
                )
                self._notify(
                    PipelineStage.SUMMARIZATION, 100, "Summarization failed",
                )

        if self.config.enable_plagiarism:
            self._check_cancelled()
            document.processing_state.begin_stage(PipelineStage.PLAGIARISM_CHECK)
            self._notify(
                PipelineStage.PLAGIARISM_CHECK, 0, "Checking plagiarism...",
            )
            try:
                plag_result = self.plagiarism_checker.check(current_text)
                document.set_plagiarism_score(plag_result.overall_score)
                document.processing_state.complete_stage(
                    PipelineStage.PLAGIARISM_CHECK, {
                        "overall_score": plag_result.overall_score,
                        "matches": len(plag_result.matches),
                    },
                )
                self._notify(
                    PipelineStage.PLAGIARISM_CHECK, 100,
                    f"Plagiarism: {plag_result.overall_score:.1f}%",
                )

                if (
                    self.config.enable_paraphrasing
                    and plag_result.flagged_sentences
                ):
                    self._check_cancelled()
                    document.processing_state.begin_stage(PipelineStage.PARAPHRASING)
                    self._notify(
                        PipelineStage.PARAPHRASING, 0,
                        "Generating paraphrases...",
                    )
                    paraphrase_results = self.paraphraser.paraphrase_flagged(
                        plag_result.flagged_sentences,
                        num_suggestions=self.config.num_paraphrase_suggestions,
                    )
                    document.processing_state.complete_stage(
                        PipelineStage.PARAPHRASING, {
                            "passages_paraphrased": len(paraphrase_results),
                        },
                    )
                    self._notify(
                        PipelineStage.PARAPHRASING, 100, "Paraphrasing complete",
                    )
            except InterruptedError:
                raise
            except Exception as e:
                logger.error("Plagiarism/paraphrasing stage failed: %s", e)
                document.processing_state.record_error(
                    PipelineStage.PLAGIARISM_CHECK, str(e),
                )
                self._notify(
                    PipelineStage.PLAGIARISM_CHECK, 100, "Plagiarism check failed",
                )

        if self.config.enable_formatting:
            self._check_cancelled()
            document.processing_state.begin_stage(PipelineStage.FORMATTING)
            self._notify(
                PipelineStage.FORMATTING, 0, "Detecting document type...",
            )
            detected_type = self.formatter.detect_type(current_text)
            try:
                document.doc_type = DocumentType(detected_type)
            except ValueError:
                document.doc_type = DocumentType.ESSAY
            document.processing_state.complete_stage(
                PipelineStage.FORMATTING, {"detected_type": detected_type},
            )
            self._notify(
                PipelineStage.FORMATTING, 100, f"Type: {detected_type}",
            )

        return current_text

    # ── Public entry points ──

    def process_image(self, image: np.ndarray,
                      document: Document) -> Document:
        """Run the full pipeline on a single image."""
        self._cancelled = False
        document.processing_state = ProcessingState()

        try:
            self._check_cancelled()
            document.processing_state.begin_stage(PipelineStage.PREPROCESSING)
            document.update_status(DocumentStatus.PREPROCESSING)
            self._notify(
                PipelineStage.PREPROCESSING, 0, "Preprocessing image...",
            )
            preprocessed = self.preprocessor.preprocess(
                image, apply_threshold=self.config.apply_threshold,
            )
            document.processing_state.complete_stage(
                PipelineStage.PREPROCESSING,
            )
            self._notify(
                PipelineStage.PREPROCESSING, 100, "Preprocessing complete",
            )

            self._check_cancelled()
            document.processing_state.begin_stage(PipelineStage.OCR)
            document.update_status(DocumentStatus.OCR_PROCESSING)
            self._notify(PipelineStage.OCR, 0, "Extracting text...")
            ocr_result = self.ocr_engine.extract_text(preprocessed)
            document.set_ocr_result(ocr_result.text, ocr_result.confidence)
            document.processing_state.complete_stage(PipelineStage.OCR, {
                "confidence": ocr_result.confidence,
                "word_count": len(ocr_result.text.split()),
            })
            self._notify(
                PipelineStage.OCR, 100,
                f"OCR complete (confidence: {ocr_result.confidence:.1f}%)",
            )

            self._enhance_text(ocr_result.text, document)

            document.update_status(DocumentStatus.COMPLETED)
            document.processing_state.mark_finished()
            logger.info("Pipeline complete for %s", document.filename)

        except InterruptedError:
            logger.warning("Pipeline cancelled for %s", document.filename)
            document.processing_state.record_error(
                document.processing_state.current_stage
                or PipelineStage.PREPROCESSING,
                "Cancelled by user",
            )
        except Exception as e:
            logger.error("Pipeline error for %s: %s", document.filename, e)
            stage = (
                document.processing_state.current_stage
                or PipelineStage.PREPROCESSING
            )
            document.processing_state.record_error(stage, str(e))
            try:
                document.update_status(DocumentStatus.FAILED)
            except ValueError:
                pass

        return document

    def process_images(self, images: List[np.ndarray],
                       document: Document) -> Document:
        """Process multiple page images (batch OCR then enhance combined text)."""
        self._cancelled = False
        document.processing_state = ProcessingState()

        try:
            self._check_cancelled()
            document.processing_state.begin_stage(PipelineStage.PREPROCESSING)
            document.update_status(DocumentStatus.PREPROCESSING)
            self._notify(
                PipelineStage.PREPROCESSING, 0,
                f"Preprocessing {len(images)} pages...",
            )
            preprocessed_images = [
                self.preprocessor.preprocess(
                    img, apply_threshold=self.config.apply_threshold,
                )
                for img in images
            ]
            document.processing_state.complete_stage(
                PipelineStage.PREPROCESSING,
            )
            self._notify(
                PipelineStage.PREPROCESSING, 100, "Preprocessing complete",
            )

            self._check_cancelled()
            document.processing_state.begin_stage(PipelineStage.OCR)
            document.update_status(DocumentStatus.OCR_PROCESSING)
            self._notify(PipelineStage.OCR, 0, "Batch OCR in progress...")
            ocr_results = self.ocr_engine.batch_extract(preprocessed_images)
            combined_text = "\n\n".join(r.text for r in ocr_results)
            avg_conf = (
                sum(r.confidence for r in ocr_results) / len(ocr_results)
                if ocr_results else 0
            )
            document.set_ocr_result(combined_text, avg_conf)
            document.num_pages = len(images)
            document.processing_state.complete_stage(PipelineStage.OCR, {
                "pages": len(ocr_results),
                "avg_confidence": round(avg_conf, 2),
            })
            self._notify(
                PipelineStage.OCR, 100,
                f"OCR complete ({len(ocr_results)} pages, "
                f"avg confidence: {avg_conf:.1f}%)",
            )

            self._enhance_text(combined_text, document)

            document.update_status(DocumentStatus.COMPLETED)
            document.processing_state.mark_finished()
            logger.info("Pipeline complete for %s", document.filename)

        except InterruptedError:
            logger.warning("Pipeline cancelled for %s", document.filename)
            document.processing_state.record_error(
                document.processing_state.current_stage
                or PipelineStage.PREPROCESSING,
                "Cancelled by user",
            )
        except Exception as e:
            logger.error("Pipeline error: %s", e)
            stage = (
                document.processing_state.current_stage
                or PipelineStage.PREPROCESSING
            )
            document.processing_state.record_error(stage, str(e))
            try:
                document.update_status(DocumentStatus.FAILED)
            except ValueError:
                pass

        return document
