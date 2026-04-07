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

## A word on how Transkribus measures performance

I have found two metrics that Transkribus uses to measure the accuracy of its models:

**CER**: Character Error Recognition - This is used for text models. It calculates "the percentage of characters that have been transcribed incorrectly by the Text Recognition model" by comparing its validation dataset to the ground truth. So the **lower** the CER, the better the model. 

**MAP**: Mean Average Precision - This is used for Layout models. It "evaluates how accurately the system detects and labels regions, considering whether they were detected, and how well their size and shape match the validation data," also by comparing the validation set to the ground truth. So the **higher** the MAP, the better the model.

It's worth noting that I've found discrepancies between those two metrics in Transkribus itself. On this page, which allows you to pick an existing model, the metric listed next to the model names is MAP, which makes the numbers look tragically low. But once you click on a model, the metric becomes the CER, which means that low numbers are good! So beware metrics, I guess.

https://github.com/user-attachments/assets/9d0114b0-9582-4676-b42f-274d016a4721

## Training a text model - Abbreviations edition

Chant manuscripts have a lot of abbreviations, like `virginē` ("virginem"), `qƺ` ("quem"), or `ſuꝑ` ("super"). CantusDB expands all the abbreviations, so Rodan does as well, because we always give it the corrected chant text from CantusDB. We wanted to know whether it would be easier to create a Transkribus model that expands abbreviations, or a model that transcribes all abbreviations as is. (Transkribus gives the option to provide it with a corrected text, BUT that option is currently behind a paywall, so we wanted to see what it could do without any extra help.)

I created two tiny models using the same four Salzinnes folios: 060r, 100r, 149v, and 191v.  

1. I processed all folios using the layout model I had created (see above).
2. For the first ground truth, I expanded all abbreviations and turned every `ſ` into an "s". For the second ground truth, I transcribed everything as is and left every `ſ` as an `ſ`.
3. When trying to train the expanded abbreviation model the first time, I asked Transkribus to start from scratch, and to not use any existing model as a starting base. That DID NOT work. The CER was 100% (lol) and indeed when I tested the model it recognized zero words.
4. So then I trained both models using an existing model as a starting base. That was more successful.

Here are the results:

The expanded abbreviation model has a CER of 88.03%, which is quite bad. The picture speaks for itself:

<img width="965" height="516" alt="Salz 097r abbr  expanded" src="https://github.com/user-attachments/assets/e5eb7340-84a3-46dc-925e-1397980fb18a" />

The transcribed abbreviation model has a CER of 15.37%, which is decent! Keep in mind that the training data was only four folios; if we just double or triple that, I think the performance would be pretty great.

<img width="1219" height="516" alt="Salz 097r abbr  as is" src="https://github.com/user-attachments/assets/11408e38-5bcd-4f43-8ac7-57ac1bdee70d" />

I can think of a few factors that could explain the poor performance of the expanded abbreviation model:
- The dataset was only four folios, and there are a LOT of different types of abbreviations, so there were at absolute most 3-4 instances of a specific abbreviation in the whole dataset.
- As I mentioned before, I couldn't give Transkribus the corrected text to help it out. Once I get the pro version I'll try that out and see if the performance improves.
- The rubrics make things very complicated. Chants have fairly normal abbreviations, but rubrics are on a whole other level! Learning that `p̄s` is "psalm" and that `ā` is "antiphon" is a lot.

> [!Important]
> In conclusion:
> - Transkribus performs significantly better when it is taught to transcribe abbreviations as is;
> - Giving Transkribus the corrected text might completely change that;
> - If we do choose to expand abbreviations, we could consider excluding the rubrics, because they're confusing.

#### 07.04.26

## Thoughts to expand on later

When trying to give Transk pre-transcribed text, I think it tries to take line and paragraph breaks into consideration (https://help.transkribus.org/import-existing-transcriptions-with-text-image-matching). This isn't great for the text transcriptions you can get off CantusDB, because those are broken into paragraphs based on chants; new chant, new paragraph. The line breaks have nothing to do with how the chant is laid out on the folio.

Also, it feels like Transk isn't using the text to aid its transcription, but rather to validate its transcription. So it first transcribes the text on the folio using the model I created, then it tries to match that text to the provided transcription, line by line; if the Transk and the CantusDB transcription of a given line match (within a pre-established acceptable margin of error), then Transk will validate that line and it'll show up in the final transcription. Every line that doesn't match gets pushed to the bottom of the transcription, under the "Unmatched" category. So it's my impression that the Text Import feature might not actually help the text recognition training at all... Will keep exploring.



 




