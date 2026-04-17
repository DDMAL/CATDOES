For the most recent summary of results, please refer to the [Overall summary](https://github.com/DDMAL/CATDOES/edit/main/Gen_Transkribus/Gen_Transkribus_observations.md#overall-summary) lower down on this page!

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

## 16.04.26 IMPORTANT UPDATE!!!!!

I have just discovered that although Field models are measured with MAP, so the higher the better, Layout models _say_ that they're measured with MAP but they're actually measured with Percentage Lost on Validation, so it should be low! It frustrates me NO END that Transkribus uses the same name for two OPPOSITE metrics!!!!!! GAH. So anyway, that explains why all my layout models had MAPs below 10% despite looking great.

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

## Importing text

From my experiments so far, giving Transkribus chant texts from CantusDB doesn't actually seem to help... For one thing, when you give Transk pre-transcribed text, I think it tries to take line and paragraph breaks into consideration (https://help.transkribus.org/import-existing-transcriptions-with-text-image-matching). This isn't great for the text transcriptions you can get off CantusDB, because those are broken into paragraphs based on chants; new chant, new paragraph. The line breaks have nothing to do with how the chant is laid out on the folio.

Also, it feels like Transk isn't using the text to aid its transcription, but rather to validate its transcription. So it first transcribes the text on the folio using the model I created, then it tries to match that text to the provided transcription, line by line; if the Transk and the CantusDB transcription of a given line match (within a pre-established acceptable margin of error), then Transk will validate that line and it'll show up in the final transcription. Every line that doesn't match gets pushed to the bottom of the transcription, under the "Unmatched" category. If you combine that with the fact that Transk's definition of a line is different from CantusDB's definition of a line (as explained above), you can see how problems arise quickly. So it's my impression that the Text Import feature might not actually help the text recognition training at all... Will keep exploring.

#### 09.04.2026

## First Fields model attempt

Now that I have Pro Transk (woo!!) I have started exploring the Fields analysis function. I tried to train a Fields model using the eight Salzinnes folios I had used so far: 028r, 038v, 060v, 097r, 100r, 122r, 149v, and 191v. Just as I did for the Layout model I made, I made separate regions for initials, chants, rubrics, and folio numbers. In terms of the lines of text, I always separated initials from the text following, and rubrics from the text before or after. I also added one of four tags to every region: Chant, Initial, Folio number, or Rubric. Final folios looked like this (lines of text are blue and regions are outlined in green):

<img width="432" height="706" alt="028r ground truth" src="https://github.com/user-attachments/assets/9159f3dc-434e-41a9-b6c1-37b57922f757" />

When training a Fields model, you can choose to either train the tags or the line polygons. I _think_ that training the tags means you train the model to identify the tag of each region it finds, and training the line polygons means you train the model to identify the delineation of regions. BUT, Transk seems to suggest that you can run a tags Field analysis before you do anything else, which means that the model is also identifying regions? I'm honestly still confused about this, but I'm working on figuring it out. More later.

For my first ever Fields model, I decided to train line polygons, because I'm still trying to figure out how to teach Transk to identify a manuscript's wonky regions. The resulting model has an MAP of 53,49%, which is... not bad? Transk defines 60% as a reasonably good MAP, so it's a good first attempt. Here it is:

<img width="587" height="704" alt="First Fields model attempt" src="https://github.com/user-attachments/assets/55249c94-cdc6-4bfd-be88-6c5fa7db04eb" />

Two things to note:
1. You can't see any green region lines in this screenshot because the only region the model found was the entire folio. So that didn't work.
2. On the other hand, the lines are _perfect_. All of the initials are separate lines, as are all the rubrics, including lines of rubric that are aligned with lines of chant! This is a much better result than the layout model did, which is slightly mystifying, but we'll take it.

The news for the lines is great, but I don't understand why Transk is still completely incapable of identifying regions as I'm trying to teach it to do. So I'm now training a new Fields model on the exact same training data, but asking it to train the tags rather than the line polygons. I'm waiting on Transk to train that model, I'll report back soon.

Once I've (hopefully) established how training tags differs from training line polygons, I'll increase the training dataset by four folios and try two things:
- Including the initials in the chant regions (thereby removing the Initial regions altogether);
- Not do that, and keep Initial regions as they are.

#### 13.04.2026

## Report on training tags

My first Field model trained on tags is complete, and I can confirm that a tags model _only_ finds the correct tag for each region; it cannot find the regions themselves. I'm still confused, because [the documentation](https://help.transkribus.org/newspapers-layout-recognition) clearly states that you should run a Fields analysis before running a Layout analysis, so I feel like something isn't clear somewhere. 

(For the record, the mAP of that Field model is -100%, which is hilarious.)

So! My next step is to train Layout models and Field models on 12 folios instead of 8 to compare the two, and also to figure out whether each model performs better when the initials are included in the same regions as their corresponding chant, versus when they're their own regions. So it'll look something like this:

| x  | Layout model | Field model |
| ------------- | ------------- | --- |
| **Initials in chant**  | result | result |
| **Initials out chant**  | result | result |

#### 16.04.26

## Many more tests done

First, the result of the tests I described above, with two reminders:

1. My goal for these models is to have lines of text under chant text, initials, and rubrics, and to have one region per chant and per rubric; 
2. Field models measure accuracy with the MAP, which should be high, and Layout models use Percentage Lost on Validation, which should be low.

| x  | Layout model | Field model |
| ------------- | ------------- | --- |
| **Initials in chant**  | `PLV=4.24%` one big region but lines are great | `MAP=0.22%` one big region but lines are great |
| **Initials out chant**  | `PLV=4.39%` one big region but lines are great  | `MAP=0.08%` one big region but lines are great|

Looking at the four models applied to the same folio, it's clear that the results are super similar:

<img width="1181" height="411" alt="083r four models" src="https://github.com/user-attachments/assets/116fa2a2-33df-490d-8358-7dc06bb0fee7" />

In other words, whether initials are included in the same region as the chant or not makes very little difference. Transkribus can find lines, but it refuses to segment the different chants into different regions.

Since the region segmentation just wasn't working, I decided to try a new tack and forget about regions for a bit. After all, the reason that I was trying to divide the folios into regions in the first place was to separate rubrics from chant, so that Transkribus would have a better chance at reading those in the correct order. So I realized that since Transkribus was so reluctant to make multiple regions, maybe it could learn to differentiate chant from rubric without using regions at all. I tried two new tests:

1. Do one big region per folio, just like Transk would do;
2. Keep the multiple regions, but delete every region that contains a rubric.

For both, I trained a Field model, and the results look like this:

| x  | Field model |
| ------------- | ------------- |
| **One big region**  | `MAP=40.67%` some rubrics have multiple lines under them |
| **Multiple regions, rubric regions deleted**  | `MAP=48.9%` a few lines of rubric still included |

<img width="845" height="626" alt="083r one region vs  no rubrics" src="https://github.com/user-attachments/assets/84ad241c-67b2-4d51-a779-307fb3300f2b" />

Better! I wondered what would happen if I combined the two--one big region, and no lines of text under any rubrics. So I did both a Field and a Layout model with those characteristics:

| x  | Layout model | Field model |
| ------------- | ------------- | --- |
| **One big region no rubrics**  | `PLV=5.29%` looks great! No rubrics included | `MAP=49.51%` looks great! No rubrics included |

Here's 083r one final time with this final Layout model:

<img width="456" height="634" alt="083r Layout one region no rubrics" src="https://github.com/user-attachments/assets/287c7b98-a2c2-4550-b3cc-ce9a80ceaedf" />

Gorgeous! All initials have lines under them and rubrics are completely ignored. Job done! I guess regions are dumb anyway. 

# Overall summary

If we want to use Transkribus to identify and transcribe the text of a chant manuscript folio, I suggest using these parametres:
1. Train a layout (baseline) model that:
   - Has one big region that covers the whole folio;
   - Has a blue line of text under all chant text, including initials;
   - Has **_no_** line of text under rubric text.
2. Train a text model that transcribes the text as is, without expanding abbreviations like CantusDB does. (You can use Transkribus' handy dandy bespoke keyboards that have all the necessary fancy letters.)
3. Once you have both models, run the layout model first, then the text model.

From what I can tell so far, a layout model trained on a manuscript with staves works very well on other manuscripts with staves.

Some questions remaining:
- Seeing as Transk seems to be confused about CER vs. MAP vs. PLV, can we really trust those metrics to compare its performance with Rodan or other such websites? Especially the MAP, which to my eyes doesn't really represent how successful the model is visually.
- What is up with the regions? Why can't I get Transk to figure those out?
- If we ignore the rubrics, is there a way to use the text import function to improve text recognition performance? Or is that off the table if we don't train Transk to expand abbreviations?

#### 17.04.26

## Fake newspaper test

I wanted to figure out whether Transkribus not being able to find more than one region was a me-problem or a Transk-problem, so I tried making a simple fake newspaper. My goal was to have super clear headings and columns of text; Transkribus says that it should be possible to transcribe newspapers with complex layouts, so I figured if I made a super simple layout it should at least be able to find a couple of different regions.

I trained a model on four such pages of fake newspaper, making a separate region for each heading and column of text. Like this:

<img width="872" height="551" alt="Fake newspaper goal" src="https://github.com/user-attachments/assets/ffcdb2c9-6486-4243-b7f9-fa60ab66b4e6" />

And... it didn't work! Transk still wants to have one big region over the whole page. Like this: 

<img width="826" height="489" alt="Fake newspaper result" src="https://github.com/user-attachments/assets/14c86ef6-5af8-43b9-b2c9-3965d3c95983" />

And here's the best part: when testing the results of my model, I accidentally ran my Salzinnes one-region-no-rubrics model on the fake newspaper. This happened:

<img width="480" height="635" alt="Fake newspaper result 2 w: Salz layout?" src="https://github.com/user-attachments/assets/d6956719-58ba-4e57-8b07-89701c94dd11" />

What?!??? That model was _specifically_ trained to group the whole folio into one region, and that's what happens? Whereas the model that was trained to separate the regions gives me one big region? Baffled.






