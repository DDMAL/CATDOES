#!/usr/bin/env python3
"""Fetch or rename folio images so they are correctly named for run_chain.py.

run_chain.py expects images named {anything}_{folio_id}.{ext}, where folio_id
exactly matches the folio column in the CantusDB CSV for the target source.
This tool produces correctly-named files from e-codices (and future sources).

Two subcommands
---------------
fetch   Download folio images directly from a IIIF manifest, already named
        correctly. The CantusDB CSV for --source-id determines which canvases
        to download and what to name them.

rename  Rename (or copy) images already downloaded via a browser. The same
        CantusDB CSV determines canonical folio IDs and the output prefix.

Examples
--------
# Download all folios for a manuscript:
python fetch_images.py fetch \\
    --source ecodices --code sbe-0611 --source-id 678936 \\
    --out-dir ~/Downloads/DDMAL/einsiedeln-611/

# Rename browser-downloaded e-codices images:
python fetch_images.py rename \\
    --source ecodices --source-id 678936 \\
    --input-dir ~/Downloads/e-codices-sbe-0611/ \\
    --out-dir ~/Downloads/DDMAL/einsiedeln-611/
"""

import argparse
import csv
import io
import json
import logging
import re
import shutil
import sys
import urllib.request
from pathlib import Path

from sources.base import folios_match, parse_folio_label
from sources.ecodices import ECodiciesSource

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}
CANTUS_CSV_URL = "https://cantusdatabase.org/source/{source_id}/csv/"

# Maps --size flag values to IIIF Image API size strings.
# Dimensions match the e-codices download options.
SIZE_MAP = {
    "small":  "!609,812",
    "medium": "!1218,1624",
    "large":  "!2436,3248",
    "full":   "full",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fetch_url_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "CATDOES/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def _fetch_cantus_rows(source_id: int) -> "list[dict]":
    """Fetch the CantusDB CSV and return all rows as dicts."""
    url = CANTUS_CSV_URL.format(source_id=source_id)
    logging.getLogger(__name__).info("Fetching CantusDB CSV: %s", url)
    try:
        data = _fetch_url_bytes(url)
    except Exception as e:
        print(
            f"Error: could not fetch CantusDB CSV for source {source_id}: {e}",
            file=sys.stderr,
        )
        sys.exit(1)
    rows = list(csv.DictReader(io.StringIO(data.decode("utf-8-sig"))))
    if not rows:
        print(
            f"Error: CantusDB CSV for source {source_id} is empty.",
            file=sys.stderr,
        )
        sys.exit(1)
    return rows


def _folios_from_rows(rows: "list[dict]") -> "list[str]":
    """Extract unique ordered folio IDs from CantusDB rows."""
    seen: dict[str, None] = {}  # ordered set via dict
    for row in rows:
        folio = row.get("folio", "").strip()
        if folio:
            seen[folio] = None
    if not seen:
        print("Error: CantusDB CSV has no folio values.", file=sys.stderr)
        sys.exit(1)
    return list(seen)


def _make_prefix_from_rows(rows: "list[dict]") -> str:
    """Derive a manuscript prefix from CantusDB rows.

    Replicates the institution+shelfmark logic of mothra-text's
    make_output_stem() (steps/gt_manifest.py), producing e.g. 'CH-E_611':
      holding_institution: 'Einsiedeln, Stiftsbibliothek (CH-E)'
      shelfmark:           '611'
    """
    row = rows[0]
    m = re.search(
        r"\(([^)]+)\)$", row.get("holding_institution", "").strip()
    )
    institution = (
        m.group(1) if m else row.get("holding_institution", "").strip()
    )
    institution = institution.replace(" ", "_")
    shelfmark = (
        re.sub(r"\s*\([^)]*\)", "", row.get("shelfmark", ""))
        .strip()
        .replace(" ", "_")
    )
    return f"{institution}_{shelfmark}"


def _safe_output_path(out_dir: Path, name: str) -> "Path | None":
    """Return output path, or None (with a warning) if it already exists."""
    dest = out_dir / name
    if dest.exists():
        logging.getLogger(__name__).warning(
            "Skipping %s — file already exists.", dest
        )
        return None
    return dest


# ---------------------------------------------------------------------------
# fetch subcommand
# ---------------------------------------------------------------------------

def _cmd_fetch(args: argparse.Namespace) -> None:
    logger = logging.getLogger(__name__)
    source = ECodiciesSource()

    csv_rows = _fetch_cantus_rows(args.source_id)
    cantus_folios = _folios_from_rows(csv_rows)
    logger.info(
        "CantusDB folios for source %d: %d unique IDs",
        args.source_id, len(cantus_folios),
    )

    target_folios = args.folios if args.folios else cantus_folios
    if args.folios:
        logger.info("Processing subset: %s", ", ".join(target_folios))

    prefix = args.prefix or _make_prefix_from_rows(csv_rows)
    logger.info("Prefix: %s", prefix)

    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest_url = source.manifest_url(args.code)
    logger.info("Fetching manifest: %s", manifest_url)
    try:
        manifest = json.loads(_fetch_url_bytes(manifest_url))
    except Exception as e:
        print(f"Error: could not fetch manifest: {e}", file=sys.stderr)
        sys.exit(1)

    canvases = source.canvases(manifest)
    if not canvases:
        print("Error: no canvases found in manifest.", file=sys.stderr)
        sys.exit(1)
    logger.info("Manifest has %d canvas(es).", len(canvases))

    matched: set[str] = set()
    explicit_mode = bool(args.folios)
    target_set = set(target_folios)
    skipped_irregular = 0
    downloaded = 0

    for canvas in canvases:
        if explicit_mode and matched >= target_set:
            break  # all requested folios found, no need to scan further

        raw_label = source.canvas_folio_label(canvas)
        if raw_label is None:
            skipped_irregular += 1
            continue

        if parse_folio_label(raw_label) is None:
            if not explicit_mode:
                logger.warning(
                    "Skipping canvas with unrecognised label: %r", raw_label
                )
            skipped_irregular += 1
            continue

        folio_id = next(
            (cf for cf in target_folios if folios_match(cf, raw_label)), None
        )
        if folio_id is None:
            if not explicit_mode:
                logger.warning(
                    "Canvas label %r has no matching CantusDB folio — "
                    "skipping (irregular page: flyleaf, binding, etc.).",
                    raw_label,
                )
            skipped_irregular += 1
            continue

        if folio_id in matched:
            logger.warning(
                "Duplicate match for folio %r — skipping second canvas.",
                folio_id,
            )
            continue

        img_url = source.canvas_image_url(canvas, size=SIZE_MAP[args.size])
        if img_url is None:
            logger.warning(
                "No image URL for canvas with label %r — skipping.",
                raw_label,
            )
            continue

        dest = _safe_output_path(out_dir, f"{prefix}_{folio_id}.jpg")
        if dest is None:
            matched.add(folio_id)
            continue

        logger.info("  %s → %s", raw_label, dest.name)
        try:
            dest.write_bytes(_fetch_url_bytes(img_url))
        except Exception as e:
            logger.error("Failed to download %s: %s", img_url, e)
            continue

        matched.add(folio_id)
        downloaded += 1

    logger.info("Downloaded %d image(s) to %s", downloaded, out_dir)
    if skipped_irregular:
        logger.info(
            "Skipped %d canvas(es) with irregular/unmatched labels.",
            skipped_irregular,
        )

    missing = [cf for cf in target_folios if cf not in matched]
    if missing:
        print(
            f"\nWarning: {len(missing)} folio(s) not found in manifest:",
            file=sys.stderr,
        )
        for m in missing:
            print(f"  {m}", file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------------------
# rename subcommand
# ---------------------------------------------------------------------------

def _cmd_rename(args: argparse.Namespace) -> None:
    logger = logging.getLogger(__name__)
    source = ECodiciesSource()

    csv_rows = _fetch_cantus_rows(args.source_id)
    cantus_folios = _folios_from_rows(csv_rows)
    logger.info(
        "CantusDB folios for source %d: %d unique IDs",
        args.source_id, len(cantus_folios),
    )

    target_folios = args.folios if args.folios else cantus_folios
    if args.folios:
        logger.info("Processing subset: %s", ", ".join(target_folios))

    prefix = args.prefix or _make_prefix_from_rows(csv_rows)
    logger.info("Prefix: %s", prefix)

    input_dir = Path(args.input_dir).expanduser().resolve()
    if not input_dir.is_dir():
        print(
            f"Error: --input-dir is not a directory: {input_dir}",
            file=sys.stderr,
        )
        sys.exit(1)

    image_files = [
        f for f in input_dir.iterdir() if f.suffix.lower() in IMAGE_EXTS
    ]
    if not image_files:
        print(f"Error: no image files found in {input_dir}", file=sys.stderr)
        sys.exit(1)

    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    matched: set[str] = set()
    processed = 0
    skipped_unrecognised = 0

    for img in image_files:
        raw_label = source.folio_from_filename(img.name)
        if raw_label is None:
            logger.warning("Skipping unrecognised filename: %s", img.name)
            skipped_unrecognised += 1
            continue

        if parse_folio_label(raw_label) is None:
            logger.warning(
                "Skipping %s — label %r is not a recognised folio format.",
                img.name, raw_label,
            )
            skipped_unrecognised += 1
            continue

        folio_id = next(
            (cf for cf in target_folios if folios_match(cf, raw_label)), None
        )
        if folio_id is None:
            logger.warning(
                "No CantusDB match for label %r in %s — skipping.",
                raw_label, img.name,
            )
            skipped_unrecognised += 1
            continue

        if folio_id in matched:
            logger.warning(
                "Duplicate match for folio %r — skipping %s.",
                folio_id, img.name,
            )
            continue

        dest = _safe_output_path(
            out_dir, f"{prefix}_{folio_id}{img.suffix.lower()}"
        )
        if dest is None:
            matched.add(folio_id)
            continue

        logger.info("  %s → %s", img.name, dest.name)
        if args.move:
            shutil.move(str(img), dest)
        else:
            shutil.copy2(img, dest)
        matched.add(folio_id)
        processed += 1

    action = "Moved" if args.move else "Copied"
    logger.info("%s %d image(s) to %s", action, processed, out_dir)
    if skipped_unrecognised:
        logger.info(
            "Skipped %d file(s) with unrecognised filenames or labels.",
            skipped_unrecognised,
        )

    missing = [cf for cf in target_folios if cf not in matched]
    if missing:
        print(
            f"\nWarning: {len(missing)} folio(s) not found in {input_dir}:",
            file=sys.stderr,
        )
        for m in missing:
            print(f"  {m}", file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch or rename folio images for use with run_chain.py.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="subcommand", required=True)

    def _add_shared(p: argparse.ArgumentParser) -> None:
        p.add_argument(
            "--source-id", required=True, type=int, metavar="INT",
            help="Cantus source ID. Used to fetch canonical folio IDs and "
                 "the manuscript prefix from cantusdatabase.org.",
        )
        p.add_argument(
            "--out-dir", required=True, metavar="PATH",
            help="Directory to write output images.",
        )
        p.add_argument(
            "--prefix", default=None, metavar="STR",
            help="Override the output filename prefix (default: derived from "
                 "CantusDB holding_institution + shelfmark, e.g. CH-E_611).",
        )
        p.add_argument(
            "--folios", nargs="+", metavar="FOLIO", default=None,
            help="Process only these folio IDs (CantusDB format, e.g. 063v "
                 "064r). Useful for testing. Omit to process all folios.",
        )

    # fetch subcommand
    p_fetch = sub.add_parser(
        "fetch",
        help="Download folio images from a IIIF manifest.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    _add_shared(p_fetch)
    p_fetch.add_argument(
        "--code", required=True, metavar="STR",
        help="Manuscript code for the IIIF manifest (e.g. sbe-0611). "
             "Visible in the e-codices URL: "
             "/en/list/one/sbe/0611 → sbe-0611.",
    )
    p_fetch.add_argument(
        "--size", default="full", choices=list(SIZE_MAP),
        help="Image size to download (default: full). "
             "small=609×812, medium=1218×1624, large=2436×3248, "
             "full=4872×6496.",
    )
    p_fetch.set_defaults(func=_cmd_fetch)

    # rename subcommand
    p_rename = sub.add_parser(
        "rename",
        help="Rename (or copy) browser-downloaded images to run_chain.py "
             "convention.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    _add_shared(p_rename)
    p_rename.add_argument(
        "--input-dir", required=True, metavar="PATH",
        help="Directory containing the browser-downloaded images to rename.",
    )
    p_rename.add_argument(
        "--move", action="store_true", default=False,
        help="Move files instead of copying (default: copy, non-destructive).",
    )
    p_rename.set_defaults(func=_cmd_rename)

    args = parser.parse_args()
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s %(message)s", force=True
    )
    args.func(args)


if __name__ == "__main__":
    main()
