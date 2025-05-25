from langchain.embeddings import HuggingFaceEmbeddings
import torch

print(f"torch.cuda.is_available(): {torch.cuda.is_available()}")

def load_embeddings(model_name: str):
    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={
            "device": "cuda" if torch.cuda.is_available() else "cpu",
        },
        encode_kwargs={"normalize_embeddings": True}
    )
