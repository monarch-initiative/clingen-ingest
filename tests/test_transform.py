"""
An example test file for the transform script.

It uses pytest fixtures to define the input data and the mock koza transform.
The test_example function then tests the output of the transform script.

See the Koza documentation for more information on testing transforms:
https://koza.monarchinitiative.org/Usage/testing/
"""

import pytest
from koza.utils.testing_utils import mock_koza

mock_koza = mock_koza  # This line is needed to avoid black removing the import on formatting

# Define the ingest name and transform script path
INGEST_NAME = "clingen_variant"
TRANSFORM_SCRIPT = "./src/clingen_ingest/transform.py"


# define map_cache
@pytest.fixture
def map_cache():
    # Add gene lookup values to map_cache for HGNC lookup.
    # NOTE: This must match the HGNC information for 'HGNC Gene Symbol' in correct row
    return {"hgnc_gene_lookup": {"PAH": {"hgnc_id": "HGNC:8582"}}}


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


# Define the mock koza transform for a correct row
@pytest.fixture
def correct_entities(mock_koza, correct_row, map_cache):
    # Returns [entity, association_a, association_b] for a single row
    return mock_koza(INGEST_NAME, correct_row, TRANSFORM_SCRIPT, map_cache=map_cache)


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


# Define the mock koza transform for a correct row with no gene_id
@pytest.fixture
def correct_entities_no_gene_id(mock_koza, correct_row, map_cache):
    # Returns [entity, association] for a single row
    correct_row["HGNC Gene Symbol"] = "N/A"
    return mock_koza(INGEST_NAME, correct_row, TRANSFORM_SCRIPT, map_cache=map_cache)


# Test the output of the transform for a correct row
def test_correct_row_no_gene_id(correct_entities_no_gene_id):
    # test entity
    assert len(correct_entities_no_gene_id) == 2


# Define the mock koza transform for a retracted row
@pytest.fixture
def retracted_entities(mock_koza, correct_row, map_cache):
    # Returns [entity_a, entity_b, association] for a single row
    correct_row["Retracted"] = "true"
    return mock_koza(INGEST_NAME, correct_row, TRANSFORM_SCRIPT, map_cache=map_cache)


# Test the output of the transform for a retracted row
def test_retracted_row(retracted_entities):
    assert len(retracted_entities) == 0


# Define the mock koza transform for a row with an empty variation
@pytest.fixture
def empty_variation(mock_koza, correct_row, map_cache):
    correct_row["Variation"] = ""
    return mock_koza(INGEST_NAME, correct_row, TRANSFORM_SCRIPT, map_cache=map_cache)


# Test the output of the transform for a row with an empty variation
def test_empty_variation(empty_variation):
    assert len(empty_variation) == 3
    assert empty_variation[0].name == "NM_000277.2:c.1A>G"


# Define the mock koza transform for a row with a missing entity_id
@pytest.fixture
def missing_entity_id(mock_koza, correct_row, map_cache):
    correct_row["ClinVar Variation Id"] = "-"
    return mock_koza(INGEST_NAME, correct_row, TRANSFORM_SCRIPT, map_cache=map_cache)


# Test the output of the transform for a row with a missing entity_id
def test_missing_entity_id(missing_entity_id):
    assert len(missing_entity_id) == 3
    assert missing_entity_id[0].id == "CAID:CA114360"


# Define the mock koza transform for a row with 'Benign' as the clinical_significance
@pytest.fixture
def correct_entities_benign(mock_koza, correct_row, map_cache):
    correct_row["Assertion"] = "Benign"
    return mock_koza(INGEST_NAME, correct_row, TRANSFORM_SCRIPT, map_cache=map_cache)


# Test 'clinical_significance' values of 'Benign'
def test_correct_row_benign(correct_entities_benign):
    assert len(correct_entities_benign) == 0
    # entity, association_a, association_b = correct_entities_benign
    # assert association_a.predicate == 'biolink:contributes_to'
    # assert association_a.negated is True
    # assert association_a.original_predicate == 'Benign'


# Define the mock koza transform for a row with 'Likely Benign' as the clinical_significance
@pytest.fixture
def correct_entities_likely_benign(mock_koza, correct_row, map_cache):
    correct_row["Assertion"] = "Likely Benign"
    return mock_koza(INGEST_NAME, correct_row, TRANSFORM_SCRIPT, map_cache=map_cache)


# Test 'clinical_significance' values of 'Likely Benign'
def test_correct_row_likely_benign(correct_entities_likely_benign):
    assert len(correct_entities_likely_benign) == 0
    # entity, association_a, association_b = correct_entities_likely_benign
    # assert association_a.predicate == 'biolink:contributes_to'
    # assert association_a.negated is True
    # assert association_a.original_predicate == 'Likely Benign'


# Define the mock koza transform for a row with 'Likely Pathogenic' as the clinical_significance
@pytest.fixture
def correct_entities_likely_pathogenic(mock_koza, correct_row, map_cache):
    correct_row["Assertion"] = "Likely Pathogenic"
    return mock_koza(INGEST_NAME, correct_row, TRANSFORM_SCRIPT, map_cache=map_cache)


# Test 'clinical_significance' values of 'Likely Pathogenic'
def test_correct_row_likely_pathogenic(correct_entities_likely_pathogenic):
    assert len(correct_entities_likely_pathogenic) == 3
    entity, association_a, association_b = correct_entities_likely_pathogenic
    assert association_a.predicate == 'biolink:associated_with_increased_likelihood_of'
    assert association_a.negated is False
    assert association_a.original_predicate == 'Likely Pathogenic'


# Define the mock koza transform for a row with 'Uncertain Significance' as the clinical_significance
@pytest.fixture
def correct_entities_uncertain_significance(mock_koza, correct_row, map_cache):
    correct_row["Assertion"] = "Uncertain Significance"
    return mock_koza(INGEST_NAME, correct_row, TRANSFORM_SCRIPT, map_cache=map_cache)


# Test 'clinical_significance' values of 'Uncertain Significance'
def test_correct_row_uncertain_significance(correct_entities_uncertain_significance):
    assert len(correct_entities_uncertain_significance) == 3
    entity, association_a, association_b = correct_entities_uncertain_significance
    assert association_a.predicate == 'biolink:genetically_associated_with'
    assert association_a.negated is False
    assert association_a.original_predicate == 'Uncertain Significance'


def test_invalid_clinical_significance(mock_koza, correct_row, map_cache):
    correct_row["Assertion"] = "Invalid"
    with pytest.raises(ValueError) as e_info:
        mock_koza(INGEST_NAME, correct_row, TRANSFORM_SCRIPT, map_cache=map_cache)
        assert str(e_info.value) == "Not sure how to handle _assertion: 'Invalid'"
