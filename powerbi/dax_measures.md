# Power BI – DAX mere

## Competency Score

Weighted prosek assessment rezultata za izabranu kompetenciju.

```DAX
Competency Score =
DIVIDE(
    SUMX(
        FactAssessmentScore,
        FactAssessmentScore[Score] * FactAssessmentScore[Weight]
    ),
    SUM(FactAssessmentScore[Weight])
)
```

## Overall Score

Prosek pet competency score-ova, gde svaka kompetencija ima jednaku težinu na nivou kandidata.

```DAX
Overall Score =
CALCULATE(
    AVERAGEX(
        VALUES(DimCompetency[Competency]),
        [Competency Score]
    ),
    REMOVEFILTERS(DimCompetency[Competency])
)
```

## Candidate Count

```DAX
Candidate Count =
DISTINCTCOUNT(FactAssessmentScore[CandidateID])
```

## Average Assessment Score

```DAX
Average Assessment Score =
AVERAGE(FactAssessmentScore[Score])
```

## Average Method Score

```DAX
Average Method Score =
AVERAGE(FactAssessmentScore[Score])
```

## Assessment Count

```DAX
Assessment Count =
COUNT(FactAssessmentScore[Score])
```

## Candidate Name

Koristi se na Candidate Detail stranici.

```DAX
Candidate Name =
SELECTEDVALUE(DimCandidate[Candidate])
```

## Score Label

Pomoćna calculated column za distribuciju rezultata 1–5 u vizualu.

```DAX
Score Label =
FORMAT(FactAssessmentScore[Score], "0.0")
```
