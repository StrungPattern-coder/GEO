"""
Real-time web search module for dynamic fact retrieval.
Supports multiple search providers with fallback mechanisms.
"""

import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import requests
from bs4 import BeautifulSoup
import re

@dataclass
class SearchResult:
    """A single search result from the web."""
    title: str
    url: str
    snippet: str
    source: str
    timestamp: str = ""
    
    def to_fact(self) -> Dict[str, Any]:
        """Convert search result to a fact dict."""
        return {
            "id": f"{self.url}#snippet",
            "subject": self.title,
            "predicate": "content",
            "object": self.snippet,
            "source_url": self.url,
            "source_name": self.source,
            "ts": self.timestamp or time.strftime("%Y-%m-%d"),
            "truth_weight": self._compute_trust_weight(),
            "score": 0.8,  # Initial relevance score
        }
    
    def _compute_trust_weight(self) -> float:
        """Compute trust weight based on domain."""
        url_lower = self.url.lower()
        
        # High trust domains
        if any(d in url_lower for d in [".gov", ".edu", "arxiv.org", "nature.com", "science.org"]):
            return 0.9
        
        # Medium-high trust
        if any(d in url_lower for d in [".org", "wikipedia.org", "stackoverflow.com", "github.com"]):
            return 0.75
        
        # Medium trust
        if any(d in url_lower for d in ["medium.com", "towardsdatascience.com", "blog"]):
            return 0.6
        
        # Default
        return 0.5


class WebSearcher:
    """
    Real-time web search with multiple provider support.
    """
    
    def __init__(self, provider: str = "duckduckgo", api_key: Optional[str] = None):
        """
        Initialize web searcher.
        
        Args:
            provider: "duckduckgo" (free), "tavily" (paid), "serpapi" (paid), "google" (paid)
            api_key: API key for paid providers
        """
        self.provider = provider
        self.api_key = api_key
        self.timeout = 10
        
        print(f"[WebSearcher] Initialized with provider: {provider}")
    
    def search(self, query: str, num_results: int = 8) -> List[SearchResult]:
        """
        Search the web in real-time.
        
        Args:
            query: Search query
            num_results: Number of results to return
            
        Returns:
            List of SearchResult objects
        """
        print(f"[WebSearch] Searching for: '{query}' (provider: {self.provider})")
        
        try:
            if self.provider == "duckduckgo":
                return self._search_duckduckgo(query, num_results)
            elif self.provider == "tavily":
                return self._search_tavily(query, num_results)
            elif self.provider == "serpapi":
                return self._search_serpapi(query, num_results)
            elif self.provider == "google":
                return self._search_google(query, num_results)
            else:
                print(f"[WebSearch] Unknown provider: {self.provider}, falling back to DuckDuckGo")
                return self._search_duckduckgo(query, num_results)
        except Exception as e:
            print(f"[WebSearch] Error: {e}")
            return []
    
    def _search_duckduckgo(self, query: str, num_results: int) -> List[SearchResult]:
        """
        Search using DuckDuckGo (free, no API key needed).
        Uses HTML scraping as DuckDuckGo doesn't have an official API.
        """
        try:
            # DuckDuckGo HTML search
            url = "https://html.duckduckgo.com/html/"
            params = {"q": query}
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
            
            response = requests.post(url, data=params, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # Parse search results
            for result_div in soup.find_all('div', class_='result')[:num_results]:
                try:
                    # Extract title and URL
                    title_tag = result_div.find('a', class_='result__a')
                    if not title_tag:
                        continue
                    
                    title = title_tag.get_text(strip=True)
                    url = title_tag.get('href', '')
                    
                    # Extract snippet
                    snippet_tag = result_div.find('a', class_='result__snippet')
                    snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
                    
                    # Extract source domain
                    source_tag = result_div.find('span', class_='result__url')
                    source = source_tag.get_text(strip=True) if source_tag else url
                    
                    # Extract date/timestamp from snippet if available
                    timestamp = self._extract_date_from_text(snippet + " " + title)
                    
                    if title and url:
                        results.append(SearchResult(
                            title=title,
                            url=url,
                            snippet=snippet or title,
                            source=source,
                            timestamp=timestamp
                        ))
                except Exception as e:
                    print(f"[WebSearch] Error parsing result: {e}")
                    continue
            
            print(f"[WebSearch] Found {len(results)} results from DuckDuckGo")
            return results
            
        except Exception as e:
            print(f"[WebSearch] DuckDuckGo search failed: {e}")
            return []
    
    def _extract_date_from_text(self, text: str) -> str:
        """
        Extract date from text using regex patterns.
        Looks for dates like: "Mar 3, 2025", "March 2025", "2025-03-03", etc.
        """
        import re
        from datetime import datetime
        
        if not text:
            return ""
        
        # Pattern 1: "Mar 3, 2025" or "March 3, 2025"
        pattern1 = r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{1,2}),?\s+(\d{4})'
        match1 = re.search(pattern1, text, re.IGNORECASE)
        if match1:
            try:
                date_str = f"{match1.group(1)} {match1.group(2)}, {match1.group(3)}"
                parsed = datetime.strptime(date_str, "%b %d, %Y")
                return parsed.strftime("%Y-%m-%d")
            except:
                pass
        
        # Pattern 2: "3 March 2025" or "3 Mar 2025"
        pattern2 = r'(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{4})'
        match2 = re.search(pattern2, text, re.IGNORECASE)
        if match2:
            try:
                date_str = f"{match2.group(2)} {match2.group(1)}, {match2.group(3)}"
                parsed = datetime.strptime(date_str, "%b %d, %Y")
                return parsed.strftime("%Y-%m-%d")
            except:
                pass
        
        # Pattern 3: "2025-03-03" (ISO format)
        pattern3 = r'(\d{4})-(\d{2})-(\d{2})'
        match3 = re.search(pattern3, text)
        if match3:
            return match3.group(0)
        
        # Pattern 4: Just year "2025" or "2024" (last resort)
        pattern4 = r'\b(202[3-9]|203[0-9])\b'
        match4 = re.search(pattern4, text)
        if match4:
            return f"{match4.group(0)}-01-01"  # Default to Jan 1st
        
        return ""
    
    def _search_tavily(self, query: str, num_results: int) -> List[SearchResult]:
        """Search using Tavily AI API (requires API key)."""
        if not self.api_key:
            print("[WebSearch] Tavily requires API key")
            return []
        
        try:
            url = "https://api.tavily.com/search"
            payload = {
                "api_key": self.api_key,
                "query": query,
                "search_depth": "advanced",
                "max_results": num_results
            }
            
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get("results", []):
                results.append(SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("content", ""),
                    source=item.get("url", "").split("//")[-1].split("/")[0]
                ))
            
            print(f"[WebSearch] Found {len(results)} results from Tavily")
            return results
            
        except Exception as e:
            print(f"[WebSearch] Tavily search failed: {e}")
            return []
    
    def _search_serpapi(self, query: str, num_results: int) -> List[SearchResult]:
        """Search using SerpAPI (requires API key)."""
        if not self.api_key:
            print("[WebSearch] SerpAPI requires API key")
            return []
        
        try:
            url = "https://serpapi.com/search"
            params = {
                "q": query,
                "api_key": self.api_key,
                "num": num_results
            }
            
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get("organic_results", []):
                results.append(SearchResult(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                    source=item.get("displayed_link", "")
                ))
            
            print(f"[WebSearch] Found {len(results)} results from SerpAPI")
            return results
            
        except Exception as e:
            print(f"[WebSearch] SerpAPI search failed: {e}")
            return []
    
    def _search_google(self, query: str, num_results: int) -> List[SearchResult]:
        """
        Search using Google (supports both free scraping and paid API).
        
        If GOOGLE_API_KEY is set, uses official Custom Search API.
        Otherwise, falls back to free HTML scraping.
        """
        # Try official API first if API key is available
        if self.api_key:
            return self._search_google_api(query, num_results)
        else:
            # Fall back to free scraping
            print("[WebSearch] Using free Google scraping (no API key)")
            return self._search_google_scrape(query, num_results)
    
    def _search_google_api(self, query: str, num_results: int) -> List[SearchResult]:
        """Search using Google Custom Search API (paid, requires API key + CSE ID)."""
        try:
            import os
            cse_id = os.getenv("GOOGLE_CSE_ID", "")
            if not cse_id:
                print("[WebSearch] GOOGLE_CSE_ID not set, falling back to scraping")
                return self._search_google_scrape(query, num_results)
            
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": self.api_key,
                "cx": cse_id,
                "q": query,
                "num": min(num_results, 10)  # Google API limits to 10
            }
            
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get("items", []):
                results.append(SearchResult(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                    source=item.get("displayLink", ""),
                    timestamp=self._extract_date_from_text(item.get("snippet", ""))
                ))
            
            print(f"[WebSearch] Found {len(results)} results from Google API")
            return results
            
        except Exception as e:
            print(f"[WebSearch] Google API failed: {e}, trying scraping")
            return self._search_google_scrape(query, num_results)
    
    def _search_google_scrape(self, query: str, num_results: int) -> List[SearchResult]:
        """
        Search Google using free HTML scraping (no API key needed).
        Note: Google may rate-limit this method. Use responsibly.
        """
        try:
            # Google search URL
            url = "https://www.google.com/search"
            params = {"q": query, "num": num_results}
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # Parse organic search results
            # Google uses different div structures, so we try multiple selectors
            search_divs = soup.find_all('div', class_='g')
            
            for div in search_divs[:num_results]:
                try:
                    # Extract title and URL
                    title_tag = div.find('h3')
                    if not title_tag:
                        continue
                    
                    title = title_tag.get_text(strip=True)
                    
                    # Find the link (usually in parent <a> tag)
                    link_tag = div.find('a', href=True)
                    if not link_tag:
                        continue
                    
                    url = link_tag['href']
                    
                    # Skip non-http links (like javascript:void(0))
                    if not url.startswith('http'):
                        continue
                    
                    # Extract snippet/description
                    snippet_divs = div.find_all(['div', 'span'], class_=lambda x: x and ('VwiC3b' in x or 'IsZvec' in x or 'aCOpRe' in x))
                    snippet = ""
                    for s_div in snippet_divs:
                        text = s_div.get_text(strip=True)
                        if len(text) > len(snippet):
                            snippet = text
                    
                    # If no snippet found, try alternative selectors
                    if not snippet:
                        snippet_tag = div.find('div', {'data-sncf': '1'})
                        if snippet_tag:
                            snippet = snippet_tag.get_text(strip=True)
                    
                    # Extract source domain
                    cite_tag = div.find('cite')
                    source = cite_tag.get_text(strip=True) if cite_tag else url.split("//")[-1].split("/")[0]
                    
                    # Extract timestamp
                    timestamp = self._extract_date_from_text(snippet + " " + title)
                    
                    if title and url:
                        results.append(SearchResult(
                            title=title,
                            url=url,
                            snippet=snippet or title,
                            source=source,
                            timestamp=timestamp
                        ))
                        
                except Exception as e:
                    print(f"[WebSearch] Error parsing Google result: {e}")
                    continue
            
            print(f"[WebSearch] Found {len(results)} results from Google (scraping)")
            return results
            
        except Exception as e:
            print(f"[WebSearch] Google scraping failed: {e}")
            return []


def search_web_realtime(query: str, provider: str = "duckduckgo", num_results: int = 8) -> List[Dict[str, Any]]:
    """
    Convenience function for real-time web search.
    
    Args:
        query: Search query
        provider: Search provider to use
        num_results: Number of results
        
    Returns:
        List of facts extracted from search results
    """
    import os
    api_key = os.getenv(f"{provider.upper()}_API_KEY", "")
    
    searcher = WebSearcher(provider=provider, api_key=api_key)
    results = searcher.search(query, num_results)
    
    # Convert to facts
    facts = [result.to_fact() for result in results]
    return facts
