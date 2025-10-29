"""
Tests for query expansion and domain reputation scoring.
"""

import pytest
from src.backend.rag.query_expansion import QueryExpander, expand_query
from src.backend.rag.domain_reputation import DomainReputationScorer, score_domain, explain_domain_score


class TestQueryExpansion:
    """Test query expansion functionality."""
    
    def test_basic_expansion(self):
        """Test that expansion generates variants."""
        expander = QueryExpander(llm=None)
        
        query = "AI ethics"
        expansions = expander.expand(query, use_llm=False)
        
        # Should include original + expansions
        assert query in expansions
        assert len(expansions) > 1
        print(f"Expanded '{query}' to: {expansions}")
    
    def test_acronym_expansion(self):
        """Test acronym expansion."""
        expander = QueryExpander(llm=None)
        
        # Test AI expansion
        query = "What is AI?"
        expansions = expander.expand(query, use_llm=False)
        
        # Should expand AI to "artificial intelligence"
        assert any("artificial intelligence" in e.lower() for e in expansions)
        print(f"AI expansion: {expansions}")
        
        # Test ML expansion
        query = "ML models"
        expansions = expander.expand(query, use_llm=False)
        assert any("machine learning" in e.lower() for e in expansions)
        print(f"ML expansion: {expansions}")
    
    def test_synonym_expansion(self):
        """Test synonym expansion."""
        expander = QueryExpander(llm=None)
        
        query = "paper about transformers"
        expansions = expander.expand(query, use_llm=False)
        
        # Should expand "paper" to synonyms
        assert any("article" in e.lower() or "publication" in e.lower() for e in expansions)
        print(f"Synonym expansion: {expansions}")
    
    def test_no_expansion_for_empty(self):
        """Test that empty queries don't break."""
        expander = QueryExpander(llm=None)
        
        expansions = expander.expand("", use_llm=False)
        assert len(expansions) == 1
        assert expansions[0] == ""
    
    def test_expansion_deduplication(self):
        """Test that expansions don't contain duplicates."""
        expander = QueryExpander(llm=None)
        
        query = "AI and ML"
        expansions = expander.expand(query, use_llm=False)
        
        # Should not have duplicates
        assert len(expansions) == len(set(expansions))
    
    def test_expansion_limit(self):
        """Test that expansions are capped at reasonable limit."""
        expander = QueryExpander(llm=None)
        
        query = "AI ML NLP model paper method"
        expansions = expander.expand(query, use_llm=False)
        
        # Should cap at 8 total
        assert len(expansions) <= 8
        print(f"Capped expansion: {len(expansions)} variants")
    
    def test_get_expansion_stats(self):
        """Test expansion statistics."""
        expander = QueryExpander(llm=None)
        
        query = "RAG systems"
        stats = expander.get_expansion_stats(query, use_llm=False)
        
        assert stats["original"] == query
        assert stats["num_expansions"] >= 0
        assert "expansions" in stats
        assert "total_variants" in stats
        print(f"Expansion stats: {stats}")


class TestDomainReputation:
    """Test domain reputation scoring."""
    
    def test_academic_domains_high_score(self):
        """Test that academic domains get high scores."""
        scorer = DomainReputationScorer()
        
        # Top-tier academic
        assert scorer.score_domain("https://arxiv.org/abs/2301.00001") >= 0.90
        assert scorer.score_domain("https://nature.com/article/123") >= 0.90
        assert scorer.score_domain("https://science.org/doi/123") >= 0.90
        
        # Research institutions
        assert scorer.score_domain("https://mit.edu/research") >= 0.85
        assert scorer.score_domain("https://stanford.edu/ai") >= 0.85
        
        print("Academic domains scored correctly")
    
    def test_tech_domains_moderate_score(self):
        """Test that tech domains get moderate scores."""
        scorer = DomainReputationScorer()
        
        assert 0.70 <= scorer.score_domain("https://github.com/user/repo") <= 0.80
        assert 0.75 <= scorer.score_domain("https://huggingface.co/models") <= 0.85
        
        print("Tech domains scored correctly")
    
    def test_news_domains_lower_score(self):
        """Test that news domains get lower scores."""
        scorer = DomainReputationScorer()
        
        assert 0.50 <= scorer.score_domain("https://techcrunch.com/article") <= 0.65
        assert 0.55 <= scorer.score_domain("https://wired.com/story") <= 0.70
        
        print("News domains scored correctly")
    
    def test_blog_domains_low_score(self):
        """Test that blog platforms get low scores."""
        scorer = DomainReputationScorer()
        
        assert scorer.score_domain("https://medium.com/@user/post") <= 0.45
        assert scorer.score_domain("https://substack.com/article") <= 0.45
        
        print("Blog domains scored correctly")
    
    def test_social_media_lowest_score(self):
        """Test that social media gets lowest scores."""
        scorer = DomainReputationScorer()
        
        assert scorer.score_domain("https://twitter.com/user/status") <= 0.35
        assert scorer.score_domain("https://reddit.com/r/sub/post") <= 0.35
        
        print("Social media scored correctly")
    
    def test_edu_pattern_matching(self):
        """Test .edu pattern matching."""
        scorer = DomainReputationScorer()
        
        # Unknown .edu should still get decent score
        assert scorer.score_domain("https://unknown-university.edu/paper") >= 0.80
        
        print(".edu pattern matched correctly")
    
    def test_recency_weights(self):
        """Test domain-specific recency weights."""
        scorer = DomainReputationScorer()
        
        # Academic papers should age slowly
        assert scorer.get_recency_weight("https://arxiv.org/abs/123") == 0.10
        
        # News should age quickly
        assert scorer.get_recency_weight("https://techcrunch.com/article") == 0.25
        
        # Blogs moderate aging
        assert scorer.get_recency_weight("https://medium.com/post") == 0.20
        
        print("Recency weights correct")
    
    def test_explain_score(self):
        """Test score explanation."""
        scorer = DomainReputationScorer()
        
        explanation = scorer.explain_score("https://arxiv.org")
        
        assert "url" in explanation
        assert "domain_score" in explanation
        assert "category" in explanation
        assert "reason" in explanation
        assert explanation["domain_score"] >= 0.90
        assert explanation["category"] == "High Authority"
        
        print(f"Explanation: {explanation}")
    
    def test_url_parsing_robustness(self):
        """Test that URL parsing handles edge cases."""
        scorer = DomainReputationScorer()
        
        # Missing protocol
        assert scorer.score_domain("arxiv.org") >= 0.90
        
        # With www prefix
        assert scorer.score_domain("https://www.nature.com") >= 0.90
        
        # With subdomain
        assert scorer.score_domain("https://research.google.com") >= 0.85
        
        # Empty URL
        assert scorer.score_domain("") == 0.5
        
        print("URL parsing robust")
    
    def test_convenience_functions(self):
        """Test module-level convenience functions."""
        score = score_domain("https://arxiv.org")
        assert score >= 0.90
        
        explanation = explain_domain_score("https://arxiv.org")
        assert explanation["domain_score"] >= 0.90
        
        print("Convenience functions work")


if __name__ == "__main__":
    # Run tests
    print("Testing Query Expansion...")
    test_expansion = TestQueryExpansion()
    test_expansion.test_basic_expansion()
    test_expansion.test_acronym_expansion()
    test_expansion.test_synonym_expansion()
    test_expansion.test_no_expansion_for_empty()
    test_expansion.test_expansion_deduplication()
    test_expansion.test_expansion_limit()
    test_expansion.test_get_expansion_stats()
    
    print("\nTesting Domain Reputation...")
    test_domain = TestDomainReputation()
    test_domain.test_academic_domains_high_score()
    test_domain.test_tech_domains_moderate_score()
    test_domain.test_news_domains_lower_score()
    test_domain.test_blog_domains_low_score()
    test_domain.test_social_media_lowest_score()
    test_domain.test_edu_pattern_matching()
    test_domain.test_recency_weights()
    test_domain.test_explain_score()
    test_domain.test_url_parsing_robustness()
    test_domain.test_convenience_functions()
    
    print("\n✅ All tests passed!")
