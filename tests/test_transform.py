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
    # Add gene lookup values to map_cache for HGNC lookup.
    # NOTE: This must match the HGNC information for 'HGNC Gene Symbol' in correct row
    return {"hgnc_gene_lookup": {"PAH": {"hgnc_id": "8582"}}}


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
def correct_row_no_gene_id():
    return {
        'Variation': 'NC_000021.9:g.(?_35048836)_(35048905_?)del',
        'ClinVar Variation Id': '463975',
        'Allele Registry Id': '-',
        'HGVS Expressions': 'NC_000021.9:g.(?_35048836)_(35048905_?)del',
        'HGNC Gene Symbol': 'N/A',
        'Disease': 'hereditary thrombocytopenia and hematologic cancer predisposition syndrome',
        'Mondo Id': 'MONDO:0011071',
        'Mode of Inheritance': 'Autosomal dominant inheritance',
        'Assertion': 'Pathogenic',
        'Applied Evidence Codes (Met)': 'PS4, PP1_Strong, PVS1_Moderate, PM5_Supporting, PM2_Supporting',
        'Applied Evidence Codes (Not Met)': 'BP1, BP4, BP3, BP2, BA1, PS1, PS3, PS2, BP7, BP5, BS3',
        'Summary of interpretation': 'The deletion of exons 1 (non-coding) and 2 or exons 1, 2, and 3 TRUNCATED',
        'Expert Panel': 'Myeloid Malignancy VCEP',
        'Guideline': 'https://www.clinicalgenome.org/affiliation/50034/docs/assertion-criteria',
        'Approval Date': '2024-03-26',
        'Published Date': '2024-03-26',
        'Retracted': 'false',
        'Evidence Repo Link': 'https://erepo.genome.network/evrepo/ui/classification/CV463975/MONDO:0011071/008',
        'Uuid': '5d15c32f-47fc-4ba9-8d74-b998374ee11d'}


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
    # Returns [entity, association_a, association_b] for a single row
    return mock_koza(INGEST_NAME, correct_row, TRANSFORM_SCRIPT, map_cache=map_cache)


# Test the output of the transform for a correct row
def test_correct_row(correct_entities):
    assert len(correct_entities) == 3
    entity, association_a, association_b = correct_entities
    # test entity
    assert entity.id == 'CLINVAR:586'
    assert entity.name == 'NM_000277.2(PAH):c.1A>G (p.Met1Val)'
    assert entity.xref == ['CA114360']
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
def correct_entities_no_gene_id(mock_koza, correct_row_no_gene_id, map_cache):
    # Returns [entity, association] for a single row
    return mock_koza(INGEST_NAME, correct_row_no_gene_id, TRANSFORM_SCRIPT, map_cache=map_cache)


# Test the output of the transform for a correct row
def test_correct_row_no_gene_id(correct_entities_no_gene_id):
    # test entity
    assert len(correct_entities_no_gene_id) == 2
    pass


# Define the mock koza transform for a retracted row
@pytest.fixture
def retracted_entities(mock_koza, retracted_row, map_cache):
    # Returns [entity_a, entity_b, association] for a single row
    return mock_koza(INGEST_NAME, retracted_row, TRANSFORM_SCRIPT, map_cache=map_cache)


# Test the output of the transform for a retracted row
def test_retracted_row(retracted_entities):
    assert len(retracted_entities) == 0


@pytest.fixture
def empty_variation(mock_koza, correct_row, map_cache):
    correct_row["Variation"] = ""
    return mock_koza(INGEST_NAME, correct_row, TRANSFORM_SCRIPT, map_cache=map_cache)


def test_empty_variation(empty_variation):
    assert len(empty_variation) == 0


@pytest.fixture
def missing_entity_id(mock_koza, correct_row, map_cache):
    correct_row["ClinVar Variation Id"] = "-"
    return mock_koza(INGEST_NAME, correct_row, TRANSFORM_SCRIPT, map_cache=map_cache)


def test_missing_entity_id(missing_entity_id):
    assert len(missing_entity_id) == 0
