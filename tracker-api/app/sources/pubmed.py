"""PubMed via NCBI E-utilities: newest articles with abstracts."""

import xml.etree.ElementTree as ET

from app.sources.base import RawItem, http_client

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


async def fetch_pubmed(query: str, limit: int) -> list[RawItem]:
    async with http_client() as client:
        search = await client.get(
            f"{EUTILS}/esearch.fcgi",
            params={
                "db": "pubmed",
                "term": query,
                "retmax": limit,
                "sort": "pub_date",
                "retmode": "json",
            },
        )
        search.raise_for_status()
        ids = search.json().get("esearchresult", {}).get("idlist", [])
        if not ids:
            return []
        fetched = await client.get(
            f"{EUTILS}/efetch.fcgi",
            params={"db": "pubmed", "id": ",".join(ids), "retmode": "xml"},
        )
        fetched.raise_for_status()

    items: list[RawItem] = []
    for article in ET.fromstring(fetched.text).iter("PubmedArticle"):
        pmid = article.findtext(".//PMID") or ""
        title_el = article.find(".//ArticleTitle")
        title = "".join(title_el.itertext()) if title_el is not None else ""
        abstract = " ".join("".join(part.itertext()) for part in article.iter("AbstractText"))
        year = article.findtext(".//PubDate/Year") or article.findtext(".//PubDate/MedlineDate")
        items.append(
            RawItem(
                source="pubmed",
                url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                title=title.strip(),
                snippet=abstract[:2000],
                published=year,
            )
        )
    return items
