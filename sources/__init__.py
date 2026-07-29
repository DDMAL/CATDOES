"""Manuscript image source adapters."""

from sources.base import FolioParseResult, Source, folios_match, parse_folio_label
from sources.ecodices import ECodiciesSource

__all__ = [
    "ECodiciesSource",
    "FolioParseResult",
    "Source",
    "folios_match",
    "parse_folio_label",
]
