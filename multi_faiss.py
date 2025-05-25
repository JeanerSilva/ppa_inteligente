from langchain_community.vectorstores import FAISS
from langchain_core.vectorstores import VectorStore

class MultiFAISSRetriever:
    def __init__(self, stores, search_kwargs=None):
        self.stores = stores
        self.search_kwargs = search_kwargs or {"k": 5}

    def get_relevant_documents(self, query):
        all_results = []
        k = self.search_kwargs.get("k", 5)
        for store in self.stores:
            try:
                results = store.similarity_search(query, k=k)
                all_results.extend(results)
            except Exception as e:
                print(f"[MultiFAISS] Erro ao buscar: {e}")
        return all_results[:k]
