# clingen-ingest

Koza ingest for ClinGen variant data, transforming variants and their clinical significance annotations into Biolink model format.

## Data Source

[ClinGen](https://clinicalgenome.org/) is a publicly-funded resource dedicated to building an authoritative central resource that defines the clinical relevance of genes and variants for use in precision medicine and research.

Data is downloaded from: `http://erepo.clinicalgenome.org/redmine/projects/evrepo/pcer/api/classifications/all?format=tabbed`

## Output

This ingest produces:
- **Variant nodes** - Genomic variants with ClinVar IDs
- **Variant-to-Disease associations** - Links variants to associated conditions
- **Variant-to-Gene associations** - Links variants to affected genes
- **Gene-to-Disease associations** - Aggregated causal gene-disease relationships

## Usage

```bash
# Install dependencies
just install

# Run full pipeline
just run

# Or run steps individually
just download      # Download ClinGen and HGNC data
just preprocess    # Aggregate variant data to gene-disease associations
just transform-all # Run Koza transforms
just test          # Run tests
```

## Requirements

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) package manager
- [just](https://github.com/casey/just) command runner

## License

BSD-3-Clause
