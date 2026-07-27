# Dataset Formats Research Spike — Track A

Detailed per-dataset notes (file types, storage granularity, spatial encoding, image referencing, metadata, split conventions, well-designed/not well-designed) live in [`dataset_formats_notes.md`](./dataset_formats_notes.md).

## Reading the Table

Tag matrix comparison table: [`dataset_formats.csv`](./dataset_formats.csv)

Storage granularity splits roughly along task lines. Classification and retrieval datasets (HDRC-IR, both CLaMM years, COCO, Open Images) tend to aggregate everything into one master file per split. Precise localization datasets (IAM, VOC, ImageNet, PAGE XML), by contrast, favor one file per image, keeping annotation and image tightly paired.

Spatial encoding richness tracks directly with task difficulty, not dataset age or prestige. The three N/A rows are all classification/retrieval tasks that never needed spatial data at all. Three widely-used detection benchmarks (VOC, ImageNet, Open Images) stop at a simple axis-aligned box. Only two sources here (IAM, PAGE XML) go beyond a rectangle into baselines, contours, or reading order, both specifically because they're modeling handwritten text rather than photographed objects.

Image referencing is almost always local (filename or numeric ID). IIIF's nested manifest structure stands out as the one genuinely different, hierarchical approach, worth noting since it's also the only convention here tied to external, live infrastructure rather than a static file shipped with the download.

---

## Recommendations

**File types.** I recommend JPEG or TIFF for page images and JSON or XML for annotations, following either COCO's or PAGE XML's precedent rather than a custom schema. Both formats already have mature parser and tooling support; a novel schema adds adoption friction without a clear benefit here. Worth noting: CATDOES currently produces custom JSON outputs, but the project already has precedent for converting that output to PAGE XML via a simple conversion script, so PAGE XML may be the right choice given this existing infrastructure.

**Storage granularity.** I recommend one annotation file per manuscript page, following the convention used by every localization-focused source in the table (IAM, VOC, ImageNet, PAGE XML). Aggregated master files appear mainly among classification/retrieval datasets, a different task category than ours.

**Spatial encoding.** I recommend a bounding box or polygon per word, with baseline and reading-order fields modeled on PAGE XML only if the team determines our manuscript text is not reliably axis-aligned; otherwise a simpler axis-aligned box, the community default for object detection generally, is sufficient and avoids unneeded complexity.

**Image referencing.** I recommend a filename or ID-based join, the norm across nearly every source reviewed, rather than IIIF's manifest structure, which ties the dataset to live external infrastructure. A source-repository URL can still be preserved as an optional metadata field for provenance.

**Metadata.** I recommend including shelfmark, script type, language, and date as native fields, not offloaded to an external link, and shipping an inline legend for any coded/categorical fields. Several sources reviewed (CLaMM, HDRC-IR) caused friction by omitting exactly this kind of descriptive metadata.

**Split conventions.** I recommend splitting by manuscript or scribe rather than by page, following IAM's writer-independent and PAGE XML's complexity-based split conventions. Manuscripts in our collection likely span multiple hands, so a naive random split risks leaking similar handwriting across train and test.

---

## Open Questions for the Team

- **Polygon vs. bounding box vs. both**: Should we require a full polygon per word (more accurate, more annotation effort) or accept an axis-aligned box as the baseline requirement, with polygons as an optional enrichment?
- **Text alignment**: Is manuscript text in our target collection reliably axis-aligned, or does enough of it (skewed lines, curved layouts, etc.) warrant a richer polygon/baseline encoding instead of a simple bounding box?
- **Baseline and reading order**: Do we adopt PAGE XML style baseline and reading-order annotations in full, or is that scope better left for a future dataset version?
- **File format for annotations**: JSON (COCO-style, easier tooling support) versus XML (PAGE-style, closer to our existing pipeline and to community convention in the manuscript-analysis space), which better serves our anticipated users?
- **Metadata depth**: How much scholarly metadata is realistic to require per page or per manuscript (shelfmark, date, language, script type, provenance), given the added annotation burden versus the value of the "domain expertise" we want to offer?
- **Split strategy**: Should splits be defined by manuscript, by scribe/hand, or by some other unit, and do we have (or need) reliable scribe-attribution metadata to support that split in the first place?
- **License and access model**: Fully open (Zenodo/CC-BY style) versus a registration-gated download (CLaMM/IAM style); does the team have a preference, and does our data's sensitivity or institutional agreements constrain this choice?
- **Image referencing durability**: Do we want to preserve a link back to source digital libraries (IIIF or otherwise) as optional provenance metadata, and if so, whose responsibility is it to verify those links stay live over time?

---

## Bibliography

Christlein, Vincent, Anguelos Nicolaou, Mathias Seuret, Dominique Stutzmann, and Andreas Maier. "ICDAR2019 Competition on Image Retrieval for Historical Handwritten Documents (HisIR19) Dataset." Zenodo, 2019. https://doi.org/10.5281/zenodo.3262372.

Classification of Medieval Handwritings in Latin Script. "Data Set" (ICDAR2017-CLaMM). Accessed July 23, 2026. https://clamm.irht.cnrs.fr/icdar-2017/data-set/.

Classification of Medieval Handwritings in Latin Script. "Data Set" (ICDAR2019-HDRC-Image-Retrieval). Accessed July 23, 2026. https://clamm.irht.cnrs.fr/icdar2019-hdrc-ir/data-set/.

Classification of Medieval Handwritings in Latin Script. "Data Set" (ICFHR2016-CLaMM). Accessed July 23, 2026. https://clamm.irht.cnrs.fr/icfhr2016-clamm/data-set/.

COCO Consortium. "COCO – Common Objects in Context: Data Format." Accessed July 23, 2026. https://cocodataset.org/#format-data.

Everingham, Mark, S. M. Ali Eslami, Luc Van Gool, Christopher K. I. Williams, John Winn, and Andrew Zisserman. "The PASCAL Visual Object Classes Challenge: A Retrospective." *International Journal of Computer Vision* 111, no. 1 (2015): 98–136.

Google. "Open Images Dataset V7: Facts and Figures." Accessed July 27, 2026. https://storage.googleapis.com/openimages/web/factsfigures_v7.html.

Google. "Open Images Dataset V7: Download." Accessed July 27, 2026. https://storage.googleapis.com/openimages/web/download_v7.html.

Grüning, Tobias, Roger Labahn, Markus Diem, Florian Kleber, and Stefan Fiel. "READ-BAD: A New Dataset and Evaluation Scheme for Baseline Detection in Archival Documents." arXiv preprint arXiv:1705.03311, 2017. https://arxiv.org/abs/1705.03311.

Karatzas, Dimosthenis, Lluis Gomez-Bigorda, Anguelos Nicolaou, Suman Ghosh, Andrew Bagdanov, Masakazu Iwamura, Jiri Matas, Lukas Neumann, Vijay Ramaseshan Chandrasekhar, Shijian Lu, et al. "ICDAR 2015 Competition on Robust Reading." In *2015 13th International Conference on Document Analysis and Recognition (ICDAR)*, 1156–60. Piscataway, NJ: IEEE, 2015.

Marti, U.-V., and H. Bunke. "The IAM-Database: An English Sentence Database for Off-Line Handwriting Recognition." *International Journal on Document Analysis and Recognition* 5 (2002): 39–46.

PRImA Research Lab. "PAGE-XML." GitHub repository. Accessed July 27, 2026. https://github.com/PRImA-Research-Lab/PAGE-XML.

Research Group on Computer Vision and Artificial Intelligence, University of Bern. "IAM Handwriting Database." Accessed July 23, 2026. https://fki.tic.heia-fr.ch/databases/iam-handwriting-database.

Robust Reading Competition. "Tasks – Incidental Scene Text." Accessed July 23, 2026. https://rrc.cvc.uab.es/?ch=4&com=tasks.

Russakovsky, Olga, Jia Deng, Hao Su, Jonathan Krause, Sanjeev Satheesh, Sean Ma, Zhiheng Huang, Andrej Karpathy, Aditya Khosla, Michael Bernstein, Alexander C. Berg, and Li Fei-Fei. "ImageNet Large Scale Visual Recognition Challenge." *International Journal of Computer Vision* 115, no. 3 (2015): 211–252.

Stutzmann, Dominique, and Marlène Helias-Baron. "ICDAR 2017 Competition on the Classification of Medieval Handwritings in Latin Script Dataset." Zenodo, 2017. https://doi.org/10.5281/zenodo.5527690.

Stutzmann, Dominique, and Marlène Helias-Baron. "ICFHR2016 Competition on the Classification of Medieval Handwritings in Latin Script Dataset." Zenodo, 2016. https://doi.org/10.5281/zenodo.5526880.

TU Wien Computer Vision Lab. "Benchmarking (READ-BAD / cBAD Dataset)." GitHub repository. Accessed July 27, 2026. https://github.com/TUWien/Benchmarking.