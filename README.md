# CATDOES

**Chant Alignment and Text Detection on Early Manuscripts**

CATDOES is a batch pipeline for running DDMAL's [mothra-text](https://github.com/DDMAL/mothra-text) manuscript processing pipeline on directories of folio images. It wraps the mothra-text stages — YOLO-based region masking, Kraken line segmentation, Kraken HTR, Needleman-Wunsch chant alignment, and word/syllable segmentation — under a single CLI with automatic folio chaining and structured debug output.

Experiment results and pipeline outputs are saved to the [DDMAL-lab/CATDOES HuggingFace dataset](https://huggingface.co/datasets/DDMAL-lab/CATDOES).

---

## Requirements

- A local clone of [mothra-text](https://github.com/DDMAL/mothra-text) (referred to locally as `line-seg-eval`)
- A Python environment with all mothra-text dependencies installed (see mothra-text's `requirements.txt`)
- Install CATDOES-specific dependencies into the same environment:
  ```
  pip install -r requirements.txt
  ```

---

## Setup

Copy `config.yaml` and update `mothra_text_path` to point to your local mothra-text clone:

```yaml
mothra_text_path: /path/to/line-seg-eval
out_dir: ~/Downloads/DDMAL/catdoes/
```

The pipeline reads `config.yaml` from the repo root, or falls back to `~/.catdoes/config.yaml`.

---

## Usage

### Image naming convention

Images must follow the pattern `{anything}_{folio_id}.{ext}`, where `folio_id` is the folio
identifier (e.g., `063v`, `064r`). The pipeline extracts the folio ID from the last
underscore-delimited component of the filename stem:

```
ms-234_063v.jpg  →  folio 063v
ms-234_064r.jpg  →  folio 064r
```

### Running the pipeline

```bash
python run_chain.py \
    --images path/to/folio/images/ \
    --source-id 678936 \
    [--out-dir path/to/output/] \
    [--debug]
```

`--source-id` is the [Cantus Database](https://cantusdatabase.org) source ID for the manuscript.

`--debug` saves four output files per folio (see [Output](#output) below). Without `--debug`,
only the pipeline JSON is saved.

### Folio chaining

Images are discovered from `--images`, sorted by folio ID, and processed in order. FolioState
(carry-over words from chants that span a page break) is passed from each folio to the next,
but only when the two folios are actually adjacent pages (recto→verso or verso→next recto).
If a gap is detected, a warning is logged and the state is reset rather than silently
propagating stale data.

---

## Output

With `--debug`, four files are produced per folio and written to `--out-dir`:

| File | Description |
|------|-------------|
| `{stem}.json` | Pipeline JSON: lines with bounding boxes, polygons, OCR text, and Cantus-aligned word/syllable segmentation |
| `{stem}_ocr.txt` | NW alignment debug: fused OCR transcripts and per-line alignment detail with scores |
| `{stem}_mothra.json` | YOLO annotation output from Stage 0 masking; can be opened in [mothra-annotator](https://github.com/DDMAL/mothra-annotator) |
| `{stem}_yolo_debug.txt` | Human-readable YOLO detection summary: image dimensions, class counts, per-detection confidence and bounding box |

---

## Experiments

Each experiment is a documented pipeline run on a specific manuscript or folio range. Results
are saved to `experiments/{experiment_name}/` in this repo and mirrored to the HuggingFace
dataset under `data/{manuscript}/experiment{N}/`.

| Experiment | Manuscript | Folios | Source ID | Report |
|------------|-----------|--------|-----------|--------|
| [experiment1](experiments/experiment1/) | MS 0234 (CH-SGs 390) | 063v–073r (20 folios) | [678936](https://cantusdatabase.org/source/678936) | [report.md](experiments/experiment1/report.md) |

---

## Repository Structure

```
run_chain.py              # pipeline CLI
config.py                 # config loader; injects mothra-text into sys.path
config.yaml               # local configuration (mothra_text_path, out_dir, model paths)
requirements.txt          # pip dependencies
scripts/
  run_mothra_inference.py # YOLO Stage 0 wrapper (load_models, run_single)
experiments/
  experiment1/            # MS 0234, 20 folios, 2026-07-21
Gen_Transkribus/          # Notes on layout model evaluation with Transkribus
data/                     # Annotation data and notes
```
