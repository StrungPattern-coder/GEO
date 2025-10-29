import time
import re
from typing import Dict, Any, Iterable, List
try:
    import requests  # type: ignore
    import feedparser  # type: ignore
    from bs4 import BeautifulSoup  # type: ignore  # noqa: F401
    _HAS_EXT = True
except Exception:
    _HAS_EXT = False
from ..graph.client import GraphClient
from ..config import settings

# Import PDF extraction and deduplication
try:
    from .pdf_extractor import PDFExtractor
    from .deduplicator import ContentDeduplicator
    _HAS_ADVANCED = True
except ImportError:
    _HAS_ADVANCED = False
    PDFExtractor = None  # type: ignore
    ContentDeduplicator = None  # type: ignore

# Simple truth-weight heuristic
# Sources with .gov, .edu get +0.2, well-known domains +0.1, else base 0.5
TRUST_BONUS = {
    ".gov": 0.2,
    ".edu": 0.2,
    "arxiv.org": 0.15,
    "ai.googleblog.com": 0.1,
}

def truth_weight_for(url: str) -> float:
    base = 0.5
    bonus = 0.0
    for k, v in TRUST_BONUS.items():
        if k in url:
            bonus = max(bonus, v)
    return max(0.0, min(1.0, base + bonus))

class Ingestor:
    def __init__(self, graph: GraphClient, use_pdf_extraction: bool = True, use_deduplication: bool = True):
        self.graph = graph
        self.use_pdf_extraction = use_pdf_extraction and _HAS_ADVANCED
        self.use_deduplication = use_deduplication and _HAS_ADVANCED
        
        # Initialize PDF extractor
        if self.use_pdf_extraction and PDFExtractor is not None:
            try:
                self.pdf_extractor = PDFExtractor(max_pages=50, timeout=30)
                print("[Ingestor] PDF extraction enabled")
            except Exception as e:
                print(f"[Ingestor] PDF extraction disabled: {e}")
                self.pdf_extractor = None
                self.use_pdf_extraction = False
        else:
            self.pdf_extractor = None
        
        # Initialize deduplicator
        if self.use_deduplication and ContentDeduplicator is not None:
            try:
                self.deduplicator = ContentDeduplicator(threshold=0.8, num_perm=128)
                print("[Ingestor] Deduplication enabled")
            except Exception as e:
                print(f"[Ingestor] Deduplication disabled: {e}")
                self.deduplicator = None
                self.use_deduplication = False
        else:
            self.deduplicator = None

    def ingest_arxiv(self, query: str):
        if not _HAS_EXT:
            return
        url = "http://export.arxiv.org/api/query"
        params = {"search_query": query, "start": 0, "max_results": 10}
        r = requests.get(url, params=params, timeout=20)  # type: ignore
        r.raise_for_status()
        feed = feedparser.parse(r.text)  # type: ignore
        for entry in feed.entries:
            paper_id = entry.get("id", entry.get("link"))
            title_val = entry.get("title", "")
            if isinstance(title_val, list):
                title_val = " ".join(str(t) for t in title_val)
            elif title_val is None:
                title_val = ""
            title = str(title_val).strip()
            
            # Extract abstract/summary
            summary_val = entry.get("summary", "")
            if isinstance(summary_val, list):
                summary_val = " ".join(str(s) for s in summary_val)
            summary = str(summary_val or "").strip()[:500]  # Limit to 500 chars
            
            # Extract categories/tags
            tags = entry.get("tags", [])
            categories = []
            if isinstance(tags, list):
                categories = [str(t.get("term", "")) for t in tags if isinstance(t, dict) and t.get("term")]
            category_str = ", ".join(categories[:5])  # Limit to 5 categories
            
            authors_list = entry.get("authors", [])

            if not isinstance(authors_list, list):
                authors_list = []
            authors = ", ".join(
                [str(a.get("name", "")) for a in authors_list if isinstance(a, dict) and isinstance(a.get("name", ""), str)]
            )
            link = entry.get("link", paper_id)
            # arXiv uses 'updated' or 'published' fields
            ts = str(entry.get("updated", entry.get("published", "")) or "")
            tw = truth_weight_for(str(link))
            # Emit simple facts
            facts = [
                {
                    "id": f"{paper_id}#title",
                    "subject": paper_id,
                    "predicate": "title",
                    "object": title,
                    "source_url": link,
                    "source_name": "arXiv",
                    "ts": ts,
                    "truth_weight": tw,
                },
                {
                    "id": f"{paper_id}#authors",
                    "subject": paper_id,
                    "predicate": "authors",
                    "object": authors,
                    "source_url": link,
                    "source_name": "arXiv",
                    "ts": ts,
                    "truth_weight": tw,
                },
            ]
            if summary:
                facts.append({
                    "id": f"{paper_id}#abstract",
                    "subject": paper_id,
                    "predicate": "abstract",
                    "object": summary,
                    "source_url": link,
                    "source_name": "arXiv",
                    "ts": ts,
                    "truth_weight": tw,
                })
            if category_str:
                facts.append({
                    "id": f"{paper_id}#categories",
                    "subject": paper_id,
                    "predicate": "categories",
                    "object": category_str,
                    "source_url": link,
                    "source_name": "arXiv",
                    "ts": ts,
                    "truth_weight": tw,
                })
            
            # Extract full PDF content if enabled
            if self.use_pdf_extraction and self.pdf_extractor:
                try:
                    # Extract arXiv ID from paper_id (ensure string)
                    paper_id_str = str(paper_id) if paper_id else ""
                    arxiv_id = paper_id_str.split("/")[-1] if "/" in paper_id_str else paper_id_str
                    
                    # Check for duplicates before extracting PDF
                    should_extract = True
                    if self.use_deduplication and self.deduplicator:
                        # Check if we've already seen this paper (by title + abstract)
                        dedup_text = f"{title} {summary}"
                        is_dup, existing = self.deduplicator.is_duplicate(dedup_text)
                        if is_dup:
                            print(f"[Ingestor] Skipping duplicate paper: {title[:50]}... (matches {existing.source_url if existing else 'unknown'})")
                            should_extract = False
                        else:
                            # Add to deduplication index
                            link_str = str(link) if link else ""
                            self.deduplicator.add_content(dedup_text, source_url=link_str, title=title)
                    
                    if should_extract:
                        print(f"[Ingestor] Extracting PDF for {arxiv_id}")
                        pdf_content = self.pdf_extractor.extract_arxiv_pdf(arxiv_id)
                        
                        if pdf_content and pdf_content.get("sections"):
                            sections = pdf_content["sections"]
                            
                            # Add full text as a fact (truncated)
                            if sections.get("body"):
                                facts.append({
                                    "id": f"{paper_id}#fulltext",
                                    "subject": paper_id,
                                    "predicate": "fulltext",
                                    "object": sections["body"][:2000],  # First 2000 chars
                                    "source_url": link,
                                    "source_name": "arXiv PDF",
                                    "ts": ts,
                                    "truth_weight": tw,
                                })
                            
                            # Add introduction if available
                            if sections.get("introduction"):
                                facts.append({
                                    "id": f"{paper_id}#introduction",
                                    "subject": paper_id,
                                    "predicate": "introduction",
                                    "object": sections["introduction"][:1000],
                                    "source_url": link,
                                    "source_name": "arXiv PDF",
                                    "ts": ts,
                                    "truth_weight": tw,
                                })
                            
                            print(f"[Ingestor] Extracted {pdf_content.get('num_pages', 0)} pages from PDF")
                except Exception as e:
                    print(f"[Ingestor] PDF extraction failed for {paper_id}: {e}")
            
            for f in facts:
                self.graph.upsert_fact(f)

    def ingest_rss(self, urls: List[str]):
        if not _HAS_EXT:
            # minimal fallback: insert stub facts
            for u in urls:
                f = {
                    "id": f"{u}#title",
                    "subject": u,
                    "predicate": "title",
                    "object": "Feed (deps not installed)",
                    "source_url": u,
                    "truth_weight": truth_weight_for(u),
                }
                self.graph.upsert_fact(f)
            return
        for u in urls:
            feed = feedparser.parse(u)  # type: ignore
            for e in feed.entries[:10]:
                link_val = e.get("link", "")
                if isinstance(link_val, list):
                    link = " ".join(str(l) for l in link_val)
                elif link_val is None:
                    link = ""
                else:
                    link = str(link_val)
                link = str(link)  # Ensure link is always a string
                title = e.get("title", "")
                ts = str(e.get("updated", e.get("published", "")) or "")
                tw = truth_weight_for(str(link))
                fid = f"{link}#title"
                f = {
                    "id": fid,
                    "subject": link,
                    "predicate": "title",
                    "object": title,
                    "source_url": link,
                    "source_name": u,
                    "ts": ts,
                    "truth_weight": tw,
                }
                self.graph.upsert_fact(f)

    def run_all(self):
        if settings.arxiv_query:
            self.ingest_arxiv(settings.arxiv_query)
        if settings.rss_feeds:
            urls = [u.strip() for u in settings.rss_feeds.split(",") if u.strip()]
            self.ingest_rss(urls)
