"""Upstream source version fetcher for clingen-ingest.

Two logical sources:
  - infores:clingen — variant classifications from the clinicalgenome.org API
  - infores:hgnc    — HGNC complete set used for gene symbol → ID mapping

ClinGen's erepo API doesn't surface a snapshot version (no Last-Modified
header, no version preamble in the file, no /info endpoint). Instead we
derive a version from the data itself: `max("Published Date")` across
the TSV. That date moves forward as new classifications are curated and
agrees across two fetches iff the dataset is unchanged.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import duckdb

from kozahub_metadata_schema import (
    now_iso,
    urls_from_download_yaml,
    version_from_http_last_modified,
)


INGEST_DIR = Path(__file__).resolve().parents[1]
DOWNLOAD_YAML = INGEST_DIR / "download.yaml"
CLINGEN_TSV = INGEST_DIR / "data" / "clingen_variants.tsv"


def version_from_clingen_tsv(path: Path) -> tuple[str, str]:
    """Read max(Published Date) from the ClinGen classifications TSV via DuckDB."""
    if not path.is_file():
        return "unknown", "unavailable"
    try:
        result = duckdb.sql(
            f"SELECT max(CAST(\"Published Date\" AS DATE)) "
            f"FROM read_csv_auto('{path.as_posix()}', delim='\\t', header=true)"
        ).fetchone()
    except duckdb.Error:
        return "unknown", "unavailable"
    if not result or result[0] is None:
        return "unknown", "unavailable"
    return result[0].isoformat(), "max_published_date"


def get_source_versions() -> list[dict[str, Any]]:
    clingen_urls = urls_from_download_yaml(DOWNLOAD_YAML, contains=["clinicalgenome.org"])
    hgnc_urls = urls_from_download_yaml(DOWNLOAD_YAML, contains=["public-download-files/hgnc"])
    now = now_iso()

    sources: list[dict[str, Any]] = []

    if clingen_urls:
        ver, method = version_from_clingen_tsv(CLINGEN_TSV)
        sources.append({
            "id": "infores:clingen",
            "name": "ClinGen — Clinical Genome Resource",
            "urls": clingen_urls,
            "version": ver,
            "version_method": method,
            "retrieved_at": now,
        })

    if hgnc_urls:
        ver, method = version_from_http_last_modified(hgnc_urls[0])
        sources.append({
            "id": "infores:hgnc",
            "name": "HUGO Gene Nomenclature Committee",
            "urls": hgnc_urls,
            "version": ver,
            "version_method": method,
            "retrieved_at": now,
        })

    return sources
