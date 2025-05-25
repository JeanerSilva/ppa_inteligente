from typing import List
from langchain.schema import BaseRetriever, Document
from pydantic import Field

class MultiFAISSRetriever(BaseRetriever):
    retrievers: List[BaseRetriever] = Field(...)
    k: int = Field(default=5)

    def _get_relevant_documents(self, query: str) -> List[Document]:
        all_docs = []
        for retriever in self.retrievers:
            docs = retriever.invoke(query)
            all_docs.extend(docs)
        return all_docs
