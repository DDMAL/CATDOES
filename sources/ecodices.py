"""e-codices (https://www.e-codices.unifr.ch) image source."""

import re

_MANIFEST_URL = "https://www.e-codices.unifr.ch/metadata/iiif/{code}/manifest.json"

# Matches browser-downloaded filenames: e-codices_sbe-0611_001r_medium.jpg
_BROWSER_RE = re.compile(
    r"^e-codices_[^_]+_([^_]+)_[^.]+\.(jpg|jpeg)$",
    re.IGNORECASE,
)


class ECodiciesSource:
    """Source adapter for the e-codices Swiss manuscript repository."""

    def folio_from_filename(self, filename: str) -> "str | None":
        m = _BROWSER_RE.match(filename)
        return m.group(1) if m else None

    def manifest_url(self, code: str) -> str:
        return _MANIFEST_URL.format(code=code)

    def canvases(self, manifest: dict) -> "list[dict]":
        try:
            return manifest["sequences"][0]["canvases"]
        except (KeyError, IndexError):
            return []

    def canvas_folio_label(self, canvas: dict) -> "str | None":
        label = canvas.get("label")
        return str(label).strip() if label is not None else None

    def canvas_image_url(self, canvas: dict, size: str = "full") -> "str | None":
        try:
            service_base = canvas["images"][0]["resource"]["service"]["@id"]
        except (KeyError, IndexError):
            return None
        return f"{service_base}/full/{size}/0/default.jpg"
