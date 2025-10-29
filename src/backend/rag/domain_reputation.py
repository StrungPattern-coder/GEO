"""
Domain Reputation Scoring

Assigns trust scores to domains based on their authority and credibility.
Used to weight facts from different sources appropriately.
"""

from typing import Dict, Optional
from urllib.parse import urlparse
import re


class DomainReputationScorer:
    """Scores domains based on their reputation and authority."""
    
    def __init__(self):
        """Initialize with predefined domain scores."""
        # High-reputation academic/research domains
        self._academic_domains = {
            # Preprint servers
            "arxiv.org": 0.95,
            "biorxiv.org": 0.90,
            "medrxiv.org": 0.90,
            
            # Academic publishers
            "nature.com": 0.95,
            "science.org": 0.95,
            "sciencedirect.com": 0.90,
            "springer.com": 0.90,
            "acm.org": 0.92,
            "ieee.org": 0.92,
            "aaai.org": 0.92,
            "openreview.net": 0.88,
            "jmlr.org": 0.92,
            "pnas.org": 0.95,
            
            # Academic institutions
            "mit.edu": 0.93,
            "stanford.edu": 0.93,
            "berkeley.edu": 0.93,
            "cmu.edu": 0.93,
            "ox.ac.uk": 0.93,
            "cam.ac.uk": 0.93,
            
            # Research labs
            "openai.com": 0.88,
            "deepmind.com": 0.88,
            "anthropic.com": 0.88,
            "research.google": 0.88,
            "research.facebook.com": 0.85,
            "microsoft.com/research": 0.88,
            
            # Technical documentation
            "github.com": 0.75,
            "huggingface.co": 0.80,
            "paperswithcode.com": 0.82,
            "kaggle.com": 0.75,
            
            # News/Media (tech-focused)
            "techcrunch.com": 0.60,
            "wired.com": 0.65,
            "arstechnica.com": 0.70,
            "theverge.com": 0.60,
            "venturebeat.com": 0.55,
            
            # Encyclopedic
            "wikipedia.org": 0.75,
            "britannica.com": 0.80,
        }
        
        # Pattern-based scoring
        self._domain_patterns = [
            # Social media (lowest) - check first before .com pattern
            (r'(twitter\.com|x\.com|facebook\.com|linkedin\.com|reddit\.com)', 0.30),
            
            # Blog platforms (lower trust)
            (r'(medium\.com|substack\.com|wordpress\.com|blogger\.com)', 0.40),
            
            # Educational institutions (.edu domains)
            (r'\.edu$', 0.85),
            
            # Academic country codes
            (r'\.ac\.(uk|jp|kr|au|nz|za)$', 0.85),
            (r'\.edu\.(au|cn|sg|hk|tw)$', 0.85),
            
            # Government domains
            (r'\.gov$', 0.90),
            (r'\.gov\.(uk|au|ca|nz)$', 0.90),
            
            # Organization domains (mixed)
            (r'\.org$', 0.60),
            
            # Commercial domains (lower default)
            (r'\.com$', 0.45),
            (r'\.io$', 0.45),
            (r'\.co$', 0.40),
        ]
        
        # Recency decay by domain type
        self._recency_weights = {
            "academic": 0.10,  # Papers age slowly
            "news": 0.25,      # News ages quickly
            "docs": 0.15,      # Documentation moderate aging
            "blog": 0.20,      # Blogs age moderately
            "default": 0.15,   # Default aging
        }
    
    def score_domain(self, url: str) -> float:
        """
        Score a domain based on its URL.
        
        Args:
            url: Full URL or just domain
        
        Returns:
            Reputation score between 0.0-1.0
        """
        if not url:
            return 0.5  # Neutral score for missing URL
        
        try:
            # Extract domain from URL
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            domain = urlparse(url).netloc.lower()
            
            # Remove 'www.' prefix
            domain = re.sub(r'^www\.', '', domain)
            
            # Check exact match first
            if domain in self._academic_domains:
                return self._academic_domains[domain]
            
            # Check for subdomain matches (e.g., research.google.com)
            for known_domain, score in self._academic_domains.items():
                if known_domain in domain:
                    return score
            
            # Check pattern matches
            for pattern, score in self._domain_patterns:
                if re.search(pattern, domain):
                    return score
            
            # Default score for unknown domains
            return 0.45
        
        except Exception as e:
            print(f"[Domain Scoring] Error parsing URL {url}: {e}")
            return 0.45  # Neutral default
    
    def get_recency_weight(self, url: str) -> float:
        """
        Get the recency decay weight for a domain.
        
        Different domain types age at different rates:
        - Academic papers: slow decay (0.10)
        - News: fast decay (0.25)
        - Documentation: moderate decay (0.15)
        
        Args:
            url: Source URL
        
        Returns:
            Recency weight for exponential decay formula
        """
        if not url:
            return self._recency_weights["default"]
        
        try:
            domain = urlparse(url).netloc.lower() if url.startswith('http') else url.lower()
            domain = re.sub(r'^www\.', '', domain)
            
            # Academic domains
            if any(d in domain for d in ["arxiv", "acm.org", "ieee.org", ".edu", ".ac."]):
                return self._recency_weights["academic"]
            
            # News domains
            if any(d in domain for d in ["techcrunch", "wired", "theverge", "news"]):
                return self._recency_weights["news"]
            
            # Documentation
            if any(d in domain for d in ["github.com", "docs.", "documentation"]):
                return self._recency_weights["docs"]
            
            # Blog platforms
            if any(d in domain for d in ["medium", "substack", "blog"]):
                return self._recency_weights["blog"]
            
            return self._recency_weights["default"]
        
        except Exception:
            return self._recency_weights["default"]
    
    def explain_score(self, url: str) -> Dict:
        """
        Explain why a domain received its score.
        
        Args:
            url: Source URL
        
        Returns:
            Dict with score and explanation
        """
        score = self.score_domain(url)
        recency_weight = self.get_recency_weight(url)
        
        # Categorize score
        if score >= 0.90:
            category = "High Authority"
            reason = "Top-tier academic/research source"
        elif score >= 0.80:
            category = "Strong Authority"
            reason = "Reputable academic or research institution"
        elif score >= 0.70:
            category = "Good Authority"
            reason = "Trusted technical or educational source"
        elif score >= 0.60:
            category = "Moderate Authority"
            reason = "Credible but not authoritative"
        elif score >= 0.45:
            category = "Neutral"
            reason = "Unknown or commercial domain"
        else:
            category = "Low Authority"
            reason = "Blog, social media, or unverified source"
        
        return {
            "url": url,
            "domain_score": score,
            "recency_weight": recency_weight,
            "category": category,
            "reason": reason,
        }
    
    def get_all_known_domains(self) -> Dict[str, float]:
        """Return all known domain scores for debugging/monitoring."""
        return self._academic_domains.copy()


# Global instance for easy access
_domain_scorer = DomainReputationScorer()


def score_domain(url: str) -> float:
    """Convenience function to score a domain."""
    return _domain_scorer.score_domain(url)


def get_recency_weight(url: str) -> float:
    """Convenience function to get recency weight."""
    return _domain_scorer.get_recency_weight(url)


def explain_domain_score(url: str) -> Dict:
    """Convenience function to explain domain score."""
    return _domain_scorer.explain_score(url)
