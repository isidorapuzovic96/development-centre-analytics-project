# Development Center HR Analytics

## O projektu

Ovaj projekat analizira rezultate anonimnog Development Center procesa. Cilj je da se iz rezultata assessmenta dobiju konzistentni competency score-ovi, ukupni score kandidata i pregled rezultata po kompetencijama i assessment metodama.

Projekat je napravljen kao portfolio primer za Junior Data Analyst / HR Data Analytics poziciju.

## Korišćeni alati

- **Python** – čišćenje, validacija, scoring i deskriptivna analiza
- **SQL Server** – relacioni model, JOIN, filtering i agregacije
- **Power BI** – data model, DAX mere, sliceri, interakcije i drill-through
- **Git/GitHub** – organizacija i prezentacija projekta

## Poslovna logika

Assessment score je na skali 1–5, u koracima od 0.5. Prazna vrednost znači da metoda nije primenljiva za datu kompetenciju; ne tretira se kao nula.

Competency Score se računa kao weighted average:

`SUM(Score × Weight) / SUM(Weight)`

Overall Score je aritmetički prosek pet competency score-ova.

Grupa 1 koristi Prezentaciju, dok Grupa 2 nema Prezentaciju. Grupe predstavljaju različit dizajn assessment procesa i ne tretiraju se kao eksperimentalna i kontrolna grupa.

## Data quality

U source podacima pronađena su tri potvrđena pogrešna unosa: Kandidat 2, Kandidat 3 i Kandidat 4 imaju `Test = 3` za kompetenciju Integritet. Test nije primenljiv na Integritet.

Raw/source podaci ostaju nepromenjeni. Ta tri reda se isključuju iz analitičkog sloja, a problem se dokumentuje u `data/processed/data_quality_issues.csv`.

Source sloj ima 149 redova, a nakon čišćenja analitički sloj ima 146 redova.

## Validacija

Python reconciliation poredi izračunate competency i overall score-ove sa consolidated business rezultatima.

Rezultat validacije:

- 40 competency rezultata
- 8 overall rezultata
- **48/48 PASS**
- maksimalna apsolutna razlika: **0.005**

## Struktura projekta

```text
python/
    hr_analysis.py

sql/
    development_center_hr_analytics.sql

powerbi/
    HR.pbix
    dax_measures.md
    README.md

data/
    source/
    processed/

outputs/

docs/
```

## Kako pokrenuti Python deo

1. Instalirati zavisnosti:

```bash
pip install -r requirements.txt
```

2. Pokrenuti:

```bash
python python/hr_analysis.py
```

Script učitava source CSV, radi data-quality provere, čisti tri potvrđene greške, računa competency i overall score, pravi osnovne EDA outpute i radi reconciliation.

## SQL deo

U SQL Server-u prvo importovati `data/processed/assessment_scores_clean.csv` kao `dbo.AssessmentScores`, a zatim pokrenuti `sql/development_center_hr_analytics.sql`.

Skript kreira dimension i fact tabele, business views i nekoliko analitičkih upita.

## Power BI

`powerbi/HR.pbix` je finalni Power BI fajl korišćen u projektu.

Dashboard sadrži tri stranice:

1. Overview
2. Assessment Methods Analysis
3. Candidate Detail

Dashboard koristi slicere, DAX mere i drill-through funkcionalnost.

## Važne metodološke napomene

Uzorak sadrži 8 kandidata. Zbog malog uzorka analiza je prvenstveno deskriptivna. Ne izvode se inferencijalni zaključci o široj populaciji i ne koriste se metode poput regression ili clustering kao ukrasne analize bez odgovarajućeg uzorka i poslovnog pitanja.
