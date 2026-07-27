# Experiment 2 Report: CATDOES Pipeline on CH-Fco Ms. 2

**Manuscript:** CH-Fco Ms. 2 ([Cantus source 123672](https://cantusdatabase.org/source/123672))  
**Folios:** 002r, 002v, 003r, 003v, 005r, 005v, 006r, 006v, 007r, 007v, 008r, 008v, 009r, 009v, 029v, 030v, 032r, 032v, 034r, 040v (20 non-contiguous folios)  
**Date run:** 2026-07-27  
**Wall-clock time:** ~3m 11s (CPU only, ~3.4 cores via parallelism)

---

## Overview

This experiment runs the CATDOES pipeline on 20 non-contiguous folios of CH-Fco Ms. 2, a manuscript with volpiano encoding in the Cantus Database. The goals were to test two capabilities not exercised in experiment 1: (1) volpiano `77`-break anchors in the NW allocator, and (2) FolioState reset behaviour at contiguity gaps. The pipeline ran to completion with no crashes or bugs.

---

## Volpiano Encoding

Unlike experiment 1 (MS 0234), chants on this manuscript have volpiano encoding. The NW allocator uses `77` markers in the volpiano field as hard line-break anchors, snapping word boundaries to the physical end of a music line. Across the 20 folios, 19 `page_break_77` anchor hits were recorded in the debug output, confirming that volpiano-guided alignment was active throughout the run.

---

## Stage 0 Masking: Non-Chant Text

The primary source of alignment degradation on this manuscript is the Stage 0 region segmentation model failing to classify large blocks of non-chant text correctly. When these blocks are misclassified as chant regions, they are not masked out, so Kraken's line segmentation model detects them as text lines and they enter the NW allocation step.

**006v** is the most severely affected folio (mean NW score: −1.03). A large non-chant text block at the top of the page is detected as chant by the region model. Because this block appears first in reading order, the NW allocator begins aligning CantusDB words to it from the start of the folio, producing a cascading alignment failure down the entire page.

**008v** contains the single worst-scoring line in the run (norm = −7.93): a `euouae` psalm-tone termination where the allocator assigns one word to a long OCR line that actually spans non-chant text. Seven folios in the run (003v, 006v, 007r, 007v, 008r, 009r, 040v) have negative mean NW scores, all attributable to this masking issue to varying degrees.

On folios with little non-chant text — for example, **006r** — alignment quality is considerably better, demonstrating that the pipeline performs well when Stage 0 masking is accurate.

A secondary masking issue is that the region segmentation model occasionally misses individual chant words. The missed words are masked out and thus not seen by Kraken, degrading bounding-box accuracy and OCR quality on those lines even when the overall folio layout is correct.

---

## No Bugs Found

No bugs were identified in this run. The issues described above are a known limitation of the region segmentation model's ability to discriminate chant from non-chant text, not errors in the pipeline logic.

---

## Output Structure

Four output directories, 20 files each:

| Directory | Contents |
|-----------|----------|
| `pipeline_json/` | Pipeline JSON per folio: lines with bounding boxes, polygons, OCR text, and Cantus-aligned word/syllable segmentation |
| `ocr_debug/` | NW alignment debug per folio: fused OCR transcripts and per-line alignment detail |
| `mothra_json/` | YOLO annotation output from Stage 0 masking |
| `yolo_debug/` | Human-readable YOLO detection summary per folio |

Output is also stored on HuggingFace at `DDMAL-lab/CATDOES` under `data/CH-Fco_Ms2/experiment2/`. Source images are at `data/CH-Fco_Ms2/images/`.

---

## Alignment Quality

Across 253 lines (all 20 folios), normalized NW scores ranged from −7.93 to 7.80, with a mean of 2.41 and median of 2.98. 114 lines (45%) scored below 2.0, compared to 14% in experiment 1.

The increase in low-scoring lines is primarily explained by the masking failures described above. The later isolated folios (029v, 030v, 032r, 032v, 034r), which were processed with reset FolioState and appear to contain less non-chant text, scored considerably better.
