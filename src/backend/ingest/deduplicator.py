"""
Content Deduplication Module

Uses MinHash LSH (Locality-Sensitive Hashing) to detect duplicate or near-duplicate content.
Prevents storing the same information multiple times in the knowledge graph.
"""

import hashlib
import re
from typing import List, Set, Optional, Dict, Tuple, Any
from dataclasses import dataclass

try:
    from datasketch import MinHash, MinHashLSH
    HAS_DATASKETCH = True
except ImportError:
    HAS_DATASKETCH = False
    MinHash = None  # type: ignore
    MinHashLSH = None  # type: ignore


@dataclass
class ContentFingerprint:
    """Represents a content fingerprint for deduplication."""
    content_hash: str  # SHA256 hash of content
    minhash: Optional[Any] = None  # MinHash signature (if datasketch available)
    source_url: str = ""
    title: str = ""
    length: int = 0


class ContentDeduplicator:
    """Detects duplicate and near-duplicate content using MinHash LSH."""
    
    def __init__(self, threshold: float = 0.8, num_perm: int = 128):
        """
        Initialize deduplicator.
        
        Args:
            threshold: Jaccard similarity threshold (0.8 = 80% similar)
            num_perm: Number of permutations for MinHash (higher = more accurate, slower)
        """
        self.threshold = threshold
        self.num_perm = num_perm
        
        # Storage for seen content
        self._exact_hashes: Set[str] = set()
        self._content_map: Dict[str, ContentFingerprint] = {}
        
        # MinHash LSH index (if available)
        if HAS_DATASKETCH:
            self._lsh = MinHashLSH(threshold=threshold, num_perm=num_perm)
            self._has_lsh = True
        else:
            self._lsh = None
            self._has_lsh = False
            print("[Dedup] Warning: datasketch not available, using exact hash only")
    
    def _normalize_text(self, text: str) -> str:
        """
        Normalize text for comparison.
        
        Args:
            text: Raw text
        
        Returns:
            Normalized text (lowercase, whitespace normalized)
        """
        # Lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special chars (keep alphanumeric and spaces)
        text = re.sub(r'[^a-z0-9\s]', '', text)
        
        return text.strip()
    
    def _compute_exact_hash(self, text: str) -> str:
        """
        Compute exact SHA256 hash of normalized text.
        
        Args:
            text: Text to hash
        
        Returns:
            Hex digest of SHA256 hash
        """
        normalized = self._normalize_text(text)
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()
    
    def _compute_minhash(self, text: str) -> Optional[Any]:
        """
        Compute MinHash signature for fuzzy matching.
        
        Args:
            text: Text to hash
        
        Returns:
            MinHash object or None if datasketch not available
        """
        if not self._has_lsh:
            return None
        
        normalized = self._normalize_text(text)
        
        # Create shingles (3-grams of words)
        words = normalized.split()
        shingles = []
        for i in range(len(words) - 2):
            shingle = ' '.join(words[i:i+3])
            shingles.append(shingle)
        
        # Compute MinHash
        m = MinHash(num_perm=self.num_perm)
        for shingle in shingles:
            m.update(shingle.encode('utf-8'))
        
        return m
    
    def add_content(self, text: str, source_url: str = "", title: str = "") -> ContentFingerprint:
        """
        Add content to the deduplication index.
        
        Args:
            text: Content text
            source_url: Source URL
            title: Content title
        
        Returns:
            ContentFingerprint for the added content
        """
        # Compute hashes
        exact_hash = self._compute_exact_hash(text)
        minhash = self._compute_minhash(text)
        
        # Create fingerprint
        fingerprint = ContentFingerprint(
            content_hash=exact_hash,
            minhash=minhash,
            source_url=source_url,
            title=title,
            length=len(text),
        )
        
        # Store exact hash
        self._exact_hashes.add(exact_hash)
        self._content_map[exact_hash] = fingerprint
        
        # Add to LSH index
        if self._has_lsh and minhash:
            self._lsh.insert(exact_hash, minhash)
        
        return fingerprint
    
    def is_duplicate(self, text: str) -> Tuple[bool, Optional[ContentFingerprint]]:
        """
        Check if content is a duplicate (exact or near-duplicate).
        
        Args:
            text: Content text to check
        
        Returns:
            Tuple of (is_duplicate, matching_fingerprint)
        """
        # Check exact match first (fast)
        exact_hash = self._compute_exact_hash(text)
        if exact_hash in self._exact_hashes:
            return True, self._content_map[exact_hash]
        
        # Check near-duplicates with LSH (if available)
        if self._has_lsh:
            minhash = self._compute_minhash(text)
            if minhash:
                matches = self._lsh.query(minhash)
                if matches:
                    # Return first match
                    match_hash = matches[0]
                    return True, self._content_map.get(match_hash)
        
        return False, None
    
    def find_duplicates(self, text: str, limit: int = 5) -> List[Tuple[float, ContentFingerprint]]:
        """
        Find similar content with similarity scores.
        
        Args:
            text: Content text to check
            limit: Maximum number of matches to return
        
        Returns:
            List of (similarity_score, fingerprint) tuples, sorted by similarity
        """
        results = []
        
        # Compute MinHash for query
        if not self._has_lsh:
            return results
        
        query_minhash = self._compute_minhash(text)
        if not query_minhash:
            return results
        
        # Find matches in LSH
        matches = self._lsh.query(query_minhash)
        
        # Compute exact similarity for each match
        for match_hash in matches[:limit]:
            if match_hash in self._content_map:
                fingerprint = self._content_map[match_hash]
                if fingerprint.minhash:
                    similarity = query_minhash.jaccard(fingerprint.minhash)
                    results.append((similarity, fingerprint))
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x[0], reverse=True)
        
        return results[:limit]
    
    def get_stats(self) -> Dict:
        """
        Get deduplication statistics.
        
        Returns:
            Dict with stats: {num_content, has_lsh, threshold}
        """
        return {
            "num_content": len(self._exact_hashes),
            "has_lsh": self._has_lsh,
            "threshold": self.threshold,
            "num_perm": self.num_perm,
        }
    
    def clear(self):
        """Clear all stored content."""
        self._exact_hashes.clear()
        self._content_map.clear()
        
        if self._has_lsh:
            # Recreate LSH index
            self._lsh = MinHashLSH(threshold=self.threshold, num_perm=self.num_perm)


# Global deduplicator instance
_deduplicator = ContentDeduplicator(threshold=0.8, num_perm=128)


def is_duplicate_content(text: str) -> bool:
    """
    Check if content is a duplicate (convenience function).
    
    Args:
        text: Content text
    
    Returns:
        True if duplicate, False otherwise
    """
    is_dup, _ = _deduplicator.is_duplicate(text)
    return is_dup


def add_content(text: str, source_url: str = "", title: str = "") -> ContentFingerprint:
    """
    Add content to deduplication index (convenience function).
    
    Args:
        text: Content text
        source_url: Source URL
        title: Content title
    
    Returns:
        ContentFingerprint
    """
    return _deduplicator.add_content(text, source_url, title)


def find_similar_content(text: str, limit: int = 5) -> List[Tuple[float, ContentFingerprint]]:
    """
    Find similar content (convenience function).
    
    Args:
        text: Content text
        limit: Maximum results
    
    Returns:
        List of (similarity, fingerprint) tuples
    """
    return _deduplicator.find_duplicates(text, limit)
