"""Koza transform for gene-to-disease associations from aggregated ClinGen data."""

import uuid

from biolink_model.datamodel.pydanticmodel_v2 import (
    AgentTypeEnum,
    CausalGeneToDiseaseAssociation,
    KnowledgeLevelEnum,
)
from koza.cli_utils import get_koza_app

koza_app = get_koza_app("clingen_gene_disease")
hgnc_gene_lookup = koza_app.get_map("hgnc_gene_lookup")

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


while (row := koza_app.get_row()) is not None:
    gene_symbol = row["gene_symbol"]
    mondo_id = row["mondo_id"]
    strongest_assertion = row["strongest_assertion"]

    # Look up HGNC gene ID
    if gene_symbol not in hgnc_gene_lookup:
        continue
    gene_id = hgnc_gene_lookup[gene_symbol]["hgnc_id"]

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

    koza_app.write(association)
