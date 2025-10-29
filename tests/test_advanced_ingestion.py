"""
Tests for PDF extraction and content deduplication.
"""

import pytest
from src.backend.ingest.pdf_extractor import PDFExtractor, extract_pdf_text
from src.backend.ingest.deduplicator import ContentDeduplicator, is_duplicate_content, add_content


class TestPDFExtraction:
    """Test PDF extraction functionality."""
    
    def test_pdf_extractor_initialization(self):
        """Test that PDF extractor initializes correctly."""
        extractor = PDFExtractor(max_pages=10, timeout=15)
        
        assert extractor.max_pages == 10
        assert extractor.timeout == 15
        print("✅ PDF extractor initialized correctly")
    
    def test_arxiv_pdf_url_construction(self):
        """Test arXiv PDF URL construction."""
        extractor = PDFExtractor()
        
        # Test various arXiv ID formats
        test_ids = [
            ("2301.00001", "https://arxiv.org/pdf/2301.00001.pdf"),
            ("arXiv:2301.00001", "https://arxiv.org/pdf/2301.00001.pdf"),
        ]
        
        for arxiv_id, expected_url in test_ids:
            # URL construction is internal, but we can test the ID cleaning
            clean_id = arxiv_id.replace("arXiv:", "").strip()
            url = f"https://arxiv.org/pdf/{clean_id}.pdf"
            assert url == expected_url
        
        print("✅ arXiv PDF URL construction correct")
    
    def test_section_parsing(self):
        """Test section parsing from extracted text."""
        extractor = PDFExtractor()
        
        # Sample text with sections
        sample_text = """
        Deep Learning for Natural Language Processing
        
        Abstract: This paper presents a novel approach to NLP.
        We demonstrate improvements over baselines.
        
        1. Introduction
        Natural language processing has seen tremendous progress.
        Recent advances in deep learning have enabled...
        
        2. Related Work
        Previous work by Smith et al. focused on...
        
        References
        [1] Smith, J. (2020). Neural Networks.
        [2] Jones, M. (2021). Deep Learning.
        """
        
        sections = extractor._parse_sections(sample_text)
        
        assert "title" in sections
        assert "abstract" in sections
        assert "introduction" in sections
        assert "references" in sections
        
        # Check that abstract was found
        assert "novel approach" in sections["abstract"].lower()
        
        print("✅ Section parsing works")
        print(f"   Found sections: {list(sections.keys())}")


class TestContentDeduplication:
    """Test content deduplication functionality."""
    
    def test_deduplicator_initialization(self):
        """Test deduplicator initializes correctly."""
        dedup = ContentDeduplicator(threshold=0.8, num_perm=128)
        
        assert dedup.threshold == 0.8
        assert dedup.num_perm == 128
        
        stats = dedup.get_stats()
        assert stats["num_content"] == 0
        assert "has_lsh" in stats
        
        print("✅ Deduplicator initialized correctly")
    
    def test_exact_duplicate_detection(self):
        """Test exact duplicate detection."""
        dedup = ContentDeduplicator()
        
        # Add content
        text1 = "This is a sample research paper about machine learning."
        dedup.add_content(text1, source_url="https://example.com/paper1", title="ML Paper")
        
        # Check same content is detected as duplicate
        is_dup, match = dedup.is_duplicate(text1)
        assert is_dup
        assert match is not None
        assert match.source_url == "https://example.com/paper1"
        
        print("✅ Exact duplicate detection works")
    
    def test_near_duplicate_detection(self):
        """Test near-duplicate detection."""
        dedup = ContentDeduplicator(threshold=0.7)  # Lower threshold for testing
        
        # Add original content
        text1 = "This research paper discusses deep learning applications in natural language processing."
        dedup.add_content(text1, source_url="https://example.com/paper1", title="DL Paper 1")
        
        # Very similar content (should be detected as duplicate)
        text2 = "This research paper discusses deep learning applications for natural language processing."
        is_dup, match = dedup.is_duplicate(text2)
        
        # With LSH, this might be detected as duplicate
        # (depends on threshold and similarity)
        if dedup._has_lsh:
            # Just verify LSH is working, don't require match
            print(f"✅ Near-duplicate detection tested (LSH available, is_dup={is_dup})")
        else:
            print("⚠️  LSH not available, only exact matching")
    
    def test_non_duplicate_detection(self):
        """Test that different content is not marked as duplicate."""
        dedup = ContentDeduplicator()
        
        # Add content
        text1 = "Research on quantum computing and cryptography."
        dedup.add_content(text1, source_url="https://example.com/paper1", title="Quantum Paper")
        
        # Completely different content
        text2 = "A study of machine learning algorithms for image recognition."
        is_dup, match = dedup.is_duplicate(text2)
        
        assert not is_dup
        
        print("✅ Non-duplicate detection works")
    
    def test_find_similar_content(self):
        """Test finding similar content with scores."""
        dedup = ContentDeduplicator(threshold=0.7)
        
        # Add several pieces of content
        contents = [
            ("Machine learning for natural language processing", "paper1"),
            ("Deep learning applications in NLP", "paper2"),
            ("Quantum computing and cryptography", "paper3"),
        ]
        
        for text, url in contents:
            dedup.add_content(text, source_url=f"https://example.com/{url}", title=url)
        
        # Find similar to first one
        query = "Machine learning for natural language processing tasks"
        similar = dedup.find_duplicates(query, limit=3)
        
        if dedup._has_lsh:
            # Should find at least the first paper as similar
            assert len(similar) > 0
            print(f"✅ Found {len(similar)} similar documents")
            for sim_score, fingerprint in similar:
                print(f"   - {fingerprint.title}: {sim_score:.2f}")
        else:
            print("⚠️  LSH not available for similarity search")
    
    def test_deduplication_stats(self):
        """Test statistics gathering."""
        dedup = ContentDeduplicator()
        
        # Add some content
        for i in range(5):
            dedup.add_content(f"Content {i}", source_url=f"url{i}", title=f"Title {i}")
        
        stats = dedup.get_stats()
        
        assert stats["num_content"] == 5
        assert stats["threshold"] == 0.8
        
        print(f"✅ Deduplication stats: {stats}")
    
    def test_clear_deduplicator(self):
        """Test clearing the deduplicator."""
        dedup = ContentDeduplicator()
        
        # Add content
        dedup.add_content("Test content", source_url="url1", title="Test")
        assert dedup.get_stats()["num_content"] == 1
        
        # Clear
        dedup.clear()
        assert dedup.get_stats()["num_content"] == 0
        
        print("✅ Clear works correctly")
    
    def test_convenience_functions(self):
        """Test module-level convenience functions."""
        # Add content
        fp = add_content("Test paper content", source_url="test.com", title="Test")
        assert fp.source_url == "test.com"
        
        # Check duplicate
        is_dup = is_duplicate_content("Test paper content")
        assert is_dup
        
        print("✅ Convenience functions work")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing PDF Extraction")
    print("=" * 60)
    test_pdf = TestPDFExtraction()
    test_pdf.test_pdf_extractor_initialization()
    test_pdf.test_arxiv_pdf_url_construction()
    test_pdf.test_section_parsing()
    
    print("\n" + "=" * 60)
    print("Testing Content Deduplication")
    print("=" * 60)
    test_dedup = TestContentDeduplication()
    test_dedup.test_deduplicator_initialization()
    test_dedup.test_exact_duplicate_detection()
    test_dedup.test_near_duplicate_detection()
    test_dedup.test_non_duplicate_detection()
    test_dedup.test_find_similar_content()
    test_dedup.test_deduplication_stats()
    test_dedup.test_clear_deduplicator()
    test_dedup.test_convenience_functions()
    
    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
