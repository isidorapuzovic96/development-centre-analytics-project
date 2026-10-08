# Kratko objašnjenje projekta

## Šta radi Python

Python uzima source assessment podatke, proverava strukturu, raspon i format ocena, proverava duplikate, evidentira tri potvrđene greške za `Integritet + Test`, izuzima ih iz analitičkog sloja i zatim računa weighted competency score i overall score.

Posle toga radi osnovnu deskriptivnu analizu: proseke, median, standardnu devijaciju, raspone, raspodelu ocena i pregled rezultata po assessment metodama.

Na kraju Python poredi izračunate rezultate sa consolidated business rezultatima. Očekivanje je 48/48 PASS.

## Šta radi SQL

SQL predstavlja isti skup podataka kao relacioni model. Dimension tabele čuvaju kandidate, grupe, kompetencije i assessment metode. Fact tabela čuva score i weight.

Kroz JOIN i agregacije dobijamo competency i overall score, a zatim možemo da postavljamo konkretna HR pitanja kroz SQL upite.

## Šta radi Power BI

Power BI koristi fact i dimension model za interaktivni dashboard. DAX mere primenjuju istu weighted business logiku koju smo validirali u Pythonu i SQL-u.

Dashboard je podeljen na:

* **Overview** – osnovni pregled rezultata
* **Assessment Methods Analysis** – rezultati i raspodela po metodama
* **Candidate Detail** – detaljan pregled izabranog kandidata



Dataset ima 8 kandidata. Zbog toga su glavni nalazi deskriptivni i fokusirani na razlike u rezultatima, varijabilnost, raspodelu i business KPI-jeve. Ne izvode se generalizacije na širu populaciju.

