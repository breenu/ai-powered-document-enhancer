"""Readability optimization module using textstat metrics.

Provides Flesch-Kincaid scoring, comprehensive readability metrics,
and rule-based text simplification (vocabulary + sentence splitting).
"""

import logging
import re
from dataclasses import dataclass, field
from typing import List

logger = logging.getLogger(__name__)


@dataclass
class ReadabilityMetrics:
    flesch_reading_ease: float = 0.0
    flesch_kincaid_grade: float = 0.0
    gunning_fog: float = 0.0
    smog_index: float = 0.0
    coleman_liau: float = 0.0
    automated_readability: float = 0.0
    dale_chall: float = 0.0
    text_standard: str = ""
    word_count: int = 0
    sentence_count: int = 0
    avg_sentence_length: float = 0.0


@dataclass
class ReadabilityResult:
    original_text: str
    optimized_text: str
    original_metrics: ReadabilityMetrics = field(default_factory=ReadabilityMetrics)
    optimized_metrics: ReadabilityMetrics = field(default_factory=ReadabilityMetrics)
    changes_made: List[str] = field(default_factory=list)


class ReadabilityOptimizer:
    """Analyzes and optimizes text readability using textstat metrics."""

    COMPLEX_WORDS = {
        "utilize": "use",
        "implement": "set up",
        "subsequently": "then",
        "consequently": "so",
        "furthermore": "also",
        "nevertheless": "still",
        "approximately": "about",
        "demonstrate": "show",
        "facilitate": "help",
        "commence": "start",
        "terminate": "end",
        "endeavor": "try",
        "ascertain": "find out",
        "disseminate": "spread",
        "substantiate": "prove",
        "ameliorate": "improve",
        "precipitate": "cause",
        "necessitate": "require",
        "promulgate": "announce",
        "elucidate": "explain",
    }

    def analyze(self, text: str) -> ReadabilityMetrics:
        import textstat

        return ReadabilityMetrics(
            flesch_reading_ease=textstat.flesch_reading_ease(text),
            flesch_kincaid_grade=textstat.flesch_kincaid_grade(text),
            gunning_fog=textstat.gunning_fog(text),
            smog_index=textstat.smog_index(text),
            coleman_liau=textstat.coleman_liau_index(text),
            automated_readability=textstat.automated_readability_index(text),
            dale_chall=textstat.dale_chall_readability_score(text),
            text_standard=textstat.text_standard(text, float_output=False),
            word_count=textstat.lexicon_count(text, removepunct=True),
            sentence_count=textstat.sentence_count(text),
            avg_sentence_length=textstat.avg_sentence_length(text),
        )

    def simplify_vocabulary(self, text: str) -> tuple:
        changes: List[str] = []
        result = text
        for complex_word, simple_word in self.COMPLEX_WORDS.items():
            pattern = re.compile(rf"\b{complex_word}\b", re.IGNORECASE)
            if pattern.search(result):
                result = pattern.sub(simple_word, result)
                changes.append(
                    f"Replaced '{complex_word}' with '{simple_word}'"
                )
        return result, changes

    def split_long_sentences(self, text: str,
                             max_words: int = 35) -> tuple:
        """Split sentences exceeding max_words at conjunction boundaries."""
        sentences = re.split(r"(?<=[.!?])\s+", text)
        new_sentences: List[str] = []
        changes: List[str] = []

        conjunctions = (
            r"\b(and|but|however|moreover|furthermore|although|whereas)\b"
        )

        for sentence in sentences:
            words = sentence.split()
            if len(words) > max_words:
                parts = re.split(
                    f"({conjunctions})", sentence, flags=re.IGNORECASE,
                )
                if len(parts) > 1:
                    rebuilt: List[str] = []
                    current = ""
                    for part in parts:
                        if (
                            re.match(conjunctions, part.strip(), re.IGNORECASE)
                            and len(current.split()) > 10
                        ):
                            rebuilt.append(
                                current.strip().rstrip(",").rstrip(";") + "."
                            )
                            current = part.strip().capitalize() + " "
                        else:
                            current += part
                    if current.strip():
                        final = current.strip()
                        if not final.endswith((".", "!", "?")):
                            final += "."
                        rebuilt.append(final)
                    new_sentences.extend(rebuilt)
                    changes.append(
                        f"Split long sentence ({len(words)} words)"
                    )
                else:
                    new_sentences.append(sentence)
            else:
                new_sentences.append(sentence)

        return " ".join(new_sentences), changes

    def detect_passive_voice(self, text: str) -> tuple:
        """Flag passive voice constructions (heuristic detection)."""
        changes: List[str] = []
        passive_pattern = re.compile(
            r"\b(is|are|was|were|been|being)\s+(being\s+)?(\w+ed)\b",
            re.IGNORECASE,
        )
        for match in passive_pattern.finditer(text):
            changes.append(f"Possible passive voice: '{match.group()}'")
        return text, changes

    def optimize(self, text: str,
                 target_grade: float = 10.0) -> ReadabilityResult:
        original_metrics = self.analyze(text)
        optimized = text
        all_changes: List[str] = []

        optimized, vocab_changes = self.simplify_vocabulary(optimized)
        all_changes.extend(vocab_changes)

        optimized, split_changes = self.split_long_sentences(optimized)
        all_changes.extend(split_changes)

        _, passive_changes = self.detect_passive_voice(optimized)
        all_changes.extend(passive_changes)

        optimized_metrics = (
            self.analyze(optimized) if all_changes else original_metrics
        )

        logger.info(
            "Readability: %.1f -> %.1f (Flesch-Kincaid Grade)",
            original_metrics.flesch_kincaid_grade,
            optimized_metrics.flesch_kincaid_grade,
        )

        return ReadabilityResult(
            original_text=text,
            optimized_text=optimized,
            original_metrics=original_metrics,
            optimized_metrics=optimized_metrics,
            changes_made=all_changes,
        )
