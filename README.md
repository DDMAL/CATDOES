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

### Image preparation

Images must follow the pattern `{anything}_{folio_id}.{ext}`, where `folio_id` exactly
matches the folio identifier used in the CantusDB CSV for the target source (e.g. `063v`,
`064r`, or `001` depending on the source). The pipeline extracts the folio ID from the last
underscore-delimited component of the filename stem:

```
CH-E_611_063v.jpg  →  folio 063v
CH-E_611_064r.jpg  →  folio 064r
```

Use `fetch_images.py` to produce correctly-named images automatically. It supports two
subcommands:

- **`fetch`** — download images directly from a IIIF manifest, named correctly on arrival
- **`rename`** — rename (or copy) images already downloaded via a browser

**Currently supported image source: e-codices only.** Both subcommands are implemented for
the [e-codices](https://www.e-codices.unifr.ch) Swiss manuscript repository.

Both subcommands require `--source-id`. The CantusDB CSV for that source determines the
canonical folio IDs and derives the output filename prefix from the manuscript's
`holding_institution` (RISM code) and `shelfmark` fields — e.g. `CH-E_611` for
Einsiedeln, Stiftsbibliothek, Cod. 611. Use `--prefix` to override if needed.

#### Finding the e-codices manuscript code

The manuscript code is the slug visible in the e-codices URL. For example:
```
https://www.e-codices.unifr.ch/en/list/one/sbe/0611  →  code: sbe-0611
https://www.e-codices.unifr.ch/en/list/one/fcc/0002  →  code: fcc-0002
```

#### Examples

Download all folios for a manuscript:
```bash
python fetch_images.py fetch \
    --code sbe-0611 \
    --source-id 678936 \
    --out-dir ~/Downloads/DDMAL/einsiedeln-611/
```

Download at medium resolution (faster, smaller files):
```bash
python fetch_images.py fetch \
    --code sbe-0611 \
    --source-id 678936 \
    --size medium \
    --out-dir ~/Downloads/DDMAL/einsiedeln-611/
```

Download a specific subset of folios (useful for testing):
```bash
python fetch_images.py fetch \
    --code sbe-0611 \
    --source-id 678936 \
    --folios 063v 064r 064v \
    --out-dir ~/Downloads/DDMAL/einsiedeln-611/
```

Rename browser-downloaded images:
```bash
python fetch_images.py rename \
    --source-id 678936 \
    --input-dir ~/Downloads/e-codices-sbe-0611/ \
    --out-dir ~/Downloads/DDMAL/einsiedeln-611/
```

#### Folio gaps

Some manuscript pages have no chant-start entry in CantusDB (their text continues from the
previous page's chant), so they never appear in a source's folio list even though the page
exists and is imaged (see [DDMAL/mothra#165](https://github.com/DDMAL/mothra/issues/165)).
Both `fetch` and `rename` log a warning for each such single-step gap detected in the CantusDB
folio list, without attempting to fetch or guess at the missing folio — download it manually
and add it to the output directory yourself if needed (e.g. via `rename` with an explicit
`--folios`).

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

## Results

Full-manuscript production runs (as opposed to the ad hoc test runs under `experiments/`) are
saved to `results/{manuscript}/` in this repo, indexed in
[`results/manuscripts.csv`](results/manuscripts.csv) — one row per manuscript, holding
shelfmark/institution/date/language/license metadata plus which debug artifacts were kept.

Each manuscript's directory holds:

| Directory | Contents |
|-----------|----------|
| `pipeline_json/` | Custom pipeline JSON (see [Output](#output)) — the format the Pipeline Inspector consumes |
| `page_xml/` | Stock-schema PAGE XML (`Region > TextLine > Word`), generated from `pipeline_json/` by `export_page_xml.py` |
| `syllable_layer/` | Companion syllable-level XML cross-referencing `page_xml/`'s Word IDs. Kept as a separate file rather than folded into PAGE XML, so PAGE stays usable by generic tooling (Transkribus, PAGE viewers) that doesn't expect a Syllable level |
| `ocr_debug/` | NW alignment debug (kept: cheap, and the only place per-line alignment scores exist) |
| `mothra_json/` | Raw YOLO Stage 0 masking output (kept: useful for diagnosing masking-quality issues) |

`yolo_debug/` is not kept for full-manuscript runs — it's a redundant human-readable rendering of
`mothra_json/`'s same data.

`page_xml`/`syllable_layer` IDs are `{folio}_l{line}_w{word}_s{syllable}`, computed deterministically
from each element's position in `pipeline_json`'s own arrays — not from the pipeline JSON's own
`label` field, which is derived from a per-run temporary file name and is not stable across
re-exports. Word/syllable geometry follows the line's real polygon rather than assuming a flat
rectangle (see `export_page_xml.py`'s module docstring for the exact method).

| Manuscript | Source ID | Folios | Path |
|------------|-----------|--------|------|
| CH-Fco Ms. 2 | [123672](https://cantusdatabase.org/source/123672) | 490 (001r–245v) | [results/CH-Fco_Ms._2_123672/](results/CH-Fco_Ms._2_123672/) |

---

## Adding a new image source to fetch_images.py

`fetch_images.py` currently supports e-codices only. The `sources/` package is structured
for extension: `sources/base.py` defines a `Source` typing.Protocol and shared folio
helpers; `sources/ecodices.py` is the one concrete implementation.

### What a new source must implement

Create `sources/{name}.py` with a class implementing these five methods:

| Method | Used by | Notes |
|--------|---------|-------|
| `manifest_url(code: str) -> str` | fetch | Construct the manifest URL from a short code string (e.g. an ARK, shelfmark slug, or full URL). |
| `canvases(manifest: dict) -> list[dict]` | fetch | Navigate the manifest JSON to the ordered canvas list. For IIIF Presentation API 2.x this is `manifest["sequences"][0]["canvases"]`. |
| `canvas_folio_label(canvas: dict) -> str\|None` | fetch | Return the raw folio label. IIIF standard is `canvas["label"]`; some sources embed it elsewhere or use structured label objects (IIIF 3.x). |
| `canvas_image_url(canvas: dict, size: str = "full") -> str\|None` | fetch | Return a download URL. `size` is a IIIF Image API size string (`"full"`, `"!1218,1624"`, etc.). Sources that don't support IIIF sizing can ignore it and always return full resolution. |
| `folio_from_filename(filename: str) -> str\|None` | rename | Parse the raw folio label out of a browser-downloaded filename using a source-specific regex. Return `None` if the filename isn't from this source. |

Then register it in `fetch_images.py` and wire it into `_cmd_fetch` / `_cmd_rename`. See the
developer notes at the top of `fetch_images.py` for the exact steps.

### Known challenges for specific sources

**Gallica (BnF)** — IIIF compliant, manifest URL is `https://gallica.bnf.fr/iiif/ark:/{ark}/manifest.json`. Canvas labels are often inconsistent: facing-page canvases share a label, some folios are skipped or repeated, and non-folio images (title pages, spines) appear mid-sequence. `canvas_folio_label` would need label normalisation before `folios_match` can reliably use it.

**DigiVatLib** — IIIF compliant. Canvas labels are generally cleaner than Gallica but use a different URL scheme; `manifest_url` and `canvas_image_url` need source-specific construction.

**e-manuscripta** — IIIF compliant (Swiss platform, similar in spirit to e-codices). Likely straightforward to add alongside e-codices.

**Non-IIIF / flat-PDF sources** — fetch mode does not apply. A source with no manifest (e.g. a McGill manuscript available only as a PDF) would need either: (a) a sidecar metadata file mapping page numbers to folio IDs, or (b) a new CLI subcommand outside the current fetch/rename model. `rename` mode is still usable if browser-downloaded filenames embed a parseable folio label.

---

## Repository Structure

```
run_chain.py              # pipeline CLI
fetch_images.py           # image fetch/rename CLI (fetch + rename subcommands)
export_page_xml.py        # pipeline_json -> PAGE XML + SyllableLayer converter
config.py                 # config loader; injects mothra-text into sys.path
config.yaml               # local configuration (mothra_text_path, out_dir, model paths)
requirements.txt          # pip dependencies
sources/
  base.py                 # Source protocol + shared folio parse/match helpers
  ecodices.py             # e-codices source adapter
scripts/
  run_mothra_inference.py # YOLO Stage 0 wrapper (load_models, run_single)
experiments/
  experiment1/            # CH-SGs 390 (source 678936), 20 folios, 2026-07-21
  experiment2/            # CH-Fco Ms. 2 (source 123672), 20 non-contiguous folios
results/
  manuscripts.csv         # one row per manuscript: metadata + index
  CH-Fco_Ms._2_123672/    # CH-Fco Ms. 2 (source 123672), 490 folios, full manuscript
spike/                    # Research spikes and format notes (not pipeline output)
Gen_Transkribus/          # Notes on layout model evaluation with Transkribus
data/                     # Annotation data and notes
```
