"""Text summarization module supporting extractive and abstractive methods.

Extractive summarization uses LSA via sumy. Abstractive summarization
uses DistilBART (sshleifer/distilbart-cnn-12-6). Both methods support
configurable length and key-point extraction.
"""

import logging
from dataclasses import dataclass, field
from typing import List

logger = logging.getLogger(__name__)


@dataclass
class SummaryResult:
    original_text: str
    summary: str
    key_points: List[str] = field(default_factory=list)
    method: str = "extractive"
    compression_ratio: float = 0.0
    original_word_count: int = 0
    summary_word_count: int = 0


class Summarizer:
    """Provides extractive (LSA) and abstractive (DistilBART) summarization."""

    def __init__(self):
        self._abstractive_model = None
        self._abstractive_tokenizer = None

    def extractive(self, text: str, sentence_count: int = 5) -> SummaryResult:
        from sumy.nlp.tokenizers import Tokenizer
        from sumy.parsers.plaintext import PlaintextParser
        from sumy.summarizers.lsa import LsaSummarizer

        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = LsaSummarizer()
        sentences = summarizer(parser.document, sentence_count)
        summary = " ".join(str(s) for s in sentences)

        orig_words = len(text.split())
        summ_words = len(summary.split())

        return SummaryResult(
            original_text=text,
            summary=summary,
            method="extractive",
            compression_ratio=(
                round(summ_words / orig_words, 3) if orig_words else 0.0
            ),
            original_word_count=orig_words,
            summary_word_count=summ_words,
        )

    def _load_abstractive_model(self):
        if self._abstractive_model is None:
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

            model_name = "sshleifer/distilbart-cnn-12-6"
            logger.info(
                "Loading abstractive summarization model: %s", model_name,
            )
            self._abstractive_tokenizer = AutoTokenizer.from_pretrained(
                model_name,
            )
            self._abstractive_model = AutoModelForSeq2SeqLM.from_pretrained(
                model_name,
            )

    def abstractive(self, text: str, max_length: int = 150,
                    min_length: int = 40) -> SummaryResult:
        self._load_abstractive_model()

        inputs = self._abstractive_tokenizer(
            text, return_tensors="pt", max_length=1024, truncation=True,
        )
        summary_ids = self._abstractive_model.generate(
            inputs["input_ids"],
            max_length=max_length,
            min_length=min_length,
            length_penalty=2.0,
            num_beams=4,
            early_stopping=True,
        )
        summary = self._abstractive_tokenizer.decode(
            summary_ids[0], skip_special_tokens=True,
        )

        orig_words = len(text.split())
        summ_words = len(summary.split())

        return SummaryResult(
            original_text=text,
            summary=summary,
            method="abstractive",
            compression_ratio=(
                round(summ_words / orig_words, 3) if orig_words else 0.0
            ),
            original_word_count=orig_words,
            summary_word_count=summ_words,
        )

    def extract_key_points(self, text: str,
                           num_points: int = 5) -> List[str]:
        from sumy.nlp.tokenizers import Tokenizer
        from sumy.parsers.plaintext import PlaintextParser
        from sumy.summarizers.lsa import LsaSummarizer

        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = LsaSummarizer()
        sentences = summarizer(parser.document, num_points)
        return [str(s).strip() for s in sentences]

    def summarize(self, text: str, method: str = "extractive",
                  sentence_count: int = 5, max_length: int = 150,
                  min_length: int = 40,
                  num_key_points: int = 5) -> SummaryResult:
        """Unified summarization entry point with key-point extraction."""
        if method == "abstractive":
            result = self.abstractive(
                text, max_length=max_length, min_length=min_length,
            )
        else:
            result = self.extractive(text, sentence_count=sentence_count)

        result.key_points = self.extract_key_points(
            text, num_points=num_key_points,
        )

        logger.info(
            "Summarization (%s): %d -> %d words (%.1f%% compression)",
            method, result.original_word_count, result.summary_word_count,
            result.compression_ratio * 100,
        )
        return result
