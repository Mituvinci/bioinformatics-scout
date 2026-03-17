"""PubMed search tool wrapping NCBI Entrez API via Biopython."""

import os
from xml.etree import ElementTree

from agents import function_tool
from Bio import Entrez

Entrez.email = os.environ.get("NCBI_EMAIL", "user@example.com")


def _fetch_details(id_list: list[str], max_results: int = 3) -> list[dict]:
    """Fetch paper metadata for a list of PubMed IDs."""
    if not id_list:
        return []

    ids = id_list[:max_results]
    handle = Entrez.efetch(db="pubmed", id=",".join(ids), rettype="xml", retmode="xml")
    raw = handle.read()
    handle.close()

    root = ElementTree.fromstring(raw)
    papers = []
    for article in root.findall(".//PubmedArticle"):
        medline = article.find(".//MedlineCitation")
        art = medline.find(".//Article") if medline is not None else None
        if art is None:
            continue

        title_el = art.find("ArticleTitle")
        title = title_el.text if title_el is not None and title_el.text else "No title"

        abstract_el = art.find(".//AbstractText")
        abstract = abstract_el.text if abstract_el is not None and abstract_el.text else "No abstract available"

        pmid_el = medline.find("PMID")
        pmid = pmid_el.text if pmid_el is not None else ""

        # Extract DOI from ArticleIdList
        doi = ""
        for aid in article.findall(".//ArticleId"):
            if aid.get("IdType") == "doi":
                doi = aid.text or ""
                break

        papers.append(
            {
                "title": title,
                "abstract": abstract[:500],
                "pmid": pmid,
                "doi": doi,
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            }
        )

    return papers


@function_tool
def pubmed_search(query: str, max_results: int = 3) -> str:
    """Search PubMed for papers matching the query. Returns titles, abstracts, PMIDs, and DOIs.

    Args:
        query: The search query for PubMed.
        max_results: Maximum number of papers to return (default 3).
    """
    handle = Entrez.esearch(db="pubmed", term=query, retmax=max_results, sort="relevance")
    record = Entrez.read(handle)
    handle.close()

    id_list = record.get("IdList", [])
    if not id_list:
        return f"No PubMed results found for: {query}"

    papers = _fetch_details(id_list, max_results)
    if not papers:
        return f"No PubMed results found for: {query}"

    lines = []
    for i, p in enumerate(papers, 1):
        lines.append(
            f"[PubMed {i}]\n"
            f"Title: {p['title']}\n"
            f"Abstract: {p['abstract']}\n"
            f"PMID: {p['pmid']}\n"
            f"DOI: {p['doi']}\n"
            f"URL: {p['url']}\n"
        )
    return "\n".join(lines)
