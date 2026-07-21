# Experiment 1: MS 0234 Pipeline Run

**Manuscript:** CH-SGs 390 / MS 0234 ([Cantus source 678936](https://cantusdatabase.org/source/678936))
**Folio range:** 063v – 073r (20 folios)
**Date run:** 2026-07-21
**Pipeline:** CATDOES `run_chain.py` with `--debug`, source ID 678936

## Directories

### `pipeline_json/`
One JSON file per folio (`{stem}.json`). Each file is the full pipeline output for that folio:
segmented text lines with bounding boxes and polygons, OCR text, and Cantus-aligned word and
syllable segmentations. Produced by the NW chant allocator stage of the mothra-text pipeline.

### `ocr_debug/`
One `.txt` file per folio (`{stem}_ocr.txt`). Contains the per-line OCR transcripts and
Needleman-Wunsch alignment detail printed by `--debug-ocr` mode: raw Kraken OCR output,
assigned ground-truth text from the Cantus CSV, alignment scores, and anchor information.
Useful for diagnosing alignment quality.

### `mothra_json/`
One JSON file per folio (`{stem}_mothra.json`). YOLO annotation output from the stage 0
Mothra masking step, in the mothra Annotator export format:
`{ imageName, imageWidth, imageHeight, annotations: [{classId, bbox, confidence, ...}] }`.
ClassId 1 = text region, 2 = music region, 3 = staves. These bounding boxes were used to
mask non-text regions before Kraken line segmentation.

### `yolo_debug/`
One `.txt` file per folio (`{stem}_yolo_debug.txt`). Human-readable summary of the YOLO
detections: image dimensions, total annotation count broken down by class, and per-detection
lines with class label, confidence score, and bounding box coordinates.
