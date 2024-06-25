"""
An example test file for the transform script.

It uses pytest fixtures to define the input data and the mock koza transform.
The test_example function then tests the output of the transform script.

See the Koza documentation for more information on testing transforms:
https://koza.monarchinitiative.org/Usage/testing/
"""

import pytest
from koza.utils.testing_utils import mock_koza

# Define the ingest name and transform script path
INGEST_NAME = "clingen_variant"
TRANSFORM_SCRIPT = "./src/clingen_ingest/transform.py"


# define map_cache
@pytest.fixture
def map_cache():
    return {"hgnc_gene_lookup": {"GCK": {"hgnc_id": "HGNC:4195"}}}


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
        'Uuid': '89f04437-ed5d-4735-8c4a-a9b1d91d10ea'
    }


@pytest.fixture
def retracted_row():
    return {
        'Variation': '',
        'ClinVar Variation Id': '-',
        'Allele Registry Id': 'CA4239423',
        'HGVS Expressions': 'NM_001354803.2:c.182C>A',
        'HGNC Gene Symbol': 'GCK',
        'Disease': 'monogenic diabetes',
        'Mondo Id': 'MONDO:0015967',
        'Mode of Inheritance': 'Semidominant inheritance',
        'Assertion': 'Likely Pathogenic',
        'Applied Evidence Codes (Met)': 'PVS1, PM2_Supporting',
        'Applied Evidence Codes (Not Met)': 'PS4, PP4',
        'Summary of interpretation': 'The c.1148C>A variant in the glucokinase gene',
        'PubMed Articles': '',
        'Expert Panel': 'Monogenic Diabetes VCEP',
        'Guideline': '',
        'Approval Date': '2024-05-24',
        'Published Date': '2024-05-24',
        'Retracted': 'true',
        'Evidence Repo Link': 'https://erepo.genome.network/evrepo/ui/classification/CA4239423/MONDO:0015967/086',
        'Uuid': 'd5362e38-f996-4ef0-b41b-c6bbcdbfb2b5',
    }


# Define the mock koza transform for a correct row
@pytest.fixture
def correct_entities(mock_koza, correct_row, map_cache):
    # Returns [entity_a, entity_b, association] for a single row
    return mock_koza(INGEST_NAME, correct_row, TRANSFORM_SCRIPT, map_cache=map_cache)


# Test the output of the transform for a correct row
def test_correct_row(correct_entities):
    assert len(correct_entities) == 2
    entity_a, entity_b = correct_entities
    # test entity_a
    assert entity_a.id == 'CLINVAR:586'
    assert entity_a.name == 'NM_000277.2(PAH):c.1A>G (p.Met1Val)'
    assert entity_a.xref == ['CA114360']
    assert entity_a.in_taxon == ['NCBITaxon:9606']
    assert entity_a.in_taxon_label == 'Homo sapiens'

    # test entity_b
    assert entity_b.subject == 'CLINVAR:586'
    assert entity_b.predicate == 'biolink:causes'
    assert entity_b.negated is False
    assert entity_b.original_predicate == 'Pathogenic'
    assert entity_b.object == 'MONDO:0009861'
    assert entity_b.primary_knowledge_source == 'infores:clingen'
    assert entity_b.aggregator_knowledge_source == ['infores:monarchinitiative']
    assert entity_b.knowledge_level == 'knowledge_assertion'
    assert entity_b.agent_type == 'manual_agent'


# Define the mock koza transform for a retracted row
@pytest.fixture
def retracted_entities(mock_koza, retracted_row, map_cache):
    # Returns [entity_a, entity_b, association] for a single row
    return mock_koza(INGEST_NAME, retracted_row, TRANSFORM_SCRIPT, map_cache=map_cache)


# Test the output of the transform for a retracted row
def test_retracted_row(retracted_entities):
    assert len(retracted_entities) == 0


@pytest.fixture
def missing_entity_id(mock_koza, correct_row, map_cache):
    correct_row["ClinVar Variation Id"] = "-"
    return mock_koza(INGEST_NAME, correct_row, TRANSFORM_SCRIPT, map_cache=map_cache)


def test_missing_entity_id(missing_entity_id):
    assert len(missing_entity_id) == 0
