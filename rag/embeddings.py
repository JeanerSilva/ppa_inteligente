from langchain.embeddings import HuggingFaceEmbeddings
import torch
import logging

print(f"torch.cuda.is_available(): {torch.cuda.is_available()}")

def load_embeddings(model_name: str):
    #device = "cuda" if torch.cuda.is_available() else "cpu"
    device = "cpu"
    normalize_embeddings = True
    logging.info(f"Carregando embeddings com modelo {model_name}, device {device} e normalizador {normalize_embeddings}")
    return HuggingFaceEmbeddings(
        model_name=model_name,
        #model_kwargs={"device": device},
        encode_kwargs={"normalize_embeddings": normalize_embeddings}
    )

