"""
Query Complexity Analyzer

Analyzes user queries to dynamically determine the optimal number of sources needed.
No more hardcoded limits - intelligently adapts to query complexity!

Query Types:
- Simple (3-5 sources): "What is Python?", "Who is Elon Musk?"
- Medium (5-8 sources): "Explain quantum computing", "Compare React vs Vue"
- Complex (8-15 sources): "Latest developments in AI", "Is climate change real?"
- Deep Research (15-25 sources): "Comprehensive analysis of...", "What are all the..."
"""

from typing import Dict, Tuple
import re


class QueryComplexityAnalyzer:
    """Analyzes query complexity to determine optimal number of sources."""
    
    # Keywords that indicate complexity levels
    SIMPLE_INDICATORS = [
        r'\bwho is\b', r'\bwhat is\b', r'\bwhen was\b', r'\bwhere is\b',
        r'\bdefine\b', r'\bmeaning of\b', r'\bshort answer\b',
    ]
    
    COMPLEX_INDICATORS = [
        r'\bcompare\b', r'\bcontrast\b', r'\bversus\b', r'\bvs\b',
        r'\bdifference between\b', r'\badvantages and disadvantages\b',
        r'\bpros and cons\b', r'\blatest\b', r'\brecent\b', r'\bcurrent\b',
        r'\bnew\b', r'\btrending\b', r'\b2024\b', r'\b2025\b',
    ]
    
    DEEP_RESEARCH_INDICATORS = [
        r'\bcomprehensive\b', r'\bdetailed analysis\b', r'\bin-depth\b',
        r'\ball aspects\b', r'\beverything about\b', r'\bcomplete guide\b',
        r'\blist all\b', r'\bwhat are all\b', r'\btell me everything\b',
        r'\bexhaustive\b', r'\bthorough\b', r'\ball the\b',
    ]
    
    CONTROVERSY_KEYWORDS = [
        'debate', 'controversy', 'disputed', 'conflicting', 'evidence',
        'claim', 'prove', 'disprove', 'myth', 'fact check', 'true or false',
        'is it true', 'really', 'actually', 'climate change', 'vaccine',
        'conspiracy', 'fake news', 'misinformation',
    ]
    
    MULTI_ENTITY_KEYWORDS = [
        'and', 'or', 'versus', 'vs', 'compared to', 'different types of',
        'various', 'multiple', 'several', 'many', 'list of',
    ]
    
    def __init__(self):
        """Initialize the query analyzer."""
        self.min_sources = 3   # Minimum for any query
        self.max_sources = 25  # Maximum to prevent overload
    
    def analyze(self, query: str) -> Dict:
        """
        Analyze query complexity and return optimal configuration.
        
        Args:
            query: User's search query
            
        Returns:
            Dict with:
                - num_sources: Optimal number of sources (3-25)
                - complexity: 'simple', 'medium', 'complex', or 'deep_research'
                - reasoning: Explanation of the decision
                - confidence: Confidence score (0.0-1.0)
        """
        query_lower = query.lower()
        
        # Calculate complexity score
        complexity_score = self._calculate_complexity_score(query_lower)
        
        # Determine optimal number of sources
        num_sources, complexity_level = self._determine_num_sources(complexity_score, query_lower)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(query, query_lower, complexity_score, complexity_level)
        
        # Calculate confidence
        confidence = min(0.95, 0.6 + (complexity_score * 0.35))
        
        return {
            'num_sources': num_sources,
            'complexity': complexity_level,
            'reasoning': reasoning,
            'confidence': confidence,
            'complexity_score': complexity_score,
        }
    
    def _calculate_complexity_score(self, query_lower: str) -> float:
        """
        Calculate a complexity score from 0.0 (simple) to 1.0 (very complex).
        
        Factors:
        - Query length (longer = more complex)
        - Number of entities/concepts (multiple entities = more complex)
        - Presence of complexity keywords
        - Question type (comparison, latest, controversial)
        - Specificity (vague = more complex)
        """
        score = 0.0
        
        # Factor 1: Query length (max +0.2)
        word_count = len(query_lower.split())
        length_score = min(0.2, word_count / 50.0)  # 50+ words = max score
        score += length_score
        
        # Factor 2: Simple indicators (max -0.3, makes it simpler)
        for pattern in self.SIMPLE_INDICATORS:
            if re.search(pattern, query_lower):
                score -= 0.15
                break  # Only apply once
        
        # Factor 3: Complex indicators (max +0.3)
        complex_matches = sum(1 for pattern in self.COMPLEX_INDICATORS 
                            if re.search(pattern, query_lower))
        score += min(0.3, complex_matches * 0.15)
        
        # Factor 4: Deep research indicators (max +0.4)
        deep_matches = sum(1 for pattern in self.DEEP_RESEARCH_INDICATORS 
                          if re.search(pattern, query_lower))
        score += min(0.4, deep_matches * 0.2)
        
        # Factor 5: Controversy keywords (max +0.25)
        controversy_matches = sum(1 for kw in self.CONTROVERSY_KEYWORDS 
                                 if kw in query_lower)
        score += min(0.25, controversy_matches * 0.125)
        
        # Factor 6: Multiple entities (max +0.2)
        multi_entity_matches = sum(1 for kw in self.MULTI_ENTITY_KEYWORDS 
                                  if kw in query_lower)
        score += min(0.2, multi_entity_matches * 0.1)
        
        # Factor 7: Question marks (multiple questions = more complex)
        question_marks = query_lower.count('?')
        if question_marks > 1:
            score += min(0.15, (question_marks - 1) * 0.075)
        
        # Factor 8: Technical terms (heuristic: words with 8+ chars)
        long_words = [w for w in query_lower.split() if len(w) >= 8]
        tech_score = min(0.15, len(long_words) * 0.03)
        score += tech_score
        
        # Normalize to 0.0-1.0 range
        return max(0.0, min(1.0, score))
    
    def _determine_num_sources(self, complexity_score: float, query_lower: str) -> Tuple[int, str]:
        """
        Determine the optimal number of sources based on complexity score.
        
        Thresholds:
        - 0.0-0.25: Simple (3-5 sources)
        - 0.25-0.50: Medium (5-8 sources)
        - 0.50-0.75: Complex (8-15 sources)
        - 0.75-1.0: Deep Research (15-25 sources)
        """
        if complexity_score < 0.25:
            # Simple query
            num_sources = max(3, min(5, int(3 + complexity_score * 8)))
            return num_sources, 'simple'
        
        elif complexity_score < 0.50:
            # Medium complexity
            num_sources = max(5, min(8, int(5 + (complexity_score - 0.25) * 12)))
            return num_sources, 'medium'
        
        elif complexity_score < 0.75:
            # Complex query
            num_sources = max(8, min(15, int(8 + (complexity_score - 0.50) * 28)))
            return num_sources, 'complex'
        
        else:
            # Deep research
            num_sources = max(15, min(25, int(15 + (complexity_score - 0.75) * 40)))
            return num_sources, 'deep_research'
    
    def _generate_reasoning(self, query: str, query_lower: str, 
                          complexity_score: float, complexity_level: str) -> str:
        """Generate human-readable reasoning for the decision."""
        reasons = []
        
        # Check for simple indicators
        if any(re.search(pattern, query_lower) for pattern in self.SIMPLE_INDICATORS):
            reasons.append("simple definitional query")
        
        # Check for complex indicators
        if any(re.search(pattern, query_lower) for pattern in self.COMPLEX_INDICATORS):
            reasons.append("requires comparison or latest information")
        
        # Check for deep research indicators
        if any(re.search(pattern, query_lower) for pattern in self.DEEP_RESEARCH_INDICATORS):
            reasons.append("comprehensive analysis requested")
        
        # Check for controversy
        if any(kw in query_lower for kw in self.CONTROVERSY_KEYWORDS):
            reasons.append("controversial topic requiring multiple perspectives")
        
        # Check for multiple entities
        if any(kw in query_lower for kw in self.MULTI_ENTITY_KEYWORDS):
            reasons.append("multiple entities or concepts to compare")
        
        # Check query length
        word_count = len(query.split())
        if word_count > 20:
            reasons.append(f"long query ({word_count} words)")
        elif word_count < 5:
            reasons.append(f"short query ({word_count} words)")
        
        # Build reasoning string
        if not reasons:
            reasons.append("standard informational query")
        
        reasoning = f"{complexity_level.replace('_', ' ').title()} query: {', '.join(reasons)}"
        return reasoning
    
    def get_optimal_sources(self, query: str) -> int:
        """
        Convenience method to get just the number of sources.
        
        Args:
            query: User's search query
            
        Returns:
            int: Optimal number of sources (3-25)
        """
        analysis = self.analyze(query)
        return analysis['num_sources']


# Singleton instance
_analyzer = None

def analyze_query(query: str) -> Dict:
    """
    Analyze query complexity and return optimal configuration.
    
    Args:
        query: User's search query
        
    Returns:
        Dict with num_sources, complexity, reasoning, confidence
    """
    global _analyzer
    if _analyzer is None:
        _analyzer = QueryComplexityAnalyzer()
    return _analyzer.analyze(query)


def get_optimal_num_sources(query: str) -> int:
    """
    Get optimal number of sources for a query.
    
    Args:
        query: User's search query
        
    Returns:
        int: Optimal number of sources (3-25)
    """
    global _analyzer
    if _analyzer is None:
        _analyzer = QueryComplexityAnalyzer()
    return _analyzer.get_optimal_sources(query)
