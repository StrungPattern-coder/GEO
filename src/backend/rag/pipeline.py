from typing import List, Dict, Tuple, Optional

try:
    from rank_bm25 import BM25Okapi  # type: ignore
except Exception:
    BM25Okapi = None  # type: ignore

try:
    from sentence_transformers import SentenceTransformer  # type: ignore
except Exception:
    SentenceTransformer = None  # type: ignore
try:
    from sentence_transformers import CrossEncoder  # type: ignore
except Exception:
    CrossEncoder = None  # type: ignore

from ..graph.client import GraphClient
from .llm import LLM
from .query_expansion import QueryExpander
from .query_analyzer import analyze_query, get_optimal_num_sources

# Real-time web search
try:
    from ..search.web_searcher import search_web_realtime
    _HAS_WEB_SEARCH = True
except ImportError:
    _HAS_WEB_SEARCH = False
    search_web_realtime = None  # type: ignore

SYSTEM_PROMPT = (
    "You are GEO, a Generative Engine. You synthesize a clear, concise answer "
    "grounded ONLY in the provided facts. Always be direct, avoid fluff."
)

TEMPLATE = """
System:
{system}

User question:
{question}

Facts (verbatim):
{facts}

Instructions:
- Use only these facts; if insufficient, say what else is needed.
- Provide a single paragraph answer (3-6 sentences) with a confident tone.
- Cite inline with [n] where n corresponds to the facts list numbering.
- Do not fabricate sources or data.
"""


class RAGPipeline:
    def __init__(self, graph: GraphClient, llm: LLM, use_query_expansion: bool = False):
        self.graph = graph
        self.llm = llm
        self.use_query_expansion = use_query_expansion  # DISABLED for speed
        self._embedder = None
        self._reranker = None
        self._expander = None
        
        if SentenceTransformer is not None:
            try:
                self._embedder = SentenceTransformer("all-MiniLM-L6-v2")
            except Exception:
                self._embedder = None
        if CrossEncoder is not None:
            try:
                self._reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
            except Exception:
                self._reranker = None
        
        # Initialize query expander
        if use_query_expansion:
            self._expander = QueryExpander(llm=llm)

    def _normalize(self, s: str) -> str:
        return (s or "").strip()

    def _fact_text(self, f: Dict) -> str:
        return f"{self._normalize(str(f.get('subject','')))} {self._normalize(str(f.get('predicate','')))} {self._normalize(str(f.get('object','')))}"

    def _simple_cosine(self, a_tokens: List[str], b_tokens: List[str]) -> float:
        if not a_tokens or not b_tokens:
            return 0.0
        sa, sb = set(a_tokens), set(b_tokens)
        inter = len(sa & sb)
        import math
        return inter / math.sqrt(max(1, len(sa) * len(sb)))
    
    def _add_temporal_context(self, query: str) -> str:
        """
        Enhance query with temporal keywords for recency-sensitive questions.
        E.g., "Who won the latest Oscar?" → "Who won the latest Oscar 2025 97th Academy Awards"
        """
        import time
        q_lower = query.lower()
        
        # Get current year
        current_year = time.strftime("%Y")
        
        # Check for temporal keywords
        temporal_keywords = ['latest', 'recent', 'current', 'newest', 'last', 'most recent', 'this year']
        has_temporal = any(keyword in q_lower for keyword in temporal_keywords)
        
        if not has_temporal:
            return query
        
        # Already has year? Don't add duplicate
        if current_year in query or str(int(current_year) - 1) in query:
            return query
        
        # Add year to make search more recent
        enhanced = f"{query} {current_year}"
        
        # Special cases for known events
        if 'oscar' in q_lower or 'academy award' in q_lower:
            # 97th Academy Awards in 2025
            enhanced = f"{query} 2025 97th Academy Awards"
        elif 'nobel' in q_lower:
            enhanced = f"{query} {current_year} Nobel Prize"
        elif 'election' in q_lower:
            enhanced = f"{query} {current_year} election results"
        elif 'president' in q_lower or 'prime minister' in q_lower:
            enhanced = f"{query} {current_year} current"
        
        return enhanced

    def retrieve(self, query: str, k: Optional[int] = None) -> List[Dict]:
        """
        Retrieve relevant facts from web search.
        
        Args:
            query: User's search query
            k: Number of sources (if None, dynamically determined)
            
        Returns:
            List of ranked facts/sources
        """
        # 🎯 DYNAMIC SOURCE DETERMINATION
        if k is None:
            # Analyze query complexity and determine optimal number of sources
            analysis = analyze_query(query)
            k = analysis['num_sources']
            print(f"[Query Analysis] {analysis['reasoning']}")
            print(f"[Query Analysis] Optimal sources: {k} (confidence: {analysis['confidence']:.2f})")
        else:
            print(f"[Query Analysis] Using explicit k={k}")
        
        # k is now guaranteed to be int
        assert k is not None, "k should be determined by now"
        
        # Query expansion: generate multiple query variants
        queries = [query]
        if self._expander and self.use_query_expansion:
            try:
                # Use LLM expansion only for non-mock providers (to avoid latency in dev)
                from ..config import settings
                use_llm_expansion = settings.llm_provider != "mock"
                queries = self._expander.expand(query, use_llm=use_llm_expansion)
                print(f"[Query Expansion] Original: '{query}'")
                print(f"[Query Expansion] Generated {len(queries)-1} variants: {queries[1:]}")
            except Exception as e:
                print(f"[Query Expansion] Error: {e}, falling back to original query")
                queries = [query]
        
        # Enhance query with temporal context for "latest" questions
        enhanced_query = self._add_temporal_context(query)
        if enhanced_query != query:
            print(f"[Temporal Enhancement] '{query}' → '{enhanced_query}'")
            queries = [enhanced_query] + queries  # Prioritize temporally-enhanced query
        
        # **REAL-TIME WEB SEARCH** - Search the live web for each query variant
        all_facts: Dict[str, Dict] = {}  # Use dict to deduplicate by fact ID
        
        if _HAS_WEB_SEARCH and search_web_realtime:
            # Use real-time web search (like Perplexity!)
            from ..config import settings
            search_provider = settings.search_provider if hasattr(settings, 'search_provider') else "duckduckgo"
            
            print(f"[Retrieval] Using REAL-TIME web search (provider: {search_provider})")
            for q in queries:
                try:
                    web_facts = search_web_realtime(q, provider=search_provider, num_results=k)
                    for f in web_facts:
                        fact_id = f.get("id", f"{f.get('subject', '')}_{f.get('object', '')}")
                        if fact_id not in all_facts:
                            all_facts[fact_id] = f
                except Exception as e:
                    print(f"[Retrieval] Web search error for '{q}': {e}")
        else:
            # Fallback to database search (old behavior)
            print(f"[Retrieval] Web search not available, using database fallback")
            for q in queries:
                terms = [t for t in q.lower().split() if len(t) > 2]
                facts = self.graph.search_facts(terms, limit=max(k * 3, 16))
                for f in facts:
                    # Use a composite key to deduplicate
                    fact_id = f"{f.get('subject', '')}_{f.get('predicate', '')}_{f.get('object', '')}"
                    if fact_id not in all_facts:
                        all_facts[fact_id] = f
                    else:
                        # Keep the fact with higher score
                        existing_score = float(all_facts[fact_id].get("score", 0.0))
                        new_score = float(f.get("score", 0.0))
                        if new_score > existing_score:
                            all_facts[fact_id] = f
        
        base = list(all_facts.values())
        print(f"[Retrieval] Retrieved {len(base)} unique facts from {len(queries)} query variants")
        
        texts = [self._fact_text(f) for f in base]
        prev_scores = [float(f.get("score", 0.0)) for f in base]

        # BM25
        if BM25Okapi is not None and texts:
            tokenized = [t.lower().split() for t in texts]
            bm25 = BM25Okapi(tokenized)
            bm25_scores = bm25.get_scores(query.lower().split()).tolist()
        else:
            bm25_scores = [0.0] * len(texts)

        # Embeddings if available, else token cosine
        if self._embedder is not None and texts:
            try:
                q_emb = self._embedder.encode(query, normalize_embeddings=True)
                d_emb = self._embedder.encode(texts, normalize_embeddings=True)
                emb_scores = (d_emb @ q_emb).tolist()
            except Exception:
                q_tok = query.lower().split()
                emb_scores = [self._simple_cosine(q_tok, t.lower().split()) for t in texts]
        else:
            q_tok = query.lower().split()
            emb_scores = [self._simple_cosine(q_tok, t.lower().split()) for t in texts]

        # Tiny reranker: combine source score + bm25 + embedding-like score
        combo = []
        for i, _ in enumerate(base):
            s = 0.5 * prev_scores[i] + 0.3 * bm25_scores[i] + 0.7 * emb_scores[i]
            combo.append((s, i))
        combo.sort(reverse=True)
        prelim = [base[i] for (s, i) in combo[: max(k * 2, 10)]]
        # Optional cross-encoder rerank
        if self._reranker is not None and prelim:
            pairs = [(query, self._fact_text(f)) for f in prelim]
            try:
                scores = self._reranker.predict(pairs).tolist()
            except Exception:
                scores = [0.0] * len(prelim)
            order = sorted(range(len(prelim)), key=lambda i: scores[i], reverse=True)
            top = [prelim[i] for i in order[:k]]
        else:
            top = prelim[:k]
        for idx, f in enumerate(top, start=1):
            f["idx"] = idx
        return top

    def format_facts(self, facts: List[Dict]) -> str:
        lines = []
        for f in facts:
            n = f.get("idx", "-")
            lines.append(
                f"[{n}] ({f.get('truth_weight', 0.5):.2f}) [{f.get('predicate')}] {f.get('subject')} -> {f.get('object')} | {f.get('source_url')}"
            )
        return "\n".join(lines)

    def _is_conversational(self, query: str) -> tuple[bool, str]:
        """
        Use LLM to intelligently detect if query is conversational or informational.
        Returns (is_conversational, category) where category is one of:
        - 'greeting', 'appreciation', 'casual_chat', 'about_assistant', 'farewell'
        - or 'search' if it needs web search
        """
        q_lower = query.lower().strip()
        
        # Quick pattern matching for very obvious cases (performance optimization)
        obvious_greetings = ['hi', 'hello', 'hey', 'yo']
        obvious_thanks = ['thanks', 'thank you', 'thx', 'ty']
        obvious_bye = ['bye', 'goodbye', 'cya']
        
        if q_lower in obvious_greetings:
            return (True, 'greeting')
        if q_lower in obvious_thanks:
            return (True, 'appreciation')
        if q_lower in obvious_bye:
            return (True, 'farewell')
        
        # For more complex queries, use LLM classification (only for mock and non-API providers to save costs)
        from ..config import settings
        if settings.llm_provider == "mock":
            # Fallback to rule-based for mock
            return self._rule_based_classification(q_lower)
        
        # Use LLM for intelligent classification
        classification_prompt = f"""You are a query classifier. Determine if the user's message is:
1. CONVERSATIONAL - greetings, thanks, casual chat, questions about you as an assistant, farewells
2. SEARCH - questions requiring factual information, explanations, current events, how-to, etc.

Examples:
- "Hi" → CONVERSATIONAL (greeting)
- "Thanks!" → CONVERSATIONAL (appreciation)
- "How are you?" → CONVERSATIONAL (casual_chat)
- "Who are you?" → CONVERSATIONAL (about_assistant)
- "Tell me about yourself" → CONVERSATIONAL (about_assistant)
- "What can you do?" → CONVERSATIONAL (about_assistant)
- "What is Python?" → SEARCH
- "How does photosynthesis work?" → SEARCH
- "Who is the president?" → SEARCH
- "Tell me about quantum physics" → SEARCH
- "Latest news on AI" → SEARCH

User message: "{query}"

Respond with ONLY ONE WORD: either "CONVERSATIONAL" or "SEARCH"
"""
        
        try:
            # Use a very short generation (1-2 tokens)
            result = self.llm.generate(classification_prompt).strip().upper()
            
            if "CONVERSATIONAL" in result:
                # Determine subcategory
                category = self._determine_conversational_category(q_lower)
                return (True, category)
            else:
                return (False, 'search')
        except:
            # Fallback to rule-based if LLM fails
            return self._rule_based_classification(q_lower)
    
    def _rule_based_classification(self, q_lower: str) -> tuple[bool, str]:
        """Fallback rule-based classification."""
        greetings = ['hi', 'hello', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening', 'howdy', 'sup', "what's up", 'yo']
        appreciations = ['thanks', 'thank you', 'thx', 'ty', 'appreciate it', 'awesome', 'great', 'cool', 'nice', 'perfect', 'excellent', 'amazing']
        casual = ['how are you', 'how r u', 'wassup', 'whats good', 'hows it going', 'ok', 'okay']
        farewells = ['bye', 'goodbye', 'see you', 'later', 'cya', 'good night']
        about_assistant = [
            'who are you', 'what are you', 'tell me about yourself', 'what can you do', 
            'your capabilities', 'introduce yourself', 'what do you do', 'what exactly do you do',
            'how are you different', 'difference between you', 'whats the difference',
            'compare yourself', 'why use you', 'what makes you special', 'how do you work'
        ]
        
        # Check patterns
        for pattern in greetings:
            if q_lower.startswith(pattern) and len(q_lower) < 30:
                return (True, 'greeting')
        
        for pattern in appreciations:
            if pattern in q_lower and len(q_lower) < 40:
                return (True, 'appreciation')
        
        for pattern in casual:
            if pattern in q_lower:
                return (True, 'casual_chat')
        
        for pattern in farewells:
            if pattern in q_lower and len(q_lower) < 30:
                return (True, 'farewell')
        
        for pattern in about_assistant:
            if pattern in q_lower:
                return (True, 'about_assistant')
        
        return (False, 'search')
    
    def _determine_conversational_category(self, q_lower: str) -> str:
        """Determine the specific type of conversational query."""
        if any(g in q_lower for g in ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening', 'greetings']):
            return 'greeting'
        if any(a in q_lower for a in ['thanks', 'thank you', 'thx', 'appreciate']):
            return 'appreciation'
        if any(b in q_lower for b in ['bye', 'goodbye', 'see you', 'later', 'cya', 'good night']):
            return 'farewell'
        if any(about in q_lower for about in [
            'who are you', 'what are you', 'tell me about yourself', 'what can you do', 
            'your capabilities', 'what do you do', 'what exactly do you do',
            'how are you different', 'difference between you', 'whats the difference',
            'compare yourself', 'what makes you special'
        ]):
            return 'about_assistant'
        return 'casual_chat'
    
    def _get_conversational_response(self, query: str, category: str) -> str:
        """Generate contextual response based on conversation category."""
        
        if category == 'greeting':
            return "Hello! 👋 I'm GEO, your AI-powered search assistant. I search the web in real-time to give you accurate, trustworthy answers with citations from credible sources. What would you like to know?"
        
        elif category == 'appreciation':
            return "You're very welcome! 😊 I'm happy I could help. Feel free to ask me anything else—I'm here to search the web and provide you with reliable information."
        
        elif category == 'farewell':
            return "Goodbye! 👋 Come back anytime you need answers. Have a wonderful day!"
        
        elif category == 'about_assistant':
            return """I'm **GEO (Generative Engine Optimization)** 🚀, an AI-powered search engine that's fundamentally different from ChatGPT, Google, and Perplexity AI.

## 🎯 **What I Do:**
I combine **real-time web search** with **local AI processing** to give you accurate, verifiable answers with transparent source citations.

## 🔥 **How I'm Different:**

### **vs Google Search:**
✅ **Direct Answers** - I synthesize information into one answer, not 10 blue links
✅ **Trust Transparency** - I show domain reputation scores (0.95 for .edu/.gov)
✅ **Inline Citations** - Every fact has [1][2][3] citations you can verify
✅ **Privacy** - No tracking, no ads, no data collection

### **vs ChatGPT:**
✅ **Real-Time Web** - I search the live web on every query (ChatGPT has knowledge cutoff)
✅ **No Hallucinations** - Every answer is grounded in real sources with URLs
✅ **Local AI** - I use Ollama (runs on your machine), ChatGPT sends data to OpenAI
✅ **Source Verification** - You can click [1][2][3] to verify every claim

### **vs Perplexity AI:**
✅ **Transparent Trust** - I explain why each source is trusted (domain scoring algorithm is open)
✅ **100% Free & Open Source** - Perplexity charges $20/month, I'm MIT licensed
✅ **Privacy-First** - Everything runs locally, Perplexity is cloud-only
✅ **GEO Protocol** - Publishers can submit verified facts (like robots.txt for AI age)

## ⚡ **My Core Features:**
🔍 **Real-time Web Search** - DuckDuckGo, Tavily, SerpAPI, Google (your choice)
🎯 **Domain Reputation Scoring** - .gov (0.90), .edu (0.85), Nature/ArXiv (0.95)
📚 **Inline Citations** - [1][2][3] linked to exact sources
🤖 **Local LLM** - Ollama (Qwen2.5, Llama3, Mistral) runs on your hardware
🔒 **Privacy** - Zero tracking, no accounts, no data sent to cloud
📊 **Transparent Algorithms** - All trust scoring is open source

## 💡 **Try asking me:**
- "What are the latest developments in quantum computing?" (real-time search)
- "Is climate change real?" (trust-weighted sources)
- "Explain CRISPR gene editing" (cited from scientific sources)

I'm not just another chatbot—I'm a **verifiable**, **transparent**, and **privacy-respecting** AI search engine. Ask me anything! 🚀"""
        
        elif category == 'casual_chat':
            return "I'm doing great, thanks for asking! 🤖 I'm ready to help you find information. I specialize in searching the web in real-time and providing accurate answers with sources. What can I look up for you?"
        
        else:
            return "I'm GEO, your AI search assistant! 🚀 Ask me anything and I'll search the web in real-time to give you accurate answers with credible sources."

    def answer(self, query: str, k: Optional[int] = None) -> Tuple[str, List[Dict]]:
        """
        Generate answer for a query.
        
        Args:
            query: User's search query
            k: Number of sources (if None, dynamically determined based on query complexity)
            
        Returns:
            Tuple of (answer, facts)
        """
        # Check if it's conversational first
        is_conversational, category = self._is_conversational(query)
        if is_conversational:
            return self._get_conversational_response(query, category), []
        
        # Retrieve with dynamic source determination
        facts = self.retrieve(query, k)
        prompt = TEMPLATE.format(system=SYSTEM_PROMPT, question=query, facts=self.format_facts(facts))
        ans = self.llm.generate(prompt)
        return ans, facts
    
    def answer_stream(self, query: str, k: Optional[int] = None):
        """
        Stream answer generation token by token.
        
        Args:
            query: User's search query
            k: Number of sources (if None, dynamically determined based on query complexity)
        """
        # Check if it's conversational first
        is_conversational, category = self._is_conversational(query)
        if is_conversational:
            # Yield empty facts
            yield {"type": "facts", "facts": []}
            # Yield conversational response
            response = self._get_conversational_response(query, category)
            yield {"type": "text", "content": response}
            return
        
        facts = self.retrieve(query, k)
        prompt = TEMPLATE.format(system=SYSTEM_PROMPT, question=query, facts=self.format_facts(facts))
        
        # Yield facts first
        yield {"type": "facts", "facts": facts}
        
        # Then stream the answer
        for chunk in self.llm.generate_stream(prompt):
            yield {"type": "text", "content": chunk}
