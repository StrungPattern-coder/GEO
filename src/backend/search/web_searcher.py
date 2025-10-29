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
                    
                    if title and url:
                        results.append(SearchResult(
                            title=title,
                            url=url,
                            snippet=snippet or title,
                            source=source
                        ))
                except Exception as e:
                    print(f"[WebSearch] Error parsing result: {e}")
                    continue
            
            print(f"[WebSearch] Found {len(results)} results from DuckDuckGo")
            return results
            
        except Exception as e:
            print(f"[WebSearch] DuckDuckGo search failed: {e}")
            return []
    
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
        """Search using Google Custom Search API (requires API key)."""
        if not self.api_key:
            print("[WebSearch] Google API requires API key")
            return []
        
        try:
            # Note: Also needs GOOGLE_CSE_ID environment variable
            import os
            cse_id = os.getenv("GOOGLE_CSE_ID", "")
            if not cse_id:
                print("[WebSearch] Google CSE ID not found")
                return []
            
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": self.api_key,
                "cx": cse_id,
                "q": query,
                "num": min(num_results, 10)  # Google limits to 10
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
                    source=item.get("displayLink", "")
                ))
            
            print(f"[WebSearch] Found {len(results)} results from Google")
            return results
            
        except Exception as e:
            print(f"[WebSearch] Google search failed: {e}")
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
