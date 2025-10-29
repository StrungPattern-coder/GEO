"""
Query Expansion Module

Expands user queries into multiple variants to improve retrieval coverage:
1. Synonym expansion
2. Acronym expansion
3. Related concept generation
4. Rephrasing for different contexts

Uses LLM for intelligent expansion.
"""

from typing import List, Dict, Set
import re
from ..config import settings


EXPANSION_PROMPT = """You are a query expansion assistant. Given a user question, generate 3-5 alternative phrasings that capture the same information need but use different terminology.

Rules:
- Include synonyms (e.g., "ML" → "machine learning", "artificial intelligence")
- Expand acronyms (e.g., "NLP" → "natural language processing")
- Rephrase using related concepts (e.g., "AI ethics" → "algorithmic fairness", "bias in ML")
- Keep expansions concise (5-15 words each)
- Don't change the core meaning
- Return ONLY the alternative queries, one per line, no numbering or explanation

Original Query: {query}

Alternative Queries:"""


class QueryExpander:
    """Expands queries using LLM-based semantic expansion and rule-based techniques."""
    
    def __init__(self, llm=None):
        """
        Initialize query expander.
        
        Args:
            llm: LLM instance for semantic expansion. If None, only rule-based expansion is used.
        """
        self.llm = llm
        self._acronym_cache: Dict[str, List[str]] = {
            # Common CS/AI acronyms
            "ai": ["artificial intelligence", "AI"],
            "ml": ["machine learning", "ML"],
            "nlp": ["natural language processing", "NLP"],
            "llm": ["large language model", "LLM"],
            "gpt": ["generative pre-trained transformer", "GPT"],
            "bert": ["bidirectional encoder representations", "BERT"],
            "cv": ["computer vision", "CV"],
            "rl": ["reinforcement learning", "RL"],
            "dl": ["deep learning", "DL"],
            "gan": ["generative adversarial network", "GAN"],
            "cnn": ["convolutional neural network", "CNN"],
            "rnn": ["recurrent neural network", "RNN"],
            "lstm": ["long short-term memory", "LSTM"],
            "sota": ["state of the art", "SOTA"],
            "api": ["application programming interface", "API"],
            "sdk": ["software development kit", "SDK"],
            "ui": ["user interface", "UI"],
            "ux": ["user experience", "UX"],
            "qa": ["question answering", "QA"],
            "rag": ["retrieval augmented generation", "RAG"],
            "kg": ["knowledge graph", "KG"],
            "geo": ["generative engine optimization", "GEO"],
        }
        
        self._synonym_map: Dict[str, List[str]] = {
            # Common research/tech synonyms
            "model": ["model", "architecture", "system", "framework"],
            "paper": ["paper", "article", "publication", "work", "study"],
            "method": ["method", "approach", "technique", "algorithm"],
            "dataset": ["dataset", "corpus", "benchmark", "data"],
            "performance": ["performance", "results", "accuracy", "metrics"],
            "training": ["training", "learning", "optimization"],
            "inference": ["inference", "prediction", "generation"],
            "evaluation": ["evaluation", "testing", "validation", "assessment"],
            "architecture": ["architecture", "model", "network", "design"],
            "transformer": ["transformer", "attention mechanism", "self-attention"],
            "embedding": ["embedding", "representation", "encoding", "vector"],
            "attention": ["attention", "attention mechanism", "attention weights"],
            "fine-tuning": ["fine-tuning", "adaptation", "transfer learning"],
            "prompt": ["prompt", "instruction", "query", "input"],
            "context": ["context", "background", "information", "knowledge"],
            "hallucination": ["hallucination", "fabrication", "false information"],
            "grounding": ["grounding", "factual accuracy", "attribution"],
            "citation": ["citation", "reference", "source", "attribution"],
        }
    
    def _expand_acronyms(self, query: str) -> List[str]:
        """Expand known acronyms in the query."""
        expansions = [query]
        words = query.split()
        
        for i, word in enumerate(words):
            # Remove punctuation for matching
            clean_word = re.sub(r'[^\w\s]', '', word).lower()
            if clean_word in self._acronym_cache:
                variants = self._acronym_cache[clean_word]
                new_expansions = []
                for exp in expansions:
                    for variant in variants:
                        # Replace the acronym with each variant, preserving punctuation
                        new_exp = exp.replace(word, variant, 1)
                        if new_exp != exp:  # Only add if different
                            new_expansions.append(new_exp)
                expansions.extend(new_expansions)
        
        return list(set(expansions))  # Deduplicate
    
    def _expand_synonyms(self, query: str) -> List[str]:
        """Expand query using synonym replacement."""
        expansions = [query]
        words = query.lower().split()
        
        for word in words:
            clean_word = re.sub(r'[^\w\s]', '', word)
            if clean_word in self._synonym_map:
                synonyms = self._synonym_map[clean_word]
                new_expansions = []
                for exp in expansions:
                    for syn in synonyms:
                        if syn != clean_word:  # Don't replace with itself
                            new_exp = re.sub(
                                r'\b' + re.escape(word) + r'\b',
                                syn,
                                exp,
                                flags=re.IGNORECASE
                            )
                            if new_exp != exp:
                                new_expansions.append(new_exp)
                # Limit explosion: keep top 3 per word
                expansions.extend(new_expansions[:3])
        
        return list(set(expansions[:10]))  # Cap at 10 total
    
    def _llm_expand(self, query: str) -> List[str]:
        """Use LLM to generate semantic expansions."""
        if self.llm is None:
            return []
        
        try:
            prompt = EXPANSION_PROMPT.format(query=query)
            response = self.llm.generate(prompt)
            
            # Parse response: split by newlines, clean up
            expansions = []
            for line in response.strip().split('\n'):
                line = line.strip()
                # Remove numbering (1., -, *, etc.)
                line = re.sub(r'^[\d\-\*\.\)]+\s*', '', line)
                line = line.strip('"\'')
                if line and len(line) > 5:  # Sanity check
                    expansions.append(line)
            
            return expansions[:5]  # Cap at 5 LLM expansions
        
        except Exception as e:
            # Fail gracefully if LLM expansion fails
            print(f"Query expansion LLM error: {e}")
            return []
    
    def expand(self, query: str, use_llm: bool = True) -> List[str]:
        """
        Expand a query into multiple variants.
        
        Args:
            query: Original user query
            use_llm: Whether to use LLM for semantic expansion (slower but better)
        
        Returns:
            List of query variants, including the original
        """
        if not query or not query.strip():
            return [query]
        
        expansions: Set[str] = {query}  # Start with original
        
        # 1. Acronym expansion (fast, always on)
        acronym_variants = self._expand_acronyms(query)
        expansions.update(acronym_variants[:3])  # Top 3 acronym variants
        
        # 2. Synonym expansion (fast, always on)
        synonym_variants = self._expand_synonyms(query)
        expansions.update(synonym_variants[:3])  # Top 3 synonym variants
        
        # 3. LLM expansion (slow, optional)
        if use_llm and settings.llm_provider != "mock":
            llm_variants = self._llm_expand(query)
            expansions.update(llm_variants)
        
        # Return as sorted list (original first)
        result = [query]
        result.extend([e for e in sorted(expansions) if e != query])
        
        return result[:3]  # Cap at 3 total expansions (faster responses)
    
    def get_expansion_stats(self, query: str, use_llm: bool = True) -> Dict:
        """
        Get detailed statistics about query expansion.
        
        Returns:
            Dict with expansion details for debugging/monitoring
        """
        expansions = self.expand(query, use_llm=use_llm)
        
        return {
            "original": query,
            "num_expansions": len(expansions) - 1,  # Exclude original
            "expansions": expansions[1:],  # Exclude original
            "total_variants": len(expansions),
            "llm_used": use_llm and settings.llm_provider != "mock",
        }


# Helper function for quick expansion
def expand_query(query: str, llm=None, use_llm: bool = True) -> List[str]:
    """
    Convenience function for query expansion.
    
    Args:
        query: User query to expand
        llm: Optional LLM instance
        use_llm: Whether to use LLM expansion
    
    Returns:
        List of query variants
    """
    expander = QueryExpander(llm=llm)
    return expander.expand(query, use_llm=use_llm)
