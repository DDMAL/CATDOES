#!/usr/bin/env python3
"""Convert CATDOES pipeline JSON output to PAGE XML plus a companion
SyllableLayer XML.

Two files are written per input JSON:

page_xml/{stem}.xml         Stock-schema-shaped PAGE XML (Region > TextLine >
                             Word). No Syllable/Glyph level, so it stays usable
                             by generic PAGE tooling (Transkribus, PAGE
                             viewers, etc).

syllable_layer/{stem}.syl.xml   A companion file carrying syllable-level data,
                             cross-referencing the PAGE file's Word ids via
                             wordRef. Kept separate rather than stretching
                             PAGE's own schema to fit syllables.

IDs (line/word/syllable) are computed from each element's position in the
input JSON's own arrays, as {folio}_l{line_idx}_w{word_idx}_s{syl_idx} --
the input JSON's own "label" field is ignored, since it is derived from a
per-run temporary file name upstream and is not stable across re-exports.

Word/syllable geometry is derived from the line's real polygon rather than
its flat bounding box: each word/syllable keeps its existing x-range (from
the input JSON's bbox) but looks up the line's/word's actual top and bottom
y at those x-positions (linearly interpolated from the polygon's own
points), so the resulting shape follows a sloped or wavy line instead of
assuming a flat rectangle.

Usage
-----
python export_page_xml.py path/to/pipeline_json/ \\
    [--page-xml-dir path/to/page_xml/] \\
    [--syllable-layer-dir path/to/syllable_layer/]
"""

import argparse
import json
import logging
import xml.etree.ElementTree as ET
from pathlib import Path

PAGE_NS = "http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
SCHEMA_LOCATION = f"{PAGE_NS} {PAGE_NS}/pagecontent.xsd"

SYLLABLE_LAYER_SCHEMA_VERSION = "0.1"
GEOMETRY_SOURCE = "line-polygon-char-split-estimate"

ET.register_namespace("", PAGE_NS)
ET.register_namespace("xsi", XSI_NS)


# ---------------------------------------------------------------------------
# Geometry: polygon-aware word/syllable shapes
# ---------------------------------------------------------------------------

def _boundary_lookup(polygon: "list[list[float]]"):
    """Return f(x) -> (top_y, bottom_y) for a closed line/word polygon.

    Classifies each polygon point as "top" or "bottom" by comparing its y to
    the polygon's mean y, sorts each side by x, and linearly interpolates
    between the two nearest points on each side to answer "what's the
    top/bottom y at this x". Falls back to the polygon's bbox extremes if one
    side is empty (degenerate polygon).
    """
    ys = [p[1] for p in polygon]
    mean_y = sum(ys) / len(ys)
    top = sorted((tuple(p) for p in polygon if p[1] <= mean_y), key=lambda p: p[0])
    bottom = sorted((tuple(p) for p in polygon if p[1] > mean_y), key=lambda p: p[0])

    if not top or not bottom:
        xs = [p[0] for p in polygon]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        top = [(min_x, min_y), (max_x, min_y)]
        bottom = [(min_x, max_y), (max_x, max_y)]

    def _interp(chain, x):
        if x <= chain[0][0]:
            return chain[0][1]
        if x >= chain[-1][0]:
            return chain[-1][1]
        for (x0, y0), (x1, y1) in zip(chain, chain[1:]):
            if x0 <= x <= x1:
                if x1 == x0:
                    return y0
                t = (x - x0) / (x1 - x0)
                return y0 + t * (y1 - y0)
        return chain[-1][1]

    return lambda x: (_interp(top, x), _interp(bottom, x))


def _shape_from_x_range(x_min: float, x_max: float, lookup) -> "tuple[list, tuple]":
    """Build a 4-point polygon and its bbox for [x_min, x_max] using `lookup`."""
    top_y0, bottom_y0 = lookup(x_min)
    top_y1, bottom_y1 = lookup(x_max)
    polygon = [
        (x_min, top_y0),
        (x_max, top_y1),
        (x_max, bottom_y1),
        (x_min, bottom_y0),
    ]
    xs = [p[0] for p in polygon]
    ys = [p[1] for p in polygon]
    bbox = (min(xs), min(ys), max(xs), max(ys))
    return polygon, bbox


def _points_str(polygon: "list[tuple[float, float]]") -> str:
    return " ".join(f"{round(x)},{round(y)}" for x, y in polygon)


# ---------------------------------------------------------------------------
# PAGE XML
# ---------------------------------------------------------------------------

def build_page_xml(payload: dict) -> "tuple[str, list[dict]]":
    """Return (page_xml_string, syllable_records) for one pipeline JSON payload."""
    folio = payload["folio"]
    width = payload["image_width"]
    height = payload["image_height"]

    root = ET.Element(
        f"{{{PAGE_NS}}}PcGts",
        {f"{{{XSI_NS}}}schemaLocation": SCHEMA_LOCATION},
    )
    meta = ET.SubElement(root, f"{{{PAGE_NS}}}Metadata")
    ET.SubElement(meta, f"{{{PAGE_NS}}}Creator").text = "export_page_xml.py"

    page = ET.SubElement(
        root,
        f"{{{PAGE_NS}}}Page",
        {
            "imageFilename": f"{folio}.jpg",
            "imageWidth": str(width),
            "imageHeight": str(height),
        },
    )
    region = ET.SubElement(
        page, f"{{{PAGE_NS}}}TextRegion", {"id": f"{folio}_r000", "type": "paragraph"}
    )
    ET.SubElement(
        region,
        f"{{{PAGE_NS}}}Coords",
        {"points": f"0,0 {width},0 {width},{height} 0,{height}"},
    )

    syllable_records = []

    # Line order in the input JSON is the reading order; PAGE convention is
    # that document order of TextLine children within a region IS the
    # reading order, so no separate ReadingOrder element is needed here (it
    # exists in the schema to order regions relative to each other, not
    # lines within a single region).
    for line_idx, line in enumerate(payload["lines"]):
        line_id = f"{folio}_l{line_idx:03d}"
        polygon = line.get("polygon") or _bbox_to_polygon(line["bbox"])
        lookup = _boundary_lookup(polygon)

        text_line = ET.SubElement(region, f"{{{PAGE_NS}}}TextLine", {"id": line_id})
        ET.SubElement(text_line, f"{{{PAGE_NS}}}Coords", {"points": _points_str(polygon)})

        bx_min, _, bx_max, b_bottom = line["bbox"]
        ET.SubElement(
            text_line,
            f"{{{PAGE_NS}}}Baseline",
            {"points": f"{bx_min},{b_bottom} {bx_max},{b_bottom}"},
        )

        for word_idx, word in enumerate(line.get("words", [])):
            word_id = f"{line_id}_w{word_idx:03d}"
            x_min, _, x_max, _ = word["bbox"]
            word_polygon, _ = _shape_from_x_range(x_min, x_max, lookup)

            word_el = ET.SubElement(
                text_line,
                f"{{{PAGE_NS}}}Word",
                {
                    "id": word_id,
                    "custom": f"source:{word.get('source', 'fallback')};",
                },
            )
            ET.SubElement(word_el, f"{{{PAGE_NS}}}Coords", {"points": _points_str(word_polygon)})
            word_te = ET.SubElement(word_el, f"{{{PAGE_NS}}}TextEquiv")
            ET.SubElement(word_te, f"{{{PAGE_NS}}}Unicode").text = word.get("text", "")

            word_lookup = _boundary_lookup(word_polygon)
            for syl_idx, syl in enumerate(word.get("syllables", [])):
                syl_id = f"{word_id}_s{syl_idx:03d}"
                sx_min, _, sx_max, _ = syl["bbox"]
                syl_polygon, syl_bbox = _shape_from_x_range(sx_min, sx_max, word_lookup)
                syllable_records.append(
                    {
                        "id": syl_id,
                        "wordRef": word_id,
                        "text": syl.get("text", ""),
                        "polygon": syl_polygon,
                        "bbox": syl_bbox,
                    }
                )

        line_te = ET.SubElement(text_line, f"{{{PAGE_NS}}}TextEquiv")
        ET.SubElement(line_te, f"{{{PAGE_NS}}}Unicode").text = line.get("text", "")

    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="unicode", xml_declaration=True), syllable_records


def _bbox_to_polygon(bbox: "list[float]") -> "list[list[float]]":
    x0, y0, x1, y1 = bbox
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


# ---------------------------------------------------------------------------
# SyllableLayer XML
# ---------------------------------------------------------------------------

def build_syllable_layer_xml(page_ref: str, syllable_records: "list[dict]") -> str:
    root = ET.Element(
        "SyllableLayer",
        {
            "schemaVersion": SYLLABLE_LAYER_SCHEMA_VERSION,
            "pageRef": page_ref,
            "geometrySource": GEOMETRY_SOURCE,
        },
    )
    for rec in syllable_records:
        syl_el = ET.SubElement(
            root, "Syllable", {"id": rec["id"], "wordRef": rec["wordRef"]}
        )
        ET.SubElement(syl_el, "Coords", {"points": _points_str(rec["polygon"])})
        x0, y0, x1, y1 = rec["bbox"]
        ET.SubElement(
            syl_el,
            "Bbox",
            {
                "xmin": str(round(x0)),
                "ymin": str(round(y0)),
                "xmax": str(round(x1)),
                "ymax": str(round(y1)),
            },
        )
        ET.SubElement(syl_el, "Text").text = rec["text"]

    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="unicode", xml_declaration=True)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def process_directory(input_dir: Path, page_xml_dir: Path, syllable_layer_dir: Path) -> None:
    logger = logging.getLogger(__name__)
    page_xml_dir.mkdir(parents=True, exist_ok=True)
    syllable_layer_dir.mkdir(parents=True, exist_ok=True)

    json_files = sorted(input_dir.glob("*.json"))
    if not json_files:
        logger.warning("No .json files found in %s", input_dir)
        return

    ok = failed = 0
    for json_path in json_files:
        try:
            payload = json.loads(json_path.read_text(encoding="utf-8"))
            page_xml_str, syllable_records = build_page_xml(payload)

            page_name = json_path.with_suffix(".xml").name
            (page_xml_dir / page_name).write_text(page_xml_str, encoding="utf-8")

            syl_name = json_path.stem + ".syl.xml"
            syl_xml_str = build_syllable_layer_xml(page_name, syllable_records)
            (syllable_layer_dir / syl_name).write_text(syl_xml_str, encoding="utf-8")

            ok += 1
        except Exception as exc:
            logger.error("Failed %s: %s", json_path.name, exc)
            failed += 1

    logger.info(
        "Done: %d converted, %d failed. PAGE XML -> %s, SyllableLayer -> %s",
        ok, failed, page_xml_dir, syllable_layer_dir,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert CATDOES pipeline JSON to PAGE XML + a companion SyllableLayer XML.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("input_dir", type=Path, help="Directory of pipeline JSON files")
    parser.add_argument(
        "--page-xml-dir", type=Path, default=None, metavar="PATH",
        help="Output directory for PAGE XML (default: <input_dir>/../page_xml)",
    )
    parser.add_argument(
        "--syllable-layer-dir", type=Path, default=None, metavar="PATH",
        help="Output directory for SyllableLayer XML (default: <input_dir>/../syllable_layer)",
    )
    parser.add_argument(
        "--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level), format="%(levelname)s %(message)s"
    )

    input_dir = args.input_dir.expanduser().resolve()
    if not input_dir.is_dir():
        parser.error(f"input_dir is not a directory: {input_dir}")

    page_xml_dir = (args.page_xml_dir or input_dir.parent / "page_xml").expanduser().resolve()
    syllable_layer_dir = (
        args.syllable_layer_dir or input_dir.parent / "syllable_layer"
    ).expanduser().resolve()

    process_directory(input_dir, page_xml_dir, syllable_layer_dir)


if __name__ == "__main__":
    main()
