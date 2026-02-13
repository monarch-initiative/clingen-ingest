# ClinGen

[ClinGen](https://clinicalgenome.org/) (Clinical Genome Resource) is a publicly-funded resource dedicated to building an authoritative central resource that defines the clinical relevance of genes and variants for use in precision medicine and research. This ingest uses the ClinGen Evidence Repository variant classification data.

Data is downloaded from: `http://erepo.clinicalgenome.org/redmine/projects/evrepo/pcer/api/classifications/all?format=tabbed`

Gene symbol to HGNC ID mapping is resolved using the [HGNC complete set](http://storage.googleapis.com/public-download-files/hgnc/tsv/tsv/hgnc_complete_set.txt).

## [Variant Associations](#variant)

This transform creates variant nodes and two types of variant associations (variant-to-disease and variant-to-gene).

### Source File Fields

* Variation
* ClinVar Variation Id
* Allele Registry Id
* HGVS Expressions
* HGNC Gene Symbol
* Disease
* Mondo Id
* Mode of Inheritance
* Assertion
* Applied Evidence Codes (Met)
* Applied Evidence Codes (Not Met)
* Summary of interpretation
* PubMed Articles
* Expert Panel
* Guideline
* Approval Date
* Published Date
* Retracted
* Evidence Repo Link
* Uuid

### Filtering

Rows are excluded when any of the following are true:

- Assertion is "Benign" or "Likely Benign"
- Variant is retracted

### Biolink Captured

#### biolink:SequenceVariant (node)

* id (ClinVar Variation ID when available, otherwise ClinGen Allele Registry ID)
* name (Variation name, or first HGVS expression if empty)
* xref (ClinGen Allele Registry ID)
* has_gene (HGNC gene ID, resolved from gene symbol)
* in_taxon (`NCBITaxon:9606`)
* in_taxon_label (`Homo sapiens`)

#### biolink:VariantToDiseaseAssociation

* id (random uuid)
* subject (variant ID)
* predicate (mapped from Assertion, see below)
* negated (`false`)
* original_predicate (raw Assertion value)
* object (Mondo ID)
* primary_knowledge_source (`infores:clingen`)
* aggregator_knowledge_source (`["infores:monarchinitiative"]`)
* knowledge_level (`knowledge_assertion`)
* agent_type (`manual_agent`)

Predicate mapping from Assertion:

| Assertion | Predicate |
|---|---|
| Pathogenic | `biolink:causes` |
| Likely Pathogenic | `biolink:associated_with_increased_likelihood_of` |
| Uncertain Significance | `biolink:genetically_associated_with` |

#### biolink:VariantToGeneAssociation

* id (random uuid)
* subject (variant ID)
* predicate (`biolink:is_sequence_variant_of`)
* object (HGNC gene ID)
* primary_knowledge_source (`infores:clingen`)
* aggregator_knowledge_source (`["infores:monarchinitiative"]`)
* knowledge_level (`knowledge_assertion`)
* agent_type (`manual_agent`)

Only created when the gene symbol successfully resolves to an HGNC ID.

## [Gene-Disease Associations](#gene-disease)

A preprocessing step aggregates variant-level data into gene-disease associations. For each unique (gene, disease) pair, the strongest assertion across all variants is determined.

### Preprocessing

The aggregation uses DuckDB to:

1. Filter to only Pathogenic and Likely Pathogenic variants (excluding retracted, missing gene symbol, or missing Mondo ID)
2. Group by gene symbol and Mondo ID
3. Select the strongest assertion per group (Pathogenic > Likely Pathogenic)

### Biolink Captured

#### biolink:CausalGeneToDiseaseAssociation

* id (random uuid)
* subject (HGNC gene ID, resolved from gene symbol)
* predicate (mapped from strongest assertion, see below)
* original_predicate (strongest assertion value)
* object (Mondo ID)
* primary_knowledge_source (`infores:clingen`)
* aggregator_knowledge_source (`["infores:monarchinitiative"]`)
* knowledge_level (`knowledge_assertion`)
* agent_type (`manual_agent`)

Predicate mapping from strongest assertion:

| Assertion | Predicate |
|---|---|
| Pathogenic | `biolink:causes` |
| Likely Pathogenic | `biolink:associated_with_increased_likelihood_of` |

Rows where the gene symbol cannot be resolved to an HGNC ID are skipped.

## Citation

Rehm HL, Berg JS, Brooks LD, Bustamante CD, Evans JP, Landrum MJ, Ledbetter DH, Maglott DR, Martin CL, Nussbaum RL, Plon SE, Ramos EM, Sherry ST, Watson MS; ClinGen. ClinGen--the Clinical Genome Resource. N Engl J Med. 2015 Jun 4;372(23):2235-42. doi: 10.1056/NEJMsr1406261.

## License

BSD-3-Clause
