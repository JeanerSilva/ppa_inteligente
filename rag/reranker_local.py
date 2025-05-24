from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from langchain.schema import Document
from typing import List, Tuple

class LocalReranker:
    def __init__(self, model_name="BAAI/bge-reranker-large"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name).to(self.device)

    def rerank(self, query: str, docs: List[Document], top_k: int = 5) -> List[Document]:
        pairs = [(query, doc.page_content) for doc in docs]
        scores = self._score_pairs(pairs)
        doc_scores = list(zip(docs, scores))
        doc_scores.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, _ in doc_scores[:top_k]]

    def _score_pairs(self, pairs: List[Tuple[str, str]]) -> List[float]:
        encoded = self.tokenizer(
            [q for q, d in pairs],
            [d for q, d in pairs],
            padding=True,
            truncation=True,
            return_tensors="pt",
            max_length=512
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model(**encoded)
            scores = outputs.logits[:, 0].tolist()
        return scores


def rerank_local_reranker(query: str, docs: List[Document], top_k: int = 5) -> List[Document]:
    reranker = LocalReranker()
    return reranker.rerank(query, docs, top_k=top_k)
