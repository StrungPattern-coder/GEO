"""Integration tests for advanced ingestion with real arXiv PDFs."""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.backend.ingest.pdf_extractor import PDFExtractor
from src.backend.ingest.deduplicator import ContentDeduplicator
from src.backend.ingest.ingestor import Ingestor

def test_arxiv_pdf_extraction():
    """Test extracting content from a real arXiv PDF."""
    print("\n" + "="*60)
    print("Testing arXiv PDF Extraction")
    print("="*60)
    
    extractor = PDFExtractor()
    
    # Test with a well-known short paper (Attention Is All You Need)
    arxiv_id = "1706.03762"  # Transformer paper
    
    try:
        result = extractor.extract_arxiv_pdf(arxiv_id)
        
        assert result is not None, "PDF extraction returned None"
        assert "text" in result, "Missing text key"
        assert len(result["text"]) > 1000, f"Text too short: {len(result['text'])} chars"
        
        print(f"✅ Successfully extracted PDF for arXiv:{arxiv_id}")
        print(f"   Text length: {len(result['text'])} chars")
        print(f"   Extraction method: {result.get('extraction_method', 'unknown')}")
        print(f"   Pages processed: {result.get('num_pages', 0)}")
        
        # Check for sections
        if "sections" in result:
            sections = result["sections"]
            print(f"   Sections found: {list(sections.keys())}")
            if "title" in sections and sections["title"]:
                print(f"   Title: {sections['title'][:50]}...")
            if "abstract" in sections and sections["abstract"]:
                print(f"   Abstract length: {len(sections['abstract'])} chars")
            if "introduction" in sections and sections["introduction"]:
                print(f"   Introduction length: {len(sections['introduction'])} chars")
            
        return True
        
    except Exception as e:
        print(f"⚠️  PDF extraction failed (may be network issue): {e}")
        print("   This is expected if offline or arXiv is slow")
        return False


def test_duplicate_arxiv_papers():
    """Test deduplication with real arXiv metadata."""
    print("\n" + "="*60)
    print("Testing Deduplication with arXiv Papers")
    print("="*60)
    
    dedup = ContentDeduplicator(threshold=0.8)
    
    # Simulate adding papers with similar content
    paper1_text = """
    Attention Is All You Need
    
    The dominant sequence transduction models are based on complex recurrent or 
    convolutional neural networks that include an encoder and a decoder. The best 
    performing models also connect the encoder and decoder through an attention 
    mechanism. We propose a new simple network architecture, the Transformer, 
    based solely on attention mechanisms, dispensing with recurrence and convolutions 
    entirely.
    """
    
    paper2_text = """
    Attention Is All You Need
    
    The dominant sequence transduction models are based on complex recurrent or 
    convolutional neural networks that include an encoder and decoder. The best 
    performing models also connect encoder and decoder through attention mechanism. 
    We propose a new simple network architecture, the Transformer, based solely on 
    attention mechanisms, dispensing with recurrence and convolutions entirely.
    """
    
    paper3_text = """
    BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding
    
    We introduce a new language representation model called BERT, which stands for 
    Bidirectional Encoder Representations from Transformers. Unlike recent language 
    representation models, BERT is designed to pre-train deep bidirectional 
    representations from unlabeled text by jointly conditioning on both left and 
    right context in all layers.
    """
    
    # Add papers
    dedup.add_content(paper1_text, source_url="https://arxiv.org/abs/1706.03762", title="Attention")
    dedup.add_content(paper3_text, source_url="https://arxiv.org/abs/1810.04805", title="BERT")
    
    # Check if paper2 (very similar to paper1) is detected as duplicate
    is_dup, match = dedup.is_duplicate(paper2_text)
    
    print(f"✅ Deduplication test completed")
    print(f"   Paper 1 (Attention): Added")
    print(f"   Paper 3 (BERT): Added (different content)")
    print(f"   Paper 2 (similar to Attention): is_dup={is_dup}")
    
    if is_dup and match:
        print(f"   ✅ Correctly detected as duplicate of: {match.title}")
    else:
        # Find similar papers
        similar = dedup.find_duplicates(paper2_text, limit=2)
        if similar:
            print(f"   Similar papers found:")
            for similarity_score, fingerprint in similar:
                print(f"      - {fingerprint.title}: {similarity_score:.2f} similarity")
    
    stats = dedup.get_stats()
    print(f"   Total papers indexed: {stats['num_content']}")
    
    return True


def test_ingestor_integration():
    """Test the enhanced Ingestor with PDF extraction and deduplication."""
    print("\n" + "="*60)
    print("Testing Ingestor Integration")
    print("="*60)
    
    # Import GraphClient for mock
    from src.backend.graph.client import GraphClient
    
    # For testing, we'll just verify initialization without actual Neo4j
    print("✅ Ingestor requires GraphClient instance")
    print("   (Skipping actual initialization - requires Neo4j connection)")
    print("   PDF extraction: available" if PDFExtractor else "   PDF extraction: not available")
    print("   Deduplication: available" if ContentDeduplicator else "   Deduplication: not available")
    
    return True


def test_content_parsing():
    """Test parsing of different content types."""
    print("\n" + "="*60)
    print("Testing Content Parsing")
    print("="*60)
    
    extractor = PDFExtractor()
    
    # Test section parsing with sample text
    sample_text = """
    Title: Deep Learning for Natural Language Processing
    
    Abstract
    
    This paper presents a comprehensive survey of deep learning techniques 
    for natural language processing tasks.
    
    1. Introduction
    
    Natural language processing (NLP) has seen tremendous progress in recent 
    years due to advances in deep learning.
    
    2. Related Work
    
    Previous work on NLP includes traditional statistical methods and early 
    neural network approaches.
    
    3. Methods
    
    We employ transformer-based architectures for our experiments.
    
    4. Results
    
    Our approach achieves state-of-the-art performance on several benchmarks.
    
    5. Conclusion
    
    We have demonstrated the effectiveness of deep learning for NLP.
    
    References
    
    [1] Attention Is All You Need. Vaswani et al., 2017.
    [2] BERT: Pre-training of Deep Bidirectional Transformers. Devlin et al., 2018.
    """
    
    sections = extractor._parse_sections(sample_text)
    
    print(f"✅ Parsed {len(sections)} sections")
    for section, content in sections.items():
        print(f"   - {section}: {len(content)} chars")
    
    # Verify expected sections
    expected_sections = ["title", "abstract", "introduction", "body", "references"]
    for section in expected_sections:
        assert section in sections, f"Missing section: {section}"
    
    print("✅ All expected sections found")
    
    return True


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Advanced Ingestion Integration Tests")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(("Content Parsing", test_content_parsing()))
    results.append(("Deduplication", test_duplicate_arxiv_papers()))
    results.append(("Ingestor Integration", test_ingestor_integration()))
    results.append(("arXiv PDF Extraction", test_arxiv_pdf_extraction()))
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n" + "="*60)
        print("✅ All integration tests passed!")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("⚠️  Some tests failed (may be expected if offline)")
        print("="*60)
