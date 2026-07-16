#!/usr/bin/env python3
"""CATDOES pipeline CLI: run the full pipeline on a directory of folio images.

Discovers all image files in --images, extracts folio IDs from filenames
(pattern: {anything}_{folio_id}.ext), sorts them, and chains FolioState
between consecutive contiguous folios.

Usage
-----
python run_chain.py \\
    --images path/to/image/directory \\
    --source-id 123672 \\
    [--out-dir path/to/output] \\
    [--debug]
"""

import argparse
import contextlib
import io
import logging
import re
import shutil
import sys
import tempfile
from pathlib import Path

from config import load_config

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}


def _find_tridis_model() -> "str | None":
    try:
        from platformdirs import user_data_dir
        htrmopo_dir = Path(user_data_dir("htrmopo"))
        matches = list(htrmopo_dir.glob("*/Tridis_Medieval_EarlyModern.mlmodel"))
        return str(matches[0]) if matches else None
    except Exception:
        return None


def _parse_folio_id(folio_id: str) -> "tuple[int | None, str | None]":
    """Parse folio_id into (number, side) for contiguity checking.

    Handles zero-padded (001r), non-padded (1r), and number-only (1) forms.
    Returns (None, None) if the format is unrecognised.
    """
    m = re.match(r"^(\d+)([rv]?)$", folio_id.lower())
    if not m:
        return None, None
    return int(m.group(1)), m.group(2) or None


def _are_contiguous(a: str, b: str) -> bool:
    """Return True if folio b directly follows folio a in manuscript sequence.

    NOTE: This is a heuristic. If it fails for an unusual naming convention,
    consider always running with prev_folio_state=None (no chaining) or
    ensuring all input folios are contiguous.
    """
    num_a, side_a = _parse_folio_id(a)
    num_b, side_b = _parse_folio_id(b)
    if num_a is None or num_b is None:
        return False
    if side_a is None and side_b is None:
        return num_b == num_a + 1
    if side_a == "r" and side_b == "v":
        return num_a == num_b
    if side_a == "v" and side_b == "r":
        return num_b == num_a + 1
    return False


def _discover_folios(images_dir: Path) -> "list[tuple[Path, str]]":
    """Return (image_path, folio_id) pairs sorted by folio_id."""
    images = [f for f in images_dir.iterdir() if f.suffix.lower() in IMAGE_EXTS]
    if not images:
        raise ValueError(f"No image files found in {images_dir}")
    result = []
    for img in images:
        stem = img.stem
        folio_id = stem.rsplit("_", 1)[-1] if "_" in stem else stem
        result.append((img, folio_id))
    result.sort(key=lambda x: x[1])
    return result


class _Tee(io.TextIOBase):
    """Write to both a real stream and a buffer (for capturing debug output)."""

    def __init__(self, real, buf):
        self._real = real
        self._buf = buf

    def write(self, s):
        self._real.write(s)
        self._buf.write(s)
        return len(s)

    def flush(self):
        self._real.flush()
        self._buf.flush()


def _run_one(
    idx: int,
    total: int,
    image_path: Path,
    folio_id: str,
    prev_state: "object | None",
    out_dir: Path,
    mothra_json_path: "str | None",
    debug: bool,
    args: argparse.Namespace,
    run: "callable",
    export_json: "callable",
    read_folio_state: "callable",
) -> "object":
    logger = logging.getLogger(__name__)
    logger.info("Folio %d/%d: %s", idx + 1, total, folio_id)

    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    tmp_path = tmp.name
    tmp.close()

    stem = image_path.stem
    ocr_buf = io.StringIO()

    ctx = (
        contextlib.redirect_stdout(_Tee(sys.__stdout__, ocr_buf))
        if debug
        else contextlib.nullcontext()
    )

    try:
        with ctx:
            collection, manifest = run(
                image_path=str(image_path),
                folio=folio_id,
                source_id=args.source_id,
                csv_path=args.csv,
                segmentation_model=args.segmentation_model,
                recognition_model=args.recognition_model,
                device=args.device,
                column_bimodal_threshold=args.column_bimodal_threshold,
                prev_folio_state=prev_state,
                folio_state_out=tmp_path,
                debug_ocr=debug,
                column_count=args.column_count,
                mothra_json_path=mothra_json_path,
                padding=args.padding,
            )
    except Exception:
        Path(tmp_path).unlink(missing_ok=True)
        raise

    out_json = out_dir / f"{stem}.json"
    export_json(collection, str(image_path), manifest, str(out_json))
    logger.info("  Pipeline JSON → %s", out_json)

    if debug:
        ocr_text = ocr_buf.getvalue()
        if ocr_text:
            ocr_out = out_dir / f"{stem}_ocr.txt"
            ocr_out.write_text(ocr_text, encoding="utf-8")
            logger.info("  OCR debug → %s", ocr_out)

    next_state = read_folio_state(tmp_path)
    logger.info(
        "  FolioState: remaining_words=%d, fully_consumed=%s",
        len(next_state.remaining_words),
        next_state.fully_consumed,
    )
    Path(tmp_path).unlink(missing_ok=True)
    return next_state


def main() -> None:
    cfg = load_config()
    tridis = _find_tridis_model()

    parser = argparse.ArgumentParser(
        description="Run the CATDOES pipeline on a directory of folio images.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--images", required=True, metavar="DIR",
        help="Directory containing folio images (pattern: {anything}_{folio_id}.ext).",
    )
    csv_group = parser.add_mutually_exclusive_group(required=True)
    csv_group.add_argument(
        "--source-id", type=int, metavar="INT",
        help="Cantus source ID (fetches CSV from cantusdatabase.org).",
    )
    csv_group.add_argument(
        "--csv", metavar="PATH",
        help="Path to a local Cantus-format CSV file.",
    )
    parser.add_argument(
        "--out-dir", default=None, metavar="PATH",
        help="Output directory for pipeline JSONs and debug files. "
             "Defaults to out_dir in config.yaml.",
    )
    parser.add_argument(
        "--debug", action="store_true", default=False,
        help="Save per-folio mothra JSONs, YOLO region debug .txt, and OCR transcript .txt "
             "to out_dir, in addition to printing OCR detail to the terminal.",
    )
    parser.add_argument(
        "--segmentation-model", default=cfg.get("segmentation_model"), metavar="PATH",
        help="Local path to a custom Kraken BLLA segmentation model. "
             "Defaults to config.yaml value or Kraken built-in.",
    )
    parser.add_argument(
        "--recognition-model", default=cfg.get("recognition_model") or tridis, metavar="PATH",
        help="Local path to a Kraken HTR model. "
             "Defaults to config.yaml value, then Tridis if installed via htrmopo.",
    )
    parser.add_argument(
        "--stub-mode", action="store_true", default=False,
        help="Skip text recognition on all folios.",
    )
    parser.add_argument(
        "--device", default="cpu",
        help="Kraken inference device (default: cpu).",
    )
    parser.add_argument(
        "--column-count", type=int, choices=[1, 2], default=None, metavar="{1,2}",
        help="Declare the folio column count. Skips bimodal auto-detection.",
    )
    parser.add_argument(
        "--column-bimodal-threshold", type=float, default=0.5, metavar="FLOAT",
        help="Coverage-profile valley/peak ratio for gutter detection (default: 0.5).",
    )
    parser.add_argument(
        "--padding", type=int, default=15, metavar="PX",
        help="Pixels added around each text bbox when masking (default: 15).",
    )
    parser.add_argument(
        "--conf", type=float, default=0.25, metavar="FLOAT",
        help="YOLO confidence threshold for mothra inference (default: 0.25).",
    )

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s", force=True)
    logger = logging.getLogger(__name__)

    # Resolve imports from mothra-text (injected into sys.path by load_config)
    try:
        from run_pipeline import run, export_json  # noqa: E402
        from steps.nw_chant_allocator import read_folio_state  # noqa: E402
    except ImportError as e:
        print(
            f"Error: could not import from mothra-text: {e}\n"
            "Check that mothra_text_path in config.yaml points to your line-seg-eval clone.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Validate args
    images_dir = Path(args.images).expanduser().resolve()
    if not images_dir.is_dir():
        parser.error(f"--images is not a directory: {images_dir}")

    if args.csv and not Path(args.csv).expanduser().exists():
        parser.error(f"CSV not found: {args.csv}")

    if args.stub_mode:
        args.recognition_model = None
    elif args.recognition_model is None:
        print(
            "Error: no recognition model found and --stub-mode was not given.\n"
            "Install Tridis:          python -m htrmopo get 10.5281/zenodo.10788591\n"
            "Or pass a model via:     --recognition-model PATH\n"
            "Or skip recognition:     --stub-mode",
            file=sys.stderr,
        )
        sys.exit(1)

    # Resolve output directory
    out_dir_str = args.out_dir or cfg.get("out_dir")
    if not out_dir_str:
        parser.error(
            "No output directory specified. Use --out-dir or set out_dir in config.yaml."
        )
    out_dir = Path(out_dir_str).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    # Discover folios
    try:
        folios = _discover_folios(images_dir)
    except ValueError as e:
        parser.error(str(e))

    n = len(folios)
    logger.info("Found %d folio image(s) in %s", n, images_dir)

    # Run YOLO inference upfront for all folios
    from scripts.run_mothra_inference import load_models, run_single
    logger.info("Loading YOLO models...")
    tm_model, st_model = load_models(
        cfg.get("yolo_text_music_model"),
        cfg.get("yolo_stave_model"),
    )

    mothra_tmp = Path(tempfile.mkdtemp())
    mothra_jsons: dict[str, str] = {}
    yolo_debugs: dict[str, str] = {}

    logger.info("Running YOLO inference on %d image(s)...", n)
    for image_path, folio_id in folios:
        json_path, debug_text = run_single(
            str(image_path), mothra_tmp, tm_model, st_model, conf=args.conf
        )
        mothra_jsons[folio_id] = json_path
        yolo_debugs[folio_id] = debug_text
        logger.info("  %s → %s", image_path.name, Path(json_path).name)

    if args.debug:
        for image_path, folio_id in folios:
            stem = image_path.stem
            shutil.copy2(mothra_jsons[folio_id], out_dir / f"{stem}_mothra.json")
            (out_dir / f"{stem}_yolo_debug.txt").write_text(
                yolo_debugs[folio_id], encoding="utf-8"
            )
        logger.info("Mothra JSONs and YOLO debug files saved to %s", out_dir)

    # Chain folios through the pipeline
    prev_state = None
    completed = 0

    for i, (image_path, folio_id) in enumerate(folios):
        if i > 0:
            prev_folio_id = folios[i - 1][1]
            if not _are_contiguous(prev_folio_id, folio_id):
                logger.info(
                    "Folios %s and %s are not contiguous; resetting FolioState.",
                    prev_folio_id, folio_id,
                )
                prev_state = None

        try:
            prev_state = _run_one(
                idx=i,
                total=n,
                image_path=image_path,
                folio_id=folio_id,
                prev_state=prev_state,
                out_dir=out_dir,
                mothra_json_path=mothra_jsons.get(folio_id),
                debug=args.debug,
                args=args,
                run=run,
                export_json=export_json,
                read_folio_state=read_folio_state,
            )
            completed += 1
        except Exception as exc:
            logger.error(
                "Chain aborted at folio %s (%d/%d): %s", folio_id, i + 1, n, exc
            )
            logger.error("Completed %d/%d folios before failure.", completed, n)
            shutil.rmtree(mothra_tmp, ignore_errors=True)
            sys.exit(1)

    shutil.rmtree(mothra_tmp, ignore_errors=True)
    logger.info("Done: %d/%d folios completed successfully.", completed, n)


if __name__ == "__main__":
    main()
