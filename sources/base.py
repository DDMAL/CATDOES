"""Shared folio utilities and Source protocol for image fetch/rename sources."""

import re
from typing import NamedTuple, Protocol


class FolioParseResult(NamedTuple):
    num: int
    side: str  # "r", "v", or "" (page-numbered source, no recto/verso)


def parse_folio_label(label: str) -> "FolioParseResult | None":
    """Parse a folio label into (num, side), ignoring zero-padding.

    Accepts '2v', '002v', '1', '001', '63r'. Returns None for labels that
    don't match the expected pattern (roman numerals, 'Binding', etc.).
    """
    m = re.match(r"^(\d+)([rv]?)$", label.strip().lower())
    return FolioParseResult(int(m.group(1)), m.group(2)) if m else None


def folios_match(cantus_folio: str, source_label: str) -> bool:
    """True if cantus_folio and source_label refer to the same folio.

    Ignores zero-padding: '001r' matches '1r'; '001' matches '1'.
    Side must agree: '001r' does NOT match '001' or '001v'.
    """
    a = parse_folio_label(cantus_folio)
    b = parse_folio_label(source_label)
    return a is not None and b is not None and a == b


class Source(Protocol):
    """Interface for a manuscript image source (e-codices, Gallica, etc.)."""

    def folio_from_filename(self, filename: str) -> "str | None":
        """Return the raw folio label embedded in a browser-downloaded filename.

        Returns None if the filename doesn't match this source's pattern.
        """
        ...

    def manifest_url(self, code: str) -> str:
        """Construct the IIIF manifest URL for a manuscript code string."""
        ...

    def canvases(self, manifest: dict) -> "list[dict]":
        """Return the ordered list of canvas objects from a parsed manifest."""
        ...

    def canvas_folio_label(self, canvas: dict) -> "str | None":
        """Return the raw folio label from a canvas (may be unpadded, e.g. '2v')."""
        ...

    def canvas_image_url(self, canvas: dict, size: str = "full") -> "str | None":
        """Return a download URL for a canvas image at the requested IIIF size.

        size is a IIIF Image API size string: 'full' or '!w,h' (e.g. '!1218,1624').
        Sources that don't support IIIF sizing may ignore the parameter and always
        return the full-size URL.
        """
        ...
