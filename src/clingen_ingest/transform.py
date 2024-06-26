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
RELATED_TO = "biolink:related_to"

seen_variants = {}


def get_disese_predicate_and_negation(clinical_significance):
    if clinical_significance == 'Benign' or clinical_significance == 'Likely Benign':
        return CONTRIBUTES_TO, True
    elif clinical_significance == 'Likely Pathogenic' or clinical_significance == 'Pathogenic':
        return CAUSES, False
    elif clinical_significance == 'Uncertain Significance':
        # TODO: not sure how we to represent uncertain significance
        return RELATED_TO, False
    else:
        raise ValueError(f"Not sure how to handle _assertion: '{clinical_significance}'")


while (row := koza_app.get_row()) is not None:
    # Code to transform each row of data
    # For more information, see https://koza.monarchinitiative.org/Ingests/transform
    entities = []

    if row["Retracted"] == "true":
        continue

    # Initially, skip rows with no variant, TODO: Revisit this decision after consulting in the general context of g2d
    if row["ClinVar Variation Id"] == "-" or row["Variation"] == "":
        continue

    variant_id = "CLINVAR:{}".format(row['ClinVar Variation Id'])

    gene_symbol = row['HGNC Gene Symbol']
    gene_id = "HGNC:" + hgnc_gene_lookup.get(gene_symbol)['hgnc_id'] if gene_symbol in hgnc_gene_lookup else None
    original_disease_predicate = row["Assertion"]
    if variant_id not in seen_variants:
        entities.append(
            SequenceVariant(
                id=variant_id,
                name=row['Variation'],
                xref=[row['Allele Registry Id']],
                # There are no duplicate variants, so we can just populate has_gene and not worry about multiples
                has_gene= [gene_id] if gene_id is not None else None,
                in_taxon=['NCBITaxon:9606'],
                in_taxon_label='Homo sapiens',
            )
        )
    predicate, negated = get_disese_predicate_and_negation(original_disease_predicate)
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
                predicate=IS_SEQUENCE_VARIANT_OF,  # TODO: more specific predicates? is_missense_variant_of etc
                object=gene_id,
                primary_knowledge_source="infores:clingen",
                aggregator_knowledge_source=["infores:monarchinitiative"],
                knowledge_level=KnowledgeLevelEnum.knowledge_assertion,
                agent_type=AgentTypeEnum.manual_agent,
            )
        )
    koza_app.write(*entities)
