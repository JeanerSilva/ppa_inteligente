# app/config.py
import logging
import streamlit as st
from rag.chat_history import generate_session_id
from rag.utils import load_indexed_files

def setup_app():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("ppa.log", encoding="utf-8"),
            logging.StreamHandler()
        ]
    )
    st.set_page_config(page_title="PPA Inteligente", page_icon="🧐")
    logging.info("Aplicativo iniciado.")

    if "indexed_files" not in st.session_state:
        st.session_state["indexed_files"] = load_indexed_files()

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if "chat_session_id" not in st.session_state:
        st.session_state.chat_session_id = generate_session_id()
