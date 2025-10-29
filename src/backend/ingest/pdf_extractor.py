"""
PDF Content Extraction Module

Extracts text content from PDF files (especially arXiv papers).
Supports multiple extraction strategies with fallback.
"""

import io
import re
from typing import Optional, Dict, List, Tuple, Any
from urllib.parse import urlparse
import requests
import requests_cache

# Try to import PDF libraries
try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False
    pdfplumber = None  # type: ignore

try:
    from PyPDF2 import PdfReader
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False
    PdfReader = None  # type: ignore


# Configure HTTP caching to avoid re-downloading PDFs
requests_cache.install_cache(
    'pdf_cache',
    backend='sqlite',
    expire_after=86400,  # 24 hours
)


class PDFExtractor:
    """Extract text content from PDF files with multiple fallback strategies."""
    
    def __init__(self, max_pages: int = 50, timeout: int = 30):
        """
        Initialize PDF extractor.
        
        Args:
            max_pages: Maximum number of pages to extract (to limit processing time)
            timeout: HTTP timeout in seconds
        """
        self.max_pages = max_pages
        self.timeout = timeout
        
        if not HAS_PDFPLUMBER and not HAS_PYPDF2:
            raise ImportError(
                "No PDF library available. Install with: "
                "pip install pdfplumber PyPDF2"
            )
    
    def extract_from_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Download and extract text from a PDF URL.
        
        Args:
            url: URL to PDF file
        
        Returns:
            Dict with extracted content or None on failure:
            {
                "text": str,           # Full extracted text
                "sections": Dict,      # Structured sections (title, abstract, body)
                "num_pages": int,      # Number of pages processed
                "extraction_method": str,  # Which library was used
                "metadata": Dict,      # PDF metadata
            }
        """
        try:
            # Download PDF
            print(f"[PDF] Downloading from {url}")
            response = requests.get(url, timeout=self.timeout, stream=True)
            response.raise_for_status()
            
            # Check if actually PDF
            content_type = response.headers.get('Content-Type', '')
            if 'pdf' not in content_type.lower():
                print(f"[PDF] Warning: Content-Type is {content_type}, not PDF")
            
            pdf_bytes = response.content
            print(f"[PDF] Downloaded {len(pdf_bytes)} bytes")
            
            # Extract text
            return self.extract_from_bytes(pdf_bytes)
        
        except requests.exceptions.RequestException as e:
            print(f"[PDF] Download error: {e}")
            return None
        except Exception as e:
            print(f"[PDF] Extraction error: {e}")
            return None
    
    def extract_from_bytes(self, pdf_bytes: bytes) -> Optional[Dict[str, Any]]:
        """
        Extract text from PDF bytes.
        
        Args:
            pdf_bytes: Raw PDF file bytes
        
        Returns:
            Dict with extracted content or None
        """
        # Try pdfplumber first (better quality)
        if HAS_PDFPLUMBER:
            result = self._extract_with_pdfplumber(pdf_bytes)
            if result:
                return result
        
        # Fallback to PyPDF2
        if HAS_PYPDF2:
            result = self._extract_with_pypdf2(pdf_bytes)
            if result:
                return result
        
        print("[PDF] All extraction methods failed")
        return None
    
    def _extract_with_pdfplumber(self, pdf_bytes: bytes) -> Optional[Dict]:
        """Extract using pdfplumber (preferred, better quality)."""
        try:
            print("[PDF] Attempting extraction with pdfplumber")
            pdf_file = io.BytesIO(pdf_bytes)
            
            with pdfplumber.open(pdf_file) as pdf:
                num_pages = min(len(pdf.pages), self.max_pages)
                print(f"[PDF] Processing {num_pages} pages (total: {len(pdf.pages)})")
                
                # Extract text from all pages
                text_parts = []
                for i, page in enumerate(pdf.pages[:num_pages]):
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                
                full_text = "\n\n".join(text_parts)
                
                # Extract metadata
                metadata = pdf.metadata or {}
                
                # Parse into sections
                sections = self._parse_sections(full_text)
                
                return {
                    "text": full_text,
                    "sections": sections,
                    "num_pages": num_pages,
                    "extraction_method": "pdfplumber",
                    "metadata": metadata,
                }
        
        except Exception as e:
            print(f"[PDF] pdfplumber extraction failed: {e}")
            return None
    
    def _extract_with_pypdf2(self, pdf_bytes: bytes) -> Optional[Dict]:
        """Extract using PyPDF2 (fallback, lower quality)."""
        try:
            print("[PDF] Attempting extraction with PyPDF2")
            pdf_file = io.BytesIO(pdf_bytes)
            
            reader = PdfReader(pdf_file)
            num_pages = min(len(reader.pages), self.max_pages)
            print(f"[PDF] Processing {num_pages} pages (total: {len(reader.pages)})")
            
            # Extract text from all pages
            text_parts = []
            for page in reader.pages[:num_pages]:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            
            full_text = "\n\n".join(text_parts)
            
            # Extract metadata
            metadata = dict(reader.metadata) if reader.metadata else {}
            
            # Parse into sections
            sections = self._parse_sections(full_text)
            
            return {
                "text": full_text,
                "sections": sections,
                "num_pages": num_pages,
                "extraction_method": "PyPDF2",
                "metadata": metadata,
            }
        
        except Exception as e:
            print(f"[PDF] PyPDF2 extraction failed: {e}")
            return None
    
    def _parse_sections(self, text: str) -> Dict[str, str]:
        """
        Parse extracted text into structured sections.
        
        Args:
            text: Full extracted text
        
        Returns:
            Dict with sections: {title, abstract, introduction, body, references}
        """
        sections = {
            "title": "",
            "abstract": "",
            "introduction": "",
            "body": "",
            "references": "",
        }
        
        # Simple heuristics for section detection
        lines = text.split('\n')
        
        # Try to find title (usually first non-empty line or marked with "Title:")
        for line in lines[:10]:
            line = line.strip()
            if line and len(line) > 10 and len(line) < 200:
                if not sections["title"]:
                    sections["title"] = line
                    break
        
        # Find abstract
        abstract_pattern = r'(?i)abstract[:\s]*(.*?)(?=\n\n|\nintroduction|1\.|\Z)'
        abstract_match = re.search(abstract_pattern, text, re.DOTALL)
        if abstract_match:
            sections["abstract"] = abstract_match.group(1).strip()
        
        # Find introduction
        intro_pattern = r'(?i)(introduction|1\.\s*introduction)[:\s]*(.*?)(?=\n\n[0-9]\.|\nii\.|\Z)'
        intro_match = re.search(intro_pattern, text, re.DOTALL)
        if intro_match:
            sections["introduction"] = intro_match.group(2).strip()[:1000]  # Limit length
        
        # Find references
        ref_pattern = r'(?i)(references|bibliography)[:\s]*(.*)'
        ref_match = re.search(ref_pattern, text, re.DOTALL)
        if ref_match:
            sections["references"] = ref_match.group(2).strip()[:2000]  # Limit length
        
        # Body is everything not in other sections
        # For simplicity, just use full text for now
        sections["body"] = text[:5000]  # Limit to first 5000 chars
        
        return sections
    
    def extract_arxiv_pdf(self, arxiv_id: str) -> Optional[Dict]:
        """
        Extract PDF from arXiv using arXiv ID.
        
        Args:
            arxiv_id: arXiv ID (e.g., "2301.00001" or "arXiv:2301.00001")
        
        Returns:
            Extracted content dict or None
        """
        # Clean arxiv ID
        arxiv_id = arxiv_id.replace("arXiv:", "").strip()
        
        # Construct PDF URL
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        
        return self.extract_from_url(pdf_url)


def extract_pdf_text(url: str, max_pages: int = 50) -> Optional[str]:
    """
    Convenience function to extract text from PDF URL.
    
    Args:
        url: PDF URL
        max_pages: Maximum pages to process
    
    Returns:
        Extracted text or None
    """
    extractor = PDFExtractor(max_pages=max_pages)
    result = extractor.extract_from_url(url)
    
    if result:
        return result["text"]
    return None


def extract_arxiv_paper(arxiv_id: str) -> Optional[Dict]:
    """
    Extract full content from arXiv paper.
    
    Args:
        arxiv_id: arXiv ID
    
    Returns:
        Dict with sections or None
    """
    extractor = PDFExtractor(max_pages=50)
    result = extractor.extract_arxiv_pdf(arxiv_id)
    
    if result:
        return result["sections"]
    return None
