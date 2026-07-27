# Dataset Formats — Detailed Notes

Supporting research notes for [`dataset_formats.md`](./dataset_formats.md). Full per-dataset breakdown across six Track A categories, plus well-designed/not well-designed observations.

---

## ICDAR2019-HDRC-IR

- https://zenodo.org/records/3262372
- https://clamm.irht.cnrs.fr/icdar2019-hdrc-ir/data-set/

**File types**
- Images are in different resolutions and formats (jpg, tif, gray-level, color, etc.)
- Heterogeneous raw image formats, not standardized
- But source images served as JPEG via IIIF regardless of original digitization format
- CSV files hold metadata and ground truth information

**Storage granularity**
- Aggregated (test and validation data separate), not per-image

**Spatial encoding**
- N/A — task is whole-image writer retrieval, not localization

**Image referencing**
- Meta CSV files contain download links; the original source location (IIIF-hosting archive) is preserved as a URL field in the metadata, pointing to a IIIF manifest (`.json`)
- Manifest = one file per manuscript, containing one "canvas" per folio/page
- Each canvas gives 3 separate image URLs: a thumbnail, a full-resolution JPEG, and a IIIF Image API service endpoint (supports on-the-fly crop/resize)
- So referencing is nested/hierarchical (manifest → canvases → image URLs), not a flat list of image links

**Metadata**
- `test_meta.csv`, `val_meta.csv`, `wi_comp19_test_ground_truth.csv`, `wi_comp19_validation_ground_truth.csv`
- Ground truth CSVs contain `filename`, `writer id`, `category`
- Metadata CSVs contain competition ID, writer, city, institution, collection, provider, download links
- Richer descriptive metadata (shelfmark, date, language, physical format, licensing) is NOT in the dataset's own CSVs — it only exists in the linked IIIF manifest, so you'd have to follow the download link to get it

**Split conventions**
- No official "train" set distributed by this competition — organizers suggest reusing the existing ICDAR17 Historical-WI dataset for training
- Validation set provided separately: 1,200 images / 520 writers (comes with its own zip + metadata/ground truth CSVs)
- Test set: 20,000 images, released as its own zip, later re-released at higher resolution
- Each split has its own paired files: `{split}_meta.csv` + `wi_comp19_{split}_ground_truth.csv` — splits are separated by file, not by a column in one combined file
- Ground truth schema is slightly inconsistent across splits: test CSV has a `category` column, validation CSV doesn't (category must be inferred positionally instead)

**Well-designed**
- Ground truth/metadata shipped as small, individually-previewable CSVs sitting right on the Zenodo record page; can inspect column headers before downloading anything
- Clear license and citation block directly on the Zenodo landing page
- README file included
- Train/val/test cleanly separated into distinct files

**Not well-designed**
- No official training set at all — you have to go find and download a different competition's dataset (ICDAR17 Historical-WI) just to have something to train on
- Ground truth schema is inconsistent across splits: test CSV has a `category` column, validation CSV doesn't (category must be inferred positionally instead)
- Rich descriptive metadata (shelfmark, date, language) isn't in the dataset at all — you have to follow a download link out to an external IIIF manifest to get it

---

## ICDAR2017-CLaMM

- https://clamm.irht.cnrs.fr/icdar-2017/data-set/
- https://zenodo.org/records/5527690

**File types**
- Tasks 1 and 3 use a test set of 2000 greyscale, tiff, 300 dpi images, while tasks 2 and 4 use 1000 images in different formats, resolutions and color representation
- Ground truth is a single CSV per task-pair (not a separate format per task)

**Storage granularity**
- One aggregated CSV per task-pair, bundled inside the same zip as the images, joined to images via the `FILE_NAME` column. Same aggregation pattern as HDRC-IR's ground-truth CSVs, just packaged differently (inside the image zip vs. as a separate top-level Zenodo file)
- Images themselves sit in a flat folder — no subfolders by class, task, or institution

**Spatial encoding**
- N/A — script-type and date classification only, no sub-image localization

**Image referencing**
- Like HDRC-IR, images are sourced from IIIF-capable repositories (Gallica, BVMM), but again the actual distributed files are static images in zips, not manifest links
- Filenames confirm mixed source provenance: at least 4 distinct naming schemes coexist in the same dataset (`{numericID}_{shelfmark}_{page}.tif`, `{numericID}_{archivalSeries}_{page}.tif`, `IRHT_P_{plateID}.tif`, and Gallica's own `{arkID}_f{folio}.tif`) — no unified filename schema was imposed across source institutions

**Metadata**
- Dataset-level metadata (not per-image, from the site): script type, date
- Per-image ground truth CSV columns: `ICDAR_CLAMM` (task ID), `FILE_NAME`, `Script_type_ICDAR2017`, `DATE_ICDAR`
- Both label columns are numeric class indices, not human-readable strings — script type is one of several numeric classes (see site's "Script classes" page for the legend), and date is one of 15 date-range buckets (500–1600 C.E.) per the competition paper — no legend included in the CSV itself
- Metadata is filename-encoded for provenance/ID purposes, but the encoding scheme is not standardized across the dataset — it varies by source institution

**Split conventions**
- Training:
  - Tasks 1 and 2: training set consists of 3500 images used in the ICFHR 2016 competition
  - Tasks 3 and 4: training set consists of 3000 images from the 3500 above
- Testing:
  - 2000 images for tasks 1/3, 1000 images for tasks 2/4 — two separate, task-paired test sets rather than one universal test set
  - Packaged as three separate zips: Training, task1_task3, task2_task4 — splits are separated by file, not by a column

**Well-designed**
- Zenodo's zip preview let you inspect the internal file tree without downloading anything
- Consistent packaging pattern: one CSV bundled with images per task-pair, no exceptions

**Not well-designed**
- Numeric class labels (script type, date) with no legend anywhere in the CSV — you have to separately track down the site's "Script classes" page to interpret a bare number like `9`
- At least 4 different filename conventions coexist across source institutions with no unified schema

---

## ICFHR2016-CLaMM

- https://clamm.irht.cnrs.fr/icfhr2016-clamm/data-set/
- https://zenodo.org/records/5526880

**File types**
- Grey-level TIFF, 300 dpi, each picturing a 100 x 150 mm part of a manuscript — confirmed as small cropped patches, not full pages
- Ground truth is CSV, bundled inside the image zips (not separate Zenodo files)

**Storage granularity**
- All three zips (Training, task1, task2) each contain one CSV ground-truth file bundled alongside their images
- Flat image folder in each, no subfolders by class or source

**Spatial encoding**
- No bounding box, polygon, or coordinate data shipped
- Images are pre-cropped 100 x 150 mm patches, not full pages
- Filenames show a sequence number when multiple crops come from the same page (e.g. `_0005_1`, `_0005_2`), but the actual crop location is not disclosed

**Image referencing**
- Same provenance story as 2017 — French manuscript catalogues, BVMM, and Gallica
- Filenames again mix conventions: numeric-ID + shelfmark + page + crop-index (`315556101_MS0187_0005_1.tif`) alongside IRHT's own plate-ID scheme (`IRHT_P_000004.tif`) — same multi-institution inconsistency seen in 2017

**Metadata**
- Ground truth CSV columns: `FILENAME`, `SCRIPT_TYPE`
- `SCRIPT_TYPE` is a numeric class index (values seen: 1, 2, 4, 8, 11, 12), out of 12 predefined script classes

**Split conventions**
- Training set: 2000 images
- Test set: 1000 images for task 1, 2000 images for task 2 — task-paired test sets again, same convention as 2017
- Packaged as three separate zips (Training, task1, task2 — plus a separate outputs zip) — splits by file, not by column

**Well-designed**
- Data-set page explicitly states the CSV schema (`FILENAME,SCRIPT_TYPE`) before you even open anything
- Fully consistent packaging across all three zips

**Not well-designed**
- License was never clearly stated anywhere findable
- Images are confirmed pre-cropped (100 x 150 mm patches) but the actual crop location/coordinates are never disclosed, only a sequence number when multiple crops share a source page
- Same multi-institution filename inconsistency as its 2017 sibling
- Numeric labels again with no inline legend

---

## IAM Handwriting Database

- https://fki.tic.heia-fr.ch/databases/iam-handwriting-database

**File types**
- Forms, lines, and words extracted as PNG images (300 dpi, 256 grey levels), each with a matching XML sidecar
- Also ships a parallel flat ASCII summary format (`words.txt`, `lines.txt`, etc.), one row per word/line, stripped down to core fields only (no geometry beyond a bbox)

**Storage granularity**
- One XML file per form, but that single file nests annotations for every line and every word on that page

**Spatial encoding**
- Real bounding box / geometric data at multiple levels
- One XML file per form, nesting line and word annotations inside it
- Line level: baseline slope/position, ascender/descender slope/position, slant angle, plus optional upper/lower contour polylines (`<point x y>`)
- Word level: one or more `<cmp>` elements with `x, y, width, height` pixel bounding boxes (word can have multiple components)

**Image referencing**
- Images and XML are matched by a shared hierarchical ID scheme: form ID (e.g. `a01-000u`), then line ID = `{form-id}-{line-number}`, then word ID = `{line-id}-{word-number}`. So referencing is filename/ID-based, not IIIF/URI-based — a fully self-contained local addressing scheme, no external repository links at all

**Metadata**
- Per-form: creation date, writer ID, skew angle, image dimensions, status (final/verified/segmented/raw)
- Per-line: segmentation flag (ok/err), plus handwriting-geometry parameters (slant, baseline/ascender/descender slope and position)
- Per-word: `tag` (part-of-speech word type) and sentence-start flag

**Split conventions**
- Only one official task is defined: Large Writer Independent Text Line Recognition
- 9,862 text lines total, split into train / validation 1 / validation 2 / test
- All sets are mutually exclusive by writer, so no writer appears in more than one set
- Split membership distributed as a downloadable ID list (a zip of set-membership files), not as a column in the metadata itself

**Well-designed**
- Genuinely rich, multi-level spatial encoding (baseline slope, slant, contour polylines, per-word bboxes), far beyond a simple rectangle
- Ships two parallel formats (full XML + flattened ASCII) so users can pick complexity level based on their needs
- Task page gives an unambiguous, writer-independent train/val/test breakdown

**Not well-designed**
- The site's own linked example XML file is dead (old domain redirects to the homepage instead of 404ing, so it's not obviously broken at first)
- Official DTD documentation doesn't even specify what standard the `tag` field follows (literally labeled `???` in the DTD's own comments); had to confirm via a third party's inline comments in a mirrored file
- Requires registration before download

---

## RRC (Robust Reading Competition) — Incidental Scene Text

- https://rrc.cvc.uab.es/?ch=4&com=tasks

**File types**
- Images are JPEG or PNG. Ground truth is plain UTF-8 text files, comma-separated, with CR/LF line endings

**Storage granularity**
- Localization: one ground truth file per image, named `gt_[image name].txt`
- Word Recognition: transcriptions for the entire word collection go in a single master file, and a second single master file holds all the bounding box coordinates
- Note how this competition mixes both storage philosophies depending on task (as opposed to CLaMM's uniform "one CSV for everything" approach)

**Spatial encoding**
- Due to being incidental, the text is often skewed. Thus quadrilateral bboxes are used with four corner points given clockwise, format `x1,y1,x2,y2,x3,y3,x4,y4,transcription`
- "Do not care" convention: illegible or excluded regions are still included as annotated boxes, but with the literal transcription value `###`

**Image referencing**
- The ground truth file's name is deterministically derived from the image's own filename (`gt_[image name].txt`)

**Metadata**
- Just bbox coordinates and transcription
- No shelfmark/language/date-style fields here at all

**Split conventions**
- All three tasks draw from the same underlying image pool: 1,000 training / 500 test scene images
- Localization and End-to-End tasks use full scene images with per-image quadrilateral ground truth
- The Word Recognition task uses pre-cropped, individual word images extracted from that same pool (~4,500 word crops from training, ~2,000 from testing)

**Well-designed**
- Ground truth format is spelled out explicitly and precisely on the task page itself, no digging through a zip required
- Smart "do not care" convention: ambiguous regions stay spatially annotated (preserving completeness) but are flagged `###` to exclude from scoring
- Quadrilateral boxes are a deliberate, well-justified design choice given the skewed nature of incidental text

**Not well-designed**
- Storage granularity is inconsistent within the same competition (per-image files for Localization, single master files for Word Recognition); a universal parser has to handle both
- License and exact test-set size weren't directly confirmable from the primary source page itself; had to rely on secondary references

---

## COCO — Object Detection Task

- https://cocodataset.org/#format-data

**File types**
- Single JSON file per split containing everything: `info`, `licenses`, `images`, `annotations`, `categories`
- Actual images are separate JPG files, referenced by filename/URL, not embedded in the JSON

**Storage granularity**
- Maximally aggregated: one JSON file holds annotations for every image and every object instance in the entire split
- Opposite extreme from RRC's one-file-per-image convention

**Spatial encoding**
- Axis-aligned bounding box: `bbox: [x, y, width, height]`, top-left corner + dimensions, pixel units
- Also supports `segmentation` (polygon points, or RLE-encoded mask when `iscrowd = 1`) as a richer alternative to a plain box
- Simplest of all sources gathered so far: no rotation, no contours, no baseline geometry

**Image referencing**
- Each `images` entry has `id`, `file_name`, `width`, `height`; `annotations` link back to images via `image_id`
- Referencing is by numeric ID (join key), not a shared naming convention like RRC or a URI/manifest scheme like CLaMM

**Metadata**
- Dataset-level metadata lives in the `info` block: description, version, year, contributor, date created, source URL
- Licensing is tracked per-image, not globally, via a license ID
- `categories` is a two-level taxonomy: `id`, `name`, and `supercategory`

**Split conventions**
- Separate JSON files per split
- Standard practice: train/val annotations are public, test set annotations are withheld and scored via an evaluation server rather than released

**Well-designed**
- Clean, minimal, single-file schema with strong separation of concerns (`info` / `licenses` / `images` / `annotations` / `categories`)
- ID-based joins avoid any filename-parsing fragility entirely
- Two-level category taxonomy (`category`/`supercategory`) is a nice touch for hierarchical labeling
- Extremely well-documented and tool-supported, given how ubiquitous it is

**Not well-designed**
- Axis-aligned only — no native support for rotated/quadrilateral boxes, so it's a poor fit for skewed or angled text without a workaround
- Per-image licensing via an ID reference is a bit indirect if you just want a quick answer to "what license governs this dataset"
- `segmentation` field's shape changes depending on the `iscrowd` flag (polygon vs. RLE), adding a small parsing inconsistency

---

## PASCAL VOC

- http://host.robots.ox.ac.uk/pascal/VOC/

**File types**
- JPEG images
- One XML annotation file per image
- Plain text files listing image IDs per split
- For the segmentation task specifically: also ships PNG segmentation masks

**Storage granularity**
- One XML file per image — opposite pattern from COCO's single master JSON per split
- Fixed folder structure ties everything together (images, annotations, and split lists live in separate top-level folders)

**Spatial encoding**
- Axis-aligned bounding box: `x_min, y_min, x_max, y_max` (opposite corners)
- Segmentation task adds pixel-level PNG masks as a separate, richer alternative to the box

**Image referencing**
- XML's `<filename>` field matches the actual JPEG filename in `JPEGImages/`
- Pure folder/filename convention, no ID-based join (unlike COCO) and no URI/manifest scheme (unlike CLaMM)

**Metadata**
- Per-image: `folder`, `filename`, `source` (database/annotation info), `size` (width/height/depth), `segmented` flag
- Per-object: `name` (class label), plus `truncated`/`difficult`/`occluded`/`pose` flags
- No licensing, date, or provenance fields

**Split conventions**
- Splits stored as plain text ID lists (`train.txt`, `val.txt`, `trainval.txt`, `test.txt`), one image ID per line — split membership is a separate file, not a field inside each XML

**Well-designed**
- Rich per-object flags (`truncated`, `difficult`, `occluded`, `pose`) let downstream users filter out ambiguous cases from evaluation without needing to inspect images directly — more nuanced than a bare bbox+label
- Split membership as separate plain-text ID lists keeps the annotation files themselves untouched by split logic — you can redefine splits without editing every XML
- Simple, self-contained folder convention (images/annotations/splits each in their own top-level folder) with no external dependencies

**Not well-designed**
- No licensing, date, or provenance metadata anywhere in the schema
- Corner-coordinate format rather than width/height means every downstream tool that expects COCO-style boxes needs a conversion step
- One file per image (versus one master file) means split-wide operations require parsing thousands of small files instead of one, unlike COCO's single JSON

---

## ImageNet / ILSVRC

- https://www.image-net.org/challenges/LSVRC/

**File types**
- Images: JPEG (originally third-party URLs, later packaged into synset-grouped tar archives)
- Ground truth: XML, one file per image, reusing PASCAL VOC's schema rather than a new one
- A flattened CSV variant also exists in some redistributions (e.g. Kaggle), aggregating the whole split into one file

**Storage granularity**
- One XML file per image, same as VOC — `{image_id}.xml` matching `{image_id}.JPEG`
- And a convenience CSV which aggregates the whole split into one file

**Spatial encoding**
- Axis-aligned bounding box, `xmin/ymin/xmax/ymax` — identical convention to VOC, pixel coordinates
- No segmentation masks, no polygon/rotation support

**Image referencing**
- Filename-based, same convention as VOC: XML `<filename>` matches the actual JPEG
- No ID-based join, no URI/manifest scheme

**Metadata**
- Category system is WordNet synsets rather than a flat class list — a hierarchical taxonomy
- Per-object fields largely inherited from VOC's schema

**Split conventions**
- Multiple named challenge tracks (classification, single-object localization, detection) each with their own train/val/test breakdown
- Full ImageNet classification training set: roughly 1.28 million images across 1,000 classes, with 50,000 validation and 100,000 test images
- Test set annotations withheld, scored via a submission/evaluation process — same withheld-test convention as VOC2012 and COCO

**Well-designed**
- Reusing VOC's existing XML schema instead of inventing a new one meant tools built for VOC worked on ImageNet with minimal changes
- WordNet synset hierarchy gives categories real semantic structure (nested relationships), richer than a flat class list
- Multiple named challenge tracks with clearly defined train/val/test splits per task

**Not well-designed**
- Images are third-party URLs rather than hosted/owned by ImageNet itself, so licensing has to be checked per-image/per-source rather than covered by one blanket statement — a genuine long-term maintenance problem (many original URLs have since rotted)
- Dropped VOC's truncated/difficult-style flags so ImageNet boxes are lighter but carry less per-object nuance than VOC's

---

## Open Images

- https://storage.googleapis.com/openimages/web/factsfigures_v7.html
- https://storage.googleapis.com/openimages/web/download_v7.html

**File types**
- Images: JPEG, ~9 million total, hosted via URLs (with an option to bulk-download via Amazon S3/CLI tools rather than one-by-one)
- Ground truth: flat CSV files (not XML, not JSON) — a real departure from VOC/ImageNet/COCO
- Separate CSV files exist per annotation type: bounding boxes, image-level labels, segmentation masks, visual relationships, point-level labels, localized narratives (which are instead JSON Lines, one exception to the CSV pattern)

**Storage granularity**
- One CSV per split per annotation type covers every image in that split
- Large files are further split into smaller shards purely for download convenience, then meant to be concatenated back together

**Spatial encoding**
- Axis-aligned bounding box, but coordinates are normalized to a 0–1 float range, not absolute pixels
- Also supports segmentation masks (for a 350-class subset) and point-level labels (single x,y point rather than a box) as alternative annotation types
- Visual relationship annotations link pairs of boxes together with a relationship label (e.g. "is," or a verb linking two objects)

**Image referencing**
- Each row is keyed by an `ImageID`, joining across the separate CSV files (labels, boxes, relationships) the same way COCO uses `image_id`
- Images themselves are fetched via URL or bulk download tools, separate from the annotation CSVs entirely

**Metadata**
- Class descriptions given in a separate `class-descriptions.csv` mapping label codes to human-readable names — same "numeric/coded label needs a separate legend file" pattern seen in CLaMM, but here the organizers do ship the legend alongside the data
- Category hierarchy also available as a downloadable JSON tree — classes aren't flat, they're organized in a hierarchy similar in spirit to ImageNet's WordNet synsets

**Split conventions**
- Three named splits: train, validation, test
- Only a subset of the ~9 million total images (1.9 million) has the dense bounding-box/segmentation/relationship annotations; the rest have only image-level labels — so unlike other sources, split membership doesn't guarantee the same annotation richness across all images in that split

**Well-designed**
- Normalized 0–1 coordinates mean the same annotation file works regardless of what resolution you download the image at — no need to re-scale boxes if you fetch a different image size
- Class legend (`class-descriptions.csv`) shipped directly alongside the coded labels, unlike CLaMM's numeric labels with no inline mapping
- Category hierarchy provided as a separate downloadable structure, giving semantic relationships between classes without bloating the main annotation files
- Multiple annotation types (boxes, relationships, masks, points) kept in separate files rather than crammed into one schema, so users only need to load what they actually use

**Not well-designed**
- Annotation richness isn't uniform across the dataset: only ~1.9 million of the ~9 million images have dense annotations (boxes/masks/relationships), the rest are image-level-only — easy to assume full coverage and be wrong
- Large files are pre-split into shards purely for download convenience, requiring manual reconstruction (concatenation) before use — an extra processing step other sources don't impose
- CSV-per-annotation-type structure means cross-referencing something like "which boxes have a segmentation mask too" requires joining multiple large CSVs by `ImageID` yourself, rather than getting it pre-joined in one file

---

## PAGE XML — READ-BAD

- https://github.com/PRImA-Research-Lab/PAGE-XML
- https://github.com/TUWien/Benchmarking

**File types**
- Images: JPEG
- Ground truth: one PAGE XML file per page image, sitting in the same folder as its corresponding JPEG

**Storage granularity**
- Nested by archival collection, not flat: each split's archive contains a subfolder per contributing archive, with that institution's JPEGs and PAGE XMLs sitting together inside it
- Packaged as four separate `.tar.gz` archives (train/test × simple/complex), rather than one archive per split

**Spatial encoding**
- Full nested hierarchy: `Page` → `Region` → `TextLine` → `Word` → `Glyph`, each defined by a polygon outline (`Coords points="..."`), not a rectangle
- Text lines carry an explicit baseline polyline
- An explicit reading order element records logical region sequence
- Regions can nest recursively (e.g. table cell inside table region)
- Richest spatial encoding of any source gathered so far

**Image referencing**
- Filename-based, no ID join or URI/manifest scheme: the `Page` element's `imageFilename` attribute names the corresponding image directly
- Filenames encode collection/place name plus document and page identifiers (e.g. `M_Aigen_am_Inn_002-01_0000.jpg`) — a distinct scheme per contributing archive, similar in spirit to CLaMM's mixed institutional filename conventions, but here each scheme stays contained within its own subfolder rather than scattered through one flat directory

**Metadata**
- Per-file `Metadata` block: `Creator`, `Created` timestamp, `LastChange` timestamp
- Regions carry a `type` attribute (paragraph, header, caption, etc.)
- Text content stored at multiple levels (region and line) simultaneously
- Format explicitly supports custom/extension attributes (e.g. Transkribus adds its own fields on top)

**Split conventions**
- Images collected from 9 European archives (1470–1930)
- Two subsets by layout complexity: Simple Documents and Complex Documents
- Simple Documents: 216 training / 539 test
- Complex Documents: 270 training / 1,010 test
- Notably test-heavy split (~76% of the dataset is test, not training)

**Well-designed**
- Polygon boundaries handle skewed/irregular text better than any axis-aligned box
- Explicit reading order element, unlike any other source
- Nested hierarchy (region → line → word → glyph) lets users pick their own granularity
- Designed to be extended (Transkribus adds custom fields on top)
- Archive/institution grouping preserved as real folder structure, not just a metadata field
- Splitting by layout complexity isolates detection difficulty from layout reasoning difficulty

**Not well-designed**
- Image file format undocumented anywhere; had to download and inspect directly to confirm JPEG
- `.tar.gz` packaging loses Zenodo's zip-preview convenience
- Four separate archives (train/test × simple/complex) is more fragmented than most sources
- Filenames still vary by contributing archive, same parsing friction as CLaMM
- Schema richness raises the barrier to entry versus a flat CSV or simple bbox JSON