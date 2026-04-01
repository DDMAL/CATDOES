#### 24.03.26

## Initial report - Layout models vs. Text models

These are my initial impressions! For now, the proof is only in pretty pictures, but I’ll add the numbers to back those up shortly.

Transkribus organizes information on a given page with regions and lines. Regions are 2D and they cover a paragraph of text (like in a newspapers, for example, where text is organized in rubrics of various shapes and sizes), and lines are 1D and they underline any line of text. 

When analyzing a page, Transkribus tries to recognize regions and lines and then transcribe the text written on the lines it has found. Because musical manuscripts have a lot going on in them, simply asking Transkribus to perform a text analysis on a musical page doesn’t really work; it struggles to make sense of the initials, rubrics and staves, so the regions and lines it finds are wrong. Thankfully, Transkribus allows the user to train text models OR layout models. My initial thought is that training only a text model won’t be sufficient; even if Transkribus learns to read the text perfectly, it’ll still get bamboozled by initials, rubrics, and staves.

> [!Important]
> I think the solution is to train a layout model and a text model, and run them in sequence (layout first, text second). 

There are two kinds of layout analyses that could apply: the Layout analysis and the Fields analysis. The Fields analysis is behind a paywall, but from what I can tell so far, the Layout analysis finds lines of text, and the Fields analysis finds regions of text. It’s possible we may need both, unless Fields can do both regions and lines.

### First training attempt - Layout model

Since I can’t use the Field analysis at the moment, I tried to train a Layout analysis model to make sense of initials and rubrics and, most importantly, ignore staves and the neumes on them.

I trained the model using Salzinnes folios 028r, 038v, 060v, 097r, 100r, 122r, 149v, and 191v as ground truth. I annotated regions and lines and didn’t input any actual text. I tried to teach the model three things:
-	Ignore musical staves always;
-	Recognize blue or red initials as text, and separate them from the text preceding and following;
-	Separate a line of chant from a line of rubric (chant text is black, rubric text is red).
  
I used Salzinnes 083r to measure the results. The results:
-	All musical staves are ignored (eyo!!); 
-	All blue or red initials are recognized as text, and about half of them are separated from the text preceding and/or following;
-	Lines of chant are not separated from lines of rubric.

Here’s a comparison image of 083r, where the first screenshot is the Layout analysis using Transkribus’ Universal Lines model, and the second screenshot is the Layout analysis using my model.

<img width="1083" height="823" alt="Salz 083 side by side" src="https://github.com/user-attachments/assets/d6e1ad9f-833c-4c39-935f-acef22c29350" />

The very good news is that I also tried my little model on an Einsie folio (014r) and, lo and behold, it was still able to ignore all staves and neumes:

<img width="1163" height="824" alt="Einsie 014r side by side" src="https://github.com/user-attachments/assets/935551a0-63eb-4cc5-bef6-e3b89d70a6b0" />

Just for laughs, I also tried my model on a folio with adiastematic neumes (A-Wn Cod. 1890 p.23) and it didn’t do as well, but it still ignored a lot more neumes than the Universal Lines model did, which is quite rad.

<img width="1368" height="823" alt="A-Wn p 23 side by side" src="https://github.com/user-attachments/assets/64217b43-ce7f-44b2-919b-a57de8d9b9aa" />

#### 01.04.26

## Training a text model - Abbreviations edition

Chant manuscripts have a lot of abbreviations, like virginē (virginem), qƺ (quem), or ſuꝑ (super). CantusDB expands all the abbreviations, so Rodan does as well, because we always give it the corrected chant text from CantusDB. We wanted to know whether it would be easier to create a Transkribus model that expands abbreviations, or a model that transcribes all abbreviations as is. (Transkribus gives the option to provide it with a corrected text, BUT that option is currently behind a paywall, so we wanted to see what it could do without any extra help.)

TBC




