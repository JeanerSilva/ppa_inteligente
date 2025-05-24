# rag/llm_loader.py

import os
from dotenv import load_dotenv
from langchain_community.llms import LlamaCpp
from langchain_ollama import OllamaLLM
from langchain_openai import ChatOpenAI
from settings import TEMPERATURE, LLM_MODEL, OPENAI_MODEL,LLM_GGUF
import streamlit as st

load_dotenv()
openai_key = os.getenv("OPENAI_API_KEY")

@st.cache_resource(show_spinner="🔄 Carregando modelo LLM...")
def load_llm(modelo_llm: str, temperature=0.0):

    assert os.path.exists(LLM_GGUF), "Modelo não encontrado!"

    #if modelo_llm == "GGUF (offline)":
    #    return LlamaCpp(
    #        model_path=LLM_GGUF,

    #        n_ctx=4096,
    #        n_batch=64,
    #        temperature=TEMPERATURE,
    #        verbose=False
    #    )

    #el
    if modelo_llm == "Ollama (servidor)":
        base_url = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        return OllamaLLM(
            model=LLM_MODEL,
            base_url=base_url,
            temperature=TEMPERATURE
        )

    elif modelo_llm == "OpenAI (API)":
        if not openai_key:
            raise ValueError("OPENAI_API_KEY não definido no ambiente.")
        return ChatOpenAI(
            model=OPENAI_MODEL,
            temperature=TEMPERATURE,
            api_key=openai_key
        )

    else:
        raise ValueError(f"Modelo LLM desconhecido: {modelo_llm}")
