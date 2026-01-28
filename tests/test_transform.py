"""
Test file for the clingen variant transform script.

Uses KozaRunner with PassthroughWriter for Koza 2.x testing.

See the Koza documentation for more information on testing transforms:
https://koza.monarchinitiative.org/Usage/testing/
"""

import importlib.util
from pathlib import Path

import pytest
from koza.runner import KozaTransform, PassthroughWriter, load_transform

# Define the transform script path
TRANSFORM_SCRIPT = Path(__file__).parent.parent / "src" / "clingen_variant_transform.py"
MAP_FILE = Path(__file__).parent.parent / "src" / "hgnc_gene_lookup.yaml"


def load_module_from_path(path: Path):
    """Load a Python module from a file path."""
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_transform(rows: list[dict], mappings: dict = None) -> list:
    """Run the transform with given rows and optional mappings.

    Args:
        rows: List of row dictionaries to transform
        mappings: Optional mapping dict in format {map_name: {key: {column: value}}}
    """
    module = load_module_from_path(TRANSFORM_SCRIPT)

    # Reset the seen_variants global state for each test run
    module.seen_variants = {}

    hooks_by_tag = load_transform(module)
    # Get hooks for untagged transforms (key is None)
    hooks = hooks_by_tag.get(None)
    if hooks is None:
        raise ValueError("No untagged transforms found in module")

    writer = PassthroughWriter()

    # Create KozaTransform directly with mappings
    koza_transform = KozaTransform(
        mappings=mappings or {},
        writer=writer,
        extra_fields={},
    )

    # Run the transform_record functions for each row
    for row in rows:
        for transform_fn in hooks.transform_record:
            result = transform_fn(koza_transform, row)
            if result is not None:
                writer.write(result)

    return writer.data


# Define mappings in Koza 2.x format
@pytest.fixture
def mappings():
    # Koza 2.x mappings format: {map_name: {key: {column: value}}}
    return {
        "hgnc_gene_lookup": {
            "PAH": {"hgnc_id": "HGNC:8582"}
        }
    }


# Define an example row to test (as a dictionary)
@pytest.fixture
def correct_row():
    return {
        'Variation': 'NM_000277.2(PAH):c.1A>G (p.Met1Val)',
        'ClinVar Variation Id': '586',
        'Allele Registry Id': 'CA114360',
        'HGVS Expressions': 'NM_000277.2:c.1A>G, NC_000012.12:g.102917130T>C, CM000674.2:g.102917130T>C',
        'HGNC Gene Symbol': 'PAH',
        'Disease': 'phenylketonuria',
        'Mondo Id': 'MONDO:0009861',
        'Mode of Inheritance': 'Autosomal recessive inheritance',
        'Assertion': 'Pathogenic',
        'Applied Evidence Codes (Met)': 'PS3, PP4_Moderate, PM2, PM3',
        'Applied Evidence Codes (Not Met)': 'PVS1',
        'Summary of interpretation': 'PAH-specific ACMG/AMP criteria applied: PM2: gnomAD MAF=0.00002',
        'PubMed Articles': '9450897, 2574002, 2574002',
        'Expert Panel': 'Phenylketonuria VCEP',
        'Guideline': 'https://clinicalgenome.org/docs/clingen-pah-expert-panel-specifications-to-TRUNCATED/',
        'Approval Date': '2019-03-23',
        'Published Date': '2019-05-10',
        'Retracted': 'false',
        'Evidence Repo Link': 'https://erepo.genome.network/evrepo/ui/classification/CA114360/MONDO:0009861/006',
        'Uuid': '89f04437-ed5d-4735-8c4a-a9b1d91d10ea',
    }


# Define the fixture for a correct row
@pytest.fixture
def correct_entities(correct_row, mappings):
    # Returns [entity, association_a, association_b] for a single row
    return run_transform([correct_row], mappings=mappings)


# Test the output of the transform for a correct row
def test_correct_row(correct_entities):
    assert len(correct_entities) == 3
    entity, association_a, association_b = correct_entities
    # test entity
    assert entity.id == 'CLINVAR:586'
    assert entity.name == 'NM_000277.2(PAH):c.1A>G (p.Met1Val)'
    assert entity.xref == ['CAID:CA114360']
    assert entity.has_gene == ['HGNC:8582']
    assert entity.in_taxon == ['NCBITaxon:9606']
    assert entity.in_taxon_label == 'Homo sapiens'

    # test association_a
    assert association_a.subject == 'CLINVAR:586'
    assert association_a.predicate == 'biolink:causes'
    assert association_a.negated is False
    assert association_a.original_predicate == 'Pathogenic'
    assert association_a.object == 'MONDO:0009861'
    assert association_a.primary_knowledge_source == 'infores:clingen'
    assert association_a.aggregator_knowledge_source == ['infores:monarchinitiative']
    assert association_a.knowledge_level == 'knowledge_assertion'
    assert association_a.agent_type == 'manual_agent'

    # test association_b
    assert association_b.subject == 'CLINVAR:586'
    assert association_b.predicate == 'biolink:is_sequence_variant_of'
    assert association_b.negated is None
    assert association_b.original_predicate is None
    assert association_b.object == 'HGNC:8582'
    assert association_b.primary_knowledge_source == 'infores:clingen'
    assert association_b.aggregator_knowledge_source == ['infores:monarchinitiative']
    assert association_b.knowledge_level == 'knowledge_assertion'
    assert association_b.agent_type == 'manual_agent'


# Define the fixture for a correct row with no gene_id
@pytest.fixture
def correct_entities_no_gene_id(correct_row, mappings):
    # Returns [entity, association] for a single row
    row = correct_row.copy()
    row["HGNC Gene Symbol"] = "N/A"
    return run_transform([row], mappings=mappings)


# Test the output of the transform for a correct row
def test_correct_row_no_gene_id(correct_entities_no_gene_id):
    # test entity
    assert len(correct_entities_no_gene_id) == 2


# Define the fixture for a retracted row
@pytest.fixture
def retracted_entities(correct_row, mappings):
    # Returns empty list for a retracted row
    row = correct_row.copy()
    row["Retracted"] = "true"
    return run_transform([row], mappings=mappings)


# Test the output of the transform for a retracted row
def test_retracted_row(retracted_entities):
    assert len(retracted_entities) == 0


# Define the fixture for a row with an empty variation
@pytest.fixture
def empty_variation(correct_row, mappings):
    row = correct_row.copy()
    row["Variation"] = ""
    return run_transform([row], mappings=mappings)


# Test the output of the transform for a row with an empty variation
def test_empty_variation(empty_variation):
    assert len(empty_variation) == 3
    assert empty_variation[0].name == "NM_000277.2:c.1A>G"


# Define the fixture for a row with a missing entity_id
@pytest.fixture
def missing_entity_id(correct_row, mappings):
    row = correct_row.copy()
    row["ClinVar Variation Id"] = "-"
    return run_transform([row], mappings=mappings)


# Test the output of the transform for a row with a missing entity_id
def test_missing_entity_id(missing_entity_id):
    assert len(missing_entity_id) == 3
    assert missing_entity_id[0].id == "CAID:CA114360"


# Define the fixture for a row with 'Benign' as the clinical_significance
@pytest.fixture
def correct_entities_benign(correct_row, mappings):
    row = correct_row.copy()
    row["Assertion"] = "Benign"
    return run_transform([row], mappings=mappings)


# Test 'clinical_significance' values of 'Benign'
def test_correct_row_benign(correct_entities_benign):
    assert len(correct_entities_benign) == 0


# Define the fixture for a row with 'Likely Benign' as the clinical_significance
@pytest.fixture
def correct_entities_likely_benign(correct_row, mappings):
    row = correct_row.copy()
    row["Assertion"] = "Likely Benign"
    return run_transform([row], mappings=mappings)


# Test 'clinical_significance' values of 'Likely Benign'
def test_correct_row_likely_benign(correct_entities_likely_benign):
    assert len(correct_entities_likely_benign) == 0


# Define the fixture for a row with 'Likely Pathogenic' as the clinical_significance
@pytest.fixture
def correct_entities_likely_pathogenic(correct_row, mappings):
    row = correct_row.copy()
    row["Assertion"] = "Likely Pathogenic"
    return run_transform([row], mappings=mappings)


# Test 'clinical_significance' values of 'Likely Pathogenic'
def test_correct_row_likely_pathogenic(correct_entities_likely_pathogenic):
    assert len(correct_entities_likely_pathogenic) == 3
    entity, association_a, association_b = correct_entities_likely_pathogenic
    assert association_a.predicate == 'biolink:associated_with_increased_likelihood_of'
    assert association_a.negated is False
    assert association_a.original_predicate == 'Likely Pathogenic'


# Define the fixture for a row with 'Uncertain Significance' as the clinical_significance
@pytest.fixture
def correct_entities_uncertain_significance(correct_row, mappings):
    row = correct_row.copy()
    row["Assertion"] = "Uncertain Significance"
    return run_transform([row], mappings=mappings)


# Test 'clinical_significance' values of 'Uncertain Significance'
def test_correct_row_uncertain_significance(correct_entities_uncertain_significance):
    assert len(correct_entities_uncertain_significance) == 3
    entity, association_a, association_b = correct_entities_uncertain_significance
    assert association_a.predicate == 'biolink:genetically_associated_with'
    assert association_a.negated is False
    assert association_a.original_predicate == 'Uncertain Significance'


def test_invalid_clinical_significance(correct_row, mappings):
    row = correct_row.copy()
    row["Assertion"] = "Invalid"
    with pytest.raises(ValueError) as e_info:
        run_transform([row], mappings=mappings)
    assert "Not sure how to handle _assertion: 'Invalid'" in str(e_info.value)
