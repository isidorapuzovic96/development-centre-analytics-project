/*
Development Center HR Analytics
SQL Server model + business queries

Objašnjenja su na srpskom; tehnički nazivi tabela/kolona ostaju na engleskom.

Očekivanje pre pokretanja:
- Baza DevelopmentCenterHR_Analytics je kreirana.
- dbo.AssessmentScores sadrži CLEAN dataset (146 redova).
*/

IF DB_ID(N'DevelopmentCenterHR_Analytics') IS NULL
BEGIN
    CREATE DATABASE DevelopmentCenterHR_Analytics;
END;
GO

USE DevelopmentCenterHR_Analytics;
GO

/* ============================================================
   1. DIMENSION TABLES
   ============================================================ */

IF OBJECT_ID(N'dbo.DimCandidate', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.DimCandidate (
        CandidateID INT IDENTITY(1,1) PRIMARY KEY,
        Candidate NVARCHAR(50) NOT NULL UNIQUE
    );
END;
GO

IF OBJECT_ID(N'dbo.DimAssessmentGroup', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.DimAssessmentGroup (
        AssessmentGroupID INT IDENTITY(1,1) PRIMARY KEY,
        Assessment_Group NVARCHAR(50) NOT NULL UNIQUE
    );
END;
GO

IF OBJECT_ID(N'dbo.DimCompetency', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.DimCompetency (
        CompetencyID INT IDENTITY(1,1) PRIMARY KEY,
        Competency NVARCHAR(100) NOT NULL UNIQUE
    );
END;
GO

IF OBJECT_ID(N'dbo.DimAssessmentMethod', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.DimAssessmentMethod (
        AssessmentMethodID INT IDENTITY(1,1) PRIMARY KEY,
        Assessment_Method NVARCHAR(50) NOT NULL UNIQUE
    );
END;
GO

/* ============================================================
   2. POPUNJAVANJE DIMENZIJA
   ============================================================ */

INSERT INTO dbo.DimCandidate (Candidate)
SELECT DISTINCT a.Candidate
FROM dbo.AssessmentScores a
WHERE a.Candidate IS NOT NULL
  AND NOT EXISTS (
      SELECT 1 FROM dbo.DimCandidate d WHERE d.Candidate = a.Candidate
  );
GO

INSERT INTO dbo.DimAssessmentGroup (Assessment_Group)
SELECT DISTINCT a.Assessment_Group
FROM dbo.AssessmentScores a
WHERE a.Assessment_Group IS NOT NULL
  AND NOT EXISTS (
      SELECT 1 FROM dbo.DimAssessmentGroup d WHERE d.Assessment_Group = a.Assessment_Group
  );
GO

INSERT INTO dbo.DimCompetency (Competency)
SELECT DISTINCT a.Competency
FROM dbo.AssessmentScores a
WHERE a.Competency IS NOT NULL
  AND NOT EXISTS (
      SELECT 1 FROM dbo.DimCompetency d WHERE d.Competency = a.Competency
  );
GO

INSERT INTO dbo.DimAssessmentMethod (Assessment_Method)
SELECT DISTINCT a.Assessment_Method
FROM dbo.AssessmentScores a
WHERE a.Assessment_Method IS NOT NULL
  AND NOT EXISTS (
      SELECT 1 FROM dbo.DimAssessmentMethod d WHERE d.Assessment_Method = a.Assessment_Method
  );
GO

/* ============================================================
   3. FACT TABLE
   ============================================================ */

IF OBJECT_ID(N'dbo.FactAssessmentScore', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.FactAssessmentScore (
        AssessmentScoreID INT IDENTITY(1,1) PRIMARY KEY,
        CandidateID INT NOT NULL,
        AssessmentGroupID INT NOT NULL,
        CompetencyID INT NOT NULL,
        AssessmentMethodID INT NOT NULL,
        Score FLOAT NULL,
        Weight FLOAT NOT NULL,
        CONSTRAINT FK_Fact_Candidate
            FOREIGN KEY (CandidateID) REFERENCES dbo.DimCandidate(CandidateID),
        CONSTRAINT FK_Fact_AssessmentGroup
            FOREIGN KEY (AssessmentGroupID) REFERENCES dbo.DimAssessmentGroup(AssessmentGroupID),
        CONSTRAINT FK_Fact_Competency
            FOREIGN KEY (CompetencyID) REFERENCES dbo.DimCompetency(CompetencyID),
        CONSTRAINT FK_Fact_AssessmentMethod
            FOREIGN KEY (AssessmentMethodID) REFERENCES dbo.DimAssessmentMethod(AssessmentMethodID)
    );
END;
GO

IF NOT EXISTS (SELECT 1 FROM dbo.FactAssessmentScore)
BEGIN
    INSERT INTO dbo.FactAssessmentScore (
        CandidateID,
        AssessmentGroupID,
        CompetencyID,
        AssessmentMethodID,
        Score,
        Weight
    )
    SELECT
        c.CandidateID,
        g.AssessmentGroupID,
        co.CompetencyID,
        m.AssessmentMethodID,
        a.Score,
        a.Weight
    FROM dbo.AssessmentScores a
    JOIN dbo.DimCandidate c
        ON a.Candidate = c.Candidate
    JOIN dbo.DimAssessmentGroup g
        ON a.Assessment_Group = g.Assessment_Group
    JOIN dbo.DimCompetency co
        ON a.Competency = co.Competency
    JOIN dbo.DimAssessmentMethod m
        ON a.Assessment_Method = m.Assessment_Method;
END;
GO

/* ============================================================
   4. BUSINESS VIEWS
   ============================================================ */

CREATE OR ALTER VIEW dbo.vw_CandidateCompetencyScores AS
SELECT
    c.Candidate,
    g.Assessment_Group,
    co.Competency,
    SUM(f.Score * f.Weight) / SUM(f.Weight) AS Competency_Score
FROM dbo.FactAssessmentScore f
JOIN dbo.DimCandidate c
    ON f.CandidateID = c.CandidateID
JOIN dbo.DimAssessmentGroup g
    ON f.AssessmentGroupID = g.AssessmentGroupID
JOIN dbo.DimCompetency co
    ON f.CompetencyID = co.CompetencyID
WHERE f.Score IS NOT NULL
GROUP BY
    c.Candidate,
    g.Assessment_Group,
    co.Competency;
GO

CREATE OR ALTER VIEW dbo.vw_CandidateOverallScores AS
SELECT
    Candidate,
    Assessment_Group,
    AVG(Competency_Score) AS Overall_Score
FROM dbo.vw_CandidateCompetencyScores
GROUP BY
    Candidate,
    Assessment_Group;
GO

/* ============================================================
   5. ANALITIČKI UPITI
   ============================================================ */

/* Prosečan competency score po kompetenciji. */
SELECT
    Competency,
    AVG(Competency_Score) AS Average_Competency_Score
FROM dbo.vw_CandidateCompetencyScores
GROUP BY Competency
ORDER BY Average_Competency_Score DESC;
GO

/* Overall score po kandidatu. */
SELECT
    Candidate,
    Assessment_Group,
    Overall_Score
FROM dbo.vw_CandidateOverallScores
ORDER BY Candidate;
GO

/* Broj pojedinačnih assessment ocena ispod 3 po kompetenciji. */
SELECT
    co.Competency,
    COUNT(*) AS Scores_Below_3
FROM dbo.FactAssessmentScore f
JOIN dbo.DimCompetency co
    ON f.CompetencyID = co.CompetencyID
WHERE f.Score < 3
GROUP BY co.Competency
ORDER BY Scores_Below_3 DESC;
GO

/* Prosečan raw assessment score po metodi. */
SELECT
    m.Assessment_Method,
    AVG(f.Score) AS Average_Method_Score,
    COUNT(f.Score) AS Valid_Assessment_Count
FROM dbo.FactAssessmentScore f
JOIN dbo.DimAssessmentMethod m
    ON f.AssessmentMethodID = m.AssessmentMethodID
WHERE f.Score IS NOT NULL
GROUP BY m.Assessment_Method
ORDER BY Average_Method_Score DESC;
GO

/* ============================================================
   6. VALIDACIJA MODELA
   ============================================================ */

SELECT COUNT(*) AS AssessmentRows
FROM dbo.AssessmentScores;

SELECT COUNT(*) AS FactRows
FROM dbo.FactAssessmentScore;

SELECT COUNT(*) AS CandidateCompetencyRows
FROM dbo.vw_CandidateCompetencyScores;

SELECT COUNT(*) AS CandidateOverallRows
FROM dbo.vw_CandidateOverallScores;
GO
