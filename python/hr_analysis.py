"""
Development Center HR Analytics

Jedan reproducibilan Python pipeline:
1) učitavanje source long-format podataka
2) data-quality provere
3) čišćenje potvrđenih source grešaka
4) weighted competency score
5) overall score
6) osnovna EDA
7) reconciliation sa consolidated business rezultatom

Sva objašnjenja su na srpskom; tehnički nazivi kolona ostaju na engleskom
zbog konzistentnosti sa CSV/SQL/Power BI modelom.
"""

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "data" / "source"
PROCESSED_DIR = ROOT / "data" / "processed"
OUTPUT_DIR = ROOT / "outputs"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SOURCE_FILE = SOURCE_DIR / "assessment_scores_source.csv"
CONSOLIDATED_FILE = SOURCE_DIR / "consolidated_scores.csv"

COMPETENCIES = [
    "Sveobuhvatna analitička sposobnost",
    "Rezilijentnost i odlučnost",
    "Liderska sposobnost i interesovanje",
    "Razvoj i svest o sebi",
    "Integritet",
]

EXPECTED_METHODS = {
    "Igranje uloga 1",
    "Igranje uloga 2",
    "Prezentacija",
    "Intervju",
    "Test",
}

# Tri konkretna source unosa potvrđena kao greška u poslovnoj validaciji.
KNOWN_INVALID_INTEGRITY_TEST = {"Kandidat 2", "Kandidat 3", "Kandidat 4"}


def validate_structure(df: pd.DataFrame) -> None:
    required = {
        "Candidate",
        "Assessment_Group",
        "Competency",
        "Assessment_Method",
        "Score",
        "Weight",
    }
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Nedostaju obavezne kolone: {sorted(missing)}")

    if set(df["Competency"].dropna().unique()) != set(COMPETENCIES):
        raise ValueError("Skup kompetencija ne odgovara očekivanom business modelu.")

    if not set(df["Assessment_Method"].dropna().unique()).issubset(EXPECTED_METHODS):
        raise ValueError("Pronađena je neočekivana assessment metoda.")


def run():
    # 1. Učitavanje source podataka
    source = pd.read_csv(SOURCE_FILE)
    source["Assessment_Group"] = source["Assessment_Group"].astype(str).str.strip().str.lower()
    validate_structure(source)

    # 2. Data-quality provere pre čišćenja
    score_values = source["Score"].dropna()
    if ((score_values < 1) | (score_values > 5)).any():
        raise ValueError("Pronađene su ocene van raspona 1–5.")
    if ((score_values * 2) % 1 != 0).any():
        raise ValueError("Pronađene su ocene koje nisu u koracima od 0.5.")

    duplicate_mask = source.duplicated(
        subset=["Candidate", "Assessment_Group", "Competency", "Assessment_Method"],
        keep=False,
    )
    duplicate_rows = source.loc[duplicate_mask].copy()
    duplicate_rows.to_csv(OUTPUT_DIR / "duplicate_check.csv", index=False)
    if not duplicate_rows.empty:
        raise ValueError("Pronađeni su duplikati na nivou Candidate × Group × Competency × Method.")

    # 3. Identifikacija poznatih source grešaka
    invalid_mask = (
        source["Competency"].eq("Integritet")
        & source["Assessment_Method"].eq("Test")
        & source["Candidate"].isin(KNOWN_INVALID_INTEGRITY_TEST)
        & source["Score"].eq(3)
    )
    issues = source.loc[invalid_mask].copy()
    issues["Issue"] = (
        "Test nije primenljiv na Integritet; potvrđeni source unos je isključen iz analitičkog sloja."
    )
    issues["Severity"] = "Warning"
    issues.to_csv(PROCESSED_DIR / "data_quality_issues.csv", index=False)

    if len(issues) != 3:
        raise ValueError(f"Očekivane su 3 potvrđene source greške, pronađeno je {len(issues)}.")

    # 4. Cleaning — raw/source fajl ostaje netaknut.
    clean = source.loc[~invalid_mask].copy()
    clean.to_csv(PROCESSED_DIR / "assessment_scores_clean.csv", index=False)

    # 5. Weighted competency score
    valid = clean.dropna(subset=["Score"]).copy()
    valid["Weighted_Score"] = valid["Score"] * valid["Weight"]

    competency_scores = (
        valid.groupby(["Candidate", "Assessment_Group", "Competency"], as_index=False)
        .agg(
            Weighted_Sum=("Weighted_Score", "sum"),
            Total_Weight=("Weight", "sum"),
        )
    )
    competency_scores["Competency_Score"] = (
        competency_scores["Weighted_Sum"] / competency_scores["Total_Weight"]
    )
    competency_scores.to_csv(PROCESSED_DIR / "competency_scores_calculated.csv", index=False)

    # 6. Overall score — jednak ponder po kompetencijama.
    overall_scores = (
        competency_scores.groupby(["Candidate", "Assessment_Group"], as_index=False)
        .agg(Overall_Score=("Competency_Score", "mean"))
    )
    overall_scores.to_csv(PROCESSED_DIR / "overall_scores_calculated.csv", index=False)

    # Osnovne očekivane kontrole
    assert len(source) == 149, f"Očekivano 149 source redova, dobijeno {len(source)}."
    assert len(clean) == 146, f"Očekivano 146 čistih redova, dobijeno {len(clean)}."
    assert len(competency_scores) == 40, "Očekivano 40 competency rezultata."
    assert len(overall_scores) == 8, "Očekivano 8 overall rezultata."

    # 7. EDA — fokus na business-relevant analize.
    competency_summary = (
        competency_scores.groupby("Competency")["Competency_Score"]
        .agg(["mean", "median", "std", "min", "max"])
        .reset_index()
    )
    competency_summary.to_csv(OUTPUT_DIR / "competency_summary.csv", index=False)

    method_summary = (
        clean.groupby("Assessment_Method")["Score"]
        .agg(["count", "mean", "std", "min", "max"])
        .reset_index()
    )
    method_summary.to_csv(OUTPUT_DIR / "method_summary.csv", index=False)

    score_distribution = pd.crosstab(clean["Competency"], clean["Score"])
    score_distribution.to_csv(OUTPUT_DIR / "score_distribution_by_competency.csv")

    below_3 = clean.assign(Below_3=clean["Score"] < 3).groupby("Competency")["Below_3"].agg(["sum", "count"])
    below_3["Percent"] = (below_3["sum"] / below_3["count"] * 100).round(1)
    below_3.to_csv(OUTPUT_DIR / "below_3_by_competency.csv")

    # Distribucija po assessment metodama — sirovi assessment rezultati.
    method_distribution = pd.crosstab(clean["Assessment_Method"], clean["Score"])
    method_distribution.to_csv(OUTPUT_DIR / "score_distribution_by_method.csv")

    # Grafici; bez ručno zadatih boja kako bi kod ostao neutralan.
    plot_comp = competency_summary.sort_values("mean")
    plt.figure(figsize=(9, 5))
    plt.barh(plot_comp["Competency"], plot_comp["mean"])
    plt.xlabel("Average Competency Score")
    plt.xlim(0, 5)
    plt.title("Average Score by Competency")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "average_score_by_competency.png", dpi=160)
    plt.close()

    plot_method = method_summary.sort_values("mean")
    plt.figure(figsize=(9, 5))
    plt.barh(plot_method["Assessment_Method"], plot_method["mean"])
    plt.xlabel("Average Assessment Score")
    plt.xlim(0, 5)
    plt.title("Average Score by Assessment Method")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "average_score_by_method.png", dpi=160)
    plt.close()

    # 8. Reconciliation sa consolidated business fajlom.
    consolidated = pd.read_csv(CONSOLIDATED_FILE)
    consolidated["grupa"] = consolidated["grupa"].astype(str).str.strip().str.lower()
    rows = []

    for _, row in consolidated[consolidated["Ime I prezme"].notna()].iterrows():
        candidate = row["Ime I prezme"]
        group = row["grupa"]
        for competency in COMPETENCIES:
            calc = competency_scores[
                (competency_scores["Candidate"] == candidate)
                & (competency_scores["Assessment_Group"] == group)
                & (competency_scores["Competency"] == competency)
            ]
            if calc.empty:
                raise ValueError(f"Nedostaje obračun: {candidate} / {competency}")
            calculated = float(calc.iloc[0]["Competency_Score"])
            expected = float(row[competency])
            diff = expected - calculated
            rows.append({
                "Candidate": candidate,
                "Assessment_Group": group,
                "Metric": competency,
                "Calculated": calculated,
                "Consolidated": expected,
                "Difference": diff,
                "Status": "PASS" if abs(diff) <= 0.005 else "CHECK",
            })

        candidate_overall = float(
            overall_scores[
                (overall_scores["Candidate"] == candidate)
                & (overall_scores["Assessment_Group"] == group)
            ]["Overall_Score"].iloc[0]
        )
        expected_overall = float(row["Prosek"])
        diff = expected_overall - candidate_overall
        rows.append({
            "Candidate": candidate,
            "Assessment_Group": group,
            "Metric": "Overall_Score",
            "Calculated": candidate_overall,
            "Consolidated": expected_overall,
            "Difference": diff,
            "Status": "PASS" if abs(diff) <= 0.005 else "CHECK",
        })

    reconciliation = pd.DataFrame(rows)
    reconciliation.to_csv(PROCESSED_DIR / "reconciliation_report.csv", index=False)

    if not (reconciliation["Status"] == "PASS").all():
        raise ValueError("Reconciliation nije prošao za sve metrike.")

    print("Python pipeline završen uspešno.")
    print(f"Source rows: {len(source)}")
    print(f"Clean rows: {len(clean)}")
    print(f"Data-quality issues removed: {len(issues)}")
    print(f"Competency results: {len(competency_scores)}")
    print(f"Overall results: {len(overall_scores)}")
    print(f"Reconciliation: {len(reconciliation)}/{len(reconciliation)} PASS")
    print(f"Max absolute difference: {reconciliation['Difference'].abs().max():.6f}")


if __name__ == "__main__":
    run()
