"""Koza transform for ClinGen variant data to Biolink model entities."""

import uuid

import koza
from biolink_model.datamodel.pydanticmodel_v2 import (
    AgentTypeEnum,
    KnowledgeLevelEnum,
    SequenceVariant,
    VariantToDiseaseAssociation,
    VariantToGeneAssociation,
)

# Variant to gene predicate
IS_SEQUENCE_VARIANT_OF = "biolink:is_sequence_variant_of"

# Variant to disease
CAUSES = "biolink:causes"
ASSOCIATED_WITH_INCREASED_LIKELIHOOD = "biolink:associated_with_increased_likelihood_of"
GENETICALLY_ASSOCIATED_WITH = "biolink:genetically_associated_with"


def get_disease_predicate_and_negation(clinical_significance):
    """Get predicate and negation based on clinical significance."""
    if clinical_significance == 'Pathogenic':
        return CAUSES, False
    elif clinical_significance == 'Likely Pathogenic':
        return ASSOCIATED_WITH_INCREASED_LIKELIHOOD, False
    elif clinical_significance == 'Uncertain Significance':
        return GENETICALLY_ASSOCIATED_WITH, False
    else:
        raise ValueError(f"Not sure how to handle _assertion: '{clinical_significance}'")


# Track seen variants across rows
seen_variants = {}


@koza.transform_record()
def transform(koza_transform, row):
    """Transform a ClinGen variant row to Biolink entities."""
    global seen_variants
    entities = []

    # Skip rows with 'Benign' or 'Likely Benign' assertions and retracted variants
    if row["Assertion"] == "Benign" or row["Assertion"] == "Likely Benign" or row["Retracted"] == "true":
        return []

    allele_registry_curie = "CAID:{}".format(row['Allele Registry Id'])

    # When there is no 'ClinVar Variation Id', use 'Allele Registry Id' as the variant_id
    if row["ClinVar Variation Id"] == "-":
        variant_id = allele_registry_curie
    else:
        variant_id = "CLINVAR:{}".format(row['ClinVar Variation Id'])

    # When there is no 'Variation', use the first entry in 'HGVS Expressions' as the variant_name
    if row["Variation"] == "":
        variant_name = row['HGVS Expressions'].split(",")[0]
    else:
        variant_name = row["Variation"]

    gene_symbol = row['HGNC Gene Symbol']

    # Look up gene ID from HGNC lookup map using koza 2.x API
    # lookup(name, map_column, map_name) returns the value or the name if not found
    gene_id = koza_transform.lookup(gene_symbol, "hgnc_id", "hgnc_gene_lookup")
    # If lookup fails, it returns the input name - so check if it's a valid HGNC ID
    if gene_id == gene_symbol or not gene_id.startswith("HGNC:"):
        gene_id = None

    original_disease_predicate = row["Assertion"]
    if variant_id not in seen_variants:
        seen_variants[variant_id] = variant_id
        entities.append(
            SequenceVariant(
                id=variant_id,
                name=variant_name,
                xref=[allele_registry_curie],
                has_gene=[gene_id] if gene_id is not None else None,
                in_taxon=['NCBITaxon:9606'],
                in_taxon_label='Homo sapiens',
            )
        )

    predicate, negated = get_disease_predicate_and_negation(original_disease_predicate)
    entities.append(
        VariantToDiseaseAssociation(
            id=str(uuid.uuid4()),
            subject=variant_id,
            predicate=predicate,
            negated=negated,
            original_predicate=original_disease_predicate,
            object=row["Mondo Id"],
            primary_knowledge_source="infores:clingen",
            aggregator_knowledge_source=["infores:monarchinitiative"],
            knowledge_level=KnowledgeLevelEnum.knowledge_assertion,
            agent_type=AgentTypeEnum.manual_agent,
        )
    )

    if gene_id is not None:
        entities.append(
            VariantToGeneAssociation(
                id=str(uuid.uuid4()),
                subject=variant_id,
                predicate=IS_SEQUENCE_VARIANT_OF,
                object=gene_id,
                primary_knowledge_source="infores:clingen",
                aggregator_knowledge_source=["infores:monarchinitiative"],
                knowledge_level=KnowledgeLevelEnum.knowledge_assertion,
                agent_type=AgentTypeEnum.manual_agent,
            )
        )

    return entities
