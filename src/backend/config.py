import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Settings:
    neo4j_uri: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user: str = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password: str = os.getenv("NEO4J_PASSWORD", "neo4j")

    llm_provider: str = os.getenv("LLM_PROVIDER", "mock")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")

    arxiv_query: str = os.getenv("ARXIV_QUERY", "cat:cs.AI")
    rss_feeds: str = os.getenv("RSS_FEEDS", "")
    geo_feeds: str = os.getenv("GEO_FEEDS", "")
    api_key: str = os.getenv("GEO_API_KEY", "")
    
    # Real-time web search settings
    search_provider: str = os.getenv("SEARCH_PROVIDER", "duckduckgo")  # duckduckgo, tavily, serpapi, google
    tavily_api_key: str = os.getenv("TAVILY_API_KEY", "")
    serpapi_key: str = os.getenv("SERPAPI_KEY", "")
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    google_cse_id: str = os.getenv("GOOGLE_CSE_ID", "")
    
    # Production settings
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    use_json_logging: bool = os.getenv("USE_JSON_LOGGING", "false").lower() == "true"
    enable_metrics: bool = os.getenv("ENABLE_METRICS", "true").lower() == "true"

settings = Settings()
