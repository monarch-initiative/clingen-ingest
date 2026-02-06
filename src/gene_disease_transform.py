"""Koza transform for gene-to-disease associations from aggregated ClinGen data."""

import uuid

import koza
from biolink_model.datamodel.pydanticmodel_v2 import (
    AgentTypeEnum,
    CausalGeneToDiseaseAssociation,
    KnowledgeLevelEnum,
)

# Gene to disease predicates (matching variant-to-disease predicates)
CAUSES = "biolink:causes"
ASSOCIATED_WITH_INCREASED_LIKELIHOOD = "biolink:associated_with_increased_likelihood_of"


def get_predicate(assertion: str) -> str:
    """Get the predicate based on strongest assertion level."""
    if assertion == "Pathogenic":
        return CAUSES
    elif assertion == "Likely Pathogenic":
        return ASSOCIATED_WITH_INCREASED_LIKELIHOOD
    else:
        raise ValueError(f"Unexpected assertion: '{assertion}'")


@koza.transform_record()
def transform(koza_transform, row):
    """Transform an aggregated gene-disease row to a CausalGeneToDiseaseAssociation."""
    gene_symbol = row["gene_symbol"]
    mondo_id = row["mondo_id"]
    strongest_assertion = row["strongest_assertion"]

    # Look up HGNC gene ID using koza 2.x API
    # lookup(name, map_column, map_name) returns the value or the name if not found
    gene_id = koza_transform.lookup(gene_symbol, "hgnc_id", "hgnc_gene_lookup")
    # If lookup fails, it returns the input name - so check if it's a valid HGNC ID
    if gene_id == gene_symbol or not gene_id.startswith("HGNC:"):
        return []

    predicate = get_predicate(strongest_assertion)

    association = CausalGeneToDiseaseAssociation(
        id=str(uuid.uuid4()),
        subject=gene_id,
        predicate=predicate,
        object=mondo_id,
        original_predicate=strongest_assertion,
        primary_knowledge_source="infores:clingen",
        aggregator_knowledge_source=["infores:monarchinitiative"],
        knowledge_level=KnowledgeLevelEnum.knowledge_assertion,
        agent_type=AgentTypeEnum.manual_agent,
    )

    return [association]
