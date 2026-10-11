"""Bound outgoing context without changing private evidence or original offsets."""

from dataclasses import dataclass

from filingguard.modules.privacy.service import MaskedExcerpt, mask_excerpt

MAX_FILING_PASSAGE = 8000
MAX_SOURCE_PASSAGE = 12000


@dataclass(frozen=True)
class ProviderPassage:
    text: str
    original_start: int
    original_end: int
    requested_end: int
    truncated: bool
    masking: MaskedExcerpt | None = None


def prepare_passage(
    text: str,
    start: int,
    end: int,
    *,
    filing: bool,
) -> ProviderPassage:
    if (
        not isinstance(text, str)
        or type(start) is not int
        or type(end) is not int
        or not 0 <= start < end <= len(text)
        or type(filing) is not bool
        or (filing and len(text) > 100000)
    ):
        raise ValueError("Invalid provider passage boundary")
    limit = MAX_FILING_PASSAGE if filing else MAX_SOURCE_PASSAGE
    clipped = min(end, start + limit)
    masked = mask_excerpt(text, start, clipped) if filing else None
    return ProviderPassage(
        text=masked.text if masked else text[start:clipped],
        original_start=start,
        original_end=clipped,
        requested_end=end,
        truncated=clipped < end,
        masking=masked,
    )
