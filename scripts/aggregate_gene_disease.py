"""Aggregate ClinGen variant data to gene-disease associations using DuckDB."""

import duckdb
from pathlib import Path

INPUT_FILE = Path("data/clingen_variants.tsv")
OUTPUT_FILE = Path("data/clingen_gene_disease.tsv")


def aggregate_gene_disease():
    """
    Aggregate variant-disease associations to gene-disease associations.

    For each unique (gene, disease) pair, determines the strongest assertion
    from all variants:
    - Pathogenic > Likely Pathogenic
    - Skips Uncertain Significance, Benign, Likely Benign, and retracted variants
    """
    con = duckdb.connect()

    # Write to TSV using COPY
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    con.execute(f"""
        COPY (
            SELECT
                "HGNC Gene Symbol" AS gene_symbol,
                "Mondo Id" AS mondo_id,
                "Disease" AS disease_name,
                CASE
                    WHEN MAX(CASE WHEN "Assertion" = 'Pathogenic' THEN 1 ELSE 0 END) = 1
                    THEN 'Pathogenic'
                    ELSE 'Likely Pathogenic'
                END AS strongest_assertion
            FROM read_csv_auto('{INPUT_FILE}', delim='\t', header=true)
            WHERE "Assertion" IN ('Pathogenic', 'Likely Pathogenic')
              AND "Retracted" != 'true'
              AND "HGNC Gene Symbol" != 'N/A'
              AND "HGNC Gene Symbol" != ''
              AND "Mondo Id" != ''
            GROUP BY "HGNC Gene Symbol", "Mondo Id", "Disease"
            ORDER BY "HGNC Gene Symbol", "Mondo Id"
        ) TO '{OUTPUT_FILE}' (HEADER, DELIMITER '\t')
    """)

    # Report counts
    count_result = con.execute(f"SELECT COUNT(*) FROM read_csv_auto('{OUTPUT_FILE}', delim='\\t', header=true)")
    count = count_result.fetchone()[0]
    print(f"Aggregated to {count} unique gene-disease associations")

    # Count by assertion type
    assertion_counts = con.execute(f"""
        SELECT strongest_assertion, COUNT(*) as count
        FROM read_csv_auto('{OUTPUT_FILE}', delim='\\t', header=true)
        GROUP BY strongest_assertion
    """).fetchall()
    for assertion, cnt in assertion_counts:
        print(f"  {assertion}: {cnt}")

    con.close()


if __name__ == "__main__":
    aggregate_gene_disease()
