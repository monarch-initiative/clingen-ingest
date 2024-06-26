import uuid  # For generating UUIDs for associations

from biolink_model.datamodel.pydanticmodel_v2 import (
    AgentTypeEnum,
    KnowledgeLevelEnum,
    SequenceVariant,
    VariantToDiseaseAssociation,
    VariantToGeneAssociation,
)
from koza.cli_utils import get_koza_app

koza_app = get_koza_app("clingen_variant")
hgnc_gene_lookup = koza_app.get_map('hgnc_gene_lookup')

CAUSES = "biolink:causes"
IS_SEQUENCE_VARIANT_OF = 'biolink:is_sequence_variant_of'
CONTRIBUTES_TO = "biolink:contributes_to"
ASSOCIATED_WITH = "biolink:associated_with"


def get_disease_predicate_and_negation(clinical_significance):
    if clinical_significance == 'Benign' or clinical_significance == 'Likely Benign':
        return CONTRIBUTES_TO, True
    elif clinical_significance == 'Likely Pathogenic' or clinical_significance == 'Pathogenic':
        return CAUSES, False
    elif clinical_significance == 'Uncertain Significance':
        # DONE: not sure how we should represent uncertain significance
        # Based on my reading of the Biolink Model and a sampling of these rows
        # I think "biolink:associated_with" is the most appropriate predicate
        return ASSOCIATED_WITH, False
    else:
        raise ValueError(f"Not sure how to handle _assertion: '{clinical_significance}'")


seen_variants = {}
while (row := koza_app.get_row()) is not None:
    # Code to transform each row of data
    # For more information, see https://koza.monarchinitiative.org/Ingests/transform
    entities = []

    if row["Retracted"] == "true":
        continue

    # DONE: Initially skipping rows with no variant; revisit this decision in the general context of g2d
    # These look like meaningful variants, so I'm transforming them
    # When there is no 'ClinVar Variation Id', use 'Allele Registry Id' as the variant_id
    if row["ClinVar Variation Id"] == "-":
        variant_id = row['Allele Registry Id']
    else:
        variant_id = "CLINVAR:{}".format(row['ClinVar Variation Id'])

    # When there is no 'Variation', use the first entry in 'HGVS Expressions' as the variant_name
    if row["Variation"] == "":
        variant_name = row['HGVS Expressions'].split(",")[0]
    else:
        variant_name = row["Variation"]

    gene_symbol = row['HGNC Gene Symbol']
    gene_id = hgnc_gene_lookup.get(gene_symbol)['hgnc_id'] if gene_symbol in hgnc_gene_lookup else None
    original_disease_predicate = row["Assertion"]
    if variant_id not in seen_variants:
        seen_variants[variant_id] = variant_id
        entities.append(
            SequenceVariant(
                id=variant_id,
                name=variant_name,
                xref=[row['Allele Registry Id']],
                # DONE: populate has_gene the first time, and then append for multiple genes?
                # There is only one duplicate variant, and they appear to be identical, so I'm skipping this for now
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
                # DONE: more specific predicates? is_missense_variant_of etc.
                # I don't see any fields that state type of variant, so I don't think we can be more specific
                predicate=IS_SEQUENCE_VARIANT_OF,
                object=gene_id,
                primary_knowledge_source="infores:clingen",
                aggregator_knowledge_source=["infores:monarchinitiative"],
                knowledge_level=KnowledgeLevelEnum.knowledge_assertion,
                agent_type=AgentTypeEnum.manual_agent,
            )
        )
    koza_app.write(*entities)
