import json
from src.backend.graph.client import GraphClient
from src.backend.ingest.ingestor import Ingestor
from src.backend.rag.llm import LLM
from src.backend.rag.pipeline import RAGPipeline


def smoke_test():
    g = GraphClient()
    g.ensure_indexes()
    ing = Ingestor(g)
    ing.run_all()

    llm = LLM()
    rag = RAGPipeline(g, llm)
    ans, facts = rag.answer("Summarize the latest on cs.AI arXiv.")
    print("Answer:\n", ans)
    print("Facts:")
    print(json.dumps(facts[:3], indent=2))

if __name__ == "__main__":
    smoke_test()
