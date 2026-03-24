"""Grammar enhancement module using LanguageTool.

Provides automated grammar and spelling correction with before/after
tracking for every correction applied.
"""

import logging
from dataclasses import dataclass, field
from typing import List

logger = logging.getLogger(__name__)


@dataclass
class Correction:
    """A single correction detected by LanguageTool."""
    original: str
    corrected: str
    rule_id: str
    message: str
    offset: int
    length: int
    category: str = ""
    context: str = ""


@dataclass
class GrammarResult:
    original_text: str
    corrected_text: str
    corrections: List[Correction] = field(default_factory=list)
    total_errors: int = 0

    @property
    def correction_count(self) -> int:
        return len(self.corrections)


class GrammarEnhancer:
    """Enhances text grammar and spelling using LanguageTool."""

    def __init__(self, language: str = "en-US"):
        self.language = language
        self._tool = None

    def _get_tool(self):
        if self._tool is None:
            import language_tool_python
            self._tool = language_tool_python.LanguageTool(self.language)
        return self._tool

    def check(self, text: str) -> GrammarResult:
        tool = self._get_tool()
        matches = tool.check(text)

        corrections: List[Correction] = []
        for match in matches:
            replacement = match.replacements[0] if match.replacements else ""
            original_fragment = text[match.offset:match.offset + match.errorLength]

            context_start = max(0, match.offset - 30)
            context_end = min(len(text), match.offset + match.errorLength + 30)

            corrections.append(Correction(
                original=original_fragment,
                corrected=replacement,
                rule_id=match.ruleId,
                message=match.message,
                offset=match.offset,
                length=match.errorLength,
                category=getattr(match, "category", ""),
                context=text[context_start:context_end],
            ))

        corrected_text = self._apply_corrections(text, corrections)

        return GrammarResult(
            original_text=text,
            corrected_text=corrected_text,
            corrections=corrections,
            total_errors=len(matches),
        )

    def _apply_corrections(self, text: str,
                           corrections: List[Correction]) -> str:
        sorted_corrections = sorted(
            corrections, key=lambda c: c.offset, reverse=True,
        )
        result = text
        for corr in sorted_corrections:
            if corr.corrected:
                result = (
                    result[:corr.offset]
                    + corr.corrected
                    + result[corr.offset + corr.length:]
                )
        return result

    def enhance(self, text: str, max_passes: int = 2) -> GrammarResult:
        """Run grammar checking with multiple passes for iterative improvement."""
        all_corrections: List[Correction] = []
        current_text = text

        for pass_num in range(max_passes):
            result = self.check(current_text)
            if not result.corrections:
                break
            all_corrections.extend(result.corrections)
            current_text = result.corrected_text
            logger.info(
                "Grammar pass %d: %d corrections",
                pass_num + 1, len(result.corrections),
            )

        return GrammarResult(
            original_text=text,
            corrected_text=current_text,
            corrections=all_corrections,
            total_errors=len(all_corrections),
        )

    def close(self) -> None:
        if self._tool is not None:
            self._tool.close()
            self._tool = None
