# clingen-ingest

This is a Koza ingest repository for transforming ClinGen variant data into Biolink model format.

## Project Structure

- `download.yaml` - Configuration for downloading ClinGen data
- `src/` - Transform code and configuration
  - `clingen_variant_transform.py` / `clingen_variant_transform.yaml` - Transform for ClinGen variants
  - `gene_disease_transform.py` / `gene_disease_transform.yaml` - Transform for aggregated gene-disease associations
  - `hgnc_gene_lookup.yaml` - HGNC gene symbol to ID mapping
- `scripts/` - Preprocessing scripts
  - `aggregate_gene_disease.py` - Aggregates variant data to gene-disease associations using DuckDB
- `tests/` - Unit tests for transforms
- `output/` - Generated nodes and edges (gitignored)
- `data/` - Downloaded source data (gitignored)

## Key Commands

- `just run` - Full pipeline (download -> preprocess -> transform)
- `just download` - Download ClinGen and HGNC data
- `just preprocess` - Aggregate variant data to gene-disease associations
- `just transform-all` - Run all transforms
- `just test` - Run tests

## Preprocessing

This ingest requires a preprocessing step to aggregate variant-disease associations into gene-disease associations:
```bash
python scripts/aggregate_gene_disease.py
```

This is handled automatically by `just run` or `just preprocess`.
