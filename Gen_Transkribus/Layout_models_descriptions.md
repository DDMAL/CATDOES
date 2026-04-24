### Chant folio layout analysis models

I now have three working models to analyze the layout of a chant manuscript folio. 
UPDATE: I have four! I've updated this page to include this fourth model.

| Model name  | Trained on | Works best on |
| ------------- | ------------- | ----------- |
| Square notation model | CDN-Hsmu M2149.L4 (Salz)  | Anything with square notation, regardless of staff line colour and including two columns |
| Aquitanian model | F-Pn Latin 1090 | Anything with a single red staff line |
| Adiastematic model | CH-SGs 388 | Anything with no staves at all, just text with little squiggles on top |
| Tall staves tiny writing (TSTW) model | CH-P 18 and F-Pn Latin 12044 | Anything with staves that are much taller than the text and where the text and neumes are roughly the same size |

(Detailed information on which folios were used to train each model is at the bottom of this page.)

I tried throwing my models at different manuscripts, just to figure out what each model did best. So far, there's always at least one model that does a decent to good job, which is rad!

<img width="915" height="478" alt="Screenshot 2026-04-22 at 13 48 36" src="https://github.com/user-attachments/assets/eafbe3ee-86bf-4ba5-a4b4-24506b457aff" />

\* About PDF vs. jpg, there's a small difference in performance, but not as big as I suspected!

All of these manuscripts had at least one staff line, which is why the Adiastematic model never worked best. 

### Folios used for model training

**Square notation model**: CDN-Hsmu M2149.L4 (Salz) folios 028r, 038v, 060v, 091v, 097r, 100r, 117v, 122r, 136v, 149v, 180r, 191v

**Aquitanian model**: F-Pn Latin 1090 folios 043r, 075v, 140r, 202v, 206v

**Adiastematic model**: CH-SGs 388 pages 077, 157, 172, 213

**TSTW**: CH-P18 pages 128 and 281 + F-Pn Latin 12044 folios 042v and 084r




