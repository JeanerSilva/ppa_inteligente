# multi_faiss.py

from typing import List
from langchain.schema import BaseRetriever, Document
from langchain_core.documents import Document  # compatível com algumas versões
from pydantic import Field

class MultiFAISSRetriever(BaseRetriever):
    retrievers: List[BaseRetriever] = Field(...)
    k: int = Field(default=5)

    def get_relevant_documents(self, query: str) -> List[Document]:
        all_docs = []
        for retriever in self.retrievers:
            try:
                docs = retriever.get_relevant_documents(query)
                all_docs.extend(docs)
            except Exception as e:
                print(f"[ERRO] Retriever falhou: {e}")
        return all_docs[:self.k]

    async def aget_relevant_documents(self, query: str) -> List[Document]:
        return self.get_relevant_documents(query)
