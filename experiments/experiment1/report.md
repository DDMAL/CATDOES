# Experiment 1 Report: CATDOES Pipeline on MS 0234

**Manuscript:** CH-SGs 390 / MS 0234 ([Cantus source 678936](https://cantusdatabase.org/source/678936))
**Folio range:** 063v – 073r (20 folios)
**Date run:** 2026-07-21
**Wall-clock time:** ~3m 30s (CPU only, no GPU)

---

## Overview

This experiment runs the new `run_chain.py` CATDOES pipeline on 20 contiguous folios of
MS 0234 as a first end-to-end test. The pipeline chains the mothra-text stages (YOLO masking →
Kraken BLLA segmentation → Kraken HTR → NW chant allocation → word/syllable segmentation)
under a single CLI designed for directory-level batch runs, with FolioState continuity carried
across folios.

---

## No Volpiano on This Source

The chants on the 20 folios in this experiment have no volpiano encoding in the Cantus CSV. Volpiano `77`-break markers normally serve as line-break
anchors for the NW allocator; without them, alignment relies on OCR alone. Words are assigned
to the correct physical lines most of the time, but line-boundary errors are more frequent
than on volpiano-encoded chants.

---

## FolioState Chaining

`run_chain.py` checks whether consecutive images represent adjacent pages (recto→verso→next
recto) and, when they do, passes alignment state from one folio to the next. For this run,
all 20 folios were contiguous (063v → 064r → … → 073r), so state was carried through the
entire chain.

`FolioState` carries:
- `last_chant_sequence` — the Cantus sequence number of the last chant seen
- `remaining_words` — words from the final chant that were consumed but not yet placed on a line
- `fully_consumed` — whether the last chant was fully placed

This lets a chant that spans a page break be split correctly across folios: the portion
assigned on folio N carries over into folio N+1's allocation.

Folio IDs are inferred from image filenames using `stem.rsplit("_", 1)[-1]`
(e.g., `ms-234_063v.jpg` → `063v`). Images must follow the `{stem}_{folioID}.{ext}` naming
convention for this to work. The pipeline sorts by folio ID before chaining.

---

## Bug Found: `infer_continuation` Scanning Wrong Preceding Folio

When `run_chain.py` runs without an explicit prior `FolioState` (i.e., the first folio in a
chain), the NW allocator calls `build_flat_text_and_anchors` with `infer_continuation=True`.
This tells the allocator to look back in the Cantus CSV for carry-over words from the
immediately preceding folio.

A bug was found in `nw_chant_allocator.py`: the `infer_continuation` branch searched the entire
manuscript history for rows where the volpiano field contains `77`, then selected the last one
chronologically. For this run, the last such row across the full CSV was on folio **015r**
(Venite exsultemus, Cantus 909030, Psalm 94) — not the true preceding folio **062v**.
This caused 114 Psalm 94 words to be prepended to 063v's flat text, and the NW allocator
then assigned Psalm 94 text to the entire folio instead of the correct chants.

**Fix:** The search is now scoped to the immediately preceding folio only, by computing
`max(preceding_keys)` (using `_folio_sort_key`) and filtering CSV rows to that folio before
checking for `77`. This fix is applied to `line-seg-eval/steps/nw_chant_allocator.py`.

---

## Output Structure

Four output directories, 20 files each:

| Directory | Contents |
|-----------|----------|
| `output_json/` | Pipeline JSON per folio: lines with bounding boxes, polygons, OCR text, and Cantus-aligned word/syllable segmentation |
| `ocr_debug/` | NW alignment debug per folio: fused OCR transcripts and per-line alignment detail |
| `mothra_json/` | YOLO annotation output from Stage 0 masking |
| `yolo_debug/` | Human-readable YOLO detection summary per folio |

These are mirrored in the repo under `experiments/experiment1/` (with `output_json/` renamed to
`pipeline_json/`).

---

## Debug Output Guide

**`ocr_debug/`** is the primary tool for inspecting alignment quality. Each file contains:
1. **Fused line transcripts** — the raw OCR text after adjacent text-region boxes are merged
   into a single line string
2. **Per-line NW alignment** — shows the OCR string aligned against the assigned Cantus text,
   with the word range consumed and the normalized NW score

The `norm` score is the NW alignment score divided by the assigned word count. Higher is better;
scores below ~2.0 indicate the OCR and assigned text diverged significantly (short OCR fragment,
heavy noise, or a line the model couldn't read).

**`mothra_json/`** files can be opened in the [mothra-annotator](https://github.com/DDMAL/mothra-annotator) tool to visually inspect the masking boxes produced by the YOLO model for each folio.

**`yolo_debug/`** records what Stage 0 detected on each image: image dimensions, counts by
class (text / music / staves), and per-detection confidence and bounding box. Useful for
checking whether the masking step correctly identified text regions.

---

## Alignment Quality

Across 153 lines (all 20 folios), normalized NW scores ranged from 0.07 to 7.58,
with a mean of 4.04 and median of 3.96. 22 lines (14%) scored below 2.0.

Low scores are expected on some lines due to the difficulty of medieval cursive OCR: word
boundaries are unclear, ligatures are common, and initial letters are often large or decorated.
The NW allocator still assigns the correct Cantus text in most cases even when OCR is noisy,
because the alignment is constrained by the surrounding words.

No models were changed from the mothra-text baseline — Kraken BLLA, Kraken HTR (Tridis), and
the YOLO masking models are identical. Pipeline output quality on this source is therefore
expected to be representative of what mothra-text would produce on the same images, with
differences attributable only to the absence of volpiano anchors.
