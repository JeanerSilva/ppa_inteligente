# ui/sidebar.py

import os
import streamlit as st
from settings import RETRIEVER_TOP_K, EMBEDDING_OPTIONS, TEMPERATURE
from handlers.file_handler import handle_upload_and_reindex, display_indexed_files
from pathlib import Path
def render_sidebar():
    st.sidebar.markdown("⚙️ **Configurações**")

    st.session_state["retriever_k"] = st.sidebar.slider(
        label="Número de trechos a considerar:",
        min_value=1,
        max_value=100,
        value=st.session_state.get("retriever_k", RETRIEVER_TOP_K),
        step=1
    )

    st.sidebar.markdown("🌡️ **Temperatura**")
    st.session_state["llm_temperature"] = st.sidebar.slider(
        "Temperatura da resposta:",
        min_value=0.0,
        max_value=1.0,
        value=st.session_state.get("llm_temperature", TEMPERATURE),
        step=0.1
    )

    modelo_llm = st.sidebar.radio("Modo de execução:", ["OpenAI (API)", "Ollama (servidor)"])
    st.session_state["modelo_llm"] = modelo_llm

    embed_model_label = st.sidebar.selectbox("Escolha o modelo:", list(EMBEDDING_OPTIONS.keys()))
    embed_model_name = EMBEDDING_OPTIONS[embed_model_label]
    st.session_state["embedding_model"] = embed_model_name

    st.sidebar.markdown("📂 **Índices FAISS disponíveis**")

    base_path = f"{Path().resolve()}/vectors/modelos"

    print(f"base_path {base_path}")  # Caminho absoluto resolvido
    #base_path = r"C:\SEPLAN\rag_ollama_home\vectors\modelos"
    faiss_list = [name for name in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, name))]
    selecionados = st.sidebar.multiselect("Escolha os índices:", faiss_list)
    st.session_state["faiss_selecionados"] = [os.path.join(base_path, nome) for nome in selecionados]

    handle_upload_and_reindex(embed_model_name)
    display_indexed_files()
