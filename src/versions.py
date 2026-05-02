"""Upstream source version fetcher for clingen-ingest.

Two logical sources:
  - infores:clingen — variant classifications from the clinicalgenome.org API
  - infores:hgnc    — HGNC complete set used for gene symbol → ID mapping
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from kozahub_metadata_schema import (
    now_iso,
    urls_from_download_yaml,
    version_from_http_last_modified,
)


INGEST_DIR = Path(__file__).resolve().parents[1]
DOWNLOAD_YAML = INGEST_DIR / "download.yaml"


def get_source_versions() -> list[dict[str, Any]]:
    clingen_urls = urls_from_download_yaml(DOWNLOAD_YAML, contains=["clinicalgenome.org"])
    hgnc_urls = urls_from_download_yaml(DOWNLOAD_YAML, contains=["public-download-files/hgnc"])
    now = now_iso()

    sources: list[dict[str, Any]] = []

    if clingen_urls:
        ver, method = version_from_http_last_modified(clingen_urls[0])
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
