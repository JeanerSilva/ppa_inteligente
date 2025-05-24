# app/handlers/file_handler.py
import os
import logging
import streamlit as st
from rag.utils import save_uploaded_files
from rag.vectorstore import create_vectorstore

def handle_upload_and_reindex(embed_model_name):
    st.sidebar.header("📄 Enviar documentos")
    uploaded_files = st.sidebar.file_uploader(
        "Arquivos: .pdf, .txt, .docx, .xlsx, .html",
        type=["pdf", "txt", "docx", "xlsx", "html"],
        accept_multiple_files=True,
    )
    if uploaded_files:
        save_uploaded_files(uploaded_files)
        st.sidebar.success("✅ Arquivos enviados com sucesso.")
        logging.info(f"{len(uploaded_files)} arquivos enviados e salvos.")

    if st.sidebar.button("🔁 Reindexar agora"):
        logging.info("Iniciando reindexação manual...")
        try:
            with st.spinner("🔄 Indexando documentos e criando vetor..."):
                db, metrics = create_vectorstore(embed_model_name)
                if db is None:
                    st.error("❌ A indexação falhou. Nenhum vetor foi criado.")
                else:
                    st.success("✅ Vetor criado com sucesso!")
                    st.session_state["index_metrics"] = metrics
        except Exception as e:
            st.error(f"❌ Erro ao criar o vetor: {e}")
            logging.exception("Erro durante criação da base vetorial.")



def display_indexed_files():
    indexed_files = st.session_state.get("indexed_files", [])
    if indexed_files:
        st.sidebar.markdown("📂 **Arquivos indexados:**", unsafe_allow_html=True)
        st.sidebar.markdown(
            "<ul style='padding-left:1.2em;'>"
            + "".join(f"<li style='font-size:0.8em;'>{f}</li>" for f in indexed_files)
            + "</ul>", unsafe_allow_html=True
        )
    else:
        st.sidebar.info("Nenhum arquivo indexado.")
