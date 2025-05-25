# config.py
import logging
import streamlit as st
import tempfile
from rag.chat_history import generate_session_id
from rag.utils import load_indexed_files

def setup_app():

    st.set_page_config(page_title="PPA Inteligente", page_icon="🧐", layout="wide")
    # Opcional: debug para comparar chunks antes e depois do rerank
    st.sidebar.markdown("🧪 **Debug de Reranker**")
    st.sidebar.checkbox("🔬 .session_state.get("usogging.FileHandler(log_path, mode="a")
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    print(f"📂 Logging para: {log_path}")
    logger.info("✅ Aplicativo iniciado.")


    if "indexed_files" not in st.session_state:
        st.session_state["indexed_files"] = load_indexed_files()

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if "chat_session_id" not in st.session_state:
        st.session_state.chat_session_id = generate_session_id()
