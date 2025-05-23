from langchain_huggingface import HuggingFaceEmbeddings
import torch


def load_embeddings(model_name: str):
    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={
            "device": "cuda" if torch.cuda.is_available() else "cpu",
        },
        encode_kwargs={"normalize_embeddings": True}
    )
