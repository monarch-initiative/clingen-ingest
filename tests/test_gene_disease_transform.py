"""
Tests for the gene-to-disease transform.

Tests the transformation of aggregated gene-disease data to
CausalGeneToDiseaseAssociation entities.
"""

import pytest
from koza.utils.testing_utils import mock_koza

mock_koza = mock_koza  # Prevent removal on formatting

# Define the ingest name and transform script path
INGEST_NAME = "clingen_gene_disease"
TRANSFORM_SCRIPT = "./src/clingen_ingest/gene_disease_transform.py"


@pytest.fixture
def map_cache():
    """HGNC gene lookup for test genes."""
    return {
        "hgnc_gene_lookup": {
            "PAH": {"hgnc_id": "HGNC:8582"},
            "BRCA1": {"hgnc_id": "HGNC:1100"},
        }
    }


@pytest.fixture
def pathogenic_row():
    """A row with Pathogenic as strongest assertion."""
    return {
        "gene_symbol": "PAH",
        "mondo_id": "MONDO:0009861",
        "disease_name": "phenylketonuria",
        "strongest_assertion": "Pathogenic",
    }


@pytest.fixture
def likely_pathogenic_row():
    """A row with Likely Pathogenic as strongest assertion."""
    return {
        "gene_symbol": "BRCA1",
        "mondo_id": "MONDO:0016419",
        "disease_name": "hereditary breast cancer",
        "strongest_assertion": "Likely Pathogenic",
    }


@pytest.fixture
def unknown_gene_row():
    """A row with a gene not in HGNC lookup."""
    return {
        "gene_symbol": "UNKNOWN_GENE",
        "mondo_id": "MONDO:0000001",
        "disease_name": "some disease",
        "strongest_assertion": "Pathogenic",
    }


@pytest.fixture
def pathogenic_entities(mock_koza, pathogenic_row, map_cache):
    return mock_koza(INGEST_NAME, pathogenic_row, TRANSFORM_SCRIPT, map_cache=map_cache)


@pytest.fixture
def likely_pathogenic_entities(mock_koza, likely_pathogenic_row, map_cache):
    return mock_koza(INGEST_NAME, likely_pathogenic_row, TRANSFORM_SCRIPT, map_cache=map_cache)


@pytest.fixture
def unknown_gene_entities(mock_koza, unknown_gene_row, map_cache):
    return mock_koza(INGEST_NAME, unknown_gene_row, TRANSFORM_SCRIPT, map_cache=map_cache)


def test_pathogenic_assertion(pathogenic_entities):
    """Test that Pathogenic assertion produces biolink:causes predicate."""
    assert len(pathogenic_entities) == 1
    association = pathogenic_entities[0]

    assert association.subject == "HGNC:8582"
    assert association.predicate == "biolink:causes"
    assert association.object == "MONDO:0009861"
    assert association.original_predicate == "Pathogenic"
    assert association.primary_knowledge_source == "infores:clingen"
    assert association.aggregator_knowledge_source == ["infores:monarchinitiative"]
    assert association.knowledge_level == "knowledge_assertion"
    assert association.agent_type == "manual_agent"


def test_likely_pathogenic_assertion(likely_pathogenic_entities):
    """Test that Likely Pathogenic produces associated_with_increased_likelihood_of."""
    assert len(likely_pathogenic_entities) == 1
    association = likely_pathogenic_entities[0]

    assert association.subject == "HGNC:1100"
    assert association.predicate == "biolink:associated_with_increased_likelihood_of"
    assert association.object == "MONDO:0016419"
    assert association.original_predicate == "Likely Pathogenic"


def test_unknown_gene_skipped(unknown_gene_entities):
    """Test that rows with unknown genes are skipped."""
    assert len(unknown_gene_entities) == 0


def test_invalid_assertion(mock_koza, pathogenic_row, map_cache):
    """Test that invalid assertions raise ValueError."""
    pathogenic_row["strongest_assertion"] = "Invalid"
    with pytest.raises(ValueError) as e_info:
        mock_koza(INGEST_NAME, pathogenic_row, TRANSFORM_SCRIPT, map_cache=map_cache)
    assert "Unexpected assertion" in str(e_info.value)
