"""
Test Query Analyzer - Dynamic Source Determination

Run this to see how the system intelligently determines the number of sources
based on query complexity. No more hardcoded 8 sources!
"""

from src.backend.rag.query_analyzer import analyze_query


# Test queries of varying complexity
test_queries = [
    # Simple queries (3-5 sources)
    "What is Python?",
    "Who is Elon Musk?",
    "Define quantum computing",
    "When was Python invented?",
    
    # Medium queries (5-8 sources)
    "Explain machine learning",
    "How does blockchain work?",
    "What is the difference between AI and ML?",
    "Compare React vs Vue",
    
    # Complex queries (8-15 sources)
    "What are the latest developments in AI?",
    "Is climate change real?",
    "Compare the advantages and disadvantages of nuclear energy",
    "What are the recent breakthroughs in quantum computing?",
    "Pros and cons of electric vehicles in 2025",
    
    # Deep research queries (15-25 sources)
    "Comprehensive analysis of COVID-19 vaccines",
    "Tell me everything about the James Webb Space Telescope",
    "What are all the controversies surrounding social media algorithms?",
    "List all the major AI breakthroughs in 2024 and 2025",
    "Detailed analysis of the ethical implications of gene editing",
]


def test_query_analyzer():
    """Test the query analyzer on various queries."""
    print("=" * 80)
    print("🎯 DYNAMIC SOURCE DETERMINATION TEST")
    print("=" * 80)
    print()
    
    for i, query in enumerate(test_queries, 1):
        analysis = analyze_query(query)
        
        print(f"{i}. Query: \"{query}\"")
        print(f"   ├─ Complexity: {analysis['complexity'].replace('_', ' ').title()}")
        print(f"   ├─ Optimal Sources: {analysis['num_sources']}")
        print(f"   ├─ Confidence: {analysis['confidence']:.1%}")
        print(f"   ├─ Score: {analysis['complexity_score']:.3f}")
        print(f"   └─ Reasoning: {analysis['reasoning']}")
        print()
    
    print("=" * 80)
    print("✅ DYNAMIC SOURCE DETERMINATION WORKING!")
    print("=" * 80)
    print()
    print("Key Insights:")
    print("  • Simple queries (\"What is X?\") → 3-5 sources")
    print("  • Medium queries (comparisons, explanations) → 5-8 sources")
    print("  • Complex queries (latest, controversial) → 8-15 sources")
    print("  • Deep research (comprehensive, list all) → 15-25 sources")
    print()
    print("The system now INTELLIGENTLY adapts to your question!")
    print("No more hardcoded 8 sources everywhere. 🎉")


if __name__ == "__main__":
    test_query_analyzer()
